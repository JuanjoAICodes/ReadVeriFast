### Detailed Instructions:

**1. Create the View in `app/views.py`:**
- Add a new function-based view named `article_list`.
- This view must query the database for all `Article` objects where the `processing_status` is `'complete'`.
- It should pass these articles to a new template.
- Add the following code to `app/views.py`:
```python
from .models import Article # Make sure to import the Article model

def article_list(request):
    """A view to list all successfully processed articles."""
    completed_articles = Article.objects.filter(processing_status='complete').order_by('-publication_date')
    context = {
        'articles': completed_articles,
        'title': 'Browse Articles'
    }
    return render(request, 'app/article_list.html', context)
```

**2. Create the Template in `app/templates/app/article_list.html`:**

Create a new file at this path.

This template should display the title and a list of the articles.

For now, the links for each article can be placeholders (#).

The content should be:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
</head>
<body>
    <main class="container">
      <h1>{{ title }}</h1>
      {% if articles %}
        <article>
          <ul>
            {% for article in articles %}
              <li>
                <a href="#">{{ article.title }}</a>
                <small> - Published on: {{ article.publication_date|date:"Y-m-d" }}</small>
              </li>
            {% endfor %}
          </ul>
        </article>
      {% else %}
        <p>No articles have been processed yet. Please check back later or add one via the admin panel.</p>
      {% endif %}
    </main>
</body>
</html>
```

**3. Update the App's URLs in `app/urls.py`:**

Add a new path for `/articles/` that maps to the `article_list` view.

**FIND:**
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
]
```

**REPLACE WITH:**
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('articles/', views.article_list, name='article_list'), # Add this line
]
```

**4. Update the Homepage Link in `app/templates/app/index.html`:**

Finally, fix the placeholder link on the homepage.

**FIND:**
```html
<a href="#" role="button" class="contrast">Browse Articles</a>
```

**REPLACE WITH:**
```html
<a href="{% url 'article_list' %}" role="button" class="contrast">Browse Articles</a>
```

### Validation Steps:
Command: `python manage.py check`
