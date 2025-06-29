from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserProfile(BaseModel):
    """User profile information for job applications"""
    name: str = Field(..., description="Full name of the applicant")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: str = Field(..., description="Current location")
    experience_years: int = Field(..., description="Years of experience")
    skills: List[str] = Field(..., description="List of skills")
    education: str = Field(..., description="Educational background")
    resume_url: Optional[str] = Field(None, description="URL to resume")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    portfolio_url: Optional[str] = Field(None, description="Portfolio URL")
    cover_letter_template: Optional[str] = Field(None, description="Cover letter template")

class JobPosting(BaseModel):
    """Job posting information"""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Job description")
    requirements: List[str] = Field(default=[], description="Job requirements")
    salary_range: Optional[str] = Field(None, description="Salary range")
    job_url: str = Field(..., description="URL to the job posting")
    hiring_manager_email: Optional[str] = Field(None, description="Hiring manager email")
    application_deadline: Optional[datetime] = Field(None, description="Application deadline")
    job_type: Optional[str] = Field(None, description="Job type (full-time, part-time, etc.)")
    remote_option: Optional[bool] = Field(None, description="Remote work option available")

class JobApplicationRequest(BaseModel):
    """Request model for job application process"""
    keywords: List[str] = Field(..., description="Job search keywords")
    location: str = Field(..., description="Preferred job location")
    max_jobs: int = Field(default=10, description="Maximum number of jobs to process")
    # User profile fields for direct input
    user_name: str = Field(..., description="Full name of the applicant")
    user_email: str = Field(..., description="Email address")
    experience_years: int = Field(..., description="Years of experience")
    skills: List[str] = Field(..., description="List of skills")
    education: str = Field(..., description="Educational background")
    # Optional fields
    user_profile: Optional[UserProfile] = Field(None, description="Complete user profile information")
    job_sites: List[str] = Field(default=["indeed", "linkedin"], description="Job sites to scrape")
    auto_apply: bool = Field(default=True, description="Automatically apply to jobs")
    email_template: Optional[str] = Field(None, description="Custom email template")

class JobApplicationResponse(BaseModel):
    """Response model for job application process"""
    message: str = Field(..., description="Response message")
    status: str = Field(..., description="Process status")
    request_id: str = Field(..., description="Unique request identifier")
    jobs_found: Optional[int] = Field(None, description="Number of jobs found")
    applications_sent: Optional[int] = Field(None, description="Number of applications sent")

class EmailRequest(BaseModel):
    """Request model for email generation"""
    job_posting: JobPosting = Field(..., description="Job posting information")
    user_profile: UserProfile = Field(..., description="User profile information")
    email_type: str = Field(default="cover_letter", description="Type of email to generate")

class EmailResponse(BaseModel):
    """Response model for email generation"""
    subject: str = Field(..., description="Email subject")
    content: str = Field(..., description="Email content")
    recipient_email: Optional[str] = Field(None, description="Recipient email address")
    attachments: List[str] = Field(default=[], description="List of attachment URLs")

class ApplicationStatus(BaseModel):
    """Model for application status tracking"""
    request_id: str = Field(..., description="Request identifier")
    status: str = Field(..., description="Current status")
    jobs_processed: int = Field(default=0, description="Number of jobs processed")
    emails_sent: int = Field(default=0, description="Number of emails sent")
    errors: int = Field(default=0, description="Number of errors encountered")
    start_time: datetime = Field(..., description="Process start time")
    end_time: Optional[datetime] = Field(None, description="Process end time")
    details: Dict[str, Any] = Field(default={}, description="Additional details") 