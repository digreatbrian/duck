from django.db import models

class ConsultationRequest(models.Model):
    """
    Model to store a request for a consultation service. This includes the client's 
    details, preferred consultation time, and service type.

    Attributes:
        fullname (str): The full name of the person requesting the consultation.
        email (str): The email address of the person requesting the consultation.
        company (str): The name of the company the person represents.
        number_employees (int): The number of employees at the company.
        consultancy_service_type (str): Type of consultancy service requested (e.g., Strategy, HR, Operations).
        additional_info (str): Any additional details the client wants to provide about the consultation.
        preferred_date (date): The preferred date for the consultation.
        preferred_time (time): The preferred time for the consultation.
        consultation_channel (str): The preferred method of consultation (e.g., Phone call, Google Meeting).
        created_at (datetime): The timestamp of when the consultation request was created.
    """
    
    fullname = models.CharField(
        max_length=64,
        help_text="The full name of the person requesting the consultation."
    )
    email = models.EmailField(
        max_length=64,
        help_text="The email address of the person requesting the consultation."
    )
    company = models.CharField(
        max_length=64,
        help_text="The name of the company the person represents."
    )
    number_employees = models.IntegerField(
        help_text="The number of employees at the company."
    )
    consultancy_service_type = models.CharField(
        max_length=64,
        choices=[
            ("Strategy Consulting", "Strategy Consulting"),
            ("Human Resources (HR) Consulting", "Human Resources (HR) Consulting"),
            ("Operations Consulting", "Operations Consulting"),
        ],
        help_text="Type of consultancy service requested (e.g., Strategy, HR, Operations)."
    )
    additional_info = models.TextField(
        blank=True, null=True,
        help_text="Any additional details the client wants to provide about the consultation."
    )
    preferred_date = models.DateField(
        help_text="The preferred date for the consultation."
    )
    preferred_time = models.TimeField(
        help_text="The preferred time for the consultation."
    )
    consultation_channel = models.CharField(
        max_length=64,
        choices=[("Phone call", "Phone call"), ("Google Meeting", "Google Meeting")],
        help_text="The preferred method of consultation (e.g., Phone call, Google Meeting)."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The timestamp of when the consultation request was created."
    )
    

    def __str__(self):
        """
        Returns a string representation of the consultation request.
        
        The representation includes the full name and company of the person requesting 
        the consultation for easier identification.
        
        Returns:
            str: A string representation of the ConsultationRequest object.
        """
        return f"ConsultationRequest from {self.fullname} ({self.company})"

    class Meta:
        """
        Meta options for the ConsultationRequest model.

        - ordering: Orders the ConsultationRequest objects by creation date, with the most 
          recent request appearing first.
        """
        ordering = ['-created_at']  # Order by most recent first
