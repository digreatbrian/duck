"""
Proxy module for Django which is essential for configuring urlpatterns registered with Duck to be accessible within Django. 
"""
import re
from typing import List

from django.urls import path, re_path
from django.views.decorators.http import require_http_methods

from duck.backend.django import views
from duck.backend.django.utils import duck_url_to_django_syntax
from duck.settings import SETTINGS
from duck.settings.loaded import (
    BLUEPRINTS,
    URLPATTERNS,
)
from duck.exceptions.all import (
    PortError,
    RouteError,
    BlueprintError,
)
from duck.setup import setup


try:
    # Ensure Duck app is properly set up
    setup(make_app_dirs=False)
except (RouteError, BlueprintError, PortError) as setup_error:
    # Catch setup errors but continue execution (e.g., if Duck app is already set up)
     pass


class DjangoURLConflict(RouteError):
    """
    Raised when a URL pattern that is said to be only known to Django has been 
    defined within Duck.
    """


def get_duck_urlpatterns() -> List:
    """
    Returns all urlpatterns registered within Duck including blueprint urlpatterns.
    """
    duck_urlpatterns = URLPATTERNS
    for blueprint in BLUEPRINTS:
        duck_urlpatterns.extend(blueprint.urlpatterns)
    return duck_urlpatterns


def get_correct_urlpatterns() -> List:
    """
    Returns all urlpatterns registered within Duck
    converted to urlpatterns understood by Django.
    """
    urlpatterns = []
    duck_urlpatterns = get_duck_urlpatterns()

    # make new django urlpatterns
    for urlpattern in duck_urlpatterns:
        url, name, methods = (
            urlpattern.get("url"),
            urlpattern.get("name", None),
            urlpattern.get("methods", []),
        )
        
        # Check if url is not matching DJANGO_SIDE_URLS
        # DJANGO_SIDE_URLS are only known to Django not Duck.
        django_side_urls = SETTINGS["DJANGO_SIDE_URLS"]
        regex_url = re.compile(url)
        
        if any([regex_url.fullmatch(i) for i in django_side_urls]):
            raise DjangoURLConflict(
                f"You seem to have defined that urlpattern '{urlpattern}' is only known to Django "
                f"according to DJANGO_SIDE_URLS setting, yet you added it to Duck urlpatterns."
            )
    
        # Strip left forward slash if present to suppress Django warnings
        url = url.lstrip("/")
        duck_django_view = views.duck_django_view
        
        if methods:
            duck_django_view = require_http_methods(methods)(views.duck_django_view)
        
        # add to django urlpatterns
        if urlpattern.regex:
            # This pattern is a regex url pattern
            urlpatterns.append(
                re_path(
                    "^" + url if not url.startswith('^') else url,
                    duck_django_view,
                    name=name,
                ))
        else:
            # its a normal url pattern
            url = duck_url_to_django_syntax(url)
            
            urlpatterns.append(
                path(
                    url,
                    duck_django_view,
                    name=name,
                ))
    return urlpatterns


urlpatterns = get_correct_urlpatterns()
