from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255)
    """
    The name of the company offering the job. Max length: 255 characters.
    """
    
    image = models.ImageField(
        upload_to="uploads/company_images",
        null=True, blank=True)
    """
    The image source for the company's logo or branding. This image is uploaded to 'company_images/'.
    Can be left blank or null if no image is provided.
    """
