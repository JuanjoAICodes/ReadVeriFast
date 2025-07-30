# AI-Assisted Code Modification Request

### File(s) to Modify:
# The base template is the single source of truth for site-wide styling.
- [verifast_app/templates/verifast_app/base.html]

### Type of Change:
- [Frontend Tweak]

### Goal:
- [Apply the Pico.css framework to the entire user-facing site to provide a clean, modern, and consistent base style.]

---

### Detailed Instructions:

**1. Add the Pico.css Stylesheet Link:**
- In the `base.html` file, inside the `<head>` tag, we need to add the link to the Pico.css CDN.

- FIND:
```html
<title>VeriFast</title>
'''
REPLACE WITH:

'''html
<title>VeriFast</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@latest/css/pico.min.css" />```

**2. Add the Main Container Class:**
- For Pico.css to center the content correctly, the main content block should be wrapped in a `<main>` tag with the `container` class.

- FIND:
```html
{% block content %}{% endblock %}
'''
REPLACE WITH:

'''html
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
'''
Scope and Boundaries (Safety Rules):
Only modify the base.html file as specified.