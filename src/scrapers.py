"""
Job Scrapers Module
Fetch job data from Adzuna API and other sources
"""
import requests
import pandas as pd
from datetime import datetime
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.logger import logging
from src.exception import CustomException


class AdzunaAPI:
    """
    Adzuna API Integration for fetching Indian tech jobs
    
    To use: Sign up at https://developer.adzuna.com/
    Get your app_id and app_key
    """
    
    def __init__(self, app_id=None, app_key=None):
        """
        Initialize Adzuna API client
        
        Args:
            app_id: Adzuna application ID
            app_key: Adzuna application key
        """
        # Get credentials from environment variables or parameters
        self.app_id = app_id or os.getenv('ADZUNA_APP_ID', 'YOUR_APP_ID')
        self.app_key = app_key or os.getenv('ADZUNA_APP_KEY', 'YOUR_APP_KEY')
        self.base_url = "https://api.adzuna.com/v1/api/jobs"
        self.country = "in"  # India
        
        logging.info("Initialized Adzuna API client")
    
    def search_jobs(self, keywords="software engineer", location="", page=1, results_per_page=50, timeout=10):
        """
        Search for jobs using Adzuna API with retry logic
        
        Args:
            keywords: Job search keywords
            location: Location filter
            page: Page number
            results_per_page: Number of results per page (max 50)
            timeout: Request timeout in seconds
            
        Returns:
            List of job dictionaries
        """
        try:
            url = f"{self.base_url}/{self.country}/search/{page}"
            
            params = {
                'app_id': self.app_id,
                'app_key': self.app_key,
                'results_per_page': results_per_page,
                'what': keywords,
                'content-type': 'application/json'
            }
            
            if location:
                params['where'] = location
            
            logging.info(f"Fetching jobs: {keywords} in {location} (page {page})")
            
            # Add retry logic
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    response = requests.get(url, params=params, timeout=timeout)
                    response.raise_for_status()
                    
                    data = response.json()
                    jobs = data.get('results', [])
                    
                    logging.info(f"✓ Fetched {len(jobs)} jobs for {keywords} in {location}")
                    return jobs
                    
                except requests.exceptions.Timeout:
                    if attempt < max_retries:
                        logging.warning(f"Timeout attempt {attempt + 1}/{max_retries + 1}, retrying...")
                        time.sleep(1)
                        continue
                    else:
                        logging.error("API timeout - max retries exceeded")
                        return []
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries:
                        logging.warning(f"Connection error attempt {attempt + 1}/{max_retries + 1}, retrying...")
                        time.sleep(1)
                        continue
                    else:
                        logging.error("API connection error - max retries exceeded")
                        return []
            
            return []
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request error: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error in search_jobs: {str(e)}")
            return []
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request error: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error in search_jobs: {str(e)}")
            return []
    
    def fetch_multiple_roles(self, roles, locations, max_results_per_role=100):
        """
        Fetch jobs for multiple roles and locations using parallel execution
        
        Args:
            roles: List of job roles to search
            locations: List of locations
            max_results_per_role: Maximum results per role
            
        Returns:
            DataFrame with all jobs
        """
        try:
            all_jobs = []
            results_per_page = 50
            
            # Create list of tasks (role, location) combinations
            tasks = []
            for role in roles:
                for location in locations:
                    pages_needed = (max_results_per_role // results_per_page) + 1
                    for page in range(1, pages_needed + 1):
                        tasks.append((role, location, page, results_per_page))
            
            logging.info(f"⚡ Starting parallel scraping with {len(tasks)} tasks")
            
            # Use ThreadPoolExecutor for parallel requests (3 workers for safe rate limiting)
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(self.search_jobs, task[0], task[1], task[2], task[3]): task 
                    for task in tasks
                }
                
                # Collect results as they complete
                completed = 0
                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        jobs = future.result()
                        if jobs:
                            all_jobs.extend(jobs)
                        completed += 1
                        if completed % 10 == 0:
                            logging.info(f"⏳ Progress: {completed}/{len(tasks)} requests completed ({len(all_jobs)} jobs so far)")
                    except Exception as e:
                        logging.error(f"Task failed for {task[0]} in {task[1]}: {str(e)}")
            
            # Convert to DataFrame
            jobs_df = self._parse_jobs_to_dataframe(all_jobs)
            logging.info(f"✅ Total jobs fetched: {len(jobs_df)}")
            
            return jobs_df
            
        except Exception as e:
            logging.error(f"Error in fetch_multiple_roles: {str(e)}")
            raise CustomException(e, sys)
    
    def _parse_jobs_to_dataframe(self, jobs):
        """
        Parse Adzuna API response to DataFrame
        
        Args:
            jobs: List of job dictionaries from API
            
        Returns:
            DataFrame with standardized columns
        """
        try:
            parsed_jobs = []
            
            for job in jobs:
                # Extract skills from description or category
                skills = self._extract_skills(job)
                
                # Extract experience level
                experience = self._extract_experience(job)
                
                # Parse salary
                salary_min = job.get('salary_min', 0)
                salary_max = job.get('salary_max', 0)
                salary = f"{salary_min}-{salary_max}" if salary_min and salary_max else "Not specified"
                
                parsed_job = {
                    'job_id': job.get('id', ''),
                    'title': job.get('title', ''),
                    'company': job.get('company', {}).get('display_name', 'Unknown'),
                    'skills': ', '.join(skills),
                    'location': job.get('location', {}).get('display_name', ''),
                    'experience': experience,
                    'salary': salary,
                    'salary_min': salary_min,
                    'salary_max': salary_max,
                    'description': job.get('description', '')[:500],  # Truncate
                    'posted_date': job.get('created', datetime.now().isoformat()),
                    'url': job.get('redirect_url', ''),
                    'category': job.get('category', {}).get('label', '')
                }
                
                parsed_jobs.append(parsed_job)
            
            df = pd.DataFrame(parsed_jobs)
            
            # Convert posted_date to datetime
            df['posted_date'] = pd.to_datetime(df['posted_date'], errors='coerce')
            
            return df
            
        except Exception as e:
            logging.error(f"Error parsing jobs: {str(e)}")
            return pd.DataFrame()
    
    def _extract_skills(self, job):
        """
        Extract skills from job description
        
        Args:
            job: Job dictionary
            
        Returns:
            List of skills
        """
        common_skills = [
            'Python', 'Java', 'JavaScript', 'React', 'Node.js', 'Angular',
            'Vue.js', 'Django', 'Flask', 'Spring Boot', 'AWS', 'Azure',
            'Docker', 'Kubernetes', 'SQL', 'MongoDB', 'PostgreSQL',
            'Machine Learning', 'AI', 'Data Science', 'DevOps', 'CI/CD',
            'Git', 'REST API', 'Microservices', 'Agile', 'Scrum',
            'HTML', 'CSS', 'TypeScript', 'C++', 'C#', '.NET', 'PHP',
            'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin', 'TensorFlow',
            'PyTorch', 'Spark', 'Hadoop', 'Tableau', 'Power BI'
        ]
        
        description = job.get('description', '').lower()
        title = job.get('title', '').lower()
        category = job.get('category', {}).get('label', '').lower()
        
        found_skills = []
        
        for skill in common_skills:
            if skill.lower() in description or skill.lower() in title or skill.lower() in category:
                found_skills.append(skill)
        
        # If no skills found, add some based on category
        if not found_skills:
            if 'software' in title or 'developer' in title:
                found_skills = ['Python', 'JavaScript', 'SQL']
            elif 'data' in title:
                found_skills = ['Python', 'SQL', 'Data Science']
            elif 'devops' in title:
                found_skills = ['Docker', 'Kubernetes', 'AWS']
        
        return found_skills[:10]  # Limit to 10 skills
    
    def _extract_experience(self, job):
        """
        Extract experience level from job
        
        Args:
            job: Job dictionary
            
        Returns:
            Experience string
        """
        description = job.get('description', '').lower()
        title = job.get('title', '').lower()
        
        # Look for experience patterns
        if 'senior' in title or 'lead' in title or 'principal' in title:
            return '5-10 years'
        elif 'junior' in title or 'entry' in title or 'fresher' in title:
            return '0-2 years'
        elif 'mid' in title or 'intermediate' in title:
            return '2-5 years'
        elif '5+' in description or 'minimum 5' in description:
            return '5-10 years'
        elif '3+' in description or 'minimum 3' in description:
            return '2-5 years'
        else:
            return '0-2 years'


def fetch_and_save_jobs(app_id=None, app_key=None):
    """
    Main function to fetch jobs and save to CSV with parallel execution
    
    Args:
        app_id: Adzuna app ID
        app_key: Adzuna app key
        
    Returns:
        DataFrame with fetched jobs, or None if fetch fails
    """
    try:
        start_time = time.time()
        logging.info("=" * 60)
        logging.info("🚀 Starting parallel job fetch process")
        logging.info("=" * 60)
        
        # Initialize API
        api = AdzunaAPI(app_id, app_key)
        
        # Define roles and locations to search
        roles = [
            'software engineer',
            'backend developer',
            'frontend developer',
            'full stack developer',
            'python developer',
            'data scientist',
            'devops engineer',
            'machine learning engineer',
            'java developer',
            'react developer',
            'cloud engineer',
            'qa engineer',
            'mobile developer',
            'solutions architect',
            'technical lead'
        ]
        
        locations = [
            'Bangalore',
            'Mumbai',
            'Delhi',
            'Hyderabad',
            'Pune',
            'Chennai',
            'Gurgaon',
            'Noida',
            'Ahmedabad',
            'Kochi'
        ]
        
        logging.info(f"📊 Configuration:")
        logging.info(f"   - Roles: {len(roles)}")
        logging.info(f"   - Locations: {len(locations)}")
        logging.info(f"   - Total combinations: {len(roles) * len(locations)}")
        logging.info(f"   - Parallel workers: 3 (ThreadPoolExecutor)")
        logging.info(f"   - Expected duration: ~2-3 minutes")
        logging.info("=" * 60)
        
        # Fetch jobs with parallel execution
        jobs_df = api.fetch_multiple_roles(roles, locations, max_results_per_role=50)
        
        if jobs_df.empty:
            logging.warning("⚠️ No jobs fetched from API")
            return None
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        # Delete old model file
        model_file = 'models/recommendation_model.pkl'
        if os.path.exists(model_file):
            try:
                file_size = os.path.getsize(model_file) / (1024*1024)
                os.remove(model_file)
                logging.info("=" * 60)
                logging.info("🗑️  DELETING OLD PICKLE MODEL FILE")
                logging.info("=" * 60)
                logging.info(f"❌ PICKLE DELETED: {model_file}")
                logging.info(f"   - Size: {file_size:.2f} MB")
                logging.info(f"   - Reason: New data fetched, model will retrain")
                logging.info("=" * 60)
            except Exception as e:
                logging.warning(f"Could not delete model file: {str(e)}")
        
        # Save to CSV
        from src.data_loader import save_jobs_to_csv
        save_jobs_to_csv(jobs_df)
        
        logging.info("=" * 60)
        logging.info(f"✅ SUCCESS: Fetched and saved {len(jobs_df)} jobs")
        logging.info(f"⏱️  Total time: {minutes}m {seconds}s")
        logging.info(f"📈 Average: {len(jobs_df) / elapsed_time:.1f} jobs/sec")
        logging.info("=" * 60)
        
        return jobs_df
        
    except Exception as e:
        logging.error(f"❌ Error in fetch_and_save_jobs: {str(e)}")
        return None


if __name__ == "__main__":
    # For testing - run this directly to fetch jobs
    fetch_and_save_jobs()
