# Indian Tech Job Market Intelligence Platform

<div align="center">

### Built by [vignesh-DA](https://github.com/vignesh-DA)

[![GitHub](https://img.shields.io/badge/GitHub-vignesh--DA-181717?logo=github)](https://github.com/vignesh-DA)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-000000?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

AI-powered platform for job discovery, recommendation, and market intelligence focused on the Indian tech ecosystem.

[Features](#key-features) | [Quick Start](#local-development-setup) | [Architecture](#architecture) | [CI/CD](#cicd-scheduled-job-refresh) | [API](#api-overview)

</div>

## Overview

This project combines live job ingestion, recommendation scoring, market analytics, and conversational career guidance in a single web application.

Core capabilities:

- Personalized job recommendations by skills, experience, and location
- Real-time market insights (salary trends, top skills, top companies, location distribution)
- Google OAuth login and session-based access control
- Chat assistant for salary, skills, role, and company guidance
- Automated job refresh pipeline using GitHub Actions and Neon PostgreSQL

## Architecture

The application is organized into four layers:

1. Web/API layer: server.py
2. Scraping layer: src/scrapers.py
3. Storage layer: src/database.py with fallback loader in src/data_loader.py
4. Intelligence layer: src/recommendation_engine.py and src/chatbot_engine.py

High-level flow:

1. Jobs are fetched from Adzuna.
2. Data is normalized and batch-upserted into PostgreSQL (Neon).
3. APIs read from PostgreSQL (with CSV fallback where applicable).
4. Frontend consumes APIs for recommendations and dashboards.
5. Chat endpoint uses profile context plus market data for responses.

## Technology Stack

- Backend: Flask, SQLAlchemy
- Frontend: HTML, CSS, Vanilla JavaScript
- Data and ML: pandas, numpy, scikit-learn
- Database: Neon PostgreSQL
- Authentication: Google OAuth 2.0
- Scheduling: GitHub Actions (cron)

## Key Features

### Personalized Recommendations

- Role, skills, experience, and location-aware matching
- Match score breakdown
- Missing skills and learning suggestions

### Market Intelligence Dashboard

- Salary trends
- Top skills and companies
- Role and experience distribution
- Location-level market summaries

### Authentication and User Session

- Google OAuth login flow
- Secure cookie-based session handling for serverless deployment

### Chat Assistant

- Intent-driven responses for salary, skills, role planning, and market guidance
- Profile-aware suggestions

## Project Structure

```text
.
|-- server.py
|-- src/
|   |-- analytics.py
|   |-- chatbot_engine.py
|   |-- data_loader.py
|   |-- database.py
|   |-- oauth_handler.py
|   |-- recommendation_engine.py
|   |-- scrapers.py
|   `-- user_db.py
|-- frontend/
|   |-- index.html
|   |-- market-dashboard.html
|   |-- recommendations.html
|   |-- saved-jobs.html
|   `-- assets/
|-- scripts/
|   `-- run_scrape_job.py
`-- .github/workflows/
	`-- scrape-jobs.yml
```

## Local Development Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/vignesh-DA/Indian-Tech-Job-Market-Intelligence-Platform1.git
cd gravito
pip install -r requirements.txt
```

### Environment Variables

Create a .env file in the repository root.

Minimum required for local run:

```env
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
DATABASE_URL=your_database_url
FLASK_SECRET_KEY=your_secret_key

GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5000/api/auth/callback
```

Optional:

```env
OPENROUTER_API_KEY=your_key
```

### Run the App

```bash
python server.py
```

Open http://localhost:5000

## Deployment Model

### Production Topology

- Vercel: frontend + read APIs + auth endpoints
- Neon PostgreSQL: primary persistent data store
- GitHub Actions: scheduled scraping and database refresh

Recommended pattern:

- Do not run long scraping jobs on Vercel serverless functions.
- Run scraping via GitHub Actions and write directly to Neon.

## CI/CD: Scheduled Job Refresh

Workflow file:

- .github/workflows/scrape-jobs.yml

Typical behavior:

- Triggered by cron (daily schedule recommended)
- Optionally supports manual dispatch
- Executes scripts/run_scrape_job.py

Required GitHub repository secrets:

- DATABASE_URL
- ADZUNA_APP_ID
- ADZUNA_APP_KEY
- FLASK_SECRET_KEY

Optional scrape controls:

- SCRAPE_ROLES
- SCRAPE_LOCATIONS
- SCRAPE_MAX_RESULTS_PER_ROLE

## API Overview

Authentication:

- GET /api/auth/login
- GET /api/auth/callback
- POST /api/auth/logout
- GET /api/auth/user

Jobs and recommendations:

- GET /api/jobs
- GET /api/roles
- POST /api/recommendations

Market analytics:

- GET /api/stats
- GET /api/analytics
- GET /api/salary-trends
- GET /api/top-skills
- GET /api/role-distribution
- GET /api/experience-distribution
- GET /api/location-stats
- GET /api/posting-trends
- GET /api/summary-stats

Operations:

- POST /api/fetch-jobs
- GET /api/fetch-jobs-status
- GET /api/last-updated
- GET /health

## Reliability Notes

- PostgreSQL writes use upsert semantics on job_id to avoid duplicates.
- Deduplication is applied before bulk upsert to prevent ON CONFLICT cardinality errors.
- Session handling is cookie-based and hardened for HTTPS deployments.
- CSV fallback remains available if DB reads fail.

## Troubleshooting

### Login redirects back to /login

- Ensure OAuth redirect URI matches your deployment domain.
- Clear browser cookies for the domain after auth/session changes.
- Confirm /api/auth/user returns authenticated true after login.

### Vercel import errors

- Verify required files exist in the deployed commit.
- Redeploy without cache when adding new source modules.

### Scrape jobs stop early

- Run scraping from GitHub Actions, not Vercel.
- Check workflow logs for Adzuna 429 responses and batch save status.

## Roadmap

- Multi-source aggregation beyond Adzuna
- Enhanced role transition intelligence
- Resume parsing and profile enrichment
- Alerting and subscription workflows

## License

MIT
