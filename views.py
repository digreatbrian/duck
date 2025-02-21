
from datetime import datetime, timezone
from duck.backend.django.utils import to_django_uploadedfile
from duck.shortcuts import render
from duck.utils.validation import (
    validate_email,
    validate_phone,
)
from duck.http.mimes import guess_data_mimetype
from duck.http.response import JsonResponse

from backend.django.duckapp.core.models import (
    JobApplication,
    Job
)

def home_view(request):
    ctx = {}
    return render(request, "index.html", ctx, engine="django")


def about_view(request):
    ctx = {}
    return render(request, "about.html", ctx, engine="django")


def contact_view(request):
    ctx = {}
    return render(request, "contact.html", ctx, engine="django")


def services_view(request):
    ctx = {}
    return render(request, "services.html", ctx, engine="django")


def consultation_view(request):
    ctx = {}
    return render(request, "consultation.html", ctx, engine="django")


def jobs_view(request):
    ctx = {}
    return render(request, "jobs.html", ctx, engine="django")


def job_application_view(request, job_id):
    POST = request.POST
    FILES = request.FILES
    ctx = {}
    
    def get_job_application_response(job_id) -> dict:
        """
        Returns job application status as a dictionary
        """
        fullname = POST.get("fullname", "").strip()
        email = POST.get("email", '').strip()
        phone = POST.get("phone", "").strip()
        cover_letter = POST.get("cover_letter", "").strip()
        resume = FILES.get('resume', None)
            
        # Form validation
        if not fullname:
            return {"error": "Name required"}
        
        if not email:
            return {"error": "Email required"}
        
        if not validate_email(email):
            return {"error": "Email not valid"}
        
        if not phone:
            return {"error": "Phone required"}
        
        if not validate_phone(phone):
            return {"error": "Phone not valid"}
       
        if not resume:
            return {"error": "Resume required"}
       
        # Validate the data type and size of resume file
        # Docx, Doc & Pdf respectively
        valid_mimetypes = ("application/zip", "application/msword", "application/pdf")
        first_bytes = resume.read(16)
       
        if guess_data_mimetype(first_bytes) not in valid_mimetypes:
           return {"error": "Uknown resume file. Allowed file types: .pdf, .doc, .docx"}
       
        # Check resume size
        # Move cursor to end of file
        resume.seek(0, 2) # end of file
        size = resume.tell()
        resume.seek(0) # move to start of file
       
        if size > 2.097152e6: # 2MB
           return {"error": "Resume too large, should be a max of 2 MB"}
       
        job = None
        
        try:
           job_id = int(job_id)
           job = Job.objects.get(job_id=job_id)
           utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)  # Current UTC time

           if job.expiration_date:
              # Make sure job.expiration_date is aware (in UTC)
              if job.expiration_date.tzinfo is None:
                  job.expiration_date = job.expiration_date.replace(tzinfo=timezone.utc)
            
           if job.expiration_date and job.expiration_date <= utc_now:
               return {"error": f"Job with id: {job_id} expired"}
        except Job.DoesNotExist:
            return {"error": f"Job with id: {job_id} doesn't exist anymore"}
        except Exception:
           return {"error": f"Error retrieving job with id: {job_id}"}
       
        # Everything is ok, continue
        try:
           job_application = JobApplication.objects.get(fullname=fullname, email=email)
           
           if job_application.job.job_id == job.job_id:
               return {"error": "You have already applied for the job"}
        except JobApplication.DoesNotExist:
           pass
       
       # Create and save new application
        job_application = JobApplication(
           job=job,
           fullname=fullname,
           email=email,
           phone=phone,
           cover_letter=cover_letter,
           resume=to_django_uploadedfile(resume)
        )
       
       # Save job application
        job_application.save()
        return {"success": "Application submitted"}
       
    if request.method == "POST":
        try:
            response = get_job_application_response(job_id)
            if "error" in response:
                return JsonResponse(content=response, status_code=400)
            return JsonResponse(content=response)
        except Exception:
            response = {"error": "Error processing request"}
            return JsonResponse(content=response, status_code=400)
        
    return render(request, "job-application.html", ctx, engine="django")


def receive_email_view(request):
    return "Email received"


def privacy_view(request):
    ctx = {}
    return render(request, "privacy_policy.html", ctx, engine="django")


def tos_view(request):
    ctx = {}
    return render(request, "tos.html", ctx, engine="django")
