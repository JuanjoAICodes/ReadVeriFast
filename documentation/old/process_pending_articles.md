# AI-Assisted Code Modification Request

### File(s) to Modify:
# The agent will create or modify these files.
- [verifast_app/tasks.py]
- [verifast_app/services.py] # A new file for the LLM logic
- [verifast_app/admin.py] # To add an action to the admin panel

### Type of Change:
- [Feature Addition]

### Goal:
- [Create an asynchronous task that finds 'pending' articles, generates quizzes and tags for them using an LLM, and updates their status to 'complete'.]

---

### Detailed Instructions:

**1. Create a Service for LLM Interaction in `verifast_app/services.py`:**
- If the file doesn't exist, create it.
- This file will contain the logic for interacting with the Gemini API. This separates our core logic from the task runner.
```python
import os
import google.generativeai as genai

# Configure the API key from environment variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

def generate_quiz_and_tags_from_text(text: str) -> dict:
    """
    Sends text to the Gemini API and asks for a quiz and tags.
    Returns a dictionary with 'quiz_data' and 'tags'.
    """
    if not text:
        return {'quiz_data': {}, 'tags': []}

    prompt = f"""
    Based on the following article text, please generate a quiz with 5 multiple-choice questions and a list of 3-5 relevant tags.

    The output MUST be a valid JSON object with two keys: "quiz_data" and "tags".
    - "quiz_data" should be a list of objects, where each object has "question", "options" (a list of 4 strings), and "correct_answer".
    - "tags" should be a list of strings.

    Article Text:
    ---
    {text[:4000]}
    ---

    JSON Output:
    """
    
    try:
        chat_session = model.start_chat()
        response = chat_session.send_message(prompt)
        # Simple parsing, a real app would have more robust validation
        import json
        data = json.loads(response.text.strip())
        return {
            'quiz_data': data.get('quiz_data', {}),
            'tags': data.get('tags', [])
        }
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return {'quiz_data': {}, 'tags': []}
```

**2. Create the Processing Task in `verifast_app/tasks.py`:**

Add a new Celery task that uses the LLM service.

```python
from celery import shared_task
from .models import Article, Tag
from .services import generate_quiz_and_tags_from_text

 @shared_task
def process_article(article_id):
    """
    Fetches a pending article, generates quiz/tags via LLM, and updates it.
    """
    try:
        article = Article.objects.get(id=article_id, processing_status='pending')
    except Article.DoesNotExist:
        return f"Article {article_id} not found or not pending."

    # Call the LLM service to get the data
    llm_data = generate_quiz_and_tags_from_text(article.raw_content)

    if llm_data and llm_data.get('quiz_data'):
        article.quiz_data = llm_data['quiz_data']
        
        # Handle tags
        tag_names = llm_data.get('tags', [])
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
            article.tags.add(tag)

        article.processing_status = 'complete'
        article.save()
        return f"Successfully processed Article ID: {article.id}"
    else:
        article.processing_status = 'failed'
        article.save()
        return f"Failed to process Article ID: {article.id} due to LLM error."
```

**3. Modify the Scraper Task in `verifast_app/tasks.py`:**

Update the `scrape_and_save_article` task to automatically trigger the `process_article` task after an article is created.

FIND:
```python
return f"Successfully created Article ID: {new_article.id} with pending status."
```

REPLACE WITH:
```python
# Now, trigger the processing task for the new article
process_article.delay(new_article.id)
return f"Successfully created Article ID: {new_article.id} and queued for processing."
```

### Validation Steps:
Command: `python manage.py check`

#### Step 2: Run the Agent to Build the Processing Pipeline

Now, execute the plan. In your terminal (with `venv` active), run:

```bash
python agent.py --modify process_pending_articles.md
```
Approve the changes when the diff is shown.