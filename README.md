# Auto Job Application System

An automated job application system that uses CrewAI, FastAPI, and Groq to scrape job postings, generate personalized emails, and send applications to hiring managers.

## Features

- **Job Scraping**: Automatically scrape job postings from multiple sites (Indeed, LinkedIn, Glassdoor)
- **AI-Powered Email Generation**: Use Groq LLM to generate personalized cover letters and application emails
- **CrewAI Integration**: Multi-agent system for job analysis, email strategy, and application coordination
- **Email Automation**: Send professional job application emails with attachments
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Background Processing**: Asynchronous job processing with status tracking

## Architecture

The system consists of several key components:

1. **Job Scraper**: Scrapes job postings from various job sites
2. **Email Generator**: Uses Groq LLM to generate personalized emails
3. **Email Sender**: Handles SMTP email sending
4. **CrewAI Manager**: Orchestrates the entire application process using AI agents
5. **FastAPI Backend**: Provides RESTful API endpoints

## Setup

### Prerequisites

- Python 3.8+
- Chrome browser (for web scraping)
- Groq API key
- SMTP email credentials

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd auto-mail-sender
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
# Groq Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama3-8b-8192

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
EMAIL_FROM=your_email@gmail.com
```

4. Run the application:
```bash
python main.py  
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Job Management
- `POST /jobs/scrape` - Scrape job postings
- `POST /jobs/apply` - Apply to jobs using CrewAI
- `GET /jobs/status/{request_id}` - Get application status

### Email Management
- `POST /email/generate` - Generate personalized email
- `POST /email/send` - Send email

## Usage Examples

### 1. Scrape Jobs

```python
import requests

# Scrape job postings
response = requests.post("http://localhost:8000/jobs/scrape", json={
    "keywords": ["python developer", "software engineer"],
    "location": "San Francisco, CA",
    "max_jobs": 10,
    "user_profile": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "location": "San Francisco, CA",
        "experience_years": 5,
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL"],
        "education": "Bachelor's in Computer Science",
        "resume_url": "https://example.com/resume.pdf",
        "linkedin_url": "https://linkedin.com/in/johndoe"
    }
})

jobs = response.json()
print(f"Found {len(jobs)} jobs")
```

### 2. Apply to Jobs

```python
# Apply to jobs using CrewAI
response = requests.post("http://localhost:8000/jobs/apply", json={
    "keywords": ["python developer"],
    "location": "San Francisco, CA",
    "max_jobs": 5,
    "user_profile": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "location": "San Francisco, CA",
        "experience_years": 5,
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL"],
        "education": "Bachelor's in Computer Science",
        "resume_url": "https://example.com/resume.pdf",
        "linkedin_url": "https://linkedin.com/in/johndoe"
    },
    "auto_apply": True
})

result = response.json()
print(f"Application started: {result['request_id']}")
```

### 3. Generate Email

```python
# Generate personalized email
response = requests.post("http://localhost:8000/email/generate", json={
    "job_posting": {
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "description": "We are looking for a senior Python developer...",
        "requirements": ["Python", "Django", "PostgreSQL"],
        "job_url": "https://example.com/job",
        "hiring_manager_email": "hiring@techcorp.com"
    },
    "user_profile": {
        "name": "John Doe",
        "email": "john@example.com",
        "experience_years": 5,
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL"],
        "education": "Bachelor's in Computer Science"
    },
    "email_type": "cover_letter"
})

email_data = response.json()
print(f"Generated email: {email_data['email_content']}")
```

## CrewAI Agents

The system uses three specialized AI agents:

1. **Job Research Specialist**: Analyzes job postings and extracts key information
2. **Email Strategy Specialist**: Develops personalized email strategies
3. **Application Coordinator**: Coordinates and executes job applications

## Configuration

### Job Sites
Supported job sites can be configured in `config/settings.py`:
- Indeed
- LinkedIn
- Glassdoor
- Monster
- ZipRecruiter

### Email Templates
Email templates can be customized in `services/email_generator.py`:
- Cover letters
- Follow-up emails
- Networking emails

### Scraping Settings
- Delay between requests
- Maximum retries
- User agent configuration

## Error Handling

The system includes comprehensive error handling:
- Rate limiting for API calls
- Fallback email templates
- Graceful degradation when services are unavailable
- Detailed logging for debugging

## Security Considerations

- API keys stored in environment variables
- SMTP authentication
- Input validation using Pydantic
- CORS configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue on GitHub. 