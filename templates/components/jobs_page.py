from datetime import datetime

from duck.etc.templatetags import static
from duck.html.components.input import CSRFInput
from duck.html.components.select import  Select, Option
from duck.html.components.button import FlatButton
from duck.utils.string import smart_truncate
from duck.utils.urlcrack import URL
from duck.utils.dateutils import (
    build_readable_date,
    datetime_difference_upto_now,
)
from duck.shortcuts import resolve

from theme import Theme

from .container import FlexContainer
from .card import Card
from .image import Image
from .style import Style
from .script import Script


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
        
        # Add truncated job description
        job_description = smart_truncate(job_description, cap=250)
        right_container.inner_body += f"<p>{job_description}</p>"


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
                 
                 apply_url = resolve('job-application', fallback_url="#")
                 apply_url = apply_url.replace('job_id', str(job.job_id))
                 cta_btn.properties["onclick"] = "window.open('{}');".format(apply_url)
                 self.add_child(cta_btn)


class JobsContainer(FlexContainer):
    def on_create(self):
        self.style["display"] = "flex"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "10px"
        self.style["padding"] = "10px"
        self.style["background-color"] = "transparent"
        self.style["backdrop-filter"] = "blur(50px)"
        self.properties["class"] = "jobs-container"
        
        if "jobs" in self.kwargs:
            jobs = self.kwargs.get('jobs') or []
            for job in jobs:
                job_card = JobCard(job=job)
                self.add_child(job_card)


class JobsPage(FlexContainer):
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
        self.properties["id"] = "jobs-page"
        
        # Add info container
        info_container = FlexContainer()
        info_container.style["flex-direction"] = "column"
        info_container.style["gap"] = "5px"
        info_container.style["font-size"] = "1.5rem"
        info_container.style["align-items"] = "center"
        info_container.properties["id"] = "info-container"
        self.add_child(info_container)
        
        # Add jobs container
        jobs_container = JobsContainer()
        self.add_child(jobs_container)
        
        # Add load more jobs btn
        load_more_jobs_button = FlatButton(inner_body="Load more jobs")
        load_more_jobs_button.style["background-color"] = "var(--secondary-color)"
        load_more_jobs_button.style["color"] = "#ccc"
        load_more_jobs_button.style["border"] = "1px solid #ccc"
        load_more_jobs_button.style["border-radius"] = Theme.border_radius
        load_more_jobs_button.properties["id"] = 'load-more-jobs-btn'
        load_more_jobs_button.properties["onclick"] = "loadMoreJobs()"
        
        self.add_child(load_more_jobs_button)
        
        # Add script for loading more jobs
        script = Script(
            inner_body="""
                let jobs_page = 1;

                function disableLoadMoreJobsButton(disableMsg) {
                    const jobsPage = $("#jobs-page");
                    const btn = jobsPage.find('#load-more-jobs-btn');
                
                    if (disableMsg) {
                        btn.text(disableMsg);
                    }
                
                    btn.prop('disabled', true);
                }
                
                function setInfo(msg) {
                    const jobsPage = $("#jobs-page");
                    const infoContainer = jobsPage.find('#info-container');  // Fixed missing quote
                    infoContainer.text(msg);
                }
                
                function clearInfo() {
                    const jobsPage = $("#jobs-page");
                    const infoContainer = jobsPage.find('#info-container');  // Fixed missing quote
                    infoContainer.text("");
                }
                
                function loadMoreJobs() {
                    const jobsContainer = $("#jobs-page .jobs-container");
                    const loadMoreJobsButton = $('#load-more-jobs-btn');
                
                    loadMoreJobsButton.text("Loading...");
                    
                    $.ajax({
                        url: '%s',
                        data: { 'page': jobs_page },
                        success: function(response, status, xhr) {
                            if (xhr.getResponseHeader("X-No-More-Jobs") === "true") {
                                disableLoadMoreJobsButton("No more jobs");
                                
                                if (jobs_page > 1) {
                                    alert(response);
                                    clearInfo();
                                } else {
                                    setInfo("No jobs at the moment, come back another time");
                                }
                            } else {
                                jobsContainer.append(response);  // Append job listings
                                jobs_page += 1;  // Corrected increment
                                loadMoreJobsButton.text("Load more jobs");
                                clearInfo();
                            }
                        },
                        error: function(xhr, status, error) {
                            if (xhr.responseText) {
                                if (jobs_page > 1) {
                                    alert("Server returned error response: " + xhr.responseText.toLowerCase());
                                    clearInfo();
                                } else {
                                    setInfo("Server returned error response: " + xhr.responseText.toLowerCase());
                                }
                            } else {
                                if (jobs_page > 1) {
                                    alert('An error occurred while loading more jobs, check your internet connection.');
                                    clearInfo();
                                } else {
                                    setInfo('An error occurred while loading more jobs, check your internet connection.');
                                }
                            }
                            loadMoreJobsButton.text("Load more jobs");
                        }
                    });
                }
                
                // Load jobs initially
                $(document).ready(function () {
                    setInfo("Loading jobs, wait a few seconds");
                    loadMoreJobs();  // Trigger initial load
                });
            """%(resolve('jobs', fallback_url="#"))
        )
        
        # add script
        self.add_child(script)

