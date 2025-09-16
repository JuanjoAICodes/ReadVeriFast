# AI-Assisted Code Modification Request

### File(s) to Modify:
# The agent will create or modify these files.
- [requirements.txt]
- [verifast_app/models.py]
- [verifast_app/services.py]
- [verifast_app/tasks.py]
- [verifast_app/gamification.py] # Or wherever XP is calculated

### Type of Change:
- [Feature Addition]

### Goal:
- [Enhance the article processing pipeline to perform advanced text analysis: calculate a reading complexity score, extract named entities (people, companies), validate them against Wikipedia, and extract the largest monetary value mentioned to use as tags.]

---

### Detailed Instructions:

**1. Update Dependencies in `requirements.txt`:**
- Add the necessary libraries for NLP and text analysis.
```
Add these lines to requirements.txt
spacy==3.7.2
textstat==0.7.3
wikipedia-api==0.6.0
```
- **Post-installation step (for human operator):** After these are installed, the spaCy language models must be downloaded. This will be done manually.
  - `python -m spacy download en_core_web_sm`
  - `python -m spacy download es_core_news_sm`

**2. Update the Article Model in `verifast_app/models.py`:**
- The `reading_level` field should store a numerical score for calculations, not a string.
- FIND:
`reading_level = models.CharField(max_length=255, null=True, blank=True)` (or similar)
- REPLACE WITH:
`reading_level_score = models.FloatField(null=True, blank=True)`

**3. Enhance the LLM Service in `verifast_app/services.py`:**
- We will add a new, powerful analysis function to this file.
```python
import spacy
import textstat
import wikipediaapi
import re
from .models import Article, Tag

# Load spaCy models
nlp_en = spacy.load("en_core_web_sm")
nlp_es = spacy.load("es_core_news_sm")

wiki_en = wikipediaapi.Wikipedia('en')
wiki_es = wikipediaapi.Wikipedia('es')

def analyze_text_content(text: str, language: str = 'en') -> dict:
    """
    Performs NLP analysis on text to extract reading score and named entities.
    """
    nlp = nlp_es if language == 'es' else nlp_en
    doc = nlp(text)

    # 1. Calculate Reading Level
    # Flesch-Kincaid Grade is a good, simple metric.
    reading_score = textstat.flesch_kincaid_grade(text)

    # 2. Extract Named Entities
    people = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
    orgs = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
    money = [ent.text for ent in doc.ents if ent.label_ == 'MONEY']
    
    # Remove duplicates
    people = list(set(people))
    orgs = list(set(orgs))

    return {
        "reading_score": reading_score,
        "people": people,
        "organizations": orgs,
        "money_mentions": money
    }

def get_valid_wikipedia_tags(entities: list, language: str = 'en') -> list:
    """Checks a list of entities against Wikipedia to see if they are notable."""
    wiki = wiki_es if language == 'es' else wiki_en
    valid_tags = []
    for entity in entities:
        page = wiki.page(entity)
        if page.exists():
            valid_tags.append(entity)
    return valid_tags

def find_largest_monetary_tag(money_mentions: list) -> str | None:
    """Finds the largest monetary value from a list of strings."""
    if not money_mentions:
        return None
    
    max_value = 0
    # This is a simplified parser. A real app might use a more robust library.
    for mention in money_mentions:
        # Remove symbols and commas
        numeric_part = re.sub(r'[$,€£,]', '', mention).lower()
        value = 0
        if 'billion' in numeric_part:
            value = float(re.findall(r'[\d\.]+', numeric_part)) * 1_000_000_000
        elif 'million' in numeric_part:
            value = float(re.findall(r'[\d\.]+', numeric_part)) * 1_000_000
        elif re.findall(r'[\d\.]+', numeric_part):
            value = float(re.findall(r'[\d\.]+', numeric_part))
        
        if value > max_value:
            max_value = value
            
    if max_value > 0:
        return f"Value: ${max_value:,.0f}" # Format for readability
    return None
```
**4. Upgrade the Processing Task in `verifast_app/tasks.py`:**

The `process_article` task will now call our new analysis services.

FIND:

```python
# The entire process_article task
 @shared_task
def process_article(article_id):
    # ... existing code ...
```
REPLACE WITH:

```python
from .services import generate_quiz_and_tags_from_text, analyze_text_content, get_valid_wikipedia_tags, find_largest_monetary_tag

 @shared_task
def process_article(article_id):
    """
    Enhances an article with LLM quizzes, NLP analysis, and Wikipedia-validated tags.
    """
    logger.info(f"Starting ADVANCED processing for article ID: {article_id}")
    try:
        article = Article.objects.get(id=article_id, processing_status='pending')
    except Article.DoesNotExist:
        logger.warning(f"Article {article_id} not found or not pending. Task aborted.")
        return

    # --- NEW: Perform NLP Analysis First ---
    analysis_data = analyze_text_content(article.raw_content, article.language)
    article.reading_level_score = analysis_data.get("reading_score")
    
    # --- NEW: Validate entities and create tags ---
    people_tags = get_valid_wikipedia_tags(analysis_data.get("people", []), article.language)
    org_tags = get_valid_wikipedia_tags(analysis_data.get("organizations", []), article.language)
    largest_money_tag = find_largest_monetary_tag(analysis_data.get("money_mentions", []))
    
    all_new_tags = people_tags + org_tags
    if largest_money_tag:
        all_new_tags.append(largest_money_tag)
        
    for tag_name in set(all_new_tags): # Use set to avoid duplicates
        tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
        article.tags.add(tag)
        
    # --- Generate Quiz using LLM ---
    llm_data = generate_quiz_and_tags_from_text(article.raw_content)

    if llm_data and llm_data.get('quiz_data'):
        article.quiz_data = llm_data['quiz_data']
        # We can also add LLM-generated tags if we want
        for tag_name in llm_data.get('tags', []):
            tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
            article.tags.add(tag)
            
        article.processing_status = 'complete'
        article.save()
        logger.info(f"Successfully processed and completed Article ID: {article.id}")
    else:
        article.processing_status = 'failed'
        article.save()
        logger.error(f"Failed to get LLM data for Article ID: {article.id}. Status set to 'failed'.")
```
**5. Update Gamification Logic:**

Instruct the agent to find the `calculate_xp` function (likely in `verifast_app/gamification.py`) and modify the `Complejidad_Texto_Factor` to be based on the new `article.reading_level_score`. A simple multiplication factor can be used.