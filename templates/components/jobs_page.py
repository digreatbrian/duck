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


class Job:
    def __init__(self, job_id, title, company, location, job_type, salary, description, requirements, benefits, industry, posting_date=None, expiration_date=None):
        self.job_id = job_id
        self.title = title
        self.company = company
        self.company_image_source = static('images/yannick-logo.png')
        self.location = location
        self.job_type = job_type
        self.salary = salary
        self.description = description
        self.requirements = requirements
        self.benefits = benefits
        self.industry = industry
        self.posting_date = datetime.now()
        self.expiration_date = datetime.now()
        
    def __repr__(self):
        return f"Job({self.job_id}, {self.title}, {self.company}, {self.location}, {self.job_type})"


class JobsPageStyle(Style):
    def on_create(self):
        super().on_create()


class JobCardTopItems(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "row"
        self.style["gap"] = "10px"
        self.properties["class"] = "job-card-top-items"
        
        job = self.kwargs["job"]
        job_title = job.title
        job_posting = job.posting_date
        job_expiration_date = job.expiration_date
        job_description = job.description
        job_company = job.company
        job_company_image = job.company_image_source

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
        image = Image(source=job_company_image)
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
        diff_upto_now = datetime_difference_upto_now(job_expiration_date)
        job_expiration_date = build_readable_date(diff_upto_now)
        right_container.inner_body += f"<p>Expire in: {job_expiration_date}</p>"
        
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
                 
                 if apply_url != "#":
                     apply_url = URL.urljoin(apply_url, str(job.job_id))
                 
                 cta_btn.properties["onclick"] = "window.open('{}', '_blank');".format(
                     apply_url,
                     job.job_id)
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
        
        from .mock_jobs import jobs
        jobs_container = JobsContainer(jobs=jobs)
        
        self.add_child(jobs_container)
