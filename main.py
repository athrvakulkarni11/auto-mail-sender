import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from models.schemas import JobApplicationRequest, UserProfile, JobPosting
from services.crew_manager import CrewManager
from services.job_scraper import JobScraper
from services.email_generator import EmailGenerator
from services.email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for services
crew_manager = None
job_scraper = None
email_generator = None
email_sender = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global crew_manager, job_scraper, email_generator, email_sender
    
    # Startup
    logger.info("Starting Auto Mail Sender application...")
    
    try:
        # Initialize services
        crew_manager = CrewManager()
        job_scraper = JobScraper()
        email_generator = EmailGenerator()
        email_sender = EmailSender()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Auto Mail Sender application...")

# Create FastAPI app
app = FastAPI(
    title="Auto Mail Sender",
    description="Automated job application system using CrewAI and Groq",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Auto Mail Sender API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "crew_manager": crew_manager is not None,
            "job_scraper": job_scraper is not None,
            "email_generator": email_generator is not None,
            "email_sender": email_sender is not None
        }
    }

@app.post("/api/jobs/scrape")
async def scrape_jobs(request: JobApplicationRequest):
    """Scrape jobs based on keywords and location"""
    try:
        logger.info(f"Scraping jobs for keywords: {request.keywords}")
        
        jobs = await job_scraper.scrape_jobs(
            keywords=request.keywords,
            location=request.location,
            max_jobs=request.max_jobs
        )
        
        return {
            "success": True,
            "jobs_found": len(jobs),
            "jobs": [job.dict() for job in jobs]
        }
        
    except Exception as e:
        logger.error(f"Error scraping jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/generate")
async def generate_email(request: dict):
    """Generate personalized email for job application"""
    try:
        job_posting = JobPosting(**request["job_posting"])
        user_profile = UserProfile(**request["user_profile"])
        
        email_content = await email_generator.generate_email(job_posting, user_profile)
        
        return {
            "success": True,
            "email_content": email_content
        }
        
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/send")
async def send_email(request: dict):
    """Send email for job application"""
    try:
        job_posting = JobPosting(**request["job_posting"])
        user_profile = UserProfile(**request["user_profile"])
        email_content = request["email_content"]
        
        result = await email_sender.send_email(job_posting, user_profile, email_content)
        
        return {
            "success": True,
            "email_sent": result
        }
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/application/process")
async def process_application(request: dict):
    """Process a single job application using CrewAI"""
    try:
        job_posting = JobPosting(**request["job_posting"])
        user_profile = UserProfile(**request["user_profile"])
        
        result = await crew_manager.process_job_application(job_posting, user_profile)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/application/pipeline")
async def run_application_pipeline(request: JobApplicationRequest, background_tasks: BackgroundTasks):
    """Run complete job application pipeline"""
    try:
        logger.info(f"Starting application pipeline for keywords: {request.keywords}")
        
        # Create user profile from request
        user_profile = UserProfile(
            name=request.user_name,
            email=request.user_email,
            experience_years=request.experience_years,
            skills=request.skills,
            education=request.education
        )
        
        # Run pipeline in background
        background_tasks.add_task(
            crew_manager.create_application_pipeline,
            request.keywords,
            request.location,
            user_profile,
            request.max_jobs
        )
        
        return {
            "success": True,
            "message": "Application pipeline started in background",
            "keywords": request.keywords,
            "location": request.location,
            "max_jobs": request.max_jobs
        }
        
    except Exception as e:
        logger.error(f"Error starting application pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crew/status")
async def get_crew_status():
    """Get status of CrewAI agents"""
    try:
        if not crew_manager:
            raise HTTPException(status_code=503, detail="Crew manager not initialized")
        
        status = crew_manager.get_agent_status()
        
        return {
            "success": True,
            "agents": status
        }
        
    except Exception as e:
        logger.error(f"Error getting crew status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Get application configuration (without sensitive data)"""
    return {
        "groq_model": settings.GROQ_MODEL,
        "scraping_delay": settings.SCRAPING_DELAY,
        "crew_verbose": settings.CREW_VERBOSE,
        "max_retries": settings.MAX_RETRIES
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
