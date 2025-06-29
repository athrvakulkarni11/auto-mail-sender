import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Settings:
    """Application settings"""
    
    # API Configuration
    API_TITLE = "Auto Job Application System"
    API_VERSION = "1.0.0"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Groq Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    # Email Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    EMAIL_FROM = os.getenv("EMAIL_FROM")
    
    # Job Sites Configuration
    SUPPORTED_JOB_SITES = [
        "indeed",
        "linkedin", 
        "glassdoor",
        "monster",
        "ziprecruiter"
    ]
    
    # Scraping Configuration
    SCRAPING_DELAY = float(os.getenv("SCRAPING_DELAY", 2.0))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    # CrewAI Configuration
    CREW_MAX_RPM = int(os.getenv("CREW_MAX_RPM", 10))
    CREW_VERBOSE = os.getenv("CREW_VERBOSE", "True").lower() == "true"
    
    # Database Configuration (for future use)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./job_applications.db")
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    
    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    @classmethod
    def validate_settings(cls):
        """Validate required settings"""
        required_settings = [
            ("GROQ_API_KEY", cls.GROQ_API_KEY),
            ("SMTP_USERNAME", cls.SMTP_USERNAME),
            ("SMTP_PASSWORD", cls.SMTP_PASSWORD),
            ("EMAIL_FROM", cls.EMAIL_FROM),
        ]
        
        missing_settings = []
        for name, value in required_settings:
            if not value:
                missing_settings.append(name)
        
        if missing_settings:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_settings)}")
        
        return True

# Global settings instance
settings = Settings() 