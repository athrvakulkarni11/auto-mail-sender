import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime
import os

from config.settings import settings

logger = logging.getLogger(__name__)

class EmailSender:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM
        
        # Validate settings
        if not all([self.username, self.password, self.from_email]):
            logger.warning("Email settings not fully configured. Email sending will be disabled.")
    
    async def send_email(self, to_email: str, subject: str, content: str, 
                        attachments: List[str] = None, from_name: str = None) -> Dict[str, Any]:
        """
        Send an email with optional attachments
        """
        try:
            if not all([self.username, self.password, self.from_email]):
                raise ValueError("Email settings not configured")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{from_name} <{self.from_email}>" if from_name else self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(content, 'html'))
            
            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    await self._add_attachment(msg, attachment_path)
            
            # Send email
            result = await self._send_smtp_email(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "to_email": to_email,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "to_email": to_email,
                "subject": subject,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _send_smtp_email(self, msg: MIMEMultipart) -> bool:
        """Send email via SMTP"""
        try:
            # Create secure SSL/TLS context
            context = ssl.create_default_context()
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(self.from_email, msg['To'], text)
                
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise
    
    async def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add attachment to email"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Attachment file not found: {file_path}")
                return
            
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {e}")
    
    async def send_bulk_emails(self, emails: List[Dict[str, Any]], 
                             delay_between_emails: float = 2.0) -> List[Dict[str, Any]]:
        """
        Send multiple emails with delay between each
        """
        results = []
        
        for email_data in emails:
            try:
                result = await self.send_email(
                    to_email=email_data['to_email'],
                    subject=email_data['subject'],
                    content=email_data['content'],
                    attachments=email_data.get('attachments', [])
                )
                results.append(result)
                
                # Add delay between emails to avoid rate limiting
                if delay_between_emails > 0:
                    await asyncio.sleep(delay_between_emails)
                    
            except Exception as e:
                logger.error(f"Error in bulk email sending: {e}")
                results.append({
                    "success": False,
                    "message": f"Failed to send email: {str(e)}",
                    "to_email": email_data.get('to_email', 'unknown'),
                    "subject": email_data.get('subject', 'unknown'),
                    "timestamp": datetime.now().isoformat()
                })
        
        return results
    
    async def send_job_application_email(self, job_data: Dict[str, Any], 
                                       user_profile: Dict[str, Any],
                                       email_content: str) -> Dict[str, Any]:
        """
        Send a job application email with proper formatting
        """
        try:
            # Format email content as HTML
            html_content = f"""
            <html>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                        <h2 style="color: #333;">Job Application</h2>
                        <p><strong>Position:</strong> {job_data.get('title', 'N/A')}</p>
                        <p><strong>Company:</strong> {job_data.get('company', 'N/A')}</p>
                        <p><strong>Applicant:</strong> {user_profile.get('name', 'N/A')}</p>
                    </div>
                    <div style="padding: 20px;">
                        {email_content.replace(chr(10), '<br>')}
                    </div>
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-top: 20px;">
                        <p><strong>Contact Information:</strong></p>
                        <p>Email: {user_profile.get('email', 'N/A')}</p>
                        <p>Phone: {user_profile.get('phone', 'N/A')}</p>
                        <p>Location: {user_profile.get('location', 'N/A')}</p>
                        {f'<p>LinkedIn: <a href="{user_profile.get("linkedin_url")}">{user_profile.get("linkedin_url")}</a></p>' if user_profile.get('linkedin_url') else ''}
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Send email
            result = await self.send_email(
                to_email=job_data.get('hiring_manager_email', f"hiring@{job_data.get('company', 'company').lower().replace(' ', '')}.com"),
                subject=f"Application for {job_data.get('title', 'Position')} - {user_profile.get('name', 'Applicant')}",
                content=html_content,
                from_name=user_profile.get('name', 'Job Applicant')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending job application email: {e}")
            return {
                "success": False,
                "message": f"Failed to send job application email: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_follow_up_email(self, job_data: Dict[str, Any], 
                                 user_profile: Dict[str, Any],
                                 application_date: str) -> Dict[str, Any]:
        """
        Send a follow-up email for a job application
        """
        try:
            follow_up_content = f"""
            Dear Hiring Manager,
            
            I hope this email finds you well. I wanted to follow up on my application for the {job_data.get('title', 'position')} role at {job_data.get('company', 'your company')}, which I submitted on {application_date}.
            
            I remain very interested in this opportunity and would appreciate any updates on the status of my application. I am available for an interview at your convenience.
            
            Thank you for your time and consideration.
            
            Best regards,
            {user_profile.get('name', 'Applicant')}
            """
            
            result = await self.send_email(
                to_email=job_data.get('hiring_manager_email', f"hiring@{job_data.get('company', 'company').lower().replace(' ', '')}.com"),
                subject=f"Follow-up: {job_data.get('title', 'Position')} Application",
                content=follow_up_content,
                from_name=user_profile.get('name', 'Job Applicant')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending follow-up email: {e}")
            return {
                "success": False,
                "message": f"Failed to send follow-up email: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            if not all([self.username, self.password, self.from_email]):
                return False
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                
            return True
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False 