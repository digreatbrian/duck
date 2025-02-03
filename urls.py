"""
This contains URL patterns to register for the application.
"""
from duck.urls import re_path, path
from duck.shortcuts import render


def home_view(request):
    ctx = {}
    return render(request, "index.html", ctx)


urlpatterns = [
    
]
