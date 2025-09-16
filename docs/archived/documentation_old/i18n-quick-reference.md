# VeriFast Internationalization Quick Reference

## 🚀 Quick Commands

### Development Workflow
```bash
# Extract new translatable strings
python manage.py makemessages -l es

# Edit translations
nano locale/es/LC_MESSAGES/django.po

# Compile translations
python manage.py compilemessages

# Test with Spanish
python manage.py runserver
# Visit: http://localhost:8000/?language=es
```

### Adding New Languages
```bash
# Create French translations
python manage.py makemessages -l fr

# Add to settings.py
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
    ('fr', 'Français'),
]
```

## 📝 Code Patterns

### Models
```python
from django.utils.translation import gettext_lazy as _

class MyModel(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name"),
        help_text=_("Enter the name")
    )
```

### Forms
```python
from django.utils.translation import gettext_lazy as _

class MyForm(forms.Form):
    title = forms.CharField(
        label=_("Title"),
        help_text=_("Enter a title")
    )
```

### Templates
```html
{% load i18n %}

<!-- Simple translation -->
<h1>{% trans "Welcome" %}</h1>

<!-- With variables -->
<p>{% blocktrans with name=user.name %}Hello {{ name }}!{% endblocktrans %}</p>

<!-- Pluralization -->
<p>{% blocktrans count counter=items.count %}
    There is {{ counter }} item.
{% plural %}
    There are {{ counter }} items.
{% endblocktrans %}</p>
```

### Views
```python
from django.utils.translation import gettext as _, ngettext

def my_view(request):
    messages.success(request, _('Success message'))
    
    # Pluralization
    count = items.count()
    message = ngettext(
        'There is %(count)d item',
        'There are %(count)d items',
        count
    ) % {'count': count}
```

### JavaScript (Minimal Usage in HTMX Architecture)
```html
<!-- Only needed for minimal Alpine.js components -->
<script src="{% url 'javascript-catalog' %}"></script>
<script>
// Global translation function for Alpine.js components
window._ = function(key, params = {}) {
    return window.i18n ? window.i18n._(key, params) : key;
};

// Usage in Alpine.js speed reader
function speedReader(wordChunks, settings, articleId) {
    return {
        currentChunk: _('click_start_reading'),
        completeMessage: _('reading_complete'),
        
        showMessage(key) {
            return _(key);
        }
    }
}

// Traditional JavaScript (minimal usage)
const message = gettext('Loading...');
const formatted = interpolate(gettext('Hello %s'), [name]);
</script>
```

## 🔧 Common Tasks

### Language Switcher
```html
{% load i18n %}
<form action="{% url 'set_language' %}" method="post">
    {% csrf_token %}
    <select name="language" onchange="this.form.submit();">
        {% get_current_language as LANGUAGE_CODE %}
        {% get_available_languages as LANGUAGES %}
        {% for lang_code, lang_name in LANGUAGES %}
            <option value="{{ lang_code }}"{% if lang_code == LANGUAGE_CODE %} selected{% endif %}>
                {{ lang_name }}
            </option>
        {% endfor %}
    </select>
</form>
```

### URL Patterns
```python
from django.conf.urls.i18n import i18n_patterns

# Non-translated URLs
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]

# Translated URLs
urlpatterns += i18n_patterns(
    path('', views.home, name='home'),
    path('articles/', views.articles, name='articles'),
)
```

## 📊 Translation Status

### ✅ Completed (85%)
- Navigation menu
- Form labels and help text
- Model field descriptions
- Base template elements
- JavaScript UI strings
- User profile interface
- Article reading interface

### ⚠️ In Progress (15%)
- Welcome messages
- Error messages
- Admin interface
- Email templates

## 🐛 Troubleshooting

### Translation Not Showing
```bash
# Check if marked for translation
grep -r "Your String" .

# Regenerate messages
python manage.py makemessages -l es --ignore=venv

# Check .po file
grep -A 2 "Your String" locale/es/LC_MESSAGES/django.po

# Recompile
python manage.py compilemessages

# Restart server
python manage.py runserver
```

### JavaScript Issues
```javascript
// Check if catalog loaded
console.log(typeof gettext); // Should be 'function'

// Check for errors
console.log(gettext('Test')); // Should return translation or 'Test'
```

## 📚 Key Spanish Translations

| English | Spanish |
|---------|---------|
| Articles | Artículos |
| Profile | Perfil |
| Login | Iniciar Sesión |
| Register | Registrarse |
| Logout | Cerrar Sesión |
| Submit Article | Enviar Artículo |
| Start Reading | Comenzar Lectura |
| Speed Reader | Lector Rápido |
| Premium Features | Funciones Premium |
| Total XP | XP Total |
| Spendable XP | XP Disponible |
| Quizzes Completed | Cuestionarios Completados |

## 🎯 Best Practices

1. **Always use lazy translation** in models and forms
2. **Use context** in complex translations
3. **Test in multiple languages** before deployment
4. **Keep strings simple** and avoid concatenation
5. **Use comments** for translator context
6. **Compile before deployment** - never deploy .po files without .mo

## 🔗 Resources

- [Full Documentation](internationalization-implementation.md)
- [Django i18n Docs](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [Translation Best Practices](https://docs.djangoproject.com/en/stable/topics/i18n/translation/#standard-translation)