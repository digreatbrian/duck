"""
Import your views here, make sure to include them in __all__ list. This
ensures your views don't get removed when different formatters
format your python files.

*Note:* Adding views to __all__ is not mandatory.

"""
from ..templates.components.email import SimpleEmail
from ..mail import send_email

#send_email(
#        to=to_email,
#        subject="Welcome to Our Service",
#        name="Duck framework",
#        body=template.content.decode('utf-8'),
#    )

def receive_email_view(request):
    # Lets send ourself an email
    to_email = "digreatbrian@gmail.com"
    return SimpleEmail(
        heading="Feedback from John Doe",
        subheading="Email: johndoe@gmail.com",
        body="Hello there",
    ).to_string()
    