"""
You can store your application `views` in a `single file` (this file) or use a `folder module` for better organization.
A folder module allows you to group different views into separate files and access them in `__init__.py`, making it easier to manage and scale your application.
This approach keeps your codebase clean and improves maintainability.

Example views:

```py
from duck.shortcuts import to_response

def home(request):
	return "<b>Hello world</b>"

def about(request):
	return to_response("This is the about page") # Produces HttpResponse object for the provided content.
```
"""
