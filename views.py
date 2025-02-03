"""
Use this for storing your application Views

.e.g:
	def home(request):
		return "<b>Hello world</b>"
"""
from duck.shortcuts import render


def home_view(request):
    ctx = {}
    return render(request, "index.html", ctx)
