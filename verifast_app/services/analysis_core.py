import os
import json
import logging
import re
from typing import List

import wikipediaapi  # type: ignore
import textstat  # type: ignore

# Optional spacy import - graceful fallback if not available
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None  # type: ignore

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from pydantic import ValidationError

from ..models import Tag
from ..decorators import with_fallback
from ..pydantic_models.llm import MasterAnalysisResponse
from .model_selector import model_selector

logger = logging.getLogger(__name__)

# Configure the API key from environment variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Simple per-process rate limiter by model
import time
from collections import deque

# Map model groups to official limits (RPM, RPD)
# Source: user-provided limits table
_LIMITS = {
    'gemini-2.5-pro':      (int(os.environ.get('GEMINI_PRO_RPM', 5)),   int(os.environ.get('GEMINI_PRO_RPD', 100))),
    'gemini-2.5-flash':    (int(os.environ.get('GEMINI_FLASH_RPM', 10)), int(os.environ.get('GEMINI_FLASH_RPD', 250))),
    'gemini-2.5-flash-lite': (int(os.environ.get('GEMINI_FLASH_LITE_RPM', 15)), int(os.environ.get('GEMINI_FLASH_LITE_RPD', 1000))),
    'gemini-2.0-flash':    (int(os.environ.get('GEMINI20_FLASH_RPM', 15)), int(os.environ.get('GEMINI20_FLASH_RPD', 200))),
    'gemini-2.0-flash-lite': (int(os.environ.get('GEMINI20_FLASH_LITE_RPM', 30)), int(os.environ.get('GEMINI20_FLASH_LITE_RPD', 200))),
}

# Track timestamps for per-minute and per-day windows per model group
_minute_times = {k: deque() for k in _LIMITS}
_day_times = {k: deque() for k in _LIMITS}


def _model_group(model_name: str) -> str:
    name = (model_name or '').lower()
    if '2.5' in name and 'pro' in name:
        return 'gemini-2.5-pro'
    if '2.5' in name and 'flash-lite' in name:
        return 'gemini-2.5-flash-lite'
    if '2.5' in name and 'flash' in name:
        return 'gemini-2.5-flash'
    if '2.0' in name and 'flash-lite' in name:
        return 'gemini-2.0-flash-lite'
    if '2.0' in name and 'flash' in name:
        return 'gemini-2.0-flash'
    # default to 2.5-flash limits
    return 'gemini-2.5-flash'


def _throttle(model_name: str):
    """Block until under RPM and fail fast on daily cap for given model group.
    For per-minute, we sleep to queue locally. If daily cap is reached, raise to let Celery retry later.
    """
    group = _model_group(model_name)
    rpm, rpd = _LIMITS.get(group, (10, 250))
    now = time.time()

    # Per-minute window
    mt = _minute_times.setdefault(group, deque())
    while mt and now - mt[0] > 60:
        mt.popleft()
    if len(mt) >= rpm:
        sleep_for = 60 - (now - mt[0])
        if sleep_for > 0:
            logger.info(f"Rate limit (RPM) reached for {group}; sleeping {sleep_for:.1f}s")
            time.sleep(sleep_for)
    # Per-day window
    dt = _day_times.setdefault(group, deque())
    while dt and now - dt[0] > 86400:
        dt.popleft()
    if rpd and len(dt) >= rpd:
        # Don't spin-wait for day window; signal retry to task layer
        logger.warning(f"Daily cap (RPD) reached for {group}; signaling retry")
        raise google_exceptions.ResourceExhausted(f"Daily cap reached for {group}")

    # Record reservation timestamps (approximate in-process)
    mt.append(time.time())
    dt.append(time.time())


def calculate_optimal_question_count(article_text: str, min_questions: int = 5, max_questions: int = 30) -> int:
    if not article_text or not article_text.strip():
        return min_questions
    word_count = len(article_text.split())
    base_questions = max(min_questions, word_count // 250)
    sentences = len([s for s in article_text.split('.') if s.strip()])
    if sentences > 0:
        avg_sentence_length = word_count / sentences
        if avg_sentence_length > 20:
            base_questions = int(base_questions * 1.2)
    paragraphs = len([p for p in article_text.split('\n\n') if p.strip()])
    if paragraphs > 10:
        base_questions = int(base_questions * 1.1)
    optimal_count = min(max(base_questions, min_questions), max_questions)
    logger.info(f"Article analysis: {word_count} words, {sentences} sentences, {paragraphs} paragraphs → {optimal_count} questions")
    return optimal_count


@with_fallback(fallback_return={'quiz': [], 'tags': []})
def generate_master_analysis(model_name: str, entity_list: List[str], article_text: str, language: str = 'en', source: str = 'user_submission') -> dict:
    if not article_text:
        logger.warning("generate_master_analysis called with empty article_text.")
        return {'quiz': [], 'tags': []}

    question_count = calculate_optimal_question_count(article_text)
    word_count = len(article_text.split())
    logger.info(f"Generating {question_count} questions for article with {word_count} words")

    # Calculate reading level for model selection
    try:
        reading_level = textstat.flesch_kincaid_grade(article_text)
    except Exception:
        reading_level = 50.0  # Default moderate level

    # Use model selector to get the best available model
    selected_model, model_config = model_selector.select_model(
        reading_level=reading_level,
        word_count=word_count,
        language=language,
        source=source
    )
    
    # Override the passed model_name with the selected one
    actual_model_name = selected_model
    logger.info(f"Model selector chose: {actual_model_name} (requested: {model_name})")
    
    # Get optimized generation config for the selected model
    generation_config = model_selector.get_generation_config(model_config, question_count)

    # Try the selected model first, then fallback models if needed
    models_to_try = [actual_model_name]
    
    # Add fallback models if the selected one fails
    fallback_models = ["gemini-2.5-flash", "gemma-3-27b-it"]
    for fallback in fallback_models:
        if fallback != actual_model_name and fallback in model_selector.models:
            models_to_try.append(fallback)

    last_error = None
    
    # Prepare prompts
    prompts = {
        'en': f"""Analyze the following article and generate a single JSON object with comprehensive quiz questions and tags.

**QUIZ GENERATION INSTRUCTIONS:**
1. First, identify ALL main ideas, thesis statements, and key concepts in the article
2. Create ONE comprehensive multiple-choice question for EACH unique main idea
3. If a main idea is repeated multiple times, create only ONE question that covers that concept thoroughly
4. Ensure questions cover the breadth and depth of the article's content
5. Generate exactly {question_count} questions based on the article's length and complexity
6. Each question should test understanding of a distinct main point or concept

**TAGS GENERATION INSTRUCTIONS:**
Perform co-reference resolution on the provided entities and select the 5-7 most important canonical names.

**Article Text:**
{article_text[:6000]}

**Potential Entities Found:**
{entity_list}

**Required JSON Format:**
{{
    "quiz": [
        {{
            "question": "Question text about main idea 1",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Correct option text"
        }},
        // ... exactly {question_count} questions covering all main ideas
    ],
    "tags": ["canonical_entity_1", "canonical_entity_2", ...]
}}

Return only the raw JSON object and nothing else.""",
        'es': f"""Analiza el siguiente artículo y genera un único objeto JSON con preguntas de quiz comprehensivas y etiquetas.

**INSTRUCCIONES PARA GENERACIÓN DE QUIZ:**
1. Primero, identifica TODAS las ideas principales, declaraciones de tesis y conceptos clave del artículo
2. Crea UNA pregunta comprehensiva de opción múltiple para CADA idea principal única
3. Si una idea principal se repite múltiples veces, crea solo UNA pregunta que cubra ese concepto completamente
4. Asegúrate de que las preguntas cubran la amplitud y profundidad del contenido del artículo
5. Genera exactamente {question_count} preguntas basadas en la longitud y complejidad del artículo
6. Cada pregunta debe evaluar la comprensión de un punto principal o concepto distinto

**INSTRUCCIONES PARA GENERACIÓN DE ETIQUETAS:**
Realiza resolución de correferencia en las entidades proporcionadas y selecciona los 5-7 nombres canónicos más importantes.

**Texto del Artículo:**
{article_text[:6000]}

**Entidades Potenciales Encontradas:**
{entity_list}

**Formato JSON Requerido:**
{{
    "quiz": [
        {{
            "question": "Texto de pregunta sobre idea principal 1",
            "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
            "answer": "Texto de opción correcta"
        }},
        // ... exactamente {question_count} preguntas cubriendo todas las ideas principales
    ],
    "tags": ["entidad_canónica_1", "entidad_canónica_2", ...]
}}

Devuelve solo el objeto JSON sin formato y nada más.""",
    }

    prompt = prompts.get(language, prompts['en'])
    
    # Try each model in the fallback chain
    for attempt, try_model_name in enumerate(models_to_try):
        try:
            logger.info(f"Attempt {attempt + 1}: Trying model {try_model_name}")
            
            # Update generation config for this specific model
            if try_model_name in model_selector.models:
                current_config = model_selector.models[try_model_name]
                generation_config = model_selector.get_generation_config(current_config, question_count)
            
            model = genai.GenerativeModel(
                try_model_name,
                generation_config=generation_config,  # type: ignore
            )

            logger.info(f"Sending request to {try_model_name} for master analysis...")
            _throttle(model_name)
            chat_session = model.start_chat()
            response = chat_session.send_message(prompt)
            logger.info(f"Successfully received response from {try_model_name}")
            
            # Safely extract text from response (handle empty Parts)
            raw_text = None
            try:
                raw_text = response.text
            except Exception:
                raw_text = None
                
            if not raw_text:
                try:
                    candidates = getattr(response, 'candidates', []) or []
                    for c in candidates:
                        parts = getattr(getattr(c, 'content', None), 'parts', None) or getattr(c, 'parts', None) or []
                        for p in parts:
                            if hasattr(p, 'text') and p.text:
                                raw_text = p.text
                                break
                        if raw_text:
                            break
                except Exception:
                    raw_text = None
                    
            if not raw_text:
                logger.warning(f"Model {try_model_name} returned no text parts")
                last_error = "Empty response parts"
                continue

            # Clean and parse JSON
            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            data = json.loads(clean_text)
            
            # Validate with Pydantic
            validated_data = MasterAnalysisResponse.model_validate(data)
            logger.info(f"Successfully validated LLM response from {try_model_name}. Quiz: {len(validated_data.quiz)}, Tags: {len(validated_data.tags)}")
            
            # Record success for model selector
            model_selector.record_model_success(try_model_name)
            
            return validated_data.model_dump()

        except google_exceptions.ResourceExhausted as e:
            logger.warning(f"Model {try_model_name} quota exceeded: {e}")
            model_selector._record_model_failure(try_model_name, f"Quota exceeded: {e}")
            last_error = f"Quota exceeded: {e}"
            continue
            
        except google_exceptions.NotFound as e:
            logger.error(f"Model {try_model_name} not found: {e}")
            model_selector._record_model_failure(try_model_name, f"Model not found: {e}")
            last_error = f"Model not found: {e}"
            continue
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {try_model_name}: {e}")
            logger.debug(f"Raw response was: {raw_text[:500] if 'raw_text' in locals() else 'None'}...")
            last_error = f"JSON decode error: {e}"
            continue
            
        except ValidationError as e:
            logger.error(f"Pydantic validation failed for {try_model_name}: {e}")
            logger.debug(f"Invalid data was: {clean_text[:500] if 'clean_text' in locals() else 'None'}...")
            last_error = f"Validation error: {e}"
            continue
            
        except Exception as e:
            logger.error(f"Unexpected error with {try_model_name}: {e}", exc_info=True)
            model_selector._record_model_failure(try_model_name, f"Unexpected error: {e}")
            last_error = f"Unexpected error: {e}"
            continue

    # If all models failed, raise the last error
    logger.error(f"All models failed. Last error: {last_error}")
    raise Exception(f"All fallback models failed. Last error: {last_error}")


# Load spaCy models if available
if SPACY_AVAILABLE:
    try:
        nlp_en = spacy.load("en_core_web_sm")
        nlp_es = spacy.load("es_core_news_sm")
    except OSError:
        logger.warning("spaCy models not found - NLP features will be disabled")
        SPACY_AVAILABLE = False
        nlp_en = None
        nlp_es = None
else:
    nlp_en = None
    nlp_es = None

# Re-initialize Wikipedia API clients
wiki_en = wikipediaapi.Wikipedia(language='en', user_agent='VeriFastApp/1.0')
wiki_es = wikipediaapi.Wikipedia(language='es', user_agent='VeriFastApp/1.0')


@with_fallback(fallback_return={"reading_score": 0, "people": [], "organizations": [], "money_mentions": []})
def analyze_text_content(text: str, language: str = 'en') -> dict:
    try:
        reading_score = textstat.flesch_kincaid_grade(text)
    except (KeyError, Exception) as e:
        logger.warning(f"Error calculating reading score: {e}")
        reading_score = 0

    people = []
    orgs = []
    money = []

    if SPACY_AVAILABLE and nlp_en and nlp_es:
        try:
            nlp = nlp_es if language == 'es' else nlp_en
            doc = nlp(text)
            people = list(set([ent.text for ent in doc.ents if ent.label_ == 'PERSON']))
            orgs = list(set([ent.text for ent in doc.ents if ent.label_ == 'ORG']))
            money = [ent.text for ent in doc.ents if ent.label_ == 'MONEY']
        except Exception as e:
            logger.warning(f"Error in NLP analysis: {e}")

    return {
        "reading_score": reading_score,
        "people": people,
        "organizations": orgs,
        "money_mentions": money
    }


@with_fallback(fallback_return=[])
def get_valid_wikipedia_tags(entities: List[str], language: str = 'en') -> list:
    wiki = wiki_es if language == 'es' else wiki_en
    canonical_name_map = {}

    
    flat_entities = [item for sublist in entities for item in (sublist if isinstance(sublist, list) else [sublist]) if isinstance(item, str)]
    for entity_name in set(flat_entities):
        if not isinstance(entity_name, str) or not entity_name.strip():
            logger.warning(f"Invalid entity name skipped: {entity_name}")
            continue

        try:
            page_obj = wiki.page(entity_name)
            if page_obj.exists():
                canonical_name = page_obj.title
                canonical_name_map[entity_name] = canonical_name
            else:
                logger.warning(f"Wikipedia page for '{entity_name}' does not exist. Skipping canonicalization.")
        except Exception as e:
            logger.warning(f"Wikipedia API error for tag '{entity_name}': {e}. Skipping canonicalization.")
            continue

    unique_canonical_names = set(canonical_name_map.values())
    validated_tags = []

    for canonical_name in unique_canonical_names:
        tag, created = Tag.objects.get_or_create(name=canonical_name)
        if created:
            logger.info(f"Created new canonical tag: '{canonical_name}'.")
        validated_tags.append(tag)

    return validated_tags


def find_largest_monetary_tag(money_mentions: list) -> str | None:
    if not money_mentions:
        return None

    max_value = 0.0
    for mention in money_mentions:
        numeric_part = re.sub(r'[$,€£,]', '', mention).lower()
        value = 0.0
        if 'billion' in numeric_part:
            value = float(re.findall(r'[\d\.]+', numeric_part)[0]) * 1_000_000_000
        elif 'million' in numeric_part:
            value = float(re.findall(r'[\d\.]+', numeric_part)[0]) * 1_000_000
        elif re.findall(r'[\d\.]+', numeric_part):
            value = float(re.findall(r'[\d\.]+', numeric_part)[0])
        if value > max_value:
            max_value = value

    if max_value > 0:
        return f"Value: ${max_value:,.0f}"
    return None
