"""
DJANGO Settings configuration file integrated with DUCK settings

WARNING: Please modify settings that uses Duck SETTINGS variable if you know what you are doing
"""

from pathlib import Path

from duck.settings import SETTINGS

# Build paths inside the project like this: BASE_DIR / 'subdir'. Duck home directory.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SETTINGS["SECRET_KEY"]  #!: duck modified

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = SETTINGS["DEBUG"]  #!: duck modified

# WARNING: don't modify this! Only allow requests from Duck App acting as Proxy
ALLOWED_HOSTS = [SETTINGS["DJANGO_SHARED_SECRET_DOMAIN"]]  #!: duck modified

SESSION_COOKIE_NAME = SETTINGS["SESSION_COOKIE_NAME"]  #!: duck modified

SESSION_ENGINE = SETTINGS["SESSION_ENGINE"]

CSRF_COOKIE_NAME = SETTINGS["CSRF_COOKIE_NAME"]

CSRF_HEADER_NAME = SETTINGS["CSRF_HEADER_NAME"]

CSRF_USE_SESSIONS = True

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "duck.backend.django.middlewares.security.SecurityMiddleware",
    "duck.backend.django.middlewares.datashare.DuckToDjangoMetaDataReceiverMiddleware",
    "duck.backend.django.middlewares.session.DuckSessionMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "duck.backend.django.middlewares.common.CommonMiddleware",
    "duck.backend.django.middlewares.csrf.CsrfViewMiddleware",
    "duck.backend.django.middlewares.auth.AuthenticationMiddleware",
    "duck.backend.django.middlewares.messages.MessageMiddleware",
    "duck.backend.django.middlewares.clickjacking.XFrameOptionsMiddleware",
    "duck.backend.django.middlewares.response_headers.ResponseHeadersMiddleware",
]  #!: duck modified

ROOT_URLCONF = "duckapp.urls"  #!: duck modified

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "duckapp/templates",  #!: duck-modified
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "libraries": {
                "ducktags":
                "duck.backend.django.templatetags.ducktags"  #!: duck-modified
            },
        },
    },
]

WSGI_APPLICATION = "duckapp.wsgi.application"  #!: duck modified

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
        "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = SETTINGS["STATIC_URL"]  #: duck-modified
STATIC_ROOT = SETTINGS["STATIC_ROOT"]  #: duck-modified

# Media files
MEDIAL_URL = SETTINGS["MEDIA_URL"]  #: duck-modified
MEDIA_ROOT = SETTINGS["MEDIA_ROOT"]  #: duck-modified

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
