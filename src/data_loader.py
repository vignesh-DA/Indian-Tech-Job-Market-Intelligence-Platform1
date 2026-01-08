"""
Data Loader Module
Loads job data from CSV files and caches for performance
"""
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
from src.logger import logging
from src.exception import CustomException
from functools import lru_cache

# Simple in-memory cache for loaded jobs
_job_cache = {}
_cache_timestamp = None
CACHE_TTL = 3600  # 1 hour

def load_recent_jobs(days=30):
    """
    Load jobs from PostgreSQL database with CSV fallback
    
    Args:
        days: Number of days to look back
        
    Returns:
        DataFrame with recent jobs
    """
    try:
        # Try loading from PostgreSQL first
        logging.info("Attempting to load jobs from PostgreSQL database")
        from src.database import load_jobs_from_db
        
        df = load_jobs_from_db(days=days)
        
        if not df.empty:
            logging.info(f"Loaded {len(df)} jobs from PostgreSQL")
            return df
        else:
            logging.warning("No jobs in PostgreSQL, falling back to CSV")
            
    except Exception as db_error:
        logging.warning(f"PostgreSQL load failed: {str(db_error)}, using CSV fallback")
    
    # Fallback to CSV if database fails or is empty
    try:
        logging.info("Loading jobs from latest CSV file")
        data_dir = "data"
        
        if not os.path.exists(data_dir):
            logging.warning("Data directory not found")
            return pd.DataFrame()
        
        # Get all CSV files in data directory
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            logging.warning("No CSV files found in data directory")
            return pd.DataFrame()
        
        # Get the latest file by modification time
        file_paths = [os.path.join(data_dir, f) for f in csv_files]
        latest_file = max(file_paths, key=os.path.getmtime)
        latest_filename = os.path.basename(latest_file)
        
        try:
            df = pd.read_csv(latest_file)
            
            # Convert posted_date to datetime with UTC timezone
            df['posted_date'] = pd.to_datetime(df['posted_date'], errors='coerce', utc=True)
            
            logging.info(f"Loaded {len(df)} jobs from {latest_filename}")
            return df
            
        except Exception as e:
            logging.error(f"Error loading {latest_filename}: {str(e)}")
            return pd.DataFrame()
        
    except Exception as e:
        logging.error(f"Error in load_recent_jobs: {str(e)}")
        raise CustomException(e, sys)


def load_all_jobs_for_training():
    """
    Load latest job data for ML model training
    
    Returns:
        DataFrame with latest job data
    """
    try:
        logging.info("Loading latest jobs for training")
        data_dir = "data"
        
        if not os.path.exists(data_dir):
            logging.warning("Data directory not found")
            return pd.DataFrame()
        
        # Get all CSV files
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            return pd.DataFrame()
        
        # Get the latest file by modification time
        file_paths = [os.path.join(data_dir, f) for f in csv_files]
        latest_file = max(file_paths, key=os.path.getmtime)
        latest_filename = os.path.basename(latest_file)
        
        try:
            df = pd.read_csv(latest_file)
            logging.info(f"Loaded {len(df)} jobs from {latest_filename} for training")
            return df
        except Exception as e:
            logging.error(f"Error loading {latest_filename}: {str(e)}")
            return pd.DataFrame()
        
    except Exception as e:
        logging.error(f"Error in load_all_jobs_for_training: {str(e)}")
        raise CustomException(e, sys)


def save_jobs_to_csv(jobs_df):
    """
    Save jobs dataframe to CSV with today's date
       
    WARNING: On platforms with ephemeral storage (like Render free tier),
    this data will be lost on restart. Use Render Disks or external storage.
    
    Args:
        jobs_df: DataFrame with job data
    """
    try:
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        
        logging.warning("⚠️  Saving to ephemeral storage - data may be lost on platform restart!")
        
        # Delete all old CSV files
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        
        if csv_files:
            logging.info("=" * 60)
            logging.info("DELETING OLD CSV FILES")
            logging.info("=" * 60)
        
        for file in csv_files:
            old_filepath = os.path.join(data_dir, file)
            try:
                file_size = os.path.getsize(old_filepath) / (1024*1024)
                os.remove(old_filepath)
                logging.info(f"❌ CSV DELETED: {file}")
                logging.info(f"   - Size: {file_size:.2f} MB")
                logging.info(f"   - Path: {old_filepath}")
            except Exception as e:
                logging.error(f"Error deleting {file}: {str(e)}")
        
        # Save new file
        today = datetime.now().strftime("%Y_%m_%d")
        filename = f"jobs_{today}.csv"
        filepath = os.path.join(data_dir, filename)
        
        jobs_df.to_csv(filepath, index=False)
        file_size = os.path.getsize(filepath) / (1024*1024)
        
        logging.info("=" * 60)
        logging.info("CREATING NEW CSV FILE")
        logging.info("=" * 60)
        logging.info(f"CSV CREATED: {filename}")
        logging.info(f"   - Jobs: {len(jobs_df)}")
        logging.info(f"   - Size: {file_size:.2f} MB")
        logging.info(f"   - Path: {filepath}")
        logging.info(f"   - Columns: {', '.join(jobs_df.columns.tolist())}")
        logging.info("=" * 60)
        
    except Exception as e:
        logging.error(f"Error saving jobs to CSV: {str(e)}")
        raise CustomException(e, sys)


def get_unique_skills(jobs_df):
    """
    Extract unique skills from all jobs
    
    Args:
        jobs_df: DataFrame with job data
        
    Returns:
        List of unique skills
    """
    try:
        if jobs_df.empty or 'skills' not in jobs_df.columns:
            return []
        
        all_skills = set()
        for skills_str in jobs_df['skills'].dropna():
            if isinstance(skills_str, str):
                skills = [s.strip() for s in skills_str.split(',')]
                all_skills.update(skills)
        
        return sorted(list(all_skills))
        
    except Exception as e:
        logging.error(f"Error extracting skills: {str(e)}")
        return []


def get_unique_locations(jobs_df):
    """
    Get unique job locations
    
    Args:
        jobs_df: DataFrame with job data
        
    Returns:
        List of unique locations
    """
    try:
        if jobs_df.empty or 'location' not in jobs_df.columns:
            return []
        
        locations = jobs_df['location'].dropna().unique().tolist()
        return sorted(locations)
        
    except Exception as e:
        logging.error(f"Error extracting locations: {str(e)}")
        return []


def normalize_location(location_str):
    """
    Normalize granular locations to parent cities
    
    Maps specific areas/streets to their parent city names
    E.g., "Powai Iit, Mumbai" -> "Mumbai"
    
    Args:
        location_str: Raw location string from CSV
        
    Returns:
        Normalized city name
    """
    if pd.isna(location_str):
        return 'Unknown'
    
    location = str(location_str).strip().lower()
    
    # City mapping - handles common cases
    city_keywords = {
        'mumbai': ['mumbai', 'powai', 'goregaon', 'andheri', 'charni', 'prabhadevi', 'trombay', 'nana peth'],
        'bangalore': ['bangalore', 'madivala', 'muthusandra', 'banasavangee'],
        'hyderabad': ['hyderabad', 'kyasaram'],
        'pune': ['pune', 'baner', 'vadgaon', 'hadapsar', 'warje', 'nana peth'],
        'chennai': ['chennai', 'injambakkam', 'chintadripet', 'ttti taramani', 'egmore', 'gopalapuram'],
        'delhi': ['delhi', 'new delhi', 'north delhi', 'south delhi', 'chandni chowk', 'timarpur', 'jeevan park', 'lajpat nagar', 'sarita vihar', 'sansad marg'],
        'remote': ['remote']
    }
    
    for city, keywords in city_keywords.items():
        for keyword in keywords:
            if keyword in location:
                return city.title()
    
    # Default: return first major city mentioned or 'Other'
    if 'india' in location:
        return 'India'
    
    return 'Other'


def get_normalized_locations(jobs_df):
    """
    Get normalized unique locations from jobs dataframe
    
    Args:
        jobs_df: DataFrame with job data
        
    Returns:
        List of normalized unique locations
    """
    try:
        if jobs_df.empty or 'location' not in jobs_df.columns:
            return []
        
        normalized_locs = jobs_df['location'].apply(normalize_location).unique().tolist()
        # Remove 'Other', 'Unknown', and 'India' from recommendations
        normalized_locs = [loc for loc in normalized_locs if loc not in ['Other', 'Unknown', 'India']]
        return sorted(normalized_locs)
        
    except Exception as e:
        logging.error(f"Error normalizing locations: {str(e)}")
        return []


def get_unique_companies(jobs_df):
    """
    Get unique company names
    
    Args:
        jobs_df: DataFrame with job data
        
    Returns:
        List of unique companies
    """
    try:
        if jobs_df.empty or 'company' not in jobs_df.columns:
            return []
        
        companies = jobs_df['company'].dropna().unique().tolist()
        return sorted(companies)
        
    except Exception as e:
        logging.error(f"Error extracting companies: {str(e)}")
        return []
