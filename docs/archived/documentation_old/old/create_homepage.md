# AI-Assisted Code Modification Request

### File(s) to Modify:
# The agent will need to create/modify these files.
- [app/views.py]
- [app/templates/app/index.html]
- [config/urls.py]

### Type of Change:
# Choose one: Refactor / Style / Variable Rename / Logic Adjustment / Frontend Tweak / Bug Fix
- [Logic Adjustment]

### Goal:
# A clear, one-sentence description of the desired outcome.
- [Create a simple homepage view and template, and map it to the root URL ('/').]

---

### Detailed Instructions:
This task has three parts: create the view, create the template, and connect them in the URL configuration.

**1. Create the View in `app/views.py`:**
- Add the following Python code to the `app/views.py` file to create a simple view that renders a homepage template.
```python
from django.shortcuts import render

def index(request):
    """A simple view for the homepage."""
    return render(request, 'app/index.html')
```

**2. Create the Template in app/templates/app/index.html:**

Create a new file at app/templates/app/index.html with the following HTML content. It should extend the base.html template.

```html
{% extends 'base.html' %}

{% block content %}
<main class="container">
  <div style="text-align: center; padding: 4rem 0;">
    <h1>Welcome to VeriFast</h1>
    <p>Your journey to faster reading and better comprehension starts here.</p>
    <a href="#" role="button" class="contrast">Browse Articles</a>
  </div>
</main>
{% endblock %}
```

**3. Update the URL Configuration in config/urls.py:**

Modify the config/urls.py file to import the new index view and map it to the root path ('').

FIND:
```python
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
```
REPLACE WITH:
```python
from django.contrib import admin
from django.urls import path
from app import views as app_views # Import the views from our app

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', app_views.index, name='index'), # Add the root path
]
```
### Scope and Boundaries (Safety Rules):
Only modify or create the files listed above.
