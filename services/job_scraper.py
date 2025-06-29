import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict, Any
import time
import re
import logging
from urllib.parse import urljoin, urlparse

from models.schemas import JobPosting
from config.settings import settings

logger = logging.getLogger(__name__)

class JobScraper:
    """Service for scraping job postings from various job sites"""
    
    def __init__(self):
        self.session = None
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Selenium WebDriver for dynamic content scraping"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-agent={settings.USER_AGENT}")
            
            # Use the new Service class and correct WebDriver initialization
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            self.driver = None
    
    async def scrape_jobs(self, keywords: List[str], location: str, max_jobs: int = 10) -> List[JobPosting]:
        """
        Scrape jobs from multiple sources based on keywords and location
        """
        jobs = []
        
        # Scrape from different job sites
        for site in settings.SUPPORTED_JOB_SITES:
            try:
                site_jobs = await self._scrape_site(site, keywords, location, max_jobs // len(settings.SUPPORTED_JOB_SITES))
                jobs.extend(site_jobs)
                
                if len(jobs) >= max_jobs:
                    break
                    
                # Add delay between sites
                await asyncio.sleep(settings.SCRAPING_DELAY)
                
            except Exception as e:
                logger.error(f"Error scraping {site}: {e}")
                continue
        
        return jobs[:max_jobs]
    
    async def _scrape_site(self, site: str, keywords: List[str], location: str, max_jobs: int) -> List[JobPosting]:
        """Scrape jobs from a specific site"""
        if site == "indeed":
            return await self._scrape_indeed(keywords, location, max_jobs)
        elif site == "linkedin":
            return await self._scrape_linkedin(keywords, location, max_jobs)
        elif site == "glassdoor":
            return await self._scrape_glassdoor(keywords, location, max_jobs)
        else:
            logger.warning(f"Unsupported job site: {site}")
            return []
    
    async def _scrape_indeed(self, keywords: List[str], location: str, max_jobs: int) -> List[JobPosting]:
        """Scrape jobs from Indeed"""
        jobs = []
        keyword_str = " ".join(keywords)
        
        try:
            # Construct Indeed search URL
            search_url = f"https://www.indeed.com/jobs?q={keyword_str.replace(' ', '+')}&l={location.replace(' ', '+')}"
            
            if self.driver:
                self.driver.get(search_url)
                await asyncio.sleep(3)  # Wait for page to load
                
                # Find job cards
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-jk]")
                
                for card in job_cards[:max_jobs]:
                    try:
                        job_data = self._extract_indeed_job_data(card)
                        if job_data:
                            jobs.append(JobPosting(**job_data))
                    except Exception as e:
                        logger.error(f"Error extracting job data from Indeed: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
        
        return jobs
    
    def _extract_indeed_job_data(self, card) -> Dict[str, Any]:
        """Extract job data from Indeed job card"""
        try:
            title = card.find_element(By.CSS_SELECTOR, "h2.jobTitle").text
            company = card.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text
            location = card.find_element(By.CSS_SELECTOR, "[data-testid='job-location']").text
            
            # Get job URL
            job_link = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a")
            job_url = job_link.get_attribute("href")
            
            # Get job description (basic)
            description = card.find_element(By.CSS_SELECTOR, ".job-snippet").text
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "job_url": job_url,
                "requirements": [],
                "salary_range": None,
                "hiring_manager_email": None,
                "application_deadline": None,
                "job_type": None,
                "remote_option": None
            }
        except Exception as e:
            logger.error(f"Error extracting Indeed job data: {e}")
            return None
    
    async def _scrape_linkedin(self, keywords: List[str], location: str, max_jobs: int) -> List[JobPosting]:
        """Scrape jobs from LinkedIn"""
        jobs = []
        keyword_str = " ".join(keywords)
        
        try:
            # Construct LinkedIn search URL
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword_str.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
            
            if self.driver:
                self.driver.get(search_url)
                await asyncio.sleep(3)
                
                # Find job cards
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-search-card")
                
                for card in job_cards[:max_jobs]:
                    try:
                        job_data = self._extract_linkedin_job_data(card)
                        if job_data:
                            jobs.append(JobPosting(**job_data))
                    except Exception as e:
                        logger.error(f"Error extracting job data from LinkedIn: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
        
        return jobs
    
    def _extract_linkedin_job_data(self, card) -> Dict[str, Any]:
        """Extract job data from LinkedIn job card"""
        try:
            title = card.find_element(By.CSS_SELECTOR, ".job-search-card__title").text
            company = card.find_element(By.CSS_SELECTOR, ".job-search-card__subtitle").text
            location = card.find_element(By.CSS_SELECTOR, ".job-search-card__location").text
            
            # Get job URL
            job_link = card.find_element(By.CSS_SELECTOR, ".job-search-card__title")
            job_url = job_link.get_attribute("href")
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "description": "",  # Would need to visit individual job page
                "job_url": job_url,
                "requirements": [],
                "salary_range": None,
                "hiring_manager_email": None,
                "application_deadline": None,
                "job_type": None,
                "remote_option": None
            }
        except Exception as e:
            logger.error(f"Error extracting LinkedIn job data: {e}")
            return None
    
    async def _scrape_glassdoor(self, keywords: List[str], location: str, max_jobs: int) -> List[JobPosting]:
        """Scrape jobs from Glassdoor"""
        jobs = []
        keyword_str = " ".join(keywords)
        
        try:
            # Construct Glassdoor search URL
            search_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keyword_str.replace(' ', '+')}&locT=N&locId=1&jobType=&fromAge=-1&minSalary=0&includeUnknownSalary=false&radius=100&cityId=-1&minRating=0.0&industryId=-1&sgocId=-1&seniorityType=all&companyId=-1&employerSizes=0&applicationType=0&remoteWorkType=0"
            
            if self.driver:
                self.driver.get(search_url)
                await asyncio.sleep(3)
                
                # Find job cards
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".react-job-listing")
                
                for card in job_cards[:max_jobs]:
                    try:
                        job_data = self._extract_glassdoor_job_data(card)
                        if job_data:
                            jobs.append(JobPosting(**job_data))
                    except Exception as e:
                        logger.error(f"Error extracting job data from Glassdoor: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Glassdoor: {e}")
        
        return jobs
    
    def _extract_glassdoor_job_data(self, card) -> Dict[str, Any]:
        """Extract job data from Glassdoor job card"""
        try:
            title = card.find_element(By.CSS_SELECTOR, "[data-test='job-link']").text
            company = card.find_element(By.CSS_SELECTOR, "[data-test='employer-name']").text
            location = card.find_element(By.CSS_SELECTOR, "[data-test='location']").text
            
            # Get job URL
            job_link = card.find_element(By.CSS_SELECTOR, "[data-test='job-link']")
            job_url = job_link.get_attribute("href")
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "description": "",  # Would need to visit individual job page
                "job_url": job_url,
                "requirements": [],
                "salary_range": None,
                "hiring_manager_email": None,
                "application_deadline": None,
                "job_type": None,
                "remote_option": None
            }
        except Exception as e:
            logger.error(f"Error extracting Glassdoor job data: {e}")
            return None
    
    async def get_job_details(self, job_url: str) -> Dict[str, Any]:
        """Get detailed job information from a specific job URL"""
        try:
            if self.driver:
                self.driver.get(job_url)
                await asyncio.sleep(3)
                
                # Extract detailed information
                description = self.driver.find_element(By.CSS_SELECTOR, ".job-description").text
                
                # Try to find requirements
                requirements = []
                try:
                    req_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-requirements li")
                    requirements = [elem.text for elem in req_elements]
                except:
                    pass
                
                return {
                    "description": description,
                    "requirements": requirements
                }
                
        except Exception as e:
            logger.error(f"Error getting job details: {e}")
            return {}
    
    def __del__(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit() 