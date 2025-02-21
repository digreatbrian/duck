from .jobs_page import Job

# Mock job postings
jobs = [
    Job(
        job_id=1,
        title="Python Backend Developer",
        company="TechCorp",
        location="Remote",
        job_type="Full-time",
        salary="$80,000 - $100,000 per year",
        description="Develop and maintain scalable backend services.",
        requirements=["Python", "Django", "REST APIs", "PostgreSQL"],
        benefits=["Health insurance", "Remote work", "Stock options"],
        industry="Technology",
        expiration_date=None
    ),
    Job(
        job_id=2,
        title="Machine Learning Engineer",
        company="AI Innovators",
        location="San Francisco, CA",
        job_type="Hybrid",
        salary="$120,000 - $150,000 per year",
        description="Build and deploy ML models for real-world applications.",
        requirements=["Python", "TensorFlow", "PyTorch", "Data Science"],
        benefits=["401(k)", "Health insurance", "Flexible hours"],
        industry="Artificial Intelligence",
        expiration_date="2025-04-10"
    ),
    Job(
        job_id=3,
        title="Frontend Developer",
        company="WebSolutions Inc.",
        location="New York, NY",
        job_type="Full-time",
        salary="$70,000 - $90,000 per year",
        description="Develop interactive and responsive web applications.",
        requirements=["JavaScript", "React", "CSS", "HTML"],
        benefits=["Paid time off", "Wellness programs", "Remote work option"],
        industry="Web Development",
        expiration_date="2025-05-15"
    ),
    Job(
        job_id=4,
        title="DevOps Engineer",
        company="CloudOps Ltd.",
        location="London, UK",
        job_type="Remote",
        salary="£75,000 - £95,000 per year",
        description="Manage CI/CD pipelines and cloud infrastructure.",
        requirements=["AWS", "Docker", "Kubernetes", "CI/CD"],
        benefits=["Flexible work hours", "Stock options", "Education allowance"],
        industry="Cloud Computing",
        expiration_date="2025-06-30"
    ),
    Job(
        job_id=5,
        title="Cybersecurity Analyst",
        company="SecureTech",
        location="Berlin, Germany",
        job_type="Full-time",
        salary="€80,000 - €110,000 per year",
        description="Monitor and improve security posture across networks.",
        requirements=["Security analysis", "Penetration testing", "SIEM tools"],
        benefits=["Health benefits", "Remote work", "Security certifications"],
        industry="Cybersecurity",
        expiration_date="2025-07-20"
    )
]

# Print job listings
for job in jobs:
    print(job)