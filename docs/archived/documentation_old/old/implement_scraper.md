# AI-Assisted Code Modification Request

### File(s) to Modify:
# The agent will create or modify these files.
- [verifast_app/forms.py]
- [verifast_app/tasks.py]
- [verifast_app/views.py]
- [verifast_app/urls.py]
- [verifast_app/templates/verifast_app/scrape_article.html]
- [verifast_app/templates/verifast_app/base.html] # To add the nav link

### Type of Change:
- [Feature Addition]

### Goal:
- [Implement a page where users can submit a URL. The URL is then passed to an asynchronous background task that scrapes the article content and saves it to the database with a 'pending' status.]

---

### Detailed Instructions:

**1. Create a Form in `verifast_app/forms.py`:**
- If the file doesn't exist, create it.
- Add a new Django Form named `ArticleURLForm` for URL submission.
```python
from django import forms

class ArticleURLForm(forms.Form):
    url = forms.URLField(
        label='Article URL',
        required=True,
        widget=forms.URLInput(attrs={'placeholder': 'https://example.com/news/article'})
    )
```
