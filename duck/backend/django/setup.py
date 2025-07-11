"""
Django setup module.
"""
import os
import django

from duck.settings import SETTINGS

    
def prepare_django(setup: bool = False):
    """
    Sets up Django settings if they are not already configured.  
    This is useful when running Django-specific tasks that require access  
    to the settings module, such as database operations or management commands.
    
    Args:
        setup (bool): Whether to setup Django if django apps not ready.
    """
    from django.apps import apps
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", SETTINGS['DJANGO_SETTINGS_MODULE'])
    
    if setup and not apps.ready:
        django.setup()
