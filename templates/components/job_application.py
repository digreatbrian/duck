from datetime import datetime

from duck.etc.templatetags import static
from duck.html.components import InnerHtmlComponent
from duck.html.components.input import CSRFInput
from duck.html.components.select import  Select, Option
from duck.html.components.button import FlatButton
from duck.utils.string import smart_truncate
from duck.utils.dateutils import (
    build_readable_date,
    datetime_difference_upto_now,
)
from duck.shortcuts import resolve

from theme import Theme
from backend.django.duckapp.core.models import Job

from .container import FlexContainer
from .form import Form, TextArea, InputField
from .card import Card
from .image import Image
from .style import Style
from .script import Script
from .icon import Icon


class JobCardTopItems(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "row"
        self.style["gap"] = "10px"
        self.style["flex-wrap"] = "wrap"
        self.properties["class"] = "job-card-top-items"
        
        job = self.kwargs["job"]
        job_title = job.title
        job_posting = job.posting_date
        job_expiration_date = job.expiration_date
        job_description = job.description
        job_company = job.company.name
        
        # Create left and right containers
        # Create left container
        left_container = FlexContainer()
        left_container.style["flex-direction"] = "column"
        
        # Create right container
        right_container = FlexContainer()
        right_container.style["align-items"] = "flex-start"
        right_container.style["flex-direction"] = "column"
        
        self.add_child(left_container)
        self.add_child(right_container)
        
        # Add items to left container
        # Add company image
        image = Image(source=job.company_image_url)
        image.style['border'] = "1px solid #ccc"
        image.style['width'] = "200px"
        image.style["height"] = "200px"
        image.style["border-radius"] = Theme.border_radius
        image.properties["class"] = "job-card-company-image"
        
        left_container.add_child(image)
        
        # Add items to the right container
        # Add job title
        right_container.inner_body += f"<h1>{job_title}</h1>"
        
        # Add company name
        right_container.inner_body += f"<h4>{job_company}</h4>"
        
        # Add job posting
        diff_upto_now = datetime_difference_upto_now(job_posting)
        job_posting = build_readable_date(diff_upto_now)
        job_posting = job_posting + " ago" if "now" not in job_posting else job_posting
        right_container.inner_body += f"<p>Posted: {job_posting}</p>"
        
        # Add job expiration
        if not job.expired:
            job_expiration_date = job.readable_expiration_date
            right_container.inner_body += f"<p>Expire in: {job_expiration_date}</p>"
        else:
            right_container.inner_body += f"<p style='color: red'>Expired</p>"


class JobCardBottomItems(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["align-items"] = "flex-start"
        self.properties["class"] = "job-card-bottom-items"
        
        job = self.kwargs["job"]
        job_industry = job.industry
        job_salary = job.salary
        job_location = job.location
        job_id = job.job_id
        
        # Add job industry
        if job_industry:
            self.inner_body += f"<p>Industry:  {job_industry}</p>"
        
        # Add job salary and salary period
        self.inner_body += f"<p>{job_salary}</p>" if job_salary else None
        
        # Add job location
        self.inner_body += f"<p>Location: {job_location}</p>"
        
        # Add job id
        self.inner_body += f"<p>ID: {job_id}</p>"
        
     
class JobCard(Card):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["gap"] = "10px"
        self.style["border"] = "1px solid #ccc"
        self.style['border-radius'] = Theme.border_radius
        self.style["align-items"] = "flex-start"
        self.style["flex-wrap"] = "wrap"
        self.style["text-align"] = "start"
        self.properties["class"] = "job-card"
        
        if "job" in self.kwargs:
            job = self.kwargs.get('job')
            if job:
                 top_items = JobCardTopItems(job=job)
                 bottom_items = JobCardBottomItems(job=job)
                 
                 # Add top and bottom items
                 self.add_child(top_items)
                 self.add_child(bottom_items)
                 
                 # Now add Apply button
                 cta_btn = FlatButton()
                 cta_btn.inner_body = "Apply now"
                 cta_btn.style["background-color"] = "rgba(100, 100, 100, .25)"
                 cta_btn.style["color"] = "#ccc"
                 cta_btn.style["margin-top"] = "5px"
                 cta_btn.style["border-radius"] = Theme.border_radius
                 cta_btn.style["font-size"] = "1.2rem"
                 cta_btn.style["border"] = ".25px solid #ccc"
                 cta_btn.style["width"] = "100%"
                 cta_btn.properties["onclick"] = "$('.job-application-popup').css('display', 'flex');"
                 self.add_child(cta_btn)


class JobTopContainer(FlexContainer):
    def on_create(self):
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "10px"
        self.style["padding"] = "10px"
        self.style["background-color"] = "transparent"
        self.style["backdrop-filter"] = "blur(50px)"
        self.properties["class"] = "job-top-container"
        
        job = None
        
        if "job" in self.kwargs:
            job = self.kwargs.get('job')
            if not job:
                return
        
        # Add job card
        job_card = JobCard(job=job)
        self.add_child(job_card)


class JobBottomContainer(FlexContainer):
    def on_create(self):
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "10px"
        self.style["padding"] = "10px"
        self.style["background-color"] = "transparent"
        self.style["backdrop-filter"] = "blur(50px)"
        self.properties["class"] = "job-bottom-container"
        
        job = None
        
        if "job" in self.kwargs:
            job = self.kwargs.get('job')
            if not job:
                return
        
        job_description = job.description
        job_requirements = job.requirements
        job_benefits = job.benefits
        
        # Add Job Metadata
        # Add job description
        job_description = job_description
        self.inner_body += f"<h2>Job description</h2><p>{job_description}</p>"
        
        # Add job requirements
        job_requirements = job_requirements
        self.inner_body += f"<h2>Requirements</h2><p>{job_requirements}</p>"
        
        # Add job benefits
        if job_benefits:
            job_benefits = job_requirements
            self.inner_body += f"<h2>Benefits</h2><p>{job_benefits}</p>"


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


class FileDragAndDrop(Card):
    def on_create(self):
        super().on_create()
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["border"] = "1px dashed #ccc"
        
        self.style["gap"] = "10px"
        self.style["flex-direction"] = "column"
        self.properties['class'] = 'drag-and-drop'
        
        if "label_text" in self.kwargs:
            label_text = self.kwargs.get('label_text', '')
            label = f"<label>{label_text}</label>"
            selected_file_label = "<label class='selected-file-label'>Selected file: No file selected</label>"
            self.inner_body += label
            self.inner_body += selected_file_label
        
        if "input" in self.kwargs:
            inputfield = self.kwargs.get('input', '')
            inputfield.style['aria-hidden'] = "true"
            inputfield.style["opacity"] = "0"
            inputfield.style["width"] = "0"
            inputfield.style["height"] = "0"
            inputfield.properties["class"] = "drag-n-drop-fileinput"
            
            if inputfield:
                inputfield = inputfield.to_string()
            self.inner_body += inputfield
        
        # Now attach script for this drag n drop
        script = Script(
            inner_body="""
                function dragAndDropClick(dragAndDrop){
                    const fileInput = $(dragAndDrop).find('input[type="file"]');
                    fileInput.click();
                }
                
                function updateLabelOnFileSelect(fileInput){
                    const dragAndDrop = $(fileInput).closest('.drag-and-drop');
                    const label = dragAndDrop.find('.selected-file-label');
                    const fileName = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file selected';
                    label.text('Selected file: ' + fileName);
                    
                    if (fileName !== 'No file selected'){
                        // change drag and drop color
                        dragAndDrop.css('border-color', 'var(--green)');
                        dragAndDrop.css('border-width', '2px');
                    }
                    else {
                        dragAndDrop.css('border-color', '#ccc');
                        dragAndDrop.css('border-width', '1px');
                    }
                    
                }
                
                // Function to handle the dragover event to allow dropping
                function handleDragOver(event) {
                    event.preventDefault();  // Prevent the default behavior (Prevent file from opening in browser)
                    const dragAndDrop = $(event.target).closest('.drag-and-drop');
                    dragAndDrop.css('border-color', 'var(--green)');  // Highlight border while dragging
                    dragAndDrop.css('border-width', '2px');
                }
                
                // Function to handle the drop event
                function handleDrop(event) {
                    event.preventDefault();  // Prevent the default behavior
                    const dragAndDrop = $(event.target).closest('.drag-and-drop');
                    const fileInput = dragAndDrop.find('input[type="file"]')[0];  // Get the file input element
                    
                    // Get the dropped files
                    const files = event.originalEvent.dataTransfer.files;
                    
                    if (files.length > 0) {
                        // Set the dropped file(s) to the file input field
                        fileInput.files = files;
                
                        // Update the label text
                        updateLabelOnFileSelect(fileInput);
                    }
                    else {
                        dragAndDrop.css('border-width', '1px');
                        dragAndDrop.css('border-color', '#ccc');  // Reset the border color after drop
                    }
                }
                
                $('.drag-and-drop').on('click', function(event){
                    event.stopPropagation();
                    dragAndDropClick(this);
                });
                
                 // Update label text when a file is selected
                $('input[type="file"]').on('change', function(){
                    updateLabelOnFileSelect(this);  // Update the label with the selected file's name
                });

                $('input[type="file"]').on('click', function(event){
                    // Prevent input file click from triggering drag-and-drop click again
                    event.stopPropagation();
                });
                
                // Add event listeners for drag and drop behavior
                $('.drag-and-drop')
                    .on('dragover', handleDragOver)  // Allow dragover event to show the drop area as active
                    .on('drop', handleDrop);  // Handle the drop event when the file is dropped
            """
        )
        self.inner_body += script.to_string()


class Popup(FlexContainer):
    def on_create(self):
        self.style["width"] = "100%"
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


class JobApplicationForm(Form):
    def on_create(self):
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "10px"
        self.style["padding"] = "10px"
        self.style["background-color"] = "transparent"
        self.style["backdrop-filter"] = "blur(50px)"
        self.style["border-radius"] = Theme.border_radius
        self.style["border"] = "1px solid #ccc"
        
        self.properties["class"] = "job-application-form form"
        
        job = self.kwargs["job"]
             
        # create subheading
        subheading = InnerHtmlComponent("h5", inner_body=f"You are applying for: {job.title}")
        subheading.style["color"] = "#ccc"
        
        # Add sub heading
        self.inner_body += subheading.to_string()
        
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
        
        phone = InputWithLabel(
            label_text="Phone",
            input=InputField(
                type="tel",
                name="phone",
                placeholder="Phone eg +263...",
                required=True,
                maxlength=12,
            )
        )
        
        cover_letter = InputWithLabel(
            label_text="Cover Letter/Statement of Interest",
            input=TextArea(
                type="text",
                name="cover_letter",
                placeholder="A short message about why you’re interested in this job and why you’re a good fit (optional)",
                maxlength=255,
                properties={
                    "rows": "6",
                    "cols": "50",
                }
            )
        )
        
        resume = FileDragAndDrop(
            label_text="Drag n Drop or Choose Resume (<= 2MB)<br>Allowed files: .doc, .pdf, .docx",
            input=InputField(
                type="file",
                name="resume",
                required=True,
                properties={
                    "accept": ".doc,.pdf,.docx"
                }
            )
        )
        
        submit = InputField(
            value="Apply",
            type="button")
        
        submit.style["background-color"] = "transparent"
        submit.style["backdrop-filter"] = "blur(50px)"
        submit.style["color"] = "#ccc"
        submit.properties["class"] = "submit-button"
        submit.properties["onclick"] = "submitApplication()"
        
        # Add script for applying for the job
        script = Script(
            inner_body="""
                function submitApplication(maxSizeMB = 2) {
                    const resumeMaxSize = maxSizeMB * 1024 * 1024; // Convert MB to bytes
                    let form = document.getElementsByClassName('job-application-form')[0];
                    let resumeFileInput = $(form).find("input[type='file']");
                    
                    // Check if the form is valid using built-in validation
                    if (!form.checkValidity()) {
                        form.reportValidity(); // Show native validation messages
                        return;
                    }
                    
                    let resumeFile = resumeFileInput[0].files[0];
                    let resumeFileName = resumeFile.name;
                    
                    if (resumeFile && resumeFile.size > resumeMaxSize) {
                        showJobApplicationStatus({ "error": "Resume too large, should be a max of " + maxSizeMB + " MB" });
                        return;
                    }
                    
                    // Check file extension
                    let allowedExts = [".pdf", ".doc", ".docx"]

                    if (!(allowedExts.some(ext => resumeFileName.toLowerCase().endsWith(ext)))) {
                        showJobApplicationStatus({"error": "Uknown resume file. Allowed file types: .pdf, .doc, .docx"});
                        return;
                    }
                
                    // Convert form to jquery form
                    form = $(form);
                
                    // Show progress info status
                    showJobApplicationStatus({ "info": "Your application is being processed, please wait a few seconds" });
                
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
                                showJobApplicationStatus(response);
                            } else {
                                // Error response (no success key in the response)
                                showJobApplicationStatus(response);
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
                
                            showJobApplicationStatus({ "error": errorMsg });
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
            phone,
            cover_letter,
            resume,
            submit,
        ]
        
        # Super Create
        super().on_create()


class JobApplicationStatus(FlexContainer):
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
        self.properties["class"] = "job-application-status"
        
        icon = Icon()
        icon.style["font-size"] = "5rem"
        icon.properties["class"] = "job-application-status-icon"
        
        message = InputWithLabel(input=None)
        message.properties["class"] = "job-application-status-label"
        
        script = Script(
            inner_body="""
                function showJobApplicationStatus(response, autoHide=false) {
                    // Select the status message container
                    const statusContainer = $(".job-application-status");
                    const statusLabel = statusContainer.find(".job-application-status-label");
                    const statusIcon = statusContainer.find(".job-application-status-icon");
                    
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
                            hideJobApplicationStatus();
                        }, 5000); // Message will disappear after 5 seconds
                    }
                }
                
                function hideJobApplicationStatus() {
                    const statusContainer = $(".job-application-status");
                    statusContainer.fadeOut();
                }
            """
        )
        self.add_children([icon, message, script])
        

class JobApplicationPage(FlexContainer):
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
        self.properties["id"] = "job-application-page"
        
        # Load the job.
        try:
            context = self.kwargs.get("context")
            job_id = context.get("job_id")
            job_id = int(job_id)
            job = Job.objects.get(job_id=job_id)
            
            if job.expired:
                self.display_error_message("Job expired")
                return # no need to add more html element
            self.add_main_components(job) # Add main components
        except Job.DoesNotExist:
            self.display_error_message("Job unavailable")
            
        except Exception:
            self.display_error_message("Error retrieving job application")
            return # no need to add more html elements
    
    def add_main_components(self, job):
        # Add popup
        application_popup = Popup()
        application_popup.style["gap"] = "10px"
        application_popup.properties["class"] += " job-application-popup"
        
        # Add application status cotainer
        application_status_container = FlexContainer()
        application_status_container.style["flex-direction"] = "column"
        application_status_container.style["width"] = "100%"
        application_status_container.style["align-items"] = "center"
        
        # Add job application status to container and container to popup
        application_status = JobApplicationStatus()
        application_status.style["display"] = "none"
        application_status.style["width"] = "80%"
        application_status.style["min-height"] = "50%"
        
        application_status_container.add_child(application_status)
        application_popup.add_child(application_status_container)
        
        # Add job application form
        applicaton_form = JobApplicationForm(job=job, **self.kwargs)
        
        # Add application form to popup
        application_popup.add_child(applicaton_form)
        
        # Add application popup
        self.add_child(application_popup)
        
        # Add job top and bottom container
        job_top_container = JobTopContainer(job=job)
        job_bottom_container = JobBottomContainer(job=job)
        
        self.add_child(job_top_container)
        self.add_child(job_bottom_container)
        