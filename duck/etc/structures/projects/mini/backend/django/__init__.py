"""
Sets up Django settings if they are not already configured.  
This is useful when running Django-specific tasks that require access  
to the settings module, such as database operations or management commands.
"""
import os
import django

from django.apps import apps

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.django.duckapp.duckapp.settings")

if not apps.ready:
    django.setup()
