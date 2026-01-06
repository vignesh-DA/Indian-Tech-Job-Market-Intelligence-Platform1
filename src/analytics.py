"""
Analytics Module
Calculate market intelligence metrics for dashboard
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from src.logger import logging
from src.exception import CustomException
from src.data_loader import normalize_location


def filter_jobs_by_location(jobs_df, location):
    """
    Filter jobs by normalized location
    
    Args:
        jobs_df: DataFrame with job data
        location: Location to filter by (normalized city name)
        
    Returns:
        Filtered DataFrame
    """
    if not location or location == 'All':
        return jobs_df
    
    filtered = []
    location_lower = location.lower()
    
    for idx, row in jobs_df.iterrows():
        normalized = normalize_location(row.get('location', '')).lower()
        if normalized == location_lower or normalized == 'remote':
            filtered.append(idx)
    
    return jobs_df.loc[filtered].copy() if filtered else pd.DataFrame()


def calculate_salary_trends(jobs_df, group_by='location'):
    """
    Calculate salary trends by location or role
    
    Args:
        jobs_df: DataFrame with job data
        group_by: Column to group by ('location', 'title', etc.)
        
    Returns:
        DataFrame with salary statistics
    """
    try:
        if jobs_df.empty or 'salary_min' not in jobs_df.columns:
            return pd.DataFrame()
        
        # Filter valid salaries
        valid_salaries = jobs_df[
            (jobs_df['salary_min'] > 0) & 
            (jobs_df['salary_max'] > 0)
        ].copy()
        
        if valid_salaries.empty:
            return pd.DataFrame()
        
        # Calculate average salary
        valid_salaries['avg_salary'] = (
            valid_salaries['salary_min'] + valid_salaries['salary_max']
        ) / 2
        
        # Group and calculate stats
        salary_stats = valid_salaries.groupby(group_by).agg({
            'avg_salary': ['mean', 'median', 'min', 'max', 'count']
        }).round(0)
        
        salary_stats.columns = ['Average Salary', 'Typical Salary', 'Lowest Salary', 'Highest Salary', 'Number of Jobs']
        salary_stats = salary_stats.reset_index()
        salary_stats = salary_stats.sort_values('Average Salary', ascending=False)
        
        logging.info(f"Calculated salary trends for {len(salary_stats)} groups")
        return salary_stats
        
    except Exception as e:
        logging.error(f"Error calculating salary trends: {str(e)}")
        raise CustomException(e, sys)


def get_top_skills(jobs_df, top_n=20):
    """
    Get most in-demand skills from jobs
    
    Args:
        jobs_df: DataFrame with job data
        top_n: Number of top skills to return
        
    Returns:
        DataFrame with skill counts
    """
    try:
        if jobs_df.empty or 'skills' not in jobs_df.columns:
            return pd.DataFrame()
        
        # Count skill occurrences
        skill_counts = {}
        
        for skills_str in jobs_df['skills'].dropna():
            if isinstance(skills_str, str):
                skills = [s.strip() for s in skills_str.split(',')]
                for skill in skills:
                    if skill:
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Convert to dataframe
        skills_df = pd.DataFrame(
            list(skill_counts.items()),
            columns=['skill', 'count']
        )
        
        skills_df = skills_df.sort_values('count', ascending=False).head(top_n)
        
        logging.info(f"Found {len(skills_df)} top skills")
        return skills_df
        
    except Exception as e:
        logging.error(f"Error getting top skills: {str(e)}")
        return pd.DataFrame()


def get_top_companies(jobs_df, top_n=15):
    """
    Get companies with most job postings
    
    Args:
        jobs_df: DataFrame with job data
        top_n: Number of top companies to return
        
    Returns:
        DataFrame with company job counts
    """
    try:
        if jobs_df.empty or 'company' not in jobs_df.columns:
            return pd.DataFrame()
        
        company_counts = jobs_df['company'].value_counts().head(top_n)
        
        companies_df = pd.DataFrame({
            'company': company_counts.index,
            'job_count': company_counts.values
        })
        
        logging.info(f"Found {len(companies_df)} top companies")
        return companies_df
        
    except Exception as e:
        logging.error(f"Error getting top companies: {str(e)}")
        return pd.DataFrame()


def calculate_location_stats(jobs_df):
    """
    Calculate job statistics by location
    
    Args:
        jobs_df: DataFrame with job data
        
    Returns:
        DataFrame with location statistics
    """
    try:
        if jobs_df.empty or 'location' not in jobs_df.columns:
            return pd.DataFrame()
        
        location_stats = jobs_df.groupby('location').agg({
            'job_id': 'count',
            'salary_min': 'mean',
            'salary_max': 'mean'
        }).round(0)
        
        location_stats.columns = ['job_count', 'avg_salary_min', 'avg_salary_max']
        location_stats['avg_salary'] = (
            location_stats['avg_salary_min'] + location_stats['avg_salary_max']
        ) / 2
        
        location_stats = location_stats.reset_index()
        location_stats = location_stats.sort_values('job_count', ascending=False)
        
        logging.info(f"Calculated stats for {len(location_stats)} locations")
        return location_stats
        
    except Exception as e:
        logging.error(f"Error calculating location stats: {str(e)}")
        return pd.DataFrame()


def get_posting_trends(jobs_df, days=30):
    """
    Get job posting trends over time
    
    Args:
        jobs_df: DataFrame with job data
        days: Number of days to analyze
        
    Returns:
        DataFrame with daily job counts
    """
    try:
        if jobs_df.empty or 'posted_date' not in jobs_df.columns:
            return pd.DataFrame()
        
        # Ensure posted_date is datetime with UTC timezone
        jobs_df['posted_date'] = pd.to_datetime(jobs_df['posted_date'], errors='coerce', utc=True)
        
        # Filter recent posts (make cutoff_date timezone-aware)
        cutoff_date = pd.Timestamp(datetime.now() - timedelta(days=days)).tz_localize('UTC')
        recent_jobs = jobs_df[jobs_df['posted_date'] >= cutoff_date].copy()
        
        if recent_jobs.empty:
            return pd.DataFrame()
        
        # Extract date only
        recent_jobs['date'] = recent_jobs['posted_date'].dt.date
        
        # Count jobs per day
        daily_counts = recent_jobs.groupby('date').size().reset_index(name='count')
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])
        
        # Fill missing dates with 0
        date_range = pd.date_range(
            start=cutoff_date.date(),
            end=datetime.now().date(),
            freq='D'
        )
        
        full_range = pd.DataFrame({'date': date_range})
        daily_counts = full_range.merge(daily_counts, on='date', how='left')
        daily_counts['count'] = daily_counts['count'].fillna(0).astype(int)
        
        logging.info(f"Calculated posting trends for {len(daily_counts)} days")
        return daily_counts
        
    except Exception as e:
        logging.error(f"Error calculating posting trends: {str(e)}")
        return pd.DataFrame()


def get_experience_distribution(jobs_df):
    """
    Get distribution of experience requirements
    
    Args:
        jobs_df: DataFrame with job data
        
    Returns:
        DataFrame with experience level counts
    """
    try:
        if jobs_df.empty or 'experience' not in jobs_df.columns:
            return pd.DataFrame()
        
        exp_counts = jobs_df['experience'].value_counts()
        
        exp_df = pd.DataFrame({
            'experience_level': exp_counts.index,
            'count': exp_counts.values
        })
        
        logging.info(f"Calculated experience distribution")
        return exp_df
        
    except Exception as e:
        logging.error(f"Error calculating experience distribution: {str(e)}")
        return pd.DataFrame()


def get_role_distribution(jobs_df, top_n=10):
    """
    Get distribution of job roles
    
    Args:
        jobs_df: DataFrame with job data
        top_n: Number of top roles to return
        
    Returns:
        DataFrame with role counts
    """
    try:
        if jobs_df.empty or 'title' not in jobs_df.columns:
            return pd.DataFrame()
        
        # Simplify job titles by extracting key roles from both title and skills
        import re
        
        def extract_role(row):
            title_lower = str(row.get('title', '')).lower()
            skills_lower = str(row.get('skills', '')).lower()
            combined = title_lower + ' ' + skills_lower
            
            # Remove seniority prefixes for cleaner categorization
            title_clean = re.sub(r'^(senior|lead|staff|principal|sr\.|junior|associate|entry level|mid level)\s+', '', title_lower)
            title_clean = re.sub(r'\s+(i{1,3}|iv|[1-4]|a|b)$', '', title_clean)
            
            # Specific role checks (order matters - most specific first)
            if 'data scientist' in combined:
                return 'Data Scientist'
            elif 'data engineer' in combined:
                return 'Data Engineer'
            elif 'data analyst' in combined:
                return 'Data Analyst'
            elif 'machine learning' in combined or 'ml engineer' in combined:
                return 'ML Engineer'
            elif 'full stack' in combined or 'fullstack' in combined:
                return 'Full Stack Developer'
            elif 'backend' in combined or 'back-end' in combined or 'back end' in combined:
                return 'Backend Developer'
            elif 'frontend' in combined or 'front-end' in combined or 'front end' in combined:
                return 'Frontend Developer'
            elif 'devops' in combined:
                return 'DevOps Engineer'
            elif 'site reliability' in combined or 'sre' in combined:
                return 'Site Reliability Engineer'
            elif 'qa' in combined or 'test' in combined or 'quality assurance' in combined:
                return 'QA Engineer'
            
            # Technology-specific developers
            elif ('java' in combined and 'javascript' not in combined) or 'javaee' in combined or 'j2ee' in combined:
                return 'Java Developer'
            elif 'python' in combined or 'django' in combined or 'flask' in combined:
                return 'Python Developer'
            elif 'react native' in combined:
                return 'React Native Developer'
            elif 'react' in combined or 'reactjs' in combined or 'react.js' in combined:
                return 'React Developer'
            elif 'angular' in combined or 'angularjs' in combined:
                return 'Angular Developer'
            elif 'vue' in combined or 'vuejs' in combined:
                return 'Vue Developer'
            elif 'node' in combined or 'nodejs' in combined or 'node.js' in combined:
                return 'Node.js Developer'
            elif '.net' in combined or 'dotnet' in combined or 'c#' in combined:
                return '.NET Developer'
            elif 'php' in combined or 'laravel' in combined:
                return 'PHP Developer'
            elif 'ruby' in combined or 'rails' in combined:
                return 'Ruby Developer'
            elif 'golang' in combined or 'go developer' in combined:
                return 'Go Developer'
            elif 'rust' in combined:
                return 'Rust Developer'
            elif 'flutter' in combined or 'dart' in combined:
                return 'Flutter Developer'
            elif 'android' in combined or 'kotlin' in combined:
                return 'Android Developer'
            elif 'ios' in combined or 'swift' in combined or 'objective-c' in combined:
                return 'iOS Developer'
            elif 'mobile' in combined:
                return 'Mobile Developer'
            elif 'mern' in combined:
                return 'MERN Stack Developer'
            elif 'mean' in combined:
                return 'MEAN Stack Developer'
            
            # Infrastructure & Cloud
            elif 'cloud' in combined or 'aws' in combined or 'azure' in combined or 'gcp' in combined:
                return 'Cloud Engineer'
            elif 'embedded' in combined or 'firmware' in combined:
                return 'Embedded Engineer'
            elif 'security' in combined or 'cybersecurity' in combined:
                return 'Security Engineer'
            
            # Leadership & Architecture
            elif 'architect' in combined:
                return 'Solutions Architect'
            elif 'engineering manager' in combined or 'development manager' in combined:
                return 'Engineering Manager'
            elif 'tech lead' in combined or 'technical lead' in combined or 'team lead' in combined:
                return 'Technical Lead'
            
            # Design
            elif 'ui' in combined or 'ux' in combined or 'designer' in combined:
                return 'UI/UX Developer'
            elif 'web' in combined:
                return 'Web Developer'
            
            # Generic software engineer (after checking all specifics)
            elif 'software engineer' in title_clean or 'software developer' in title_clean:
                return 'Software Engineer'
            elif 'programmer' in combined:
                return 'Software Engineer'
            
            # If nothing matches, return simplified title
            else:
                # Capitalize first letter of each word
                return ' '.join(word.capitalize() for word in title_clean.split()[:4])
        
        jobs_df['role'] = jobs_df.apply(extract_role, axis=1)
        
        role_counts = jobs_df['role'].value_counts().head(top_n)
        
        role_df = pd.DataFrame({
            'role': role_counts.index,
            'count': role_counts.values
        })
        
        logging.info(f"Calculated role distribution")
        return role_df
        
    except Exception as e:
        logging.error(f"Error calculating role distribution: {str(e)}")
        return pd.DataFrame()


def calculate_summary_stats(jobs_df):
    """
    Calculate overall summary statistics
    
    Args:
        jobs_df: DataFrame with job data
        
    Returns:
        Dictionary with summary stats
    """
    try:
        if jobs_df.empty:
            return {}
        
        stats = {
            'total_jobs': len(jobs_df),
            'total_companies': jobs_df['company'].nunique() if 'company' in jobs_df.columns else 0,
            'total_locations': jobs_df['location'].nunique() if 'location' in jobs_df.columns else 0,
            'avg_salary': 0,
            'jobs_today': 0,
            'jobs_this_week': 0
        }
        
        # Calculate average salary
        if 'salary_min' in jobs_df.columns and 'salary_max' in jobs_df.columns:
            valid_salaries = jobs_df[
                (jobs_df['salary_min'] > 0) & 
                (jobs_df['salary_max'] > 0)
            ]
            if not valid_salaries.empty:
                avg_sal = (valid_salaries['salary_min'] + valid_salaries['salary_max']) / 2
                stats['avg_salary'] = int(avg_sal.mean())
        
        # Calculate recent postings
        if 'posted_date' in jobs_df.columns:
            jobs_df['posted_date'] = pd.to_datetime(jobs_df['posted_date'], errors='coerce')
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            stats['jobs_today'] = len(jobs_df[jobs_df['posted_date'].dt.date == today])
            stats['jobs_this_week'] = len(jobs_df[jobs_df['posted_date'].dt.date >= week_ago])
        
        logging.info("Calculated summary statistics")
        return stats
        
    except Exception as e:
        logging.error(f"Error calculating summary stats: {str(e)}")
        return {}
