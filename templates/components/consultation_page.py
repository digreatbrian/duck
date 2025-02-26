from duck.etc.templatetags import static
from duck.html.components.input import CSRFInput
from duck.html.components.select import  Select, Option
from theme import Theme

from .container import FlexContainer
from .style import Style
from .script import Script
from .form import Form, TextArea, InputField
from .video import Video
from .icon import Icon


class ConsultationPageStyle(Style):
    def on_create(self):
        super().on_create()
        self.inner_body += """
        .consultation-form input, button, textarea, select, checkbox {
            font-size: 1.75rem;
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
        
        submit.style["background-color"] = "rgba(100, 100, 100, .35)"
        submit.style["border"] = "none"
        submit.style["font-size"] = "1rem"
        submit.style["color"] = "#ccc"
        submit.properties["class"] = "submit-button"
        submit.properties["onclick"] = "submitApplication()"
        
         # Add script for applying for consultation
        script = Script(
            inner_body="""
                function submitApplication(maxSizeMB = 2) {
                    let form = document.getElementsByClassName('consultation-form')[0];
                    
                    // Check if the form is valid using built-in validation
                    if (!form.checkValidity()) {
                        form.reportValidity(); // Show native validation messages
                        return;
                    }
                    
                    // Convert form to jquery form
                    form = $(form);
                
                    // Show progress info status
                    showConsultationStatus({ "info": "Your application is being processed, please wait a few seconds" });
                
                    // Prepare FormData for AJAX
                    let formData = new FormData(form[0]); // Use form[0] to get the DOM element
                    
                    $.ajax({
                        url: form.attr("action"), // Use form's action attribute
                        type: form.attr("method") || "POST", // Use form's method (default to POST)
                        data: formData,
                        processData: false,
                        contentType: false,
                        dataType: "json", // Expect JSON response
                        success: function (response, textStatus, xhr) {
                            if (xhr.status === 200 && response.success) {
                                // Handle success (200 OK)
                                showConsultationStatus(response);
                            } else {
                                // Error response (no success key in the response)
                                showConsultationStatus(response);
                            }
                        },
                        error: function (xhr, textStatus, errorThrown) {
                            // Called when server returns non-2xx status code
                            let errorMsg = "Error submitting application.";
                
                            if (xhr.responseJSON && xhr.responseJSON.error) {
                                errorMsg = xhr.responseJSON.error; // Show error message from server
                            } else if (xhr.status !== 200) {
                                errorMsg = errorMsg + ": " + xhr.status + " " + errorThrown;
                            }
                
                            showConsultationStatus({ "error": errorMsg });
                        }
                    });
                }
            """
        )
        
        # Add script to form
        self.inner_body += script.to_string()
        
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
        

class Popup(FlexContainer):
    def on_create(self):
        self.style["min-width"] = "100vw"
        self.style["min-height"] = "100vh"
        self.style["background-color"] = "black"
        self.style["padding"] = "5px"
        self.style["position"] = "absolute"
        self.style["z-index"] = "5"
        self.style["transition"] = "display 0.3s ease"
        self.style["top"] = "0"
        self.style["left"] = "0"
        self.style["display"] = "none"
        self.style["flex-direction"] = "column"
        self.properties["class"] = "popup"
        
        script = Script(
            inner_body="""
                function movePopupToBody() {
                    var popup = $('.popup');  // Select popup using jQuery
                    if (popup.length && popup.parent()[0] !== document.body) {
                        popup.appendTo('body');  // Move popup to body
                    }
                }
                
                function closePopup(popup) {
                    $(popup).css('display', 'none');
                }
                
                // Ensure movePopupToBody is defined elsewhere in your code
                $(document).ready(function () {
                    movePopupToBody();
                    // Event handler for popup clicks
                    $('.popup').on('click', function (event) {
                        if ($(event.target).is('.popup')) {
                            closePopup(this);  // close the popup by using the reference
                        }
                    });
                });
                
                // Adjust the position of the popup when the window is resized
                $(window).resize(movePopupToBody);
                """
        )
        
        # Lets add toggle button to close popup
        exit_btn_container = FlexContainer()
        exit_btn_container.style["padding"] = "5px"
        exit_btn_container.style["justify-content"] = "flex-end"
        
        exit_btn = Icon(icon_class="bi bi-x-circle")
        exit_btn.style["color"] = "#ccc"
        exit_btn.style["font-size"] = "1.95rem"
        exit_btn.properties["onclick"] = "closePopup($(this).closest('.popup'));"
        
        # Add exit button to container
        exit_btn_container.add_child(exit_btn)
        
        # add exit button container
        self.add_child(exit_btn_container)
        
        # Add script for adding popup to topmost next body child
        self.add_child(script)


class ConsultationStatus(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["gap"] = "10px"
        self.style["padding"] = "10px"
        self.style["background-color"] = "transparent"
        self.style["backdrop-filter"] = "blur(50px)"
        self.style["border-radius"] = Theme.border_radius
        self.style["justify-content"] = "center"
        self.style["align-items"] = "center"
        self.style["color"] = "white"
        self.properties["class"] = "consultation-status"
        
        icon = Icon()
        icon.style["font-size"] = "5rem"
        icon.properties["class"] = "consultation-status-icon"
        
        message = InputWithLabel(input=None)
        message.properties["class"] = "consultation-status-label"
        
        script = Script(
            inner_body="""
                function showConsultationStatus(response, autoHide=false) {
                    // Select the status message container
                    const statusContainer = $(".consultation-status");
                    const statusLabel = statusContainer.find(".consultation-status-label");
                    const statusIcon = statusContainer.find(".consultation-status-icon");
                    
                    // Scroll to statusContainer
                    $('html, body').animate({
                        scrollTop: statusContainer.offset().top
                    }, 1000); // 1000 is the duration in milliseconds (1 second)
                    
                    let successIconClass = "bi bi-check-circle";
                    let errorIconClass = "bi bi-exclamation-circle";
                    let infoIconClass = "bi bi-upload";
                    let gradientBgClass = "gradient-bg"
                    let gradientErrorBgClass = "gradient-error-bg"
                    let gradientSuccessBgClass = "gradient-success-bg"
                    
                    // Clear status container, any existing icons before adding new ones
                    statusIcon.removeClass(successIconClass + ' ' + errorIconClass + ' ' + infoIconClass);
                    statusContainer.removeClass(gradientSuccessBgClass + ' ' + gradientErrorBgClass + ' ' + gradientBgClass);
                    
                    // Open popup already
                    $('.consultation-popup').css('display', 'flex');
                    
                    // Check for "success", "error", or "info" in the response dictionary
                    if (response.success) {
                        statusLabel.text(response["success"]);
                        statusIcon.addClass(successIconClass);
                        statusContainer.addClass(gradientSuccessBgClass);
                    } else if (response.error) {
                        statusLabel.text(response["error"]);
                        statusIcon.addClass(errorIconClass);
                        statusContainer.addClass(gradientErrorBgClass);
                    } else if (response.info) {
                        statusLabel.text(response["info"]);
                        statusIcon.addClass(infoIconClass);
                        statusContainer.addClass(gradientBgClass);
                    } else {
                        statusLabel.text("Got unexpected response");
                        statusIcon.addClass(errorIconClass);
                        statusContainer.addClass(gradientErrorBgClass);
                    }
                    
                    // Show the status container with fade effect
                    statusContainer.css('display', 'flex').fadeIn();
                    
                    if (autoHide) {
                        // Hide the message after 5 seconds (you can adjust the time as needed)
                        setTimeout(function () {
                            hideConsultationStatus();
                        }, 5000); // Message will disappear after 5 seconds
                    }
                }
                
                function hideConsultationStatus() {
                    const statusContainer = $(".consultation-status");
                    statusContainer.fadeOut();
                }
            """
        )
        self.add_children([icon, message, script])
        

class ConsultationPage(FlexContainer):
    def display_error_message(self, message):
        self.style.update({
            "align-items": "center",
            "font-size": "1.3rem"
        })
        
        error_icon = Icon()
        error_icon.style["font-size"] = "3rem"
        error_icon.properties["class"] = "bi bi-exclamation"
        
        self.inner_body += error_icon.to_string()
        self.inner_body += message
    
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
        
        # Add popup
        consultation_popup = Popup()
        consultation_popup.style["gap"] = "10px"
        consultation_popup.properties["class"] += " consultation-popup"
        
        # Add consultation status cotainer
        consultation_status_container = FlexContainer()
        consultation_status_container.style["flex-direction"] = "column"
        consultation_status_container.style["width"] = "100%"
        consultation_status_container.style["align-items"] = "center"
        
        # Add consultation status to container and container to popup
        consultation_status = ConsultationStatus()
        #consultation_status.style["display"] = "none"
        consultation_status.style["width"] = "80%"
        consultation_status.style["min-height"] = "50%"
        
        consultation_status_container.add_child(consultation_status)
        consultation_popup.add_child(consultation_status_container)
        
        # Add popup
        self.add_child(consultation_popup)
        
        