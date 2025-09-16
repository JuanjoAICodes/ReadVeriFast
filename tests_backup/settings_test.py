# Test-specific Django settings
from .settings import *  # noqa: F403

# Test database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
DEBUG = True
SECRET_KEY = "test-secret-key-for-testing-only"

# Disable external API calls during testing
GEMINI_API_KEY = "test-key"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Test Redis configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Logging for tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "verifast_app": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

# Static files for testing
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
