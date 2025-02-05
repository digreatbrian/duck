"""
DJANGO Settings configuration file integrated with DUCK settings.

WARNING: It is not recommended to modify any variables modified by Duck, 
only modify these if you know what you are doing!
"""

import os
from pathlib import Path

from duck.backend.django.logging import SIMPLE_CONFIG
from duck.settings import SETTINGS as DUCK_SETTINGS


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = DUCK_SETTINGS["SECRET_KEY"]  #!: duck modified


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = DUCK_SETTINGS["DEBUG"]  #!: duck modified


# WARNING: don't modify this! This allows Django to only accept requests from Duck.
#!: Modified by Duck
ALLOWED_HOSTS = [
    DUCK_SETTINGS["DJANGO_SHARED_SECRET_DOMAIN"],
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Other apps here...
]


# Middleware configuration
MIDDLEWARE = [
    "duck.backend.django.middlewares.security.SecurityMiddleware",
    "duck.backend.django.middlewares.session.SessionMiddleware",
    "duck.backend.django.middlewares.common.CommonMiddleware",
    "duck.backend.django.middlewares.csrf.CsrfViewMiddleware",
    "duck.backend.django.middlewares.auth.AuthenticationMiddleware",
    "duck.backend.django.middlewares.messages.MessageMiddleware",
    "duck.backend.django.middlewares.clickjacking.XFrameOptionsMiddleware",
]  #!: duck-modified


# Routing Configuration.
# The main module containing all urlpatterns
# The default set is 'duckapp.urls'. This module contains all urlpatterns registered within Duck.
# **Note:** Add your urlpatterns to the urlpatterns list rather than overriding it to avoid disabling all
# urlpatterns registered with Duck.

ROOT_URLCONF = "duckapp.urls"


# Templates Configuration
#!: Modified by Duck 
TEMPLATE_DIRS = [str(i) for i in (DUCK_SETTINGS["TEMPLATE_DIRS"] or [])]


# Templates
# For all templates rendered on Django side (templates rendered using Django's render), all template tags, filters and
# html components are disabled by default.
# To use all these, use the following line in your templates:
#    {% load ducktags %}
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": TEMPLATE_DIRS, #:! duck-modified
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "libraries": {
                "ducktags": "duck.backend.django.templatetags.ducktags",
            }, #!: duck-modified
        },
        "debug": DUCK_SETTINGS["DEBUG"],  #!: duck-modified
    },
]


WSGI_APPLICATION = "duckapp.wsgi.application"


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

STATIC_URL = "x-static/"  #!: duck-modified


STATIC_ROOT = DUCK_SETTINGS["STATIC_ROOT"]  #!: duck-modified


# Media files (Other files)
MEDIAL_URL = "x-media/"  #!: duck-modified


MEDIA_ROOT = DUCK_SETTINGS["MEDIA_ROOT"]  #!: duck-modified


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Logging configuration
# **Note**: The default logging configuration set by Duck is compatible with Duck logging system.
#!: Modified by Duck
LOGGING = SIMPLE_CONFIG


# Other settings which allow Duck and Django synchronization.
# These ensures Django and Duck are in sync.

#!: Modified by Duck
SESSION_COOKIE_NAME = DUCK_SETTINGS["SESSION_COOKIE_NAME"]


#!: Modified by Duck
SESSION_EXPIRE_AT_BROWSER_CLOSE = DUCK_SETTINGS["SESSION_EXPIRE_AT_BROWSER_CLOSE"]


#!: Modified by Duck
# Session Duration
# The duration (in seconds) for which a session will remain active.
SESSION_COOKIE_AGE = DUCK_SETTINGS["SESSION_COOKIE_AGE"]


#!: Modified by Duck
# Session Cookie Path
SESSION_COOKIE_PATH = DUCK_SETTINGS["SESSION_COOKIE_PATH"]


#!: Modified by Duck
# Session Cookie Domain
SESSION_COOKIE_DOMAIN = DUCK_SETTINGS["SESSION_COOKIE_DOMAIN"]


#!: Modified by Duck
# Session Cookie Secure
# Whether session cookie should be accessed only on https
SESSION_COOKIE_SECURE = DUCK_SETTINGS["SESSION_COOKIE_SECURE"]


#!: Modified by Duck
# Session Cookie HttpOnly
# Whether session cookie should be accessible via http only (javascript not allowed)
SESSION_COOKIE_HTTPONLY = DUCK_SETTINGS["SESSION_COOKIE_HTTPONLY"]


#!: Modified by Duck
# Session Cookie SameSite
SESSION_COOKIE_SAMESITE = DUCK_SETTINGS["SESSION_COOKIE_SAMESITE"]


#!: Modified by Duck
CSRF_COOKIE_NAME = DUCK_SETTINGS["CSRF_COOKIE_NAME"]


#!: Modified by Duck
CSRF_HEADER_NAME = DUCK_SETTINGS["CSRF_HEADER_NAME"]


#!: Modified by Duck
CSRF_COOKIE_AGE = DUCK_SETTINGS["CSRF_COOKIE_AGE"]


#!: Modified by Duck
CSRF_COOKIE_PATH = DUCK_SETTINGS["CSRF_COOKIE_PATH"]


#!: Modified by Duck
CSRF_COOKIE_DOMAIN = DUCK_SETTINGS["CSRF_COOKIE_DOMAIN"]


#!: Modified by Duck
CSRF_COOKIE_SECURE = DUCK_SETTINGS["CSRF_COOKIE_SECURE"]


#!: Modified by Duck
CSRF_COOKIE_HTTPONLY = DUCK_SETTINGS["CSRF_COOKIE_HTTPONLY"]


#!: Modified by Duck
CSRF_COOKIE_SAMESITE = DUCK_SETTINGS["CSRF_COOKIE_SAMESITE"]


#!: Modified by Duck
CSRF_USE_SESSIONS = DUCK_SETTINGS["CSRF_USE_SESSIONS"]


#!: Modified by Duck
# Csrf Session Key
# The name for the csrf secret in request sessions.
CSRF_SESSION_KEY = DUCK_SETTINGS["CSRF_SESSION_KEY"]
