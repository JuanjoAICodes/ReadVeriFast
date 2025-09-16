# AI-Assisted Code Modification Request

### File(s) to Modify:
# The logic for handling duplicate URLs is in the Celery task.
# We need to modify the view that calls it to handle this case.
- [verifast_app/views.py]
- [verifast_app/tasks.py]

### Type of Change:
- [Feature Addition]

### Goal:
- [Inform the user with a message when they submit a URL that already exists in the database.]

---

### Detailed Instructions:

**1. Modify the Celery Task in `verifast_app/tasks.py` to return a specific value for duplicates:**
- The task currently returns a string. We will modify it to return a more structured response so the view can understand what happened.
- FIND:
```python
 @shared_task
def scrape_and_save_article(url):
    """
    Scrapes an article from a URL and saves a new Article object
    with a 'pending' status for later processing by an LLM.
    """
    try:
        # Check if URL already exists to avoid duplicates
        if Article.objects.filter(url=url).exists():
            return f"Article from URL {url} already exists."
        # ... rest of the task
```
REPLACE WITH:

```python
 @shared_task
def scrape_and_save_article(url):
    """
    Scrapes an article from a URL and saves a new Article object.
    Returns a dictionary indicating the result.
    """
    try:
        # Check if URL already exists to avoid duplicates
        if Article.objects.filter(url=url).exists():
            return {'status': 'duplicate', 'url': url}

        # ... rest of the task logic ...
        # ... where it creates the new_article ...
        
        process_article.delay(new_article.id)
        return {'status': 'success', 'article_id': new_article.id}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
```

**2. Modify the View in `verifast_app/views.py` to handle the new task response:**

The `scrape_article_view` needs to be updated to no longer call the task with `.delay()` (which we can't get a return value from) and instead use `.apply_async()` and then check the result. However, for simplicity in a web flow, we will perform the check before calling the task.

FIND:

```python
from .tasks import scrape_and_save_article

def scrape_article_view(request):
    if request.method == 'POST':
        form = ArticleURLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            # Call the background task asynchronously
            scrape_and_save_article.delay(url)
            messages.success(request, 'Your article has been submitted and is being processed in the background!')
            return redirect('verifast_app:article_list')
    # ... rest of the view
```
REPLACE WITH:

```python
from .tasks import scrape_and_save_article
from .models import Article # Make sure Article is imported

def scrape_article_view(request):
    if request.method == 'POST':
        form = ArticleURLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            
            # --- ADD THIS CHECK ---
            # Check for duplicates BEFORE calling the background task.
            if Article.objects.filter(url=url).exists():
                messages.warning(request, f'This article from URL {url} is already in our database.')
                return redirect('verifast_app:article_list')
            # --- END CHECK ---

            # Call the background task asynchronously
            scrape_and_save_article.delay(url)
            messages.success(request, 'Your article has been submitted and is being processed in the background!')
            return redirect('verifast_app:article_list')
    else:
        form = ArticleURLForm()
    
    return render(request, 'verifast_app/scrape_article.html', {'form': form})
```

### Validation Steps:
The `base.html` template must be configured to display Django messages.

Command: `python manage.py check`

#### Step 2: Ensure Your Template Can Display Messages

The `messages.warning(...)` call only works if your `base.html` template has a place to render them.

1.  Open your `base.html` template.
2.  Add the following block of code, usually right after the `<nav>` or before the `{% block content %}`.

```html
<main class="container">
    {% if messages %}
        {% for message in messages %}
            <article class="{{ message.tags }}" aria-label="Message">
                {{ message }}
            </article>
        {% endfor %}
    {% endif %}

    {% block content %}{% endblock %}
</main>
