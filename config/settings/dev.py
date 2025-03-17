from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "http://localhost:3000",
    "http://localhost:8000",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

STATIC_ROOT = None
