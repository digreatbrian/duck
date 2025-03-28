"""
Form components module.

Available Forms:
- `Form`: Basic form component.
- `FeedbackForm`: Basic feedback form component.
"""
from duck.html.components import InnerHtmlComponent
from duck.html.components import Theme

from .input import Input, CSRFInput
from .textarea import TextArea


class Form(InnerHtmlComponent):
    """
    Basic Form component.
    
    Args:
        action (str): Form URL action.
        method (str): Form method.
        enctype (str): Form enctype
        fields (list[HtmlComponent]): List of html components, usually input html components.
    """
    def get_element(self):
        return "form"
    
    def on_create(self):
        if "action" in self.kwargs:
            self.properties["action"] = self.kwargs.get("action") or "#"
            
        if "method" in self.kwargs:
            self.properties["method"] = self.kwargs.get("method") or "post"
        
        if "enctype" in self.kwargs:
            self.properties["enctype"] = self.kwargs.get("enctype") or "multipart/form-data"
        
        if "fields" in self.kwargs:
            for field in self.kwargs.get("fields", []):
                field.style["border-radius"] = Theme.border_radius
                field.style["font-size"] = "1.5rem"
                if "class" in field.properties:
                    field.properties["class"] += " form-control"
                else:
                    field.properties["class"] = "form-control"
                self.inner_body += field.to_string()


class FeedbackForm(Form):
    """
    Feedback Form component.
    
    Notes:
    - Use this form directly inside a template so that it will be able to access the current
      request or parse context argument (dictionary with request key provided).
   - This is done to be so that the form will have the CSRF token (needed for security reasons).
        
    Available Fields:
    - `fullname` (Input): Text Input html component
    - `email` (Input): Email Input html component.
    - `feedback` (TextArea): TextArea html component.
    """
    def on_create(self):
        # Set form style
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "20px"
        self.style["padding"] = "10px"
        self.style["border-radius"] = Theme.border_radius
        self.style["border"] = "1px solid #ccc"
        
        self.properties["class"] = "feedback-form form"
        
        # Create fullname textfield
        fullname = Input(
            type="text",
            placeholder="Full Name",
            required=True,
            maxlength=64,
            name="fullname")
        
        email = Input(
            type="email",
            placeholder="Email",
            required=True,
            maxlength=64,
            name="email")
        
        textarea = TextArea(
            placeholder="What is it you like to say?",
            maxlength=255,
            required=True,
            name="feedback")
        
        textarea.properties["rows"] = "4"
        textarea.properties["cols"] = "50"
            
        submit = Input(type="submit", value="Submit",)
        submit.style["border"] = "none"
        submit.style["font-size"] = "1rem"
        submit.style["color"] = "#ccc"
        submit.style["background-color"] = "green"
        
        context = self.kwargs.get("context")
        request = context.get('request')
        
        self.kwargs["fields"] = [
            CSRFInput(request=request),
            fullname,
            email,
            textarea,
            submit]
        
        # Super Create
        super().on_create()
