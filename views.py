
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator, EmptyPage

from duck.backend.django.utils import to_django_uploadedfile
from duck.shortcuts import render
from duck.utils.dateutils import parse_date, parse_time
from duck.utils.urlcrack import URL
from duck.utils.safemarkup import mark_safe
from duck.utils.validation import (
    validate_email,
    validate_phone,
)
from duck.http.mimes import guess_data_mimetype
from duck.http.response import (
    JsonResponse,
    HttpBadRequestResponse,
    HttpResponse,
)
from duck.etc.templatetags import resolve

from backend.django.duckapp.core.models import (
    JobApplication,
    Feedback, Job,
    ConsultationRequest,
)
from apps.mail.mail import (
    Gmail,
    render_email,
    GMAIL_ACCOUNT,
)
from automations import queue_email
from templates.components.jobs_page import JobCard


def home_view(request):
    ctx = {}
    return render(request, "index.html", ctx, engine="django")


def about_view(request):
    ctx = {}
    return render(request, "about.html", ctx, engine="django")


def contact_view(request):
    ctx = {}
    
    if request.method == "POST":
        # This is a feedback
        POST = request.POST
        try:
            fullname = POST["fullname"][0]
            email = POST["email"][0]
            feedback = POST["feedback"][0]
            
            feedback = Feedback(
                full_name=fullname,
                email=email,
                feedback=feedback,
            )
            feedback.save()
            ctx["feedback-message"] = "<p style='color: green'>Successfully submitted feedback</p>"
            
            # Schedule an email to us
            admin_site = resolve('home', fallback_url="#")
            
            if admin_site != "#":
                admin_site = URL(admin_site).innerjoin("admin").to_str()
                
            our_email = Gmail(
                to="digreatbrian@gmail.com",
                subject="New feedback",
                name="Yannick Web",
                body=render_email(
                    context={
                        "request": request,
                        "heading": f"New feedback from {fullname}",
                        "subheading": f"Email: {email}",
                        "body": f"{feedback}<br><br>Attend to this directly in Admin site: %s"%(admin_site),
                    }
                 ),
                 recipients=[GMAIL_ACCOUNT], # Also send a copy to official company email (the one responsible for sending emails)
                 use_bc=True,
            )
            
            # Schedule the email
            queue_email(our_email)
        except Exception:
            ctx["feedback-message"] = "<p style='color: red'>Error submitting feedback</p>"
    return render(request, "contact.html", ctx, engine="django")


def services_view(request):
    ctx = {}
    return render(request, "services.html", ctx, engine="django")


def consultation_view(request):
    ctx = {}
    POST = request.POST
    
    def get_consultation_response() -> dict:
        """
        Returns consultation status as a dictionary
        """
        fullname = POST.get("fullname", "").strip()
        email = POST.get("email", "").strip()
        company = POST.get("company", "").strip()
        employees = POST.get("number_employees", "").strip()
        consultancy_service_type = POST.get("consultancy_service_type", "").strip()
        consultation_channel = POST.get("consultation_channel", "").strip()
        additional_info = POST.get("additional_info", "").strip()
        preferred_date = POST.get("preferred_date", "").strip()
        preferred_time = POST.get("preferred_time", "").strip()
    
        # Form validation
        required_fields = {
            "fullname": fullname,
            "email": email,
            "company": company,
            "number_employees": employees,
            "consultancy_service_type": consultancy_service_type,
            "consultation_channel": consultation_channel,
            "preferred_date": preferred_date,
            "preferred_time": preferred_time,
        }
    
        for field, value in required_fields.items():
            if not value:
                return {"error": f"{field.replace('_', ' ').title()} is required"}
        
        try:
            preferred_date = parse_date(
                preferred_date.replace('/', '-'), "%d-%m-%Y")
        except Exception:
            try:
                # try in different format for the last time
                preferred_date = parse_date(
                    preferred_date.replace('/', '-'), "%Y-%m-%d")
            except Exception:
                return {"error": "Error parsing preferred date"}
        
        try:
            preferred_time = parse_time(preferred_time, "%H:%M")
        except Exception:
            return {"error": "Error parsing preferred time"}
        
        consultation = ConsultationRequest(
            fullname=fullname,
            email=email,
            company=company,
            number_employees=int(employees),
            consultancy_service_type=consultancy_service_type,
            consultation_channel=consultation_channel,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
        )
        
        consultation.save()
        
        # Schedule an email to us
        admin_site = resolve('home', fallback_url="#")
        
        if admin_site != "#":
            admin_site = URL(admin_site).innerjoin("admin").to_str()
        
        # Schedule ourselves an email
        our_email = Gmail(
            to="digreatbrian@gmail.com",
            subject="New consultation request",
            name="Yannick Web",
            body=render_email(
                context={
                    "request": request,
                    "heading": f"New consultation request from {fullname}",
                    "subheading": f"Email: {email}",
                    "body": f"Attend to this directly in Admin site: %s"%(admin_site),
                }
            ),
            recipients=[GMAIL_ACCOUNT], # Also send a copy to official company email (the one responsible for sending emails)
            use_bc=True,
         )
        
        # Schedule client email also
        client_email = Gmail(
            to=email,
            subject="Consultation at Yannick",
            name="Yannick Consultancy",
            body=render_email(
                context={
                    "request": request,
                    "heading": f"Consultancy service at Yannick Consultancy",
                    "subheading": f"Consultancy Service: {consultancy_service_type}",
                    "body": "We have received your consultation request, we will get back to you soon. Thank you for choosing Yannick Consultancy.",
                },
            )
         )
        
        # Schedule the emails
        emails = [client_email, our_email]
        [queue_email(email) for email in emails]
        return {"success": "Consultation request has been submitted"}
       
    if request.method == "POST":
        try:
            response = get_consultation_response()
            if "error" in response:
                return JsonResponse(content=response, status_code=400)
            return JsonResponse(content=response)
        except Exception:
            response = {"error": "Error processing request"}
            return JsonResponse(content=response, status_code=400)
    
    return render(request, "consultation.html", ctx, engine="django")


def jobs_view(request):
    ctx = {}
    GET = request.GET
    if "page" in GET:
        try:
            page = GET.get("page", [1])[0]
            page = int(page)
            job_list = Job.objects.all().order_by('-created_at')
            
            if not job_list:
                response = HttpResponse("No more jobs")
                response.set_header("x-no-more-jobs", "true")
                return response
            
            paginator = Paginator(job_list, 10)
            page_obj = paginator.page(page)
            current_jobs = page_obj.object_list
            
            jobs_as_html = "".join([JobCard(job=job).to_string() for job in current_jobs])
            response = HttpResponse(jobs_as_html)
            return response
        
        except EmptyPage:
            response = HttpResponse("No more jobs")
            response.set_header("x-no-more-jobs", "true")
            return response
        
        except Exception:
            return HttpBadRequestResponse("Error retrieving jobs")
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
           if job.expired:
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
        
        # Schedule an email to us
        admin_site = resolve('home', fallback_url="#")
        
        if admin_site != "#":
            admin_site = URL(admin_site).innerjoin(
                "/admin/?next=/core/job-applications").to_str()
            
        # Schedule ourselves an email
        our_email = Gmail(
            to="digreatbrian@gmail.com",
            subject="New Job Application",
            name="Yannick Web",
            body=render_email(
                context={
                    "request": request,
                    "heading": f"New job application from {fullname}",
                    "subheading": mark_safe(f"Role: {job.title}<br>Email: {email}"),
                    "body": mark_safe("Attend to this directly in <a href='%s'>Admin site</a>"%(admin_site)),
                }
            ),
            recipients=[GMAIL_ACCOUNT], # Also send a copy to official company email (the one responsible for sending emails)
            use_bc=True,
         )
        
        # Schedule client email also
        client_email = Gmail(
            to=email,
            subject="Job application at Yannick",
            name="Yannick Consultancy",
            body=render_email(
                context={
                    "request": request,
                    "heading": f"Job application for {job.title} role at Yannick Consultancy",
                    "subheading": f"Hey job applicant👋",
                    "body": "We have received your job application, we will get back to you as soon as possible.",
                },
            )
         )
        
        # Schedule the emails
        emails = [client_email, our_email]
        [queue_email(email) for email in emails]
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
    ctx["job_id"] = job_id # Set Job ID
    return render(request, "job-application.html", ctx, engine="django")


def privacy_view(request):
    ctx = {}
    return render(request, "privacy_policy.html", ctx, engine="django")


def tos_view(request):
    ctx = {}
    return render(request, "tos.html", ctx, engine="django")
