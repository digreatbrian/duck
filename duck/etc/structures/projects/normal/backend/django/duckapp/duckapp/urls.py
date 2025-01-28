"""
Django URL Patterns Registration Module

This module is utilized by Django to register URL patterns using the Duck framework.

WARNING: Do not overwrite the `urlpatterns` variable as it contains all URL patterns registered using Duck.

Instead of overwriting `urlpatterns`, append your new URL patterns to the list.

Example Usage:
--------------
from duck.backend.django import urls as duck_urls

# Append new URL patterns
urlpatterns = duck_urls.urlpatterns + [
    # Your new URL patterns here
]
"""

from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import include, path
from django.contrib.auth.models import User
from duck.backend.django import urls as duck_urls


def login_view(request):
    print("View session: ", dict(request.session))
    print(request.user)
    if request.user.is_authenticated:
        return HttpResponse("User already logged in")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        username = request.POST["username"]
        password = request.POST["password"]

        if form.is_valid():
            user = form.get_user()
            print(user)
            login(request, user)
            print("Logged in, new session: ")
            print(request.session)
            request
            return HttpResponse("Logged in")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


def signup_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup")

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        # Create the user
        user = User.objects.create_user(username=username,
                                        email=email,
                                        password=password)

        # Log the user in after successful signup
        login(request, user)

        #messages.success(request, "Account created successfully!")
        return redirect("home")  # Redirect to home after signup

    return render(request, "signup.html")


urlpatterns = duck_urls.urlpatterns + [
    # Your new URL patterns here eg.
    # path("", include("backend.django.duckapp.xxx"))
    path("admin/", admin.site.urls),
    path("login", login_view, name="login"),
    path("signup", signup_view, name="signup"),
    path("home", lambda x: HttpResponse("Home page"), name="home"),
]
