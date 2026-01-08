"""
PostgreSQL Database Module for Persistent Job Storage
Replaces CSV file storage with persistent database
"""
import os
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import pandas as pd
from src.logger import logging

# Database connection URL (from environment variable)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///gravito.db')

# Fix for Render's PostgreSQL URL (postgres:// -> postgresql://)
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,  # Verify connections are alive
    pool_recycle=3600,   # Recycle connections every hour
    pool_size=5,         # Connection pool size
    max_overflow=10      # Max connections beyond pool_size
)

# Session factory
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Base class for models
Base = declarative_base()

# ============================================================================
# DATABASE MODELS
# ============================================================================

class Job(Base):
    """Job posting model - stores all job data"""
    __tablename__ = "jobs"
    
    # Primary columns
    job_id = Column(String(200), primary_key=True, unique=True)  # Prevent duplicates
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(100), nullable=False, index=True)
    
    # Skills and experience
    skills = Column(Text)  # Comma-separated skills
    experience = Column(String(100))
    
    # Salary information
    salary = Column(String(100))
    salary_min = Column(Integer, default=0)
    salary_max = Column(Integer, default=0)
    
    # Job details
    description = Column(Text)
    url = Column(String(500))
    category = Column(String(100))
    
    # Timestamps
    posted_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite indexes for faster queries
    __table_args__ = (
        Index('idx_location_title', 'location', 'title'),
        Index('idx_company_location', 'company', 'location'),
        Index('idx_salary_range', 'salary_min', 'salary_max'),
    )
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'job_id': self.job_id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'skills': self.skills,
            'experience': self.experience,
            'salary': self.salary,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'description': self.description,
            'url': self.url,
            'category': self.category,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None
        }

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("Database initialized successfully")
        logging.info(f"   Using: {DATABASE_URL.split('@')[0]}@***")  # Hide password in logs
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}")
        logging.warning("   Will fall back to CSV storage")

# ============================================================================
# DATA OPERATIONS
# ============================================================================

def save_jobs_to_db(jobs_df):
    """
    Save jobs DataFrame to PostgreSQL database
    
    Args:
        jobs_df: pandas DataFrame with job data
        
    Returns:
        int: Number of jobs saved
    """
    if jobs_df is None or jobs_df.empty:
        logging.warning("No jobs to save to database")
        return 0
    
    session = SessionLocal()
    try:
        # Delete old jobs (keep only last 30 days of data)
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted_count = session.query(Job).filter(Job.posted_date < cutoff_date).delete()
        if deleted_count > 0:
            logging.info(f"🗑️  Deleted {deleted_count} old jobs (>30 days)")
        
        # Insert/update new jobs
        inserted = 0
        updated = 0
        
        for _, row in jobs_df.iterrows():
            try:
                job_id = str(row.get('job_id', ''))
                
                # Check if job already exists
                existing_job = session.query(Job).filter(Job.job_id == job_id).first()
                
                if existing_job:
                    # Update existing job
                    existing_job.title = row.get('title', '')
                    existing_job.company = row.get('company', '')
                    existing_job.location = row.get('location', '')
                    existing_job.skills = str(row.get('skills', ''))
                    existing_job.experience = row.get('experience', '')
                    existing_job.salary = row.get('salary', '')
                    existing_job.salary_min = int(row.get('salary_min', 0)) if pd.notna(row.get('salary_min')) else 0
                    existing_job.salary_max = int(row.get('salary_max', 0)) if pd.notna(row.get('salary_max')) else 0
                    existing_job.description = row.get('description', '')
                    existing_job.url = row.get('url', '')
                    existing_job.category = row.get('category', '')
                    updated += 1
                else:
                    # Create new job
                    job = Job(
                        job_id=job_id,
                        title=row.get('title', ''),
                        company=row.get('company', ''),
                        location=row.get('location', ''),
                        skills=str(row.get('skills', '')),
                        experience=row.get('experience', ''),
                        salary=row.get('salary', ''),
                        salary_min=int(row.get('salary_min', 0)) if pd.notna(row.get('salary_min')) else 0,
                        salary_max=int(row.get('salary_max', 0)) if pd.notna(row.get('salary_max')) else 0,
                        description=row.get('description', ''),
                        url=row.get('url', ''),
                        category=row.get('category', ''),
                        posted_date=row.get('posted_date', datetime.utcnow())
                    )
                    session.add(job)
                    inserted += 1
                    
            except Exception as e:
                logging.warning(f"Could not save job {job_id}: {str(e)}")
                continue
        
        # Commit all changes
        session.commit()
        
        logging.info("=" * 70)
        logging.info("✅ SAVED JOBS TO POSTGRESQL")
        logging.info("=" * 70)
        logging.info(f"   Inserted: {inserted} new jobs")
        logging.info(f"   Updated: {updated} existing jobs")
        logging.info(f"   Total in database: {session.query(Job).count()}")
        logging.info("=" * 70)
        
        return inserted + updated
        
    except Exception as e:
        session.rollback()
        logging.error(f"❌ Error saving jobs to database: {str(e)}")
        raise
    finally:
        session.close()

def load_jobs_from_db(days=30, location=None, limit=10000):
    """
    Load jobs from PostgreSQL database
    
    Args:
        days: Number of days to look back
        location: Filter by location (optional)
        limit: Maximum number of jobs to return
        
    Returns:
        pandas DataFrame with job data
    """
    session = SessionLocal()
    try:
        from datetime import timedelta
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        query = session.query(Job).filter(Job.posted_date >= cutoff_date)
        
        # Apply location filter if provided
        if location:
            query = query.filter(Job.location.ilike(f"%{location}%"))
        
        # Order by date and limit
        query = query.order_by(Job.posted_date.desc()).limit(limit)
        
        # Execute query
        jobs = query.all()
        
        # Convert to DataFrame
        data = [job.to_dict() for job in jobs]
        df = pd.DataFrame(data)
        
        logging.info(f"Loaded {len(df)} jobs from PostgreSQL (last {days} days)")
        
        return df
        
    except Exception as e:
        logging.error(f"❌ Error loading from database: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error
    finally:
        session.close()

def get_job_count():
    """Get total number of jobs in database"""
    session = SessionLocal()
    try:
        count = session.query(Job).count()
        return count
    finally:
        session.close()

def clear_all_jobs():
    """Clear all jobs from database (use with caution!)"""
    session = SessionLocal()
    try:
        deleted = session.query(Job).delete()
        session.commit()
        logging.info(f"🗑️  Cleared {deleted} jobs from database")
        return deleted
    except Exception as e:
        session.rollback()
        logging.error(f"Error clearing jobs: {str(e)}")
        raise
    finally:
        session.close()
