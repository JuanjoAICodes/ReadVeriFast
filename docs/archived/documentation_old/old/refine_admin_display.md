# AI-Assisted Code Modification Request

### File(s) to Modify:
- [verifast_app/admin.py]
- [verifast_app/tasks.py]

### Type of Change:
- [Bug Fix & Refinement]

### Goal:
- [Create a custom `ArticleAdmin` class to correctly display only the relevant tags for each article in the Django admin. Refine the processing task to ensure it is robust.]

---

### Detailed Instructions:

**1. Create a Custom Admin View in `verifast_app/admin.py`:**
- We need to define a `ModelAdmin` class for `Article` to control how the many-to-many `tags` field is rendered.
- FIND:
```python
from django.contrib import admin
from .models import Article, Comment, QuizAttempt, Tag

admin.site.register(Article)
admin.site.register(Comment)
admin.site.register(QuizAttempt)
admin.site.register(Tag)
```
REPLACE WITH:

```python
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms
from .models import Article, Comment, QuizAttempt, Tag

# --- Create a custom form to override the widget ---
class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'
        widgets = {
            'tags': FilteredSelectMultiple(
                verbose_name='tags',
                is_stacked=False,
                # This is the crucial line that points to our custom template
                attrs={'template_name': 'admin/widgets/custom_filter_horizontal.html'}
            ),
        }

# --- Define the custom ArticleAdmin class ---
class ArticleAdmin(admin.ModelAdmin):
    # Use our custom form
    form = ArticleAdminForm
    
    # Existing configurations
    list_display = ('title', 'source', 'processing_status', 'publication_date')
    list_filter = ('processing_status', 'source', 'language')
    search_fields = ('title', 'url')
    
    # Note: We no longer need 'filter_horizontal' here because the form widget handles it.

# --- Register all models ---
admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment)
admin.site.register(QuizAttempt)
admin.site.register(Tag)
```
**2. Final Refinement of the Processing Task in verifast_app/tasks.py:**

Let's make the tag handling logic even more explicit and robust to guarantee correctness.

FIND:

```python
# The beginning of the tag generation section in process_article
article.tags.clear()
```
REPLACE WITH:

```python
# The new, more robust tag handling section.
# It builds a list of new tag objects first, then sets them all at once.

    # --- 3. Generate and Assign Tags (CORRECTED LOGIC) ---
    final_tags_for_this_article = []

    # Generate NLP-based tags
    people_tags = get_valid_wikipedia_tags(analysis_data.get("people", []), article.language)
    org_tags = get_valid_wikipedia_tags(analysis_data.get("organizations", []), article.language)
    largest_money_tag = find_largest_monetary_tag(analysis_data.get("money_mentions", []))
    
    all_nlp_tags = people_tags + org_tags
    if largest_money_tag:
        all_nlp_tags.append(largest_money_tag)
        
    for tag_name in set(all_nlp_tags):
        tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
        final_tags_for_this_article.append(tag)
        
    # --- 4. Generate Quiz and LLM Tags ---
    llm_data = generate_quiz_and_tags_from_text(article.content)

    if llm_data and llm_data.get('quiz_data'):
        article.quiz_data = llm_data['quiz_data']
        # Add LLM-generated tags
        for tag_name in llm_data.get('tags', []):
            tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
            final_tags_for_this_article.append(tag)
            
        # --- 5. Final, Atomic Tag Assignment ---
        # This is the most reliable way to set ManyToMany relationships.
        # It replaces all existing tags with the new list.
        article.tags.set(final_tags_for_this_article)

        # ... (Image generation logic remains the same) ...

        article.processing_status = 'complete'
        article.save()
        logger.info(f"Successfully processed Article ID: {article.id}")
    else:
        # ... (failure logic remains the same) ...
```