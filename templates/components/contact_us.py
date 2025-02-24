from duck.html.components import InnerHtmlComponent
from duck.etc.templatetags import static
from duck.shortcuts import resolve

from theme import Theme
from .container import (
    FlexContainer,
    Container)
from .card import Card
from .video import Video
from .form import FeedbackForm
from .icon import IconLink
from .style import Style
from .script import Script


class ContactDetails(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["padding"] = Theme.padding
        self.style["gap"] = "20px"
        self.properties["id"] = "contact-us-details"
        
        # Add Email icon
        email_icon = IconLink(
            inner_body="<span class='icon email-icon bi bi-envelope fs-1' aria-label='Email'></span>",
            url="mailto:guzuzut@gmail.com?subject=Inquiry%20for%20Services&body=Hello,%0A%0A%20I%20would%20like%20to%20inquire%20about%20the%20services%20your%20company%20offers.%20Could%20you%20please%20provide%20more%20information%20on%20what%20services%20are%20available%20and%20the%20pricing%20details?%0A%0ALooking%20forward%20to%20hearing%20from%20you.%0A%0ABest%20regards,%0A[Your%20Name]")
        self.inner_body += email_icon.to_string()
        
        # Add Phone icon
        phone_icon = IconLink(
            inner_body="<span class='icon phone-icon bi bi-telephone fs-1' aria-label='Phone'></span>",
            url="tel:+263774174175")
        self.inner_body += phone_icon.to_string()
        
        # Add icon style
        style = Style(inner_body="""#contact-us-details span.icon {font-size: 3rem;}""")
        self.inner_body += style.to_string()


class Content(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        
        # Add heading
        self.inner_body += "<h2>Contact Us</h2>"
        
        # Add video
        video = Video(
            source=static('videos/contact-us.mp4'),
            autoplay=True,
            muted=True,
            loop=True,
            playsinline=True)
        
        video.style["width"] = "100%"
        video.style["object-fit"] = "contain"
        video.style["border"] = "1px solid #cccc"
        video.style["border-radius"] = Theme.border_radius
        
        self.inner_body += video.to_string()
        
        # Add About us content
        intro = """
        Get Expert Consultancy with Yannick Consultancy
        At Yannick, we provide expert guidance and tailored solutions to help you succeed. 
        Whether it's strategy, technology, or business growth, we’re here to assist."""
        self.inner_body += f"<p id='contact-intro' class='text-color-ccc'>{intro}</p>"
        
        # Add feedback heading and form
        self.inner_body += "<br>"
        self.inner_body += "<h1 class='text-color-ccc'>Provide some feedback</h1>"
        
        # Add feedback form
        form_container = FlexContainer()
        form_container.style["flex-direction"] = "column"
        form_container.style["gap"] = "5px"
        form_container.style["width"] = "100%"
        
        # Add feedback message
        feedback_msg = FlexContainer()
        feedback_msg.style["color"] = "#ccc"
        feedback_msg.style["padding"] = "5px"
        
        # Add feedback message
        if "feedback-message" in self.kwargs:
            msg = self.kwargs.get("feedback-message", "")
            feedback_msg.inner_body += msg
            
        form_container.add_child(feedback_msg)
        
        feedback_form = FeedbackForm(
            enctype="form/multipart-data",
            action="#feedback-form",
            method="post",
            **self.kwargs)
        feedback_form.style["width"] = "60%"
        feedback_form.properties["id"] = "feedback-form"
        
        # Add form to form container
        form_container.add_child(feedback_form)
        
        # Add form container
        self.inner_body += form_container.to_string()
        
        # Add contact details
        contact_details = ContactDetails(**self.kwargs)
        self.inner_body += contact_details.to_string()


class ContactUs(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["min-width"] = "80%"
        self.style["min-height"] = "200px"
        self.style["border"] = "1px solid #ccc"
        self.style['border-radius'] = Theme.border_radius
        self.style["padding"] = "20px"
        self.style["margin-top"] = "0px"
        self.style["color"] = "#ccc"
        self.style["backdrop-filter"] = "blur(20px)"
        self.style["font-size"] = "1.8rem"
        self.style["background-size"] = "cover"
        self.style["background-repeat"] = "no-repeat"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "15px"
        self.properties["id"] = "contact-us"
        
        # Add content
        context = self.kwargs.get('context')
        if "feedback-message" in context:
            self.kwargs["feedback-message"] = context.get('feedback-message')
        content = Content(**self.kwargs)
        self.add_child(content)
        