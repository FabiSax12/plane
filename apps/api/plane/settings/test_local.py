"""Local Test Settings — runs without Docker (uses local PostgreSQL)."""

import os
import dj_database_url

from .test import *  # noqa

# Use local PostgreSQL — override via DATABASE_URL env var if desired
_DEFAULT_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:CONTRASEÑAPOSTGRE@localhost:5432/plane_test",
)
DATABASES = {
    "default": dj_database_url.parse(_DEFAULT_DB_URL),
}

# Provide a base URL so auth views (base_host) don't crash
APP_BASE_URL = "http://localhost:3000"
WEB_URL = "http://localhost:3000"

# Disable Redis — use local-memory cache instead
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Run Celery tasks synchronously
CELERY_TASK_ALWAYS_EAGER = True

# Provide a dummy Redis URL — redis.Redis.from_url is lazy (no actual connection)
# and with CELERY_TASK_ALWAYS_EAGER = True no task ever touches it.
REDIS_URL = "redis://localhost:6379/0"
REDIS_SSL = False

# Disable S3 / Minio storage — use local file storage
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
AWS_S3_ENDPOINT_URL = None
USE_MINIO = False