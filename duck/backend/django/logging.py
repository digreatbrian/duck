"""
Logging configuration for Django, ensuring compatibility with Duck logs.
"""
from duck.logging import logger
from duck.settings import SETTINGS


LATEST_LOGFILE = logger.get_current_log_file()

HANDLERS = ["error_console"]

if SETTINGS["LOG_TO_FILE"]:
    HANDLERS.append("error_file")

# Simple Logging Configuration,
# This only log exceptions to console and to file (if LOG_TO_FILE=True) and then
# Duck will handle the rest of the logs (e.g. responses)
SIMPLE_CONFIG  = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "exception_only": {
            "format": "{message}",
            "style": "{"
        }
    },
    "handlers": {
        "error_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": LATEST_LOGFILE,
            "formatter": "exception_only",
        },
        "error_console": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "exception_only",
        },
    },
    "loggers": {
        "django": {
            "handlers": HANDLERS,
            "level": "ERROR",
            "propagate": True,
        },
        # Disable other default loggers if needed
        'django.server': {
            'handlers': HANDLERS,
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


if SETTINGS["DJANGO_SILENT"]:
    # Disable Django console and file logs
    # Disable all logging, regardless of the level
    SIMPLE_CONFIG = {
        "version": 1,
        "disable_existing_loggers": True,  # Disable all existing loggers
        "handlers": {
            "null": {
                "class": "logging.NullHandler",  # Discard all logs
            },
        },
        "root": {
            "handlers": ["null"],
        },
        "loggers": {
            "*": {  # Match all loggers
                "handlers": ["null"],
                "propagate": False,
            },
        },
    }
