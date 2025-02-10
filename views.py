from duck.shortcuts import render


def home_view(request):
    ctx = {}
    return render(request, "index.html", ctx, engine="django")


def about_view(request):
    ctx = {}
    return render(request, "about.html", ctx, engine="django")
