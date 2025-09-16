# AI-Assisted Code Modification Request

### File(s) to Modify:
- [verifast_app/admin.py]
- [verifast_app/tasks.py]

### Type of Change:
- [Bug Fix & Feature Addition]

### Goal:
- [Fix the bug where all existing tags are incorrectly assigned to new articles. Also, create a new admin view to manage all tags globally.]

---

### Detailed Instructions:

**1. Create a Global Tag Management View in `verifast_app/admin.py`:**
- Register the `Tag` model with the Django admin so we can see and manage all tags in one place.
- FIND:
```python
# The current content of the admin.py file
from django.contrib import admin
from .models import Article, Comment, QuizAttempt # Tag might be missing

admin.site.register(Article)
admin.site.register(Comment)
admin.site.register(QuizAttempt)
```
REPLACE WITH:

```python
# Import Tag and register it.
from django.contrib import admin
from .models import Article, Comment, QuizAttempt, Tag

admin.site.register(Article)
admin.site.register(Comment)
admin.site.register(QuizAttempt)
admin.site.register(Tag) # <-- ADD THIS LINE
```
**2. Correct the Tag Assignment Logic in verifast_app/tasks.py:**

We will rewrite the entire process_article task to ensure the tag logic is clean and correct. It must clear existing tags for the article before adding the new, specific ones.

FIND:

```python
# The entire existing process_article task function.
 @shared_task(bind=True)
def process_article(self, article_id):
    # ... all existing (buggy) code ...
```
REPLACE WITH:

```python
# This is the new, corrected version of the task.
from celery import shared_task
from celery.utils.log import get_task_logger
from .models import Article, Tag
from .services import (
    generate_quiz_and_tags_from_text, 
    analyze_text_content, 
    get_valid_wikipedia_tags, 
    find_largest_monetary_tag,
    # get_llm_for_article, # This function is not defined in the provided services.py
    # generate_image_for_book # This function is not defined in the provided services.py
)

logger = get_task_logger(__name__)

 @shared_task(bind=True)
def process_article(self, article_id):
    """
    Orchestrates the full analysis pipeline with corrected tag handling.
    """
    logger.info(f"Starting corrected processing for article ID: {article_id}")
    try:
        article = Article.objects.get(id=article_id, processing_status='pending')
    except Article.DoesNotExist:
        logger.warning(f"Article {article_id} not found or not pending. Task aborted.")
        return

    # --- 1. Perform initial NLP Analysis ---
    analysis_data = analyze_text_content(article.content, article.language)
    article.reading_level_score = analysis_data.get("reading_score")
    
    # --- 2. Route to get the correct models ---
    # models_to_use = get_llm_for_article(article) # This function is not defined in the provided services.py

    # --- 3. Generate and Assign Tags (CORRECTED LOGIC) ---
    # First, clear any potentially stale tags from previous runs.
    article.tags.clear()
    
    # Generate NLP-based tags
    people_tags = get_valid_wikipedia_tags(analysis_data.get("people", []), article.language)
    org_tags = get_valid_wikipedia_tags(analysis_data.get("organizations", []), article.language)
    largest_money_tag = find_largest_monetary_tag(analysis_data.get("money_mentions", []))
    
    all_nlp_tags = people_tags + org_tags
    if largest_money_tag:
        all_nlp_tags.append(largest_money_tag)
        
    for tag_name in set(all_nlp_tags):
        tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
        article.tags.add(tag)
        
    # --- 4. Generate Quiz and LLM Tags ---
    llm_data = generate_quiz_and_tags_from_text(article.content)

    if llm_data and llm_data.get('quiz_data'):
        article.quiz_data = llm_data['quiz_data']
        # Add LLM-generated tags
        for tag_name in llm_data.get('tags', []):
            tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
            article.tags.add(tag)

        # ... (Image generation logic remains the same) ...

        article.processing_status = 'complete'
        article.save()
        logger.info(f"Successfully processed Article ID: {article.id}")
    else:
        article.processing_status = 'failed'
        article.save()
        logger.error(f"Failed to get LLM data for Article ID: {article.id}")
```