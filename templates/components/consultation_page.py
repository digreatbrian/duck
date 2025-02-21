from duck.etc.templatetags import static
from duck.html.components.input import CSRFInput
from duck.html.components.select import  Select, Option
from theme import Theme

from .container import FlexContainer
from .style import Style
from .form import Form, TextArea, InputField
from .video import Video


class ConsultationPageStyle(Style):
    def on_create(self):
        super().on_create()
        self.inner_body += """
        .consultation-form input, button, textarea, select, checkbox {
            font-size: 1.75rem !important;
            border-radius: {border_radius} !important;
        }
        """.replace("{border_radius}", Theme.border_radius)


class ConsultationVideo(Video):
    def on_create(self):
        self.style["width"] = "100%"
        self.style["object-fit"] = "contain"
        self.style["border"] = "1px solid #cccc"
        self.style["border-radius"] = Theme.border_radius
        super().on_create()


class InputWithLabel(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["gap"] = "10px"
        self.style["flex-direction"] = "column"
        
        if "label_text" in self.kwargs:
            label_text = self.kwargs.get('label_text', '')
            label = f"<label>{label_text}</label>"
            self.inner_body += label
        
        if "input" in self.kwargs:
            inputfield = self.kwargs.get('input', '')
            if inputfield:
                inputfield = inputfield.to_string()
            self.inner_body += inputfield


class ConsultationForm(Form):
    def on_create(self):
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "10px"
        self.style["padding"] = "10px"
        self.style["background-color"] = "transparent"
        self.style["backdrop-filter"] = "blur(50px)"
        self.style["border-radius"] = Theme.border_radius
        self.style["border"] = "1px solid #ccc"
        
        self.properties["class"] = "consultation-form form"
        
        # Creating input fields
        # Create fullname textfield
        fullname = InputWithLabel(
            label_text="Full Name",
            input=InputField(
                type="text",
                name="fullname",
                placeholder="Full Name",
                required=True,
                maxlength=64,
            )
        )
        
        email = InputWithLabel(
            label_text="Email",
            input=InputField(
                type="email",
                name="email",
                placeholder="Email",
                required=True,
                maxlength=64,
            )
        )
        
        company = InputWithLabel(
            label_text="Company",
            input=InputField(
                type="text",
                name="company",
                placeholder="Name of company",
                required=True,
                maxlength=64,
            )
        )
        
        number_employees = InputWithLabel(
            label_text="Employees",
            input=InputField(
                type="number",
                name="number_employees",
                placeholder="Number of employees",
                required=True,
                maxlength=64,
            )
        )
        
        consultancy_service_type = InputWithLabel(
            label_text="Consultancy Service Type",
            input=Select(
                options = [
                    "Strategy Consulting",
                    "Human Resources (HR) Consulting",
                    "Operations Consulting",
                ],
                properties={"required": "true", "name": "consultancy_service_type"},
            )
        )
        
        additional_info = InputWithLabel(
            label_text="Additional Information",
            input=TextArea(
                name="additional_info",
                placeholder="Additional details, including service wanted and other information",
                properties={"rows": "5", "cols": "50"},
            )
        )
        
        preferred_date = InputWithLabel(
            label_text="Preferred Date",
            input=InputField(
                name="preferred_date",
                type="date",
                placeholder="Your preferred date",
                properties={"required": "true"}
            )
        )
        
        preferred_time = InputWithLabel(
            label_text="Preferred Time",
            input=InputField(
                name="preferred_time",
                type="time",
                placeholder="Your preferred time",
                properties={"required": "true"}
            )
        )
        
        consultation_channel = InputWithLabel(
            label_text="Consultation channel",
            input=Select(
                options=["Phone call", "Google Meeting"],
                properties={"required": "true", "name": "consultation_channel"},
            )
        )
        
        submit = InputField(
            value="Request consultancy service",
            type="button")
        
        submit.style["background-color"] = "transparent"
        submit.style["backdrop-filter"] = "blur(50px)"
        submit.style["color"] = "#ccc"
        
        notification_label = InputWithLabel(
            label_text="We will confirm your consultation in about 24 hours!",
            properties={
                "class": "text-center",
            }
         )
        
        # Super create
        context = self.kwargs.get("context")
        request = context.get('request')
        
        self.kwargs["fields"] = [
            CSRFInput(request=request),
            fullname,
            email,
            company,
            number_employees,
            consultancy_service_type,
            consultation_channel,
            additional_info,
            preferred_date,
            preferred_time,
            submit,
        ]
        
        # Super Create
        super().on_create()
        
        # Add notification label
        self.inner_body += notification_label.to_string()


class ConsultationPage(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["min-width"] = "80%"
        self.style["min-height"] = "200px"
        self.style["border"] = "1px solid #ccc"
        self.style['border-radius'] = Theme.border_radius
        self.style["padding"] = "20px"
        self.style["margin-top"] = "10px"
        self.style["color"] = "#ccc"
        self.style["backdrop-filter"] = "blur(20px)"
        self.style["background-size"] = "cover"
        self.style["background-repeat"] = "no-repeat"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "15px"
        self.style["align-items"] = "center"
        self.properties["id"] = "consultation-page"
