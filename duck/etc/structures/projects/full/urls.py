"""
This contains `URL patterns` to register for the application.

Example:

```py
from duck.urls import path
from . import views

urlpatterns = [
    path('/', views.home_view, 'home', ['GET'])
]
```
"""
from duck.urls import path, re_path


urlpatterns = [
    # add your urlpatterns here.
]
