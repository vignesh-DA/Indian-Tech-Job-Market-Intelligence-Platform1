"""
Flask Backend Server for Indian Tech Job Market Intelligence Platform
Replaces Streamlit with a proper REST API + modern frontend
"""
import time
# Disable MKL threading to avoid Fortran runtime errors with scikit-learn
import os
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

from flask import Flask, jsonify, request, render_template, send_from_directory, redirect, session
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
import threading
from cachetools import TTLCache
from src.data_loader import load_recent_jobs
from src.recommendation_engine import JobRecommendationEngine, get_learning_suggestions
from src.scrapers import fetch_and_save_jobs
from src.analytics import (
    calculate_salary_trends,
    get_top_skills,
    get_top_companies,
    calculate_location_stats,
    get_posting_trends,
    get_experience_distribution,
    get_role_distribution,
    calculate_summary_stats
)
from src.oauth_handler import oauth
from src.user_db import user_db
from src.logger import logging
import sys


# Load environment variables
load_dotenv()

# Initialize PostgreSQL database (retry up to 3 times for Render cold-start)
_db_available = False
_MAX_DB_INIT_ATTEMPTS = 3
for _attempt in range(1, _MAX_DB_INIT_ATTEMPTS + 1):
    try:
        from src.database import init_db
        init_db()
        _db_available = True
        break
    except Exception as _e:
        logging.error(f"Database init attempt {_attempt}/{_MAX_DB_INIT_ATTEMPTS} failed: {_e}")
        if _attempt < _MAX_DB_INIT_ATTEMPTS:
            logging.info("Retrying DB init in 3 seconds...")
            time.sleep(3)
        else:
            logging.warning("All DB init attempts failed — falling back to CSV storage")

# Initialize Flask app
app = Flask(__name__, 
            static_folder='frontend/assets',
            template_folder='frontend')

# Configure Flask session for authentication
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_TYPE'] = 'filesystem'
is_vercel = os.environ.get('VERCEL') == '1'
if is_vercel:
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
Session(app)

# ---------------------------------------------------------------------------
# CACHES (shared within each gunicorn worker process)
# ---------------------------------------------------------------------------
# ML model cache: store one trained engine per location key, expire after 30 min
_model_cache: dict = {}           # key -> {'engine': ..., 'trained_at': timestamp}
_model_cache_lock = threading.Lock()
MODEL_CACHE_TTL = 1800  # 30 minutes

# Analytics / stats response cache: expires after 10 minutes
_response_cache: TTLCache = TTLCache(maxsize=256, ttl=600)
_cache_lock = threading.Lock()

# Enable CORS
CORS(app)

# ========================
# AUTHENTICATION MIDDLEWARE
# ========================

def login_required(f):
    """Decorator to protect routes - redirect to login if not authenticated"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Helper function to load all jobs without date filtering
def load_all_jobs(limit: int = 5000):
    """Load jobs from DB (with retry) then fall back to CSV if DB is unavailable.

    Args:
        limit: Maximum rows to return (default 5000, most-recently posted first).
    """
    cache_key = f'all_jobs:{limit}'
    with _cache_lock:
        if cache_key in _response_cache:
            return _response_cache[cache_key]

    # --- Try PostgreSQL first (uses _with_retry internally) ---
    try:
        from src.database import load_jobs_from_db
        jobs_df = load_jobs_from_db(limit=limit)
        if not jobs_df.empty:
            with _cache_lock:
                _response_cache[cache_key] = jobs_df
            return jobs_df
        logging.warning("DB returned empty result — trying CSV fallback")
    except Exception as db_err:
        logging.warning(f"DB unavailable in load_all_jobs: {db_err} — falling back to CSV")

    # --- CSV fallback (load_recent_jobs has its own CSV logic) ---
    from src.data_loader import load_recent_jobs
    jobs_df = load_recent_jobs(days=None)
    if not jobs_df.empty:
        with _cache_lock:
            _response_cache[cache_key] = jobs_df
    return jobs_df

# ========================
# OAUTH ROUTES
# ========================

@app.route('/login')
def login_page():
    """Serve login page"""
    return render_template('login.html')

@app.route('/api/auth/login', methods=['GET'])
def get_auth_url():
    """Get Google OAuth authorization URL"""
    try:
        auth_url = oauth.get_authorization_url()
        return jsonify({'auth_url': auth_url})
    except Exception as e:
        logging.error(f"Error getting auth URL: {str(e)}")
        return jsonify({'error': 'Failed to get authorization URL'}), 500

@app.route('/api/auth/callback', methods=['GET'])
def oauth_callback():
    """Handle OAuth callback from Google"""
    try:
        # Get authorization code from query parameters
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            logging.warning(f"OAuth error: {error}")
            return redirect(f'/login?error={error}')
        
        if not code:
            logging.error("No authorization code received")
            return redirect('/login?error=no_code')
        
        # Exchange code for token and get user info
        success, user, error_msg = oauth.handle_oauth_callback(code)
        
        if not success:
            logging.error(f"OAuth callback failed: {error_msg}")
            return redirect(f'/login?error={error_msg}')
        
        # Create session
        session.permanent = True  # Make session persistent
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        session['user_picture'] = user['picture']
        
        logging.info(f"User {user['email']} logged in successfully")
        
        # Redirect to home page
        return redirect('/')
    
    except Exception as e:
        logging.error(f"OAuth callback error: {str(e)}")
        return redirect(f'/login?error=callback_failed')

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    try:
        user_email = session.get('user_email', 'Unknown')
        session.clear()
        logging.info(f"User {user_email} logged out")
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        logging.error(f"Logout error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/user', methods=['GET'])
def get_current_user():
    """Get current logged-in user info"""
    if 'user_id' not in session:
        return jsonify({'authenticated': False})
    
    try:
        user = user_db.get_user_by_id(session['user_id'])
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'picture': user['picture'],
                'created_at': user['created_at'],
                'last_login': user['last_login']
            }
        })
    except Exception as e:
        logging.error(f"Error getting user info: {str(e)}")
        return jsonify({'authenticated': False})

# ========================
# HEALTH CHECK ENDPOINT
# ========================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint - verify all pages are accessible"""
    try:
        return jsonify({
            'success': True,
            'message': 'Server is running',
            'pages': {
                'home': '/',
                'recommendations': '/recommendations',
                'dashboard': '/dashboard',
                'saved_jobs': '/saved-jobs'
            },
            'api_endpoints': {
                'stats': '/api/stats',
                'jobs': '/api/jobs',
                'recommendations': '/api/recommendations',
                'analytics': '/api/analytics',
                'fetch_jobs': '/api/fetch-jobs',
                'last_updated': '/api/last-updated'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ========================
# API ENDPOINTS
# ========================

@app.route('/')
def index():
    """Serve main page - requires authentication"""
    try:
        # Check if user is authenticated
        if 'user_id' not in session:
            return redirect('/login')
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error loading index.html: {str(e)}")
        return jsonify({'error': 'Failed to load home page'}), 500

@app.route('/dashboard')
def dashboard():
    """Serve dashboard page - requires authentication"""
    try:
        # Check if user is authenticated
        if 'user_id' not in session:
            return redirect('/login')
        return render_template('market-dashboard.html')
    except Exception as e:
        logging.error(f"Error loading market-dashboard.html: {str(e)}")
        return jsonify({'error': 'Failed to load dashboard page'}), 500

@app.route('/recommendations')
def recommendations():
    """Serve recommendations page"""
    try:
        return render_template('recommendations.html')
    except Exception as e:
        logging.error(f"Error loading recommendations.html: {str(e)}")
        return jsonify({'error': 'Failed to load recommendations page'}), 500

@app.route('/saved-jobs')
def saved_jobs_page():
    """Serve saved jobs page"""
    try:
        return render_template('saved-jobs.html')
    except Exception as e:
        logging.error(f"Error loading saved-jobs.html: {str(e)}")
        return jsonify({'error': 'Failed to load saved jobs page'}), 500

@app.route('/profile_pics/<filename>')
def serve_profile_pic(filename):
    """Serve profile pictures from local storage"""
    try:
        is_vercel = os.environ.get('VERCEL') == '1'
        pics_dir = '/tmp/profile_pics' if is_vercel else 'data/profile_pics'
        return send_from_directory(pics_dir, filename)
    except Exception as e:
        logging.error(f"Error serving profile picture: {str(e)}")
        # Return placeholder image
        return '', 404

# API: Get dashboard statistics
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get market statistics (cached for 10 minutes)"""
    try:
        cache_key = 'api:stats'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        # Use load_all_jobs which is itself cached and capped
        jobs_df = load_all_jobs()

        if jobs_df.empty:
            return jsonify({
                'success': False,
                'message': 'No job data available',
                'data': {}
            }), 404

        # Calculate statistics
        total_jobs = len(jobs_df)
        companies = jobs_df['company'].nunique()
        locations = jobs_df['location'].nunique()

        # Average salary
        valid_salaries = jobs_df[
            (jobs_df['salary_min'] > 0) & 
            (jobs_df['salary_max'] > 0)
        ]
        avg_salary = 0
        if not valid_salaries.empty:
            avg_sal = (valid_salaries['salary_min'] + valid_salaries['salary_max']) / 2
            avg_salary = int(avg_sal.mean())

        result = {
            'success': True,
            'data': {
                'total_jobs': int(total_jobs),
                'companies_hiring': int(companies),
                'locations': int(locations),
                'average_salary': avg_salary
            }
        }
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API: Get unique job roles from data
@app.route('/api/roles', methods=['GET'])
def get_unique_roles():
    """Get unique job roles from the dataset (cached for 10 minutes)"""
    try:
        cache_key = 'api:roles'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        jobs_df = load_all_jobs()

        if jobs_df.empty:
            return jsonify({
                'success': False,
                'message': 'No job data available',
                'data': []
            }), 404

        # Get all unique titles
        all_titles = jobs_df['title'].unique().tolist()

        # Normalize and extract main role from titles
        normalized_roles = set()

        for title in all_titles:
            if len(title) > 80 or title.count('(') > 2:
                continue
            parts = title.split('-')[0].split('|')[0].split('(')[0].strip()
            if len(parts) > 5 and not parts.isdigit():
                normalized_roles.add(parts)

        unique_roles = sorted(list(normalized_roles))[:100]

        result = {'success': True, 'data': unique_roles}
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting unique roles: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get all jobs with filtering
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get jobs with optional filtering"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        location = request.args.get('location', None)
        company = request.args.get('company', None)
        days = request.args.get('days', None, type=int)  # None = load all jobs
        
        # Load jobs - if days not specified, use capped load_all_jobs
        if days:
            jobs_df = load_recent_jobs(days=days)
        else:
            jobs_df = load_all_jobs()
        
        if jobs_df.empty:
            return jsonify({
                'success': False,
                'message': 'No job data available',
                'data': []
            }), 404
        
        # Apply filters
        if location:
            jobs_df = jobs_df[jobs_df['location'].str.contains(location, case=False, na=False)]
        
        if company:
            jobs_df = jobs_df[jobs_df['company'].str.contains(company, case=False, na=False)]
        
        # Pagination
        total = len(jobs_df)
        start = (page - 1) * limit
        end = start + limit
        
        jobs_list = jobs_df.iloc[start:end].to_dict('records')
        
        # Convert numpy types to Python types for JSON serialization
        for job in jobs_list:
            for key, value in job.items():
                if pd.isna(value):
                    job[key] = None
                elif hasattr(value, 'item'):  # numpy scalar
                    job[key] = value.item()
        
        return jsonify({
            'success': True,
            'data': jobs_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': int(total),
                'pages': (total + limit - 1) // limit
            }
        })
    
    except Exception as e:
        logging.error(f"Error getting jobs: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API: Get job recommendations
@app.route('/api/recommendations', methods=['POST'])
def get_job_recommendations():
    """Get personalized job recommendations"""
    try:
        data = request.get_json()
        
        # Get max recommendations (default 10, max 25)
        top_n = min(int(data.get('top_n', 10)), 25)
        top_n = max(top_n, 1)  # Minimum 1
        
        user_profile = {
            'skills': data.get('skills', []),
            'role': data.get('role', 'Software Engineer'),
            'experience': data.get('experience', '0-2 years'),
            'location': data.get('location', 'Bangalore'),
            'preferred_locations': data.get('preferred_locations', [])
        }
        
        # Load fresh jobs — tries PostgreSQL (with retry) then falls back to CSV
        jobs_df = load_recent_jobs(days=30)
        
        if jobs_df.empty:
            return jsonify({
                'success': True,
                'message': 'No job data available',
                'data': []
            })
        
        # Filter by location if specified
        user_location = user_profile.get('location', '')
        if user_location and user_location.lower() not in ['', 'any', 'all locations']:
            from src.data_loader import normalize_location
            
            # Normalize user's selected location
            normalized_user_loc = normalize_location(user_location).lower()
            
            # Filter jobs to only include matching locations (exact match)
            jobs_df['normalized_location'] = jobs_df['location'].apply(lambda x: normalize_location(x).lower())
            jobs_df_filtered = jobs_df[
                (jobs_df['normalized_location'] == normalized_user_loc) | 
                (jobs_df['normalized_location'].str.contains('remote', na=False))
            ].copy()
            
            # Drop the helper column
            jobs_df_filtered = jobs_df_filtered.drop('normalized_location', axis=1)
            
            if jobs_df_filtered.empty:
                return jsonify({
                    'success': True,
                    'message': f'No jobs found in {user_location}. Try a different location.',
                    'data': []
                })
            
            logging.info(f"Filtered to {len(jobs_df_filtered)} jobs in {user_location} (from {len(jobs_df)} total)")
            jobs_df = jobs_df_filtered
        
        # ------------------------------------------------------------------
        # ML model caching: train once per location, reuse for 30 minutes
        # ------------------------------------------------------------------
        # Build a stable cache key from the filtered job set
        model_cache_key = f'model:{user_location.lower().strip()}'
        import time as _time

        recommendation_engine = None
        with _model_cache_lock:
            cached = _model_cache.get(model_cache_key)
            if cached and (_time.time() - cached['trained_at']) < MODEL_CACHE_TTL:
                recommendation_engine = cached['engine']
                logging.info(f"ML model cache HIT for key '{model_cache_key}'")

        if recommendation_engine is None:
            logging.info(f"ML model cache MISS — training for key '{model_cache_key}'")
            recommendation_engine = JobRecommendationEngine()
            recommendation_engine.train(jobs_df)
            with _model_cache_lock:
                _model_cache[model_cache_key] = {
                    'engine': recommendation_engine,
                    'trained_at': _time.time()
                }
        
        # Get recommendations with specified top_n
        recommendations = recommendation_engine.calculate_match(user_profile, top_n=top_n)
        
        # Convert DataFrame to list of dicts for JSON serialization
        recommendations_list = []
        if not recommendations.empty:
            recommendations = recommendations.fillna('')
            for idx, row in recommendations.iterrows():
                # Parse skills strings to lists
                matched_skills = [s.strip() for s in str(row.get('matched_skills', '')).split(',') if s.strip()]
                missing_skills = [s.strip() for s in str(row.get('missing_skills', '')).split(',') if s.strip()]
                required_skills = [s.strip() for s in str(row['skills']).split(',') if s.strip()]
                
                recommendations_list.append({
                    'job_id': str(row['job_id']),
                    'title': row['title'],
                    'company': row['company'],
                    'location': row['location'],
                    'skills': row['skills'],
                    'required_skills': required_skills,
                    'experience': row['experience'],
                    'salary': row['salary'],
                    'match_score': float(row['match_score']),
                    'skills_match': float(row.get('skills_match', 0)),
                    'experience_match': float(row.get('experience_match', 0)),
                    'location_match': float(row.get('location_match', 0)),
                    'matched_skills': matched_skills,
                    'missing_skills': missing_skills,
                    'description': row['description'][:200] + '...' if len(str(row['description'])) > 200 else row['description'],
                    'posted_date': str(row['posted_date']),
                    'url': row['url']
                })
        
        return jsonify({
            'success': True,
            'data': recommendations_list,
            'count': len(recommendations_list)
        })
    
    except Exception as e:
        logging.error(f"Error getting recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        }), 500

# API: Get market analytics
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get market analytics and trends (cached 10 min)"""
    try:
        days = request.args.get('days', 30, type=int)
        cache_key = f'api:analytics:{days}'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        jobs_df = load_recent_jobs(days=days)
        
        if jobs_df.empty:
            return jsonify({
                'success': False,
                'message': 'No job data available'
            }), 404
        
        analytics = {
            'top_companies': jobs_df['company'].value_counts().head(10).to_dict(),
            'top_locations': jobs_df['location'].value_counts().head(10).to_dict(),
            'salary_ranges': {
                'min': int(jobs_df['salary_min'].mean()),
                'max': int(jobs_df['salary_max'].mean()),
                'avg': int(((jobs_df['salary_min'] + jobs_df['salary_max']) / 2).mean())
            }
        }
        
        result = {'success': True, 'data': analytics}
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error getting analytics: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API: Get salary trends
@app.route('/api/salary-trends', methods=['GET'])
def get_salary_trends():
    """Get salary trends by location or role (cached 10 min)"""
    try:
        days = request.args.get('days', None, type=int)
        group_by = request.args.get('group_by', 'location')
        location = request.args.get('location', '', type=str)
        cache_key = f'api:salary-trends:{days}:{group_by}:{location}'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        jobs_df = load_recent_jobs(days=days) if days else load_all_jobs()
        
        # Filter by location if provided
        if location and location != 'All':
            from src.analytics import filter_jobs_by_location
            jobs_df = filter_jobs_by_location(jobs_df, location)
        
        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})
        
        salary_trends = calculate_salary_trends(jobs_df, group_by=group_by)
        
        if salary_trends.empty:
            return jsonify({'success': True, 'data': []})
        
        trends_list = salary_trends.head(10).to_dict('records')
        for trend in trends_list:
            for key in trend:
                if isinstance(trend[key], (int, float)):
                    trend[key] = float(trend[key])
        
        result = {'success': True, 'data': trends_list}
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)
    
    except Exception as e:
        logging.error(f"Error getting salary trends: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get top skills
@app.route('/api/top-skills', methods=['GET'])
def get_skills():
    """Get top in-demand skills (cached 10 min)"""
    try:
        days = request.args.get('days', None, type=int)
        top_n = request.args.get('top_n', 15, type=int)
        location = request.args.get('location', '', type=str)
        cache_key = f'api:top-skills:{days}:{top_n}:{location}'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        jobs_df = load_recent_jobs(days=days) if days else load_all_jobs()

        if location and location != 'All':
            from src.analytics import filter_jobs_by_location
            jobs_df = filter_jobs_by_location(jobs_df, location)

        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})

        skills = get_top_skills(jobs_df, top_n=top_n)
        if skills.empty:
            return jsonify({'success': True, 'data': []})

        skills_list = skills.to_dict('records')
        for skill in skills_list:
            skill['count'] = int(skill['count'])

        result = {'success': True, 'data': skills_list}
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting skills: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get role distribution
@app.route('/api/role-distribution', methods=['GET'])
def get_roles():
    """Get job role distribution (cached 10 min)"""
    try:
        days = request.args.get('days', None, type=int)
        top_n = request.args.get('top_n', 10, type=int)
        location = request.args.get('location', '', type=str)
        cache_key = f'api:role-distribution:{days}:{top_n}:{location}'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        jobs_df = load_recent_jobs(days=days) if days else load_all_jobs()

        if location and location != 'All':
            from src.analytics import filter_jobs_by_location
            jobs_df = filter_jobs_by_location(jobs_df, location)

        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})

        roles = get_role_distribution(jobs_df, top_n=top_n)
        if roles.empty:
            return jsonify({'success': True, 'data': []})

        roles_list = roles.to_dict('records')
        for role in roles_list:
            role['count'] = int(role['count'])

        result = {'success': True, 'data': roles_list}
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting roles: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get experience distribution
@app.route('/api/experience-distribution', methods=['GET'])
def get_exp_dist():
    """Get experience level distribution (cached 10 min)"""
    try:
        days = request.args.get('days', None, type=int)
        location = request.args.get('location', '', type=str)
        cache_key = f'api:exp-dist:{days}:{location}'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        jobs_df = load_recent_jobs(days=days) if days else load_all_jobs()

        if location and location != 'All':
            from src.analytics import filter_jobs_by_location
            jobs_df = filter_jobs_by_location(jobs_df, location)

        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})

        exp_dist = get_experience_distribution(jobs_df)
        if exp_dist.empty:
            return jsonify({'success': True, 'data': []})

        exp_list = exp_dist.to_dict('records')
        for exp in exp_list:
            exp['count'] = int(exp['count'])

        result = {'success': True, 'data': exp_list}
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting experience distribution: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get location statistics
@app.route('/api/location-stats', methods=['GET'])
def get_location_stats():
    """Get job statistics by location (cached 10 min)"""
    try:
        days = request.args.get('days', None, type=int)
        location = request.args.get('location', '', type=str)
        cache_key = f'api:location-stats:{days}:{location}'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        jobs_df = load_recent_jobs(days=days) if days else load_all_jobs()

        if location and location != 'All':
            from src.analytics import filter_jobs_by_location
            jobs_df = filter_jobs_by_location(jobs_df, location)

        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})

        loc_stats = calculate_location_stats(jobs_df)
        if loc_stats.empty:
            return jsonify({'success': True, 'data': []})

        loc_list = loc_stats.head(15).to_dict('records')
        for loc in loc_list:
            for key in loc:
                if isinstance(loc[key], (int, float)):
                    loc[key] = float(loc[key])

        result = {'success': True, 'data': loc_list}
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting location stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get posting trends
@app.route('/api/posting-trends', methods=['GET'])
def get_trends():
    """Get job posting trends over time (cached 10 min)"""
    try:
        days = request.args.get('days', None, type=int)
        location = request.args.get('location', '', type=str)
        cache_key = f'api:posting-trends:{days}:{location}'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        jobs_df = load_recent_jobs(days=days) if days else load_all_jobs()

        if location and location != 'All':
            from src.analytics import filter_jobs_by_location
            jobs_df = filter_jobs_by_location(jobs_df, location)

        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})

        trends = get_posting_trends(jobs_df, days=days)

        if trends.empty:
            return jsonify({'success': True, 'data': []})

        trends_list = []
        for idx, row in trends.iterrows():
            trends_list.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'count': int(row['count'])
            })

        result = {'success': True, 'data': trends_list}
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting posting trends: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get summary statistics
@app.route('/api/summary-stats', methods=['GET'])
def get_summary():
    """Get overall market summary statistics (cached 10 min)"""
    try:
        days = request.args.get('days', None, type=int)
        location = request.args.get('location', '', type=str)
        cache_key = f'api:summary-stats:{days}:{location}'
        with _cache_lock:
            if cache_key in _response_cache:
                return jsonify(_response_cache[cache_key])

        jobs_df = load_recent_jobs(days=days) if days else load_all_jobs()

        if location and location != 'All':
            from src.analytics import filter_jobs_by_location
            jobs_df = filter_jobs_by_location(jobs_df, location)

        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data'})

        stats = calculate_summary_stats(jobs_df)
        result = {'success': True, 'data': stats}
        with _cache_lock:
            _response_cache[cache_key] = result
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting summary stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Background job status tracking
job_fetch_status = {
    'is_running': False,
    'progress': 0,
    'message': 'Not started',
    'last_started': None,
    'last_completed': None,
    'jobs_count': 0
}

def background_job_fetch(app_id, app_key):
    """Background task to fetch jobs, train model"""
    global job_fetch_status
    
    try:
        # Status is already set by fetch_jobs_api, just update progress
        time.sleep(0.5)  # Small delay to ensure API response is sent first
        job_fetch_status['progress'] = 5
        job_fetch_status['message'] = '🚀 Starting job scraper... Preparing database connection'
        logging.info("=" * 70)
        logging.info("FETCH JOBS INITIATED")
        logging.info("=" * 70)
        
        # Step 1: Delete old pickle files
        pickle_file = 'models/recommendation_model.pkl'
        if os.path.exists(pickle_file):
            try:
                file_size = os.path.getsize(pickle_file) / (1024*1024)
                os.remove(pickle_file)
                job_fetch_status['progress'] = 10
                job_fetch_status['message'] = '🗑️ Cleared old ML model... Ready for fresh training'
                logging.info(f"Deleted old pickle model: {file_size:.2f} MB")
            except Exception as e:
                logging.warning(f"Could not delete old pickle: {str(e)}")
        
        job_fetch_status['progress'] = 15
        job_fetch_status['message'] = '🔍 Connecting to Adzuna API... Scanning Indian tech jobs'
        
        # Define progress callback
        def update_progress(progress, message):
            job_fetch_status['progress'] = progress
            job_fetch_status['message'] = message
            logging.info(f"Progress: {progress}% - {message}")
        
        # WARNING: Render uses ephemeral storage!
        logging.warning("WARNING: Running on ephemeral filesystem - data will be lost on restart!")
        
        # Step 2: Fetch and save new jobs
        job_fetch_status['progress'] = 20
        job_fetch_status['message'] = '📥 Scraping jobs from API... This may take 2-4 minutes'
        
        result = fetch_and_save_jobs(app_id, app_key, progress_callback=update_progress)
        
        if result is not None and not result.empty:
            job_fetch_status['progress'] = 60
            job_fetch_status['message'] = f'💾 Moving {len(result)} jobs to PostgreSQL database...'
            logging.info(f"Scraped {len(result)} jobs successfully")
            
            # Simulate database save progress
            time.sleep(1)
            job_fetch_status['progress'] = 70
            job_fetch_status['message'] = '🤖 Training AI recommendation engine on fresh data...'
            job_fetch_status['jobs_count'] = len(result)
            
            logging.info("=" * 70)
            logging.info("🔄 TRAINING NEW RECOMMENDATION MODEL")
            logging.info("=" * 70)
            
            # Filter to only last 30 days for fresh recommendations
            from datetime import timedelta
            cutoff_date = pd.Timestamp(datetime.now() - timedelta(days=30)).tz_localize('UTC')
            fresh_jobs = result[result['posted_date'] >= cutoff_date].copy()
            
            logging.info(f"Total scraped jobs: {len(result):,}")
            logging.info(f"Fresh jobs (≤30 days): {len(fresh_jobs):,}")
            
            # Step 3: Train new model on fresh jobs only
            recommendation_engine = JobRecommendationEngine()
            recommendation_engine.train(fresh_jobs if not fresh_jobs.empty else result)
            
            job_fetch_status['progress'] = 85
            job_fetch_status['message'] = '💽 Saving trained ML model...'
            
            # Step 4: Save new model
            recommendation_engine.save_model(pickle_file)
            
            model_size = os.path.getsize(pickle_file) / (1024*1024)
            fresh_count = len(fresh_jobs) if not fresh_jobs.empty else len(result)
            logging.info(f"NEW MODEL SAVED: {model_size:.2f} MB, Trained on {fresh_count} fresh jobs (≤30 days)")
            logging.info("=" * 70)
            
            job_fetch_status['progress'] = 100
            job_fetch_status['message'] = f'✅ Success! {len(result):,} jobs saved (90-day analytics ready). AI trained on {fresh_count:,} fresh jobs (≤30 days)!'
            job_fetch_status['is_running'] = False
            job_fetch_status['last_completed'] = datetime.now().isoformat()

            # Invalidate all caches so next request picks up fresh data
            with _cache_lock:
                _response_cache.clear()
            with _model_cache_lock:
                _model_cache.clear()
            logging.info("Response and model caches cleared after successful job fetch")
        else:
            job_fetch_status['progress'] = 0
            job_fetch_status['message'] = '❌ No jobs fetched. API may be rate-limited or unavailable'
            job_fetch_status['is_running'] = False
            logging.error("Job fetch returned empty result")
            
    except Exception as e:
        logging.error(f"Background job fetch error: {str(e)}")
        job_fetch_status['progress'] = 0
        job_fetch_status['message'] = f'❌ Error: {str(e)}'
        job_fetch_status['is_running'] = False

# API: Start job fetch (non-blocking)
@app.route('/api/fetch-jobs', methods=['POST'])
def fetch_jobs_api():
    """Start background job fetch - returns immediately"""
    global job_fetch_status
    
    try:
        if job_fetch_status['is_running']:
            return jsonify({
                'success': False,
                'message': 'Job fetch already in progress',
                'status': job_fetch_status
            }), 400
        
        app_id = os.getenv('ADZUNA_APP_ID')
        app_key = os.getenv('ADZUNA_APP_KEY')
        
        if not app_id or not app_key:
            return jsonify({
                'success': False,
                'message': 'API credentials not configured'
            }), 400
        
        # Update status BEFORE starting thread to avoid "Not started" flash
        job_fetch_status['is_running'] = True
        job_fetch_status['progress'] = 0
        job_fetch_status['message'] = '⏳ Initializing scraper... Starting background process'
        job_fetch_status['last_started'] = datetime.now().isoformat()
        
        # Start background thread
        import threading
        thread = threading.Thread(target=background_job_fetch, args=(app_id, app_key))
        thread.daemon = True
        thread.start()
        
        logging.info("🚀 Job fetch started in background")
        
        return jsonify({
            'success': True,
            'message': 'Fetching the latest job listings… This may take a few minutes. Please stay on this page while we update the results.',
            'status': job_fetch_status
        })
    
    except Exception as e:
        logging.error(f"Error in fetch_jobs_api: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API: Check job fetch status
@app.route('/api/fetch-jobs-status', methods=['GET'])
def fetch_jobs_status():
    """Get current status of background job fetch"""
    return jsonify({
        'success': True,
        'status': job_fetch_status
    })

# API: Get last updated timestamp
@app.route('/api/last-updated', methods=['GET'])
def get_last_updated():
    """Get last updated timestamp"""
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
            return jsonify({
                'success': True,
                'last_updated': 'Never'
            })
        
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not csv_files:
            return jsonify({
                'success': True,
                'last_updated': 'Never'
            })
        
        file_paths = [os.path.join(data_dir, f) for f in csv_files]
        latest_file = max(file_paths, key=os.path.getmtime)
        
        mod_time = os.path.getmtime(latest_file)
        last_updated = datetime.fromtimestamp(mod_time)
        
        return jsonify({
            'success': True,
            'last_updated': last_updated.strftime("%B %d, %Y at %I:%M %p")
        })
    
    except Exception as e:
        logging.error(f"Error getting last updated: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ========================
# ERROR HANDLERS
# ========================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Route not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ========================
# MAIN
# ========================

if __name__ == '__main__':
    # Create frontend directory if it doesn't exist
    os.makedirs('frontend', exist_ok=True)
    os.makedirs('frontend/assets', exist_ok=True)
    
    # Run Flask app
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug,
        threaded=False,  # Disable threading to avoid Fortran errors with sklearn
        use_reloader=False
    )
