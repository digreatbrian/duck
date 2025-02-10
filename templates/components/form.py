from duck.html.components import InnerHtmlComponent
from duck.html.components.input import Input, CSRFInput
from duck.html.components.textarea import TextArea
from theme import Theme

class Form(InnerHtmlComponent):
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
                    field.properties["class"] += " form-group"
                else:
                    field.properties["class"] = "form-group"
                self.inner_body += field.to_string()


class InputField(Input):
    def on_create(self):
        self.properties["min-width"] = "50%"
        self.properties["min-height"] = "60px"
        
        super().on_create()
        
        if "type" in self.kwargs:
            self.properties["type"] = self.kwargs.get('type') or ''
        
        if "placeholder" in self.kwargs:
            placeholder = self.kwargs.get('placeholder') or ''
            self.properties["placeholder"] = placeholder
       
        if "required" in self.kwargs:
            self.properties["required"] = "true"
       
        if "maxlength" in self.kwargs:
           self.properties["maxlength"] = str(self.kwargs.get('maxlength')) or ''  


class TextArea(TextArea):
     def on_create(self):
        self.properties["min-width"] = "50%"
        self.properties["min-height"] = "80px"
        super().on_create()
        
        if "type" in self.kwargs:
            self.properties["type"] = self.kwargs.get('type') or ''
        
        if "placeholder" in self.kwargs:
            placeholder = self.kwargs.get('placeholder') or ''
            self.properties["placeholder"] = placeholder
        
        if "required" in self.kwargs:
            self.properties["required"] = "true"
            
        if "maxlength" in self.kwargs:
           self.properties["maxlength"] = str(self.kwargs.get('maxlength')) or ''
            

class FeedbackForm(Form):
    def on_create(self):
        # Set form style
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "10px"
        self.style["padding"] = "10px"
        self.style["background-color"] = "transparent"
        self.style["backdrop-filter"] = "blur(50px)"
        self.style["border-radius"] = Theme.border_radius
        self.style["border"] = "1px solid #ccc"
        
        self.properties["class"] = "feedback-form form"
        
        # Create fullname textfield
        fullname = InputField(
            type="text",
            placeholder="Full Name",
            required=True,
            maxlength=64,)
        
        email = InputField(
            type="email",
            placeholder="Email",
            required=True,
            maxlength=64)
        
        textarea = TextArea(
            placeholder="What is it you like to say?",
            maxlength=255,
            required=True,)
        
        textarea.properties["rows"] = "4"
        textarea.properties["cols"] = "50"
            
        submit = InputField(
            type="submit",
            value="Submit",)
        
        submit.style["background-color"] = "transparent"
        submit.style["backdrop-filter"] = "blur(50px)"
        submit.style["color"] = "#ccc"
        
        context = self.kwargs.get("context")
        request = context.get('request')
        
        self.kwargs["fields"] = [
            CSRFInput(request=request),
            fullname,
            email,
            textarea,
            submit]
        
        # Super create
        super().on_create()
