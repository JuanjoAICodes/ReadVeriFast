"""
Template tags for language functionality
"""

from django import template
from django.utils.translation import gettext as _

register = template.Library()

# Language configuration
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native_name": "English", "flag": "🇺🇸", "code": "en"},
    "es": {"name": "Spanish", "native_name": "Español", "flag": "🇪🇸", "code": "es"},
}


@register.simple_tag
def language_flag(language_code):
    """Display language flag emoji"""
    lang_info = SUPPORTED_LANGUAGES.get(language_code, {})
    return lang_info.get("flag", "🌐")


@register.simple_tag
def language_name(language_code, native=False):
    """Display language name"""
    lang_info = SUPPORTED_LANGUAGES.get(language_code, {})
    if native:
        return lang_info.get("native_name", language_code.upper())
    return lang_info.get("name", language_code.upper())


@register.inclusion_tag(
    "verifast_app/components/language_selector.html", takes_context=True
)
def language_selector(context, current_language=None, show_all=True):
    """Render language selector component"""
    request = context["request"]
    current_language = current_language or request.GET.get("lang", "all")

    languages = []

    # Add "All Languages" option
    if show_all:
        languages.append(
            {
                "code": "all",
                "name": _("All Languages"),
                "native_name": _("All Languages"),
                "flag": "🌐",
                "is_active": current_language == "all",
                "url": _build_language_url(request, "all"),
            }
        )

    # Add supported languages
    for code, info in SUPPORTED_LANGUAGES.items():
        languages.append(
            {
                "code": code,
                "name": info["name"],
                "native_name": info["native_name"],
                "flag": info["flag"],
                "is_active": current_language == code,
                "url": _build_language_url(request, code),
            }
        )

    return {
        "languages": languages,
        "current_language": current_language,
        "request": request,
    }


@register.inclusion_tag("verifast_app/components/language_badge.html")
def language_badge(language_code, size="small"):
    """Render language badge for articles"""
    lang_info = SUPPORTED_LANGUAGES.get(
        language_code,
        {
            "name": language_code.upper(),
            "native_name": language_code.upper(),
            "flag": "🌐",
        },
    )

    return {"language": lang_info, "size": size}


@register.filter
def language_filter_url(request, language_code):
    """Generate URL with language filter"""
    return _build_language_url(request, language_code)


@register.simple_tag(takes_context=True)
def user_preferred_language(context):
    """Get user's preferred language"""
    request = context["request"]
    if request.user.is_authenticated:
        return getattr(request.user, "preferred_language", "en")
    return "en"


@register.simple_tag
def language_article_count(language_code):
    """Get article count for a specific language"""
    from ..models import Article

    if language_code == "all":
        return Article.objects.filter(processing_status="complete").count()

    return Article.objects.filter(
        language=language_code, processing_status="complete"
    ).count()


@register.inclusion_tag("verifast_app/components/language_stats.html")
def language_statistics():
    """Display language distribution statistics"""
    from ..models import Article
    from django.db.models import Count

    stats = (
        Article.objects.filter(processing_status="complete")
        .values("language")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    total_articles = sum(stat["count"] for stat in stats)

    language_stats = []
    for stat in stats:
        lang_code = stat["language"]
        lang_info = SUPPORTED_LANGUAGES.get(
            lang_code, {"name": lang_code.upper(), "flag": "🌐"}
        )

        percentage = (stat["count"] / total_articles * 100) if total_articles > 0 else 0

        language_stats.append(
            {
                "code": lang_code,
                "name": lang_info["name"],
                "flag": lang_info["flag"],
                "count": stat["count"],
                "percentage": percentage,
            }
        )

    return {"language_stats": language_stats, "total_articles": total_articles}


def _build_language_url(request, language_code):
    """Helper function to build URL with language parameter"""
    params = request.GET.copy()

    if language_code == "all":
        params.pop("lang", None)
    else:
        params["lang"] = language_code

    # Build URL with parameters
    url = request.path
    if params:
        url += "?" + params.urlencode()

    return url


@register.simple_tag
def get_supported_languages():
    """Get all supported languages"""
    return SUPPORTED_LANGUAGES


@register.filter
def is_user_language(article_language, user):
    """Check if article language matches user's preferred language"""
    if not user.is_authenticated:
        return False

    user_lang = getattr(user, "preferred_language", "en")
    return article_language == user_lang


@register.inclusion_tag(
    "verifast_app/components/language_preference_form.html", takes_context=True
)
def language_preference_form(context):
    """Render language preference form for users"""
    request = context["request"]

    if not request.user.is_authenticated:
        return {"show_form": False}

    current_preference = getattr(request.user, "preferred_language", "en")

    return {
        "show_form": True,
        "current_preference": current_preference,
        "languages": SUPPORTED_LANGUAGES,
        "user": request.user,
    }
