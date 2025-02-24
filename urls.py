"""
This contains URL patterns to register for the application.
"""
from duck.urls import re_path, path


import views


urlpatterns = [
    path("/", views.home_view, name="home"),
    path("/about", views.about_view, name="about"),
    path("/contact", views.contact_view, name="contact"),
    path("/services", views.services_view, name="services"),
    path("/consultation", views.consultation_view, name="consultation"),
    path("/jobs", views.jobs_view, name="jobs"),
    path("/job-application/<job_id>", views.job_application_view, name="job-application"),
    path("/privacy", views.privacy_view, name="privacy"),
    path("/terms-and-conditions", views.tos_view, name="tos"),
]
