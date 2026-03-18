import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
Run the Adzuna scrape job and persist data to the configured database.
Designed for GitHub Actions scheduled/manual execution.
"""

from dotenv import load_dotenv

from src.logger import logging
from src.database import init_db, get_job_count
from src.scrapers import fetch_and_save_jobs


def _print_env_summary() -> None:
    roles = os.getenv("SCRAPE_ROLES", "<default>")
    locations = os.getenv("SCRAPE_LOCATIONS", "<default>")
    max_per_role = os.getenv("SCRAPE_MAX_RESULTS_PER_ROLE", "100")

    logging.info("=" * 70)
    logging.info("SCRAPE JOB STARTED (GitHub Actions)")
    logging.info(f"SCRAPE_ROLES={roles}")
    logging.info(f"SCRAPE_LOCATIONS={locations}")
    logging.info(f"SCRAPE_MAX_RESULTS_PER_ROLE={max_per_role}")
    logging.info("=" * 70)


def main() -> int:
    load_dotenv()

    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        logging.error("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY")
        return 1

    try:
        init_db()
    except Exception as db_err:
        logging.error(f"Database initialization failed: {db_err}")
        return 1

    _print_env_summary()

    before_count = get_job_count()
    logging.info(f"Jobs in DB before scrape: {before_count}")

    result_df = fetch_and_save_jobs(app_id=app_id, app_key=app_key)

    if result_df is None or result_df.empty:
        logging.error("Scrape completed with no rows returned")
        return 2

    after_count = get_job_count()
    logging.info(f"Jobs fetched in this run: {len(result_df)}")
    logging.info(f"Jobs in DB after scrape: {after_count}")
    logging.info("Scrape run completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
