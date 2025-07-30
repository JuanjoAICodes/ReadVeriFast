"""
Configuration settings for the automated content acquisition system.
"""

from django.conf import settings

# Acquisition cycle configuration
ACQUISITION_CONFIG = {
    'cycle_interval_hours': 4,
    'max_articles_per_cycle': 50,
    'max_articles_per_topic_per_language': 4,
    'api_limits': {
        'newsdata_io': {'daily': 2000, 'current': 0},
        'gemini': {'daily': 1000, 'current': 0}
    },
    'retry_attempts': 3,
    'retry_delay_seconds': 60,
}

# RSS Feed Sources
RSS_SOURCES = {
    'english': [
        {
            'name': 'BBC News',
            'url': 'http://feeds.bbci.co.uk/news/rss.xml',
            'category': 'general',
            'language': 'en'
        },
        {
            'name': 'Reuters',
            'url': 'https://feeds.reuters.com/reuters/topNews',
            'category': 'general',
            'language': 'en'
        },
        {
            'name': 'CNN',
            'url': 'http://rss.cnn.com/rss/edition.rss',
            'category': 'general',
            'language': 'en'
        },
        {
            'name': 'The Guardian',
            'url': 'https://www.theguardian.com/world/rss',
            'category': 'general',
            'language': 'en'
        },
        {
            'name': 'NPR',
            'url': 'https://feeds.npr.org/1001/rss.xml',
            'category': 'general',
            'language': 'en'
        },
        {
            'name': 'The New York Times',
            'url': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
            'category': 'general',
            'language': 'en'
        },
        {
            'name': 'Al Jazeera English',
            'url': 'https://www.aljazeera.com/xml/rss/all.xml',
            'category': 'general',
            'language': 'en'
        },
        {
            'name': 'Politico',
            'url': 'https://www.politico.com/rss/politicopicks.xml',
            'category': 'politics',
            'language': 'en'
        },
        {
            'name': 'The Economist',
            'url': 'https://www.economist.com/the-world-this-week/rss.xml',
            'category': 'business',
            'language': 'en'
        },
        {
            'name': 'Bloomberg',
            'url': 'https://feeds.bloomberg.com/markets/news.rss',
            'category': 'business',
            'language': 'en'
        }
    ],
    'spanish': [
        {
            'name': 'La Opinión',
            'url': 'https://laopinion.com/feed/',
            'category': 'general',
            'language': 'es'
        },
        {
            'name': 'Univision',
            'url': 'https://www.univision.com/rss/noticias',
            'category': 'general',
            'language': 'es'
        },
        {
            'name': 'El Nuevo Herald',
            'url': 'https://www.elnuevoherald.com/noticias/?widgetName=rssfeed&widgetContentId=712015&getXmlFeed=true',
            'category': 'general',
            'language': 'es'
        },
        {
            'name': 'Clarín',
            'url': 'https://www.clarin.com/rss/lo-ultimo/',
            'category': 'general',
            'language': 'es'
        },
        {
            'name': 'El País',
            'url': 'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada',
            'category': 'general',
            'language': 'es'
        },
        {
            'name': 'BBC News Mundo',
            'url': 'https://feeds.bbci.co.uk/mundo/rss.xml',
            'category': 'general',
            'language': 'es'
        },
        {
            'name': 'RTVE',
            'url': 'https://www.rtve.es/api/noticias.rss',
            'category': 'general',
            'language': 'es'
        },
        {
            'name': 'SBS Español',
            'url': 'https://www.sbs.com.au/language/spanish/es/rss.xml',
            'category': 'general',
            'language': 'es'
        }
    ]
}

# Topic categories and their limits
TOPIC_CATEGORIES = {
    'politics': {'limit': 4, 'keywords': ['politics', 'government', 'election', 'policy']},
    'business': {'limit': 4, 'keywords': ['business', 'economy', 'finance', 'market']},
    'technology': {'limit': 4, 'keywords': ['technology', 'tech', 'digital', 'innovation']},
    'health': {'limit': 3, 'keywords': ['health', 'medical', 'healthcare', 'medicine']},
    'sports': {'limit': 3, 'keywords': ['sports', 'football', 'soccer', 'basketball']},
    'entertainment': {'limit': 2, 'keywords': ['entertainment', 'celebrity', 'movie', 'music']},
    'science': {'limit': 3, 'keywords': ['science', 'research', 'study', 'discovery']},
    'environment': {'limit': 3, 'keywords': ['environment', 'climate', 'nature', 'green']},
    'general': {'limit': 5, 'keywords': ['news', 'world', 'international', 'breaking']}
}

# Content quality thresholds
QUALITY_THRESHOLDS = {
    'min_word_count': 100,
    'max_word_count': 5000,
    'min_quality_score': 0.6,
    'required_fields': ['title', 'content', 'url']
}

# Language-specific prompts for Gemini API
LANGUAGE_PROMPTS = {
    'en': {
        'quiz_generation': """
Create a comprehensive quiz for this English news article. Generate 5 multiple-choice questions that test understanding of key facts, implications, and context. Each question should have 4 options with one correct answer.

Article: {article_content}

Format the response as JSON with questions, options, correct_answer, and explanation fields.
""",
        'content_analysis': """
Analyze this English news article and extract key information including main topics, entities, and significance.

Article: {article_content}

Return a JSON object with: topic_category, geographic_focus, key_entities, and summary.
"""
    },
    'es': {
        'quiz_generation': """
Crea un cuestionario completo para este artículo de noticias en español. Genera 5 preguntas de opción múltiple que evalúen la comprensión de hechos clave, implicaciones y contexto. Cada pregunta debe tener 4 opciones con una respuesta correcta.

Artículo: {article_content}

Formatea la respuesta como JSON con campos de preguntas, opciones, respuesta_correcta y explicación.
""",
        'content_analysis': """
Analiza este artículo de noticias en español y extrae información clave incluyendo temas principales, entidades y significado.

Artículo: {article_content}

Devuelve un objeto JSON con: categoria_tema, enfoque_geografico, entidades_clave, y resumen.
"""
    }
}

# Cache keys for Redis
CACHE_KEYS = {
    'api_usage': 'content_acquisition:api_usage:{api_name}',
    'daily_topic_counts': 'content_acquisition:topic_counts:{language}:{date}',
    'source_status': 'content_acquisition:source_status:{source_name}',
    'acquisition_lock': 'content_acquisition:lock:cycle',
    'duplicate_hashes': 'content_acquisition:duplicates'
}

# Cache timeouts (in seconds)
CACHE_TIMEOUTS = {
    'api_usage': 86400,  # 24 hours
    'topic_counts': 86400,  # 24 hours
    'source_status': 3600,  # 1 hour
    'acquisition_lock': 7200,  # 2 hours
    'duplicate_hashes': 604800  # 7 days
}

def get_newsdata_api_key() -> str:
    """Get NewsData.io API key from environment."""
    return getattr(settings, 'NEWSDATA_API_KEY', None) or ''

def get_gemini_api_key() -> str:
    """Get Gemini API key from environment."""
    return getattr(settings, 'GEMINI_API_KEY', None) or ''

def get_acquisition_enabled() -> bool:
    """Check if automated content acquisition is enabled."""
    return getattr(settings, 'ENABLE_AUTOMATED_CONTENT_ACQUISITION', True)

def get_max_concurrent_acquisitions() -> int:
    """Get maximum number of concurrent acquisition processes."""
    return getattr(settings, 'MAX_CONCURRENT_ACQUISITIONS', 3)