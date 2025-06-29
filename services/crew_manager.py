import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq

from models.schemas import JobPosting, UserProfile
from services.job_scraper import JobScraper
from services.email_generator import EmailGenerator
from services.email_sender import EmailSender
from config.settings import settings

logger = logging.getLogger(__name__)

class CrewManager:
    """Manages CrewAI agents for job application automation"""
    
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL
        )
        
        # Initialize services
        self.job_scraper = JobScraper()
        self.email_generator = EmailGenerator()
        self.email_sender = EmailSender()
        
        # Initialize agents
        self.setup_agents()
    
    def setup_agents(self):
        """Setup CrewAI agents without tools to avoid import issues"""
        
        # Job Research Agent
        self.research_agent = Agent(
            role="Job Research Specialist",
            goal="Analyze job postings and extract key information for applications",
            backstory="""You are an expert job research specialist with years of experience 
            analyzing job postings and identifying the best opportunities for candidates. 
            You understand what hiring managers are looking for and can quickly assess 
            job requirements and company culture.""",
            verbose=settings.CREW_VERBOSE,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Email Strategy Agent
        self.strategy_agent = Agent(
            role="Email Strategy Specialist",
            goal="Develop personalized email strategies for job applications",
            backstory="""You are a communication expert who specializes in crafting 
            compelling job application emails. You understand how to tailor messages 
            to specific job requirements and company cultures. You know how to highlight 
            relevant experience and create compelling narratives.""",
            verbose=settings.CREW_VERBOSE,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Application Coordinator Agent
        self.coordinator_agent = Agent(
            role="Application Coordinator",
            goal="Coordinate and execute job applications with personalized emails",
            backstory="""You are a professional application coordinator who manages 
            the entire job application process. You ensure that applications are 
            sent professionally and on time. You coordinate between different 
            specialists to create the best possible application package.""",
            verbose=settings.CREW_VERBOSE,
            allow_delegation=True,
            llm=self.llm
        )
    
    async def process_job_application(self, job_posting: JobPosting, user_profile: UserProfile) -> Dict[str, Any]:
        """
        Process a single job application using CrewAI agents
        """
        try:
            logger.info(f"Processing job application for {job_posting.title} at {job_posting.company}")
            
            # Create tasks for the crew
            research_task = Task(
                description=f"""
                Analyze the job posting for {job_posting.title} at {job_posting.company}.
                
                Job Details:
                - Title: {job_posting.title}
                - Company: {job_posting.company}
                - Location: {job_posting.location}
                - Description: {job_posting.description}
                - Requirements: {', '.join(job_posting.requirements)}
                
                User Profile:
                - Name: {user_profile.name}
                - Experience: {user_profile.experience_years} years
                - Skills: {', '.join(user_profile.skills)}
                - Education: {user_profile.education}
                
                Analyze the job fit and provide recommendations for the application strategy.
                """,
                agent=self.research_agent,
                expected_output="Detailed analysis of job fit and application strategy recommendations"
            )
            
            strategy_task = Task(
                description=f"""
                Based on the research analysis, develop a personalized email strategy for the job application.
                
                Create a compelling cover letter that:
                1. Addresses the specific job requirements
                2. Highlights relevant experience and skills
                3. Shows enthusiasm for the company and position
                4. Is professional and well-written
                5. Includes a clear call to action
                
                Generate both the email content and subject line.
                """,
                agent=self.strategy_agent,
                expected_output="Personalized email content and subject line for the job application"
            )
            
            application_task = Task(
                description=f"""
                Execute the job application by sending the personalized email.
                
                Ensure that:
                1. The email is sent to the correct recipient
                2. The subject line is professional and attention-grabbing
                3. The content is properly formatted
                4. The application is sent in a timely manner
                5. All contact information is included
                
                Send the application and provide confirmation.
                """,
                agent=self.coordinator_agent,
                expected_output="Confirmation of email sent with details"
            )
            
            # Create and run the crew
            crew = Crew(
                agents=[self.research_agent, self.strategy_agent, self.coordinator_agent],
                tasks=[research_task, strategy_task, application_task],
                verbose=settings.CREW_VERBOSE,
                process=Process.sequential
            )
            
            # Execute the crew
            result = crew.kickoff()
            
            logger.info(f"Job application processed successfully for {job_posting.title}")
            
            return {
                "success": True,
                "job_title": job_posting.title,
                "company": job_posting.company,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing job application: {e}")
            return {
                "success": False,
                "job_title": job_posting.title,
                "company": job_posting.company,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_multiple_applications(self, jobs: List[JobPosting], user_profile: UserProfile) -> List[Dict[str, Any]]:
        """
        Process multiple job applications
        """
        results = []
        
        for job in jobs:
            try:
                result = await self.process_job_application(job, user_profile)
                results.append(result)
                
                # Add delay between applications
                await asyncio.sleep(settings.SCRAPING_DELAY)
                
            except Exception as e:
                logger.error(f"Error processing job {job.title}: {e}")
                results.append({
                    "success": False,
                    "job_title": job.title,
                    "company": job.company,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return results
    
    async def create_application_pipeline(self, keywords: List[str], location: str, 
                                        user_profile: UserProfile, max_jobs: int = 10) -> Dict[str, Any]:
        """
        Create a complete job application pipeline
        """
        try:
            logger.info(f"Starting job application pipeline for keywords: {keywords}")
            
            # Step 1: Scrape jobs
            jobs = await self.job_scraper.scrape_jobs(keywords, location, max_jobs)
            
            if not jobs:
                return {
                    "success": False,
                    "message": "No jobs found matching the criteria",
                    "jobs_processed": 0,
                    "applications_sent": 0
                }
            
            # Step 2: Process applications
            application_results = await self.process_multiple_applications(jobs, user_profile)
            
            # Step 3: Analyze results
            successful_applications = [r for r in application_results if r.get("success", False)]
            failed_applications = [r for r in application_results if not r.get("success", False)]
            
            return {
                "success": True,
                "message": "Job application pipeline completed",
                "jobs_found": len(jobs),
                "jobs_processed": len(application_results),
                "applications_sent": len(successful_applications),
                "failed_applications": len(failed_applications),
                "results": application_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in application pipeline: {e}")
            return {
                "success": False,
                "message": f"Pipeline failed: {str(e)}",
                "jobs_processed": 0,
                "applications_sent": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "research_agent": {
                "role": self.research_agent.role,
                "goal": self.research_agent.goal
            },
            "strategy_agent": {
                "role": self.strategy_agent.role,
                "goal": self.strategy_agent.goal
            },
            "coordinator_agent": {
                "role": self.coordinator_agent.role,
                "goal": self.coordinator_agent.goal
            }
        } 