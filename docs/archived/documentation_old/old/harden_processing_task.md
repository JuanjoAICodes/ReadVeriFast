# AI-Assisted Code Modification Request

### File(s) to Modify:
- [verifast_app/tasks.py]
- [verifast_app/services.py]

### Type of Change:
- [Bug Fix]

### Goal:
- [Make the `process_article` task more robust by adding detailed logging to identify why it's failing to mark articles as 'complete'.]

---

### Detailed Instructions:

**1. Add Logging to the LLM Service in `verifast_app/services.py`:**
- Import the `logging` module.
- Add log messages to trace the execution flow and catch errors.
- FIND:
```python
# The entire generate_quiz_and_tags_from_text function
def generate_quiz_and_tags_from_text(text: str):
    # ... (existing code) ...
```
REPLACE WITH:

```python
import os
import json
import logging
import google.generativeai as genai

# Get a logger instance
logger = logging.getLogger(__name__)

def generate_quiz_and_tags_from_text(text: str) -> dict:
    """
    Sends text to the Gemini API and asks for a quiz and tags.
    Returns a dictionary with 'quiz_data' and 'tags'.
    """
    # ... (the model setup code remains the same) ...
    # ...
    
    if not text:
        logger.warning("generate_quiz_and_tags_from_text called with empty text.")
        return {'quiz_data': {}, 'tags': []}

    # ... (the prompt remains the same) ...

    try:
        logger.info("Sending request to Gemini API...")
        chat_session = model.start_chat()
        response = chat_session.send_message(prompt)
        logger.info("Successfully received response from Gemini API.")
        
        # Clean the response to make it valid JSON
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean_response)
        
        logger.info(f"Successfully parsed JSON response. Tags found: {len(data.get('tags', []))}")
        return {
            'quiz_data': data.get('quiz_data', {}),
            'tags': data.get('tags', [])
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from LLM response: {e}")
        logger.debug(f"Raw response was: {response.text}")
        return {'quiz_data': {}, 'tags': []}
    except Exception as e:
        logger.error(f"An unexpected error occurred calling LLM API: {e}", exc_info=True)
        return {'quiz_data': {}, 'tags': []}
```

**2. Add Logging to the Celery Task in `verifast_app/tasks.py`:**

FIND:

```python
 @shared_task
def process_article(article_id):
    # ... (existing code) ...
```
REPLACE WITH:

```python
from celery.utils.log import get_task_logger
# ... other imports ...

logger = get_task_logger(__name__)

 @shared_task
def process_article(article_id):
    """
    Fetches a pending article, generates quiz/tags via LLM, and updates it.
    """
    logger.info(f"Starting to process article ID: {article_id}")
    try:
        article = Article.objects.get(id=article_id, processing_status='pending')
    except Article.DoesNotExist:
        logger.warning(f"Article {article_id} not found or not pending. Task aborted.")
        return f"Article {article_id} not found or not pending."

    llm_data = generate_quiz_and_tags_from_text(article.raw_content)

    if llm_data and llm_data.get('quiz_data'):
        # ... (logic to save data remains the same) ...
        article.processing_status = 'complete'
        article.save()
        logger.info(f"Successfully processed and completed Article ID: {article.id}")
        return f"Successfully processed Article ID: {article.id}"
    else:
        article.processing_status = 'failed'
        article.save()
        logger.error(f"Failed to get LLM data for Article ID: {article.id}. Status set to 'failed'.")
        return f"Failed to process Article ID: {article.id} due to LLM error."
