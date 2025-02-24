import os
import smtplib

from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# Load environment variables
load_dotenv()

GMAIL_ACCOUNT = os.getenv("GMAIL_ACCOUNT")

GMAIL_APP_PWD = os.getenv("GMAIL_APP_PWD", "").replace("\xa0", '') # \xa0 represents invisible empty spaces


class Gmail:
    """
    A class to compose and send an email via Gmail's SMTP server.

    This class allows you to create an email with a specified recipient, subject, sender's name, 
    body content, and Gmail app password. The email is sent using SMTP, and the connection is secured 
    with TLS. The email is sent from the sender's Gmail account to the recipient's email address.

    Attributes:
        to (str): The recipient's email address.
        subject (str): The subject of the email.
        name (str): The sender's name that will appear in the "From" field of the email.
        body (str): The body content of the email.
        app_pwd (str): The Gmail app password used for authentication. Defaults to `GMAIL_APP_PWD`.
        from_ (str): The sender's email address. Defaults to `GMAIL_ACCOUNT`.

    Methods:
        send(): Sends the composed email via the Gmail SMTP server.
    """

    def __init__(self, to: str, subject: str, name: str, body: str, app_pwd: str = GMAIL_APP_PWD, from_: str = GMAIL_ACCOUNT):
        """
        Initializes the Email instance with the given details.

        Args:
            to (str): Recipient's email address.
            subject (str): Subject of the email.
            name (str): Sender's name.
            body (str): Body content of the email.
            app_pwd (str, optional): Gmail app password. Defaults to `GMAIL_APP_PWD`.
            from_ (str, optional): Sender's email address. Defaults to `GMAIL_ACCOUNT`.
        """
        self.to = to
        self.subject = subject
        self.name = name
        self.body = body
        self.app_pwd = app_pwd
        self.from_ = from_
        self.is_sent = False

    def send(self):
        """
        Sends the email to the recipient using Gmail's SMTP server.

        This method connects to Gmail's SMTP server (`smtp.gmail.com`) on port 587, starts the TLS 
        encryption for secure communication, logs in using the sender's credentials, and sends the 
        email to the recipient.

        Raises:
            Exception: If an error occurs during the sending process (e.g., incorrect credentials, 
            network issues, or server problems), an exception is raised and logged.
        """
        send_email(
            to=self.to,
            subject=self.subject,
            name=self.name,
            body=self.body,
            app_pwd=self.app_pwd,
            from_=self.from_,
        )
        self.is_sent = True

    
def send_email(
    to: str,
    subject: str,
    name: str,
    body: str,
    app_pwd: str = GMAIL_APP_PWD,
    from_: str = GMAIL_ACCOUNT):
    """
    Send an email using SMTP with a simple HTML body.

    Args:
        to (str): The recipient's email address.
        subject (str): The subject of the email.
        name (str): The name of the recipient to personalize the email.
        body (str): The main content of the email.
        app_pwd (str): The Gmail app password (use an app-specific password or OAuth token).
        from_ (str, optional): The sender's email address. Defaults to `GMAIL_ACCOUNT`.

    Returns:
        None: This function does not return any value. It sends an email.
    
    Raises:
        Exception: If there is an error while sending the email, an exception will be raised.
    
    Example Usage:
        send_email(
            to="recipient@example.com",
            subject="Welcome to Our Service",
            name="John Doe",
            body="Thank you for signing up with us. We hope you enjoy our services!",
            app_pwd="your_generated_app_password_here"
        )
    """
    # Compose the email content with the recipient's name and body
    email_content = body
        
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = from_
    msg['To'] = to
    msg['Subject'] = subject
    
    # Attach the email body to the message
    msg.attach(MIMEText(email_content, 'html'))
    
    # Send the email via Gmail's SMTP server
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_, app_pwd)
        server.sendmail(from_, to, msg.as_string())
