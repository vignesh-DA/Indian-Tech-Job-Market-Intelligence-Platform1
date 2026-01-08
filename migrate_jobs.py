#!/usr/bin/env python
"""Migrate all jobs to PostgreSQL without 30-day cleanup"""

from src.database import Job, SessionLocal, engine
import pandas as pd
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert

# Load ALL jobs from CSV
print("Loading all jobs from CSV...")
jobs_df = pd.read_csv('data/jobs_2026_01_08.csv')
print(f"Total jobs in CSV: {len(jobs_df)}")

# Get existing job IDs in database
session = SessionLocal()
existing_ids = set(job.job_id for job in session.query(Job.job_id).all())
session.close()
print(f"Jobs already in database: {len(existing_ids)}")

# Filter to only new jobs
new_jobs = jobs_df[~jobs_df['job_id'].astype(str).isin(existing_ids)].copy()
print(f"New jobs to migrate: {len(new_jobs)}")

# Migrate in batches of 1000
batch_size = 1000
total_migrated = 0

for i in range(0, len(new_jobs), batch_size):
    batch = new_jobs.iloc[i:i+batch_size].copy()
    
    # Remove duplicates within this batch (keep first occurrence of each job_id)
    batch = batch.drop_duplicates(subset=['job_id'], keep='first')
    
    if len(batch) == 0:
        continue
    
    try:
        # Direct database insert without 30-day cleanup
        session = SessionLocal()
        
        # Prepare job data
        jobs_to_insert = []
        for _, row in batch.iterrows():
            posted_date = row.get('posted_date')
            if posted_date and pd.notna(posted_date):
                posted_date = pd.to_datetime(posted_date, utc=True).tz_localize(None).to_pydatetime()
            else:
                posted_date = datetime.utcnow()
            
            job_dict = {
                'job_id': str(row.get('job_id', '')),
                'title': str(row.get('title', '')),
                'company': str(row.get('company', '')),
                'location': str(row.get('location', '')),
                'skills': str(row.get('skills', '')),
                'experience': str(row.get('experience', '')),
                'salary': str(row.get('salary', '')),
                'salary_min': int(row.get('salary_min', 0)) if pd.notna(row.get('salary_min')) else 0,
                'salary_max': int(row.get('salary_max', 0)) if pd.notna(row.get('salary_max')) else 0,
                'description': str(row.get('description', '')),
                'url': str(row.get('url', '')),
                'category': str(row.get('category', '')),
                'posted_date': posted_date,
                'created_at': datetime.utcnow()
            }
            jobs_to_insert.append(job_dict)
        
        # Bulk upsert without deleting old jobs
        if jobs_to_insert:
            stmt = insert(Job).values(jobs_to_insert)
            stmt = stmt.on_conflict_do_update(
                index_elements=['job_id'],
                set_={c.name: c for c in stmt.excluded if c.name not in ['job_id', 'created_at']}
            )
            session.execute(stmt)
            session.commit()
            count = len(jobs_to_insert)
            total_migrated += count
            print(f"Batch {i//batch_size + 1}: Migrated {count} jobs (Total: {total_migrated})")
        
        session.close()
    except Exception as e:
        print(f"Error in batch {i//batch_size + 1}: {str(e)[:150]}")
        session.close()
        continue

# Final count
session = SessionLocal()
final_count = session.query(Job).count()
session.close()

print(f"\nMigration complete!")
print(f"Total jobs in database: {final_count}")
print(f"Target: 12,586 jobs")
print(f"Progress: {(final_count/12586)*100:.1f}%")

