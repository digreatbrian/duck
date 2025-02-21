from django.db import models

class Feedback(models.Model):
    """
    Model for storing feedback submissions. This model holds information about the user's full name, 
    email, and feedback content submitted through the FeedbackForm.

    Attributes:
        full_name (str): The full name of the person providing feedback.
        email (str): The email address of the person providing feedback.
        feedback (str): The feedback content submitted by the user.
        submission_date (datetime): The date and time when the feedback was submitted.
    """
    
    full_name = models.CharField(max_length=64)
    """
    The full name of the person providing feedback.
    
    Attributes:
        max_length (int): The maximum length of the name.
    """
    
    email = models.EmailField(max_length=64)
    """
    The email address of the person providing feedback.
    
    Attributes:
        max_length (int): The maximum length of the email address.
    """
    
    feedback = models.TextField()
    """
    The feedback content provided by the user.
    
    Attributes:
        blank (bool): Allows this field to be empty.
    """
    
    submission_date = models.DateTimeField(auto_now_add=True)
    """
    The date and time when the feedback was submitted.
    
    Attributes:
        auto_now_add (bool): Automatically set the date and time when the feedback is created.
    """
    
    def __str__(self):
        """
        String representation of the Feedback model, returning the full name and feedback.
        """
        return f"Feedback from {self.full_name}: {self.feedback[:50]}..."
