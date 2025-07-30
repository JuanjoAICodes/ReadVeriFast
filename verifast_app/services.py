import os
import json
import logging
import time
import wikipediaapi # type: ignore
import textstat # type: ignore
import re
import google.generativeai as genai
from pydantic import ValidationError

from .models import Tag
from .decorators import with_fallback
from .pydantic_models.llm import MasterAnalysisResponse

# Optional spacy import - graceful fallback if not available
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("spaCy not available - NLP features will be disabled")


# Configure the API key from environment variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Get a logger instance
logger = logging.getLogger(__name__)


def calculate_optimal_question_count(article_text: str, min_questions: int = 5, max_questions: int = 30) -> int:
    """
    Calculate optimal number of questions based on article characteristics.
    
    Args:
        article_text: The full text of the article
        min_questions: Minimum number of questions to generate
        max_questions: Maximum number of questions to generate
        
    Returns:
        Optimal number of questions for the article
    """
    if not article_text or not article_text.strip():
        return min_questions
    
    word_count = len(article_text.split())
    
    # Base calculation: 1 question per 200-300 words
    base_questions = max(min_questions, word_count // 250)
    
    # Adjust for content complexity
    sentences = len([s for s in article_text.split('.') if s.strip()])
    if sentences > 0:
        avg_sentence_length = word_count / sentences
        if avg_sentence_length > 20:  # Complex sentences
            base_questions = int(base_questions * 1.2)
    
    # Adjust for article structure (more paragraphs = more topics)
    paragraphs = len([p for p in article_text.split('\n\n') if p.strip()])
    if paragraphs > 10:  # Well-structured long article
        base_questions = int(base_questions * 1.1)
    
    # Cap at maximum and minimum
    optimal_count = min(max(base_questions, min_questions), max_questions)
    
    logger.info(f"Article analysis: {word_count} words, {sentences} sentences, {paragraphs} paragraphs → {optimal_count} questions")
    
    return optimal_count


@with_fallback(fallback_return={'quiz': [], 'tags': []})
def generate_master_analysis(model_name: str, entity_list: list, article_text: str, language: str = 'en') -> dict:
    """
    Sends text to the Gemini API for quiz generation and co-reference resolution of entities.
    Returns a dictionary with 'quiz' and 'tags' after Pydantic validation.
    """
    if not article_text:
        logger.warning("generate_master_analysis called with empty article_text.")
        return {'quiz': {}, 'tags': []}

    # Calculate optimal question count based on article characteristics
    question_count = calculate_optimal_question_count(article_text)
    logger.info(f"Generating {question_count} questions for article with {len(article_text.split())} words")

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config, # type: ignore
    )

    # Language-aware prompts - AI prompts should match article language
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

Devuelve solo el objeto JSON sin formato y nada más."""
    }
    
    prompt = prompts.get(language, prompts['en'])

    try:
        logger.info(f"Sending request to Gemini API with model: {model_name} for master analysis...")
        chat_session = model.start_chat()
        response = chat_session.send_message(prompt)
        logger.info("Successfully received response from Gemini API.")
        logger.debug(f"Raw LLM response: {response.text}")

        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        data = json.loads(clean_text)
        
        # Validate the response with Pydantic
        validated_data = MasterAnalysisResponse.model_validate(data)
        logger.info(f"Successfully validated LLM response. Quiz found: {len(validated_data.quiz)}, Tags found: {len(validated_data.tags)}")
        
        return validated_data.model_dump()

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from LLM response: {e}")
        logger.debug(f"Raw response was: {response.text}")
        return {'quiz': [], 'tags': []}
    except ValidationError as e:
        logger.error(f"LLM response failed Pydantic validation: {e}")
        logger.debug(f"Invalid data was: {data}")
        return {'quiz': [], 'tags': []}
    except Exception as e:
        logger.error(f"An unexpected error occurred calling LLM API: {e}", exc_info=True)
        return {'quiz': {}, 'tags': []}

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
    """
    Performs NLP analysis on text to extract reading score and named entities as strings.
    """
    # 1. Calculate Reading Level - wrap in try/catch for textstat issues
    try:
        reading_score = textstat.flesch_kincaid_grade(text)
    except (KeyError, Exception) as e:
        logger.warning(f"Error calculating reading score: {e}")
        reading_score = 0

    # 2. Extract Named Entities (as strings) - only if spaCy is available
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
def get_valid_wikipedia_tags(entities: list, language: str = 'en') -> list:
    """
    Checks a list of entity strings against Wikipedia to find valid tags.
    It uses a 'Canonical-First' approach:
    1. Resolve all entities to their canonical Wikipedia titles.
    2. Deduplicate and then fetch/create tags in the local database.
    Returns a list of valid Tag model objects.
    """
    wiki = wiki_es if language == 'es' else wiki_en
    canonical_name_map = {}

    # Step 1: Resolve All Canonical Names
    for entity_name in set(entities):
        if not isinstance(entity_name, str) or not entity_name.strip():
            logger.warning(f"Invalid entity name skipped: {entity_name}")
            continue

        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
                page_obj = wiki.page(entity_name)

                if page_obj.exists():
                    canonical_name = page_obj.title
                    canonical_name_map[entity_name] = canonical_name
                    break  # Success, break retry loop
                else:
                    logger.warning(f"Wikipedia page for '{entity_name}' does not exist. Skipping canonicalization.")
                    break # No need to retry if page doesn't exist

            except Exception as e:
                logger.warning(f"Wikipedia API error for tag '{entity_name}': {e}. Skipping canonicalization.")
                break
            except Exception as e:
                retries += 1
                logger.error(f"An unexpected error occurred during Wikipedia API call for tag '{entity_name}' (Attempt {retries}/{max_retries}): {e}")
                if retries < max_retries:
                    time.sleep(1) # Simple retry delay
                else:
                    logger.error(f"Max retries reached for tag '{entity_name}'. Skipping canonicalization.")
                    # Do not break here, let the loop finish and the entity will not be added to canonical_name_map

    # Step 2: Deduplicate and Fetch/Create Tags
    unique_canonical_names = set(canonical_name_map.values())
    validated_tags = []

    for canonical_name in unique_canonical_names:
        tag, created = Tag.objects.get_or_create(name=canonical_name)
        if created:
            logger.info(f"Created new canonical tag: '{canonical_name}'.")
        validated_tags.append(tag)

    return validated_tags



def find_largest_monetary_tag(money_mentions: list) -> str | None:
    """
    Finds the largest monetary value from a list of strings.
    """
    if not money_mentions:
        return None

    max_value = 0.0
    # This is a simplified parser. A real app might use a more robust library.
    for mention in money_mentions:
        # Remove symbols and commas
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
        return f"Value: ${max_value:,.0f}" # Format for readability
    return None