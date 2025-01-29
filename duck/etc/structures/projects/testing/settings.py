import os
from duck.meta import Meta


# This allows additional settings to be loaded via an environment variable.
extra_settings = Meta.get_metadata("DUCK_EXTRA_SETTINGS") or {}


# Minimum URL Configuration
URLPATTERNS_MODULE = "duck.etc.structures.projects.testing.urls"


for key, value in extra_settings.items():
    globals()[key.upper()] = value
