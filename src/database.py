"""
PostgreSQL Database Module for Persistent Job Storage
Replaces CSV file storage with persistent database
"""
import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import pandas as pd
from src.logger import logging

# Load environment variables
load_dotenv()

# Database connection URL (from environment variable)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///gravito.db')

# Fix for Render's PostgreSQL URL (postgres:// -> postgresql://)
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create engine with connection pooling
# Use different pool settings for SQLite vs PostgreSQL
if DATABASE_URL.startswith('sqlite'):
    # SQLite: single-file DB, no pool needed for local dev
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={'check_same_thread': False},
    )
else:
    # PostgreSQL with resilient settings for Render free-tier
    # Render free DBs drop idle SSL connections, so we:
    #   - pool_pre_ping: test each connection before use
    #   - pool_recycle=300: recycle connections every 5 min (before Render kills them)
    #   - keepalive args: OS-level TCP probes to detect dead connections
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,        # Verify connections are alive before using
        pool_recycle=300,          # Recycle connections every 5 minutes
        pool_size=5,               # Small pool — Render free tier limits connections
        max_overflow=10,           # Burst up to 15 total connections
        pool_timeout=30,           # Wait up to 30s for a connection before error
        connect_args={
            "sslmode": "require",
            "keepalives": 1,
            "keepalives_idle": 30,      # Send keepalive after 30s idle
            "keepalives_interval": 10,  # Retry keepalive every 10s
            "keepalives_count": 5,      # Drop after 5 failed keepalives
            "connect_timeout": 10,      # Abort connection attempt after 10s
        },
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
# RETRY HELPER
# ============================================================================

def _with_retry(fn, max_attempts=3, base_delay=2):
    """
    Execute `fn()` with automatic retry on transient DB errors.
    Uses exponential backoff: 2s, 4s, ...
    """
    last_exc: Exception = RuntimeError("DB retry failed with no exception captured")
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            err_str = str(e).lower()

            # Logic/data errors should not be retried.
            if 'cannot affect row a second time' in err_str or 'cardinalityviolation' in err_str:
                raise

            # Only retry on connection/SSL-level errors
            transient = any(kw in err_str for kw in [
                'ssl', 'connection', 'timeout', 'broken pipe',
                'server closed', 'operational', 'gone away'
            ])
            if not transient or attempt == max_attempts:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logging.warning(
                f"DB transient error (attempt {attempt}/{max_attempts}), "
                f"retrying in {delay}s: {e}"
            )
            # Dispose pool so next attempt gets a fresh connection
            try:
                engine.dispose()
            except Exception:
                pass
            time.sleep(delay)
    raise last_exc  # Should never reach here


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize database - create all tables, with retry on transient failures"""
    def _do_init():
        Base.metadata.create_all(bind=engine)
        logging.info("Database initialized successfully")
        logging.info(f"   Using: {DATABASE_URL.split('@')[0]}@***")  # Hide password in logs

    try:
        _with_retry(_do_init)
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}")
        logging.warning("   Will fall back to CSV storage")
        raise

# ============================================================================
# DATA OPERATIONS
# ============================================================================

def save_jobs_to_db(jobs_df):
    """
    Save jobs DataFrame to PostgreSQL database.
    Automatically retries up to 3 times on transient SSL / connection errors.

    Args:
        jobs_df: pandas DataFrame with job data

    Returns:
        int: Number of jobs saved
    """
    if jobs_df is None or jobs_df.empty:
        logging.warning("No jobs to save to database")
        return 0

    # Build the list of dicts once (outside the retry loop)
    from datetime import timedelta
    jobs_to_insert = []
    for _, row in jobs_df.iterrows():
        job_id = str(row.get('job_id', '')).strip()
        if not job_id:
            # Skip malformed rows without stable primary key.
            continue

        posted_date = row.get('posted_date')
        if posted_date and pd.notna(posted_date):
            try:
                posted_date = pd.to_datetime(posted_date, utc=True).tz_localize(None).to_pydatetime()
            except Exception:
                posted_date = datetime.utcnow()
        else:
            posted_date = datetime.utcnow()

        jobs_to_insert.append({
            'job_id':      job_id,
            'title':       row.get('title', ''),
            'company':     row.get('company', ''),
            'location':    row.get('location', ''),
            'skills':      str(row.get('skills', '')),
            'experience':  row.get('experience', ''),
            'salary':      row.get('salary', ''),
            'salary_min':  int(row.get('salary_min', 0)) if pd.notna(row.get('salary_min')) else 0,
            'salary_max':  int(row.get('salary_max', 0)) if pd.notna(row.get('salary_max')) else 0,
            'description': row.get('description', ''),
            'url':         row.get('url', ''),
            'category':    row.get('category', ''),
            'posted_date': posted_date,
            'created_at':  datetime.utcnow(),
        })

    # PostgreSQL ON CONFLICT cannot handle duplicate conflict keys in one VALUES payload.
    # Keep the last occurrence for each job_id within this save call.
    original_count = len(jobs_to_insert)
    deduped_jobs = {}
    for job in jobs_to_insert:
        deduped_jobs[job['job_id']] = job
    jobs_to_insert = list(deduped_jobs.values())

    if original_count != len(jobs_to_insert):
        logging.warning(
            f"Deduplicated {original_count - len(jobs_to_insert)} duplicate rows by job_id "
            f"before DB upsert"
        )

    if not jobs_to_insert:
        logging.warning("No valid jobs to save after filtering/deduplication")
        return 0

    def _do_save():
        session = SessionLocal()
        try:
            logging.info("=" * 70)
            logging.info("DATABASE SAVE OPERATION STARTED")
            logging.info("=" * 70)
            logging.info(f"Total jobs to save: {len(jobs_to_insert)}")

            # Delete jobs older than 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            deleted_count = session.query(Job).filter(Job.posted_date < cutoff_date).delete()
            if deleted_count > 0:
                logging.info(f"Deleted {deleted_count} old jobs (>90 days)")

            # Bulk upsert
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            stmt = pg_insert(Job).values(jobs_to_insert)
            stmt = stmt.on_conflict_do_update(
                index_elements=['job_id'],
                set_={
                    'title':       stmt.excluded.title,
                    'company':     stmt.excluded.company,
                    'location':    stmt.excluded.location,
                    'skills':      stmt.excluded.skills,
                    'experience':  stmt.excluded.experience,
                    'salary':      stmt.excluded.salary,
                    'salary_min':  stmt.excluded.salary_min,
                    'salary_max':  stmt.excluded.salary_max,
                    'description': stmt.excluded.description,
                    'url':         stmt.excluded.url,
                    'category':    stmt.excluded.category,
                    'posted_date': stmt.excluded.posted_date,
                }
            )
            session.execute(stmt)
            session.commit()

            total_count = session.query(Job).count()
            logging.info("=" * 70)
            logging.info("DATABASE SAVE COMPLETED")
            logging.info(f"Jobs saved: {len(jobs_to_insert)} | Total in DB: {total_count}")
            logging.info("=" * 70)
            return len(jobs_to_insert)

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    try:
        return _with_retry(_do_save)
    except Exception as e:
        logging.error(f"Error saving jobs to database: {str(e)}")
        raise

def load_jobs_from_db(days=None, location=None, limit=10000):
    """
    Load jobs from PostgreSQL database, with retry on transient errors.

    Args:
        days: Number of days to look back (None = load all jobs)
        location: Filter by location (optional)
        limit: Maximum number of jobs to return

    Returns:
        pandas DataFrame with job data
    """
    def _do_load():
        session = SessionLocal()
        try:
            from datetime import timedelta
            query = session.query(Job)
            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(Job.posted_date >= cutoff_date)
            if location:
                query = query.filter(Job.location.ilike(f"%{location}%"))
            query = query.order_by(Job.posted_date.desc()).limit(limit)
            jobs = query.all()
            data = [job.to_dict() for job in jobs]
            df = pd.DataFrame(data)
            days_text = f"(last {days} days)" if days else "(all)"
            logging.info(f"Loaded {len(df)} jobs from PostgreSQL {days_text}")
            return df
        finally:
            session.close()

    try:
        return _with_retry(_do_load)
    except Exception as e:
        logging.error(f"Error loading from database: {str(e)}")
        return pd.DataFrame()

def get_job_count():
    """Get total number of jobs in database, with retry on transient errors."""
    def _do_count():
        session = SessionLocal()
        try:
            return session.query(Job).count()
        finally:
            session.close()

    try:
        return _with_retry(_do_count)
    except Exception as e:
        logging.error(f"Error getting job count: {str(e)}")
        return 0

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
