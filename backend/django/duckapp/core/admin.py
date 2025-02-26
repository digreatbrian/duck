from django.contrib import admin
from .models import (
    Job,
    JobApplication,
    ConsultationRequest,
    Feedback,
    Company,
)

admin.site.register(Job)
admin.site.register(JobApplication)
admin.site.register(ConsultationRequest)
admin.site.register(Feedback)
admin.site.register(Company)
