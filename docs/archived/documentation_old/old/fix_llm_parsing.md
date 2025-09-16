# AI-Assisted Code Modification Request

### File(s) to Modify:
- [verifast_app/services.py]

### Type of Change:
- [Bug Fix]

### Goal:
- [Fix the `JSONDecodeError` by making the LLM service more robust. It must clean the raw text response from the Gemini API before attempting to parse it as JSON.]

---

### Detailed Instructions:

# The `process_article` task is failing because the text returned by the Gemini API is not clean JSON.
# We need to strip common markdown code fences and whitespace from the response.

# FIND:
# ```python
# The try...except block in the `generate_quiz_and_tags_from_text` function.
try:
    logger.info("Sending request to Gemini API...")
    chat_session = model.start_chat()
    response = chat_session.send_message(prompt)
    logger.info("Successfully received response from Gemini API.")
    
    data = json.loads(response.text.strip())
    
    logger.info(f"Successfully parsed JSON response. Tags found: {len(data.get('tags', []))}")
    return {
        'quiz_data': data.get('quiz_data', {}),
        'tags': data.get('tags', [])
    }
except json.JSONDecodeError as e:
    # ... (existing error handling)
```
REPLACE WITH:
```python
Add a cleaning step before calling json.loads().
try:
logger.info("Sending request to Gemini API...")
chat_session = model.start_chat()
response = chat_session.send_message(prompt)
logger.info("Successfully received response from Gemini API.")

# --- ADD THIS CLEANING LOGIC ---
# Strip leading/trailing whitespace and remove markdown code fences
clean_text = response.text.strip()
if clean_text.startswith("```json"):
    clean_text = clean_text[7:]
if clean_text.endswith("```"):
    clean_text = clean_text[:-3]
# --- END CLEANING LOGIC ---

data = json.loads(clean_text)

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
---
### Validation Steps:
- Command: `python manage.py check`