import asyncio
import json
from typing import Dict, Any, List
import logging
from groq import Groq
from jinja2 import Template

from models.schemas import JobPosting, UserProfile, EmailResponse
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailGenerator:
    """Service for generating personalized emails using Groq LLM"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.setup_templates()
    
    def setup_templates(self):
        """Setup email templates"""
        self.templates = {
            "cover_letter": """
You are a professional job application assistant. Generate a compelling cover letter for the following job posting.

Job Details:
- Title: {{ job.title }}
- Company: {{ job.company }}
- Location: {{ job.location }}
- Description: {{ job.description }}

Applicant Profile:
- Name: {{ user.name }}
- Experience: {{ user.experience_years }} years
- Skills: {{ user.skills|join(', ') }}
- Education: {{ user.education }}
- Location: {{ user.location }}

Instructions:
1. Write a professional cover letter that highlights the applicant's relevant experience and skills
2. Address the specific requirements mentioned in the job description
3. Show enthusiasm for the company and position
4. Keep it concise (200-300 words)
5. Use a professional tone
6. Include a clear call to action

Generate the cover letter:
""",
            "follow_up": """
You are a professional follow-up email assistant. Generate a polite follow-up email for a job application.

Job Details:
- Title: {{ job.title }}
- Company: {{ job.company }}
- Applied Date: {{ applied_date }}

Applicant Profile:
- Name: {{ user.name }}
- Email: {{ user.email }}

Instructions:
1. Write a polite follow-up email
2. Reference the specific position and application date
3. Express continued interest
4. Keep it brief and professional
5. Ask about the status of the application
6. Thank them for their time

Generate the follow-up email:
""",
            "networking": """
You are a professional networking email assistant. Generate a networking email to connect with someone at a company.

Company: {{ job.company }}
Position of Interest: {{ job.title }}

Applicant Profile:
- Name: {{ user.name }}
- Experience: {{ user.experience_years }} years
- Skills: {{ user.skills|join(', ') }}
- LinkedIn: {{ user.linkedin_url }}

Instructions:
1. Write a professional networking email
2. Introduce yourself briefly
3. Express interest in the company
4. Mention specific skills or experience relevant to the company
5. Request an informational interview or connection
6. Keep it concise and respectful

Generate the networking email:
"""
        }
    
    async def generate_email(self, job_posting: JobPosting, user_profile: UserProfile, 
                           email_type: str = "cover_letter", custom_template: str = None) -> EmailResponse:
        """
        Generate a personalized email for job application
        """
        try:
            # Prepare context for template
            context = {
                "job": job_posting,
                "user": user_profile,
                "applied_date": "recently"  # Could be made dynamic
            }
            
            # Get template
            if custom_template:
                template_content = custom_template
            else:
                template_content = self.templates.get(email_type, self.templates["cover_letter"])
            
            # Render template
            template = Template(template_content)
            prompt = template.render(**context)
            
            # Generate email using Groq
            email_content = await self._generate_with_groq(prompt, email_type)
            
            # Generate subject line
            subject = await self._generate_subject(job_posting, email_type)
            
            # Determine recipient email
            recipient_email = job_posting.hiring_manager_email or f"hiring@{job_posting.company.lower().replace(' ', '')}.com"
            
            return EmailResponse(
                subject=subject,
                content=email_content,
                recipient_email=recipient_email,
                attachments=[]
            )
            
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            raise
    
    async def _generate_with_groq(self, prompt: str, email_type: str) -> str:
        """Generate email content using Groq LLM"""
        try:
            # Add specific instructions based on email type
            if email_type == "cover_letter":
                system_prompt = "You are a professional job application assistant. Generate compelling cover letters that are personalized, professional, and highlight relevant experience."
            elif email_type == "follow_up":
                system_prompt = "You are a professional follow-up email assistant. Generate polite and professional follow-up emails for job applications."
            elif email_type == "networking":
                system_prompt = "You are a professional networking email assistant. Generate professional networking emails that are respectful and value-focused."
            else:
                system_prompt = "You are a professional email assistant. Generate professional and personalized emails."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error with Groq API: {e}")
            # Fallback to a basic template
            return self._generate_fallback_email(email_type)
    
    async def _generate_subject(self, job_posting: JobPosting, email_type: str) -> str:
        """Generate an appropriate subject line"""
        try:
            if email_type == "cover_letter":
                subject_prompt = f"Generate a professional subject line for a cover letter for the position of {job_posting.title} at {job_posting.company}. Keep it under 60 characters."
            elif email_type == "follow_up":
                subject_prompt = f"Generate a professional follow-up email subject line for the position of {job_posting.title} at {job_posting.company}. Keep it under 60 characters."
            elif email_type == "networking":
                subject_prompt = f"Generate a professional networking email subject line to connect with someone at {job_posting.company}. Keep it under 60 characters."
            else:
                subject_prompt = f"Generate a professional email subject line for {job_posting.title} position. Keep it under 60 characters."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional email subject line generator. Generate concise, professional subject lines."},
                    {"role": "user", "content": subject_prompt}
                ],
                temperature=0.5,
                max_tokens=50
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating subject: {e}")
            # Fallback subject
            return f"Application for {job_posting.title} Position"
    
    def _generate_fallback_email(self, email_type: str) -> str:
        """Generate a fallback email when LLM fails"""
        if email_type == "cover_letter":
            return """
Dear Hiring Manager,

I am writing to express my strong interest in the [Position Title] role at [Company Name]. With my background in [relevant skills] and [X] years of experience, I am confident I would be a valuable addition to your team.

I am particularly drawn to [Company Name] because of [specific reason]. My experience in [specific skill/area] aligns well with the requirements outlined in the job description.

I would welcome the opportunity to discuss how my skills and experience can contribute to [Company Name]'s continued success. Thank you for considering my application.

Best regards,
[Your Name]
"""
        elif email_type == "follow_up":
            return """
Dear Hiring Manager,

I hope this email finds you well. I wanted to follow up on my application for the [Position Title] role at [Company Name], which I submitted on [date].

I remain very interested in this opportunity and would appreciate any updates on the status of my application. I am available for an interview at your convenience.

Thank you for your time and consideration.

Best regards,
[Your Name]
"""
        else:
            return """
Dear [Name],

I hope this email finds you well. I am reaching out to connect and learn more about opportunities at [Company Name].

With my background in [relevant skills], I am interested in exploring how I might contribute to your team. I would appreciate the opportunity to have a brief conversation about your experience at [Company Name].

Thank you for your time.

Best regards,
[Your Name]
"""
    
    async def generate_bulk_emails(self, jobs: List[JobPosting], user_profile: UserProfile, 
                                 email_type: str = "cover_letter") -> List[EmailResponse]:
        """Generate emails for multiple jobs"""
        emails = []
        
        for job in jobs:
            try:
                email = await self.generate_email(job, user_profile, email_type)
                emails.append(email)
                # Add delay to avoid rate limiting
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error generating email for job {job.title}: {e}")
                continue
        
        return emails
    
    async def analyze_job_fit(self, job_posting: JobPosting, user_profile: UserProfile) -> Dict[str, Any]:
        """Analyze how well a job fits the user's profile"""
        try:
            analysis_prompt = f"""
Analyze the fit between the job posting and the candidate profile.

Job: {job_posting.title} at {job_posting.company}
Job Requirements: {', '.join(job_posting.requirements)}
Job Description: {job_posting.description[:500]}...

Candidate Skills: {', '.join(user_profile.skills)}
Candidate Experience: {user_profile.experience_years} years
Candidate Education: {user_profile.education}

Provide a JSON response with:
1. fit_score (0-100)
2. matching_skills (list of skills that match)
3. missing_skills (list of skills the candidate lacks)
4. recommendations (list of suggestions to improve fit)
5. confidence_level (high/medium/low)
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a job matching analyst. Provide detailed analysis in JSON format."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                return json.loads(analysis_text)
            except json.JSONDecodeError:
                # Fallback analysis
                return {
                    "fit_score": 70,
                    "matching_skills": user_profile.skills[:3],
                    "missing_skills": [],
                    "recommendations": ["Customize your application to highlight relevant experience"],
                    "confidence_level": "medium"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing job fit: {e}")
            return {
                "fit_score": 50,
                "matching_skills": [],
                "missing_skills": [],
                "recommendations": ["Unable to analyze job fit"],
                "confidence_level": "low"
            } 