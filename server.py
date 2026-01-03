"""
Flask Backend Server for Indian Tech Job Market Intelligence Platform
Replaces Streamlit with a proper REST API + modern frontend
"""

# Disable MKL threading to avoid Fortran runtime errors with scikit-learn
import os
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
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
from src.chatbot_engine import ChatbotEngine
from src.logger import logging
import sys

# Try to import Gemini API - optional for fallback mode
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Gemini API not installed. Using fallback responses.")

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            static_folder='frontend/assets',
            template_folder='frontend')

# Enable CORS
CORS(app)

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
    """Serve main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error loading index.html: {str(e)}")
        return jsonify({'error': 'Failed to load home page'}), 500

@app.route('/dashboard')
def dashboard():
    """Serve dashboard page"""
    try:
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

# API: Get dashboard statistics
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get market statistics"""
    try:
        jobs_df = load_recent_jobs(days=30)
        
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
        
        stats = {
            'total_jobs': int(total_jobs),
            'companies_hiring': int(companies),
            'locations': int(locations),
            'average_salary': avg_salary
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
        logging.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API: Get unique job roles from data
@app.route('/api/roles', methods=['GET'])
def get_unique_roles():
    """Get unique job roles from the dataset"""
    try:
        jobs_df = load_recent_jobs(days=30)
        
        if jobs_df.empty:
            return jsonify({
                'success': False,
                'message': 'No job data available',
                'data': []
            }), 404
        
        # Get all unique titles
        all_titles = jobs_df['title'].unique().tolist()
        
        # Normalize and extract main role from titles
        # This removes company names, experience levels, and location info
        normalized_roles = set()
        
        for title in all_titles:
            # Remove common patterns like company names, experience, location
            title_lower = str(title).lower()
            
            # Skip if it has too many special characters or is too long
            if len(title) > 80 or title.count('(') > 2:
                continue
            
            # Extract main role by taking first meaningful part
            # Remove location, experience, company references
            parts = title.split('-')[0].split('|')[0].split('(')[0].strip()
            
            # Skip if it's too short or contains only numbers
            if len(parts) > 5 and not parts.isdigit():
                normalized_roles.add(parts)
        
        # Sort and limit to top roles
        unique_roles = sorted(list(normalized_roles))[:100]
        
        return jsonify({
            'success': True,
            'data': unique_roles
        })
    
    except Exception as e:
        logging.error(f"Error getting unique roles: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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
        days = request.args.get('days', 30, type=int)
        
        # Load jobs
        jobs_df = load_recent_jobs(days=days)
        
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
        
        user_profile = {
            'skills': data.get('skills', []),
            'role': data.get('role', 'Software Engineer'),
            'experience': data.get('experience', '0-2 years'),
            'location': data.get('location', 'Bangalore'),
            'preferred_locations': data.get('preferred_locations', [])
        }
        
        # Load recent jobs and get recommendations
        jobs_df = load_recent_jobs(days=30)
        
        if jobs_df.empty:
            return jsonify({
                'success': True,
                'message': 'No job data available',
                'data': []
            })
        
        # Initialize and train recommendation engine
        recommendation_engine = JobRecommendationEngine()
        recommendation_engine.train(jobs_df)
        
        # Save model for future use (optional caching)
        try:
            recommendation_engine.save_model('models/recommendation_model.pkl')
        except Exception as save_error:
            logging.warning(f"Could not save model cache: {save_error}")
        
        # Get recommendations
        recommendations = recommendation_engine.calculate_match(user_profile, top_n=10)
        
        # Convert DataFrame to list of dicts for JSON serialization
        recommendations_list = []
        if not recommendations.empty:
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
    """Get market analytics and trends"""
    try:
        days = request.args.get('days', 30, type=int)
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
        
        return jsonify({
            'success': True,
            'data': analytics
        })
    
    except Exception as e:
        logging.error(f"Error getting analytics: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API: Get salary trends
@app.route('/api/salary-trends', methods=['GET'])
def get_salary_trends():
    """Get salary trends by location or role"""
    try:
        days = request.args.get('days', 30, type=int)
        group_by = request.args.get('group_by', 'location')
        
        jobs_df = load_recent_jobs(days=days)
        
        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})
        
        salary_trends = calculate_salary_trends(jobs_df, group_by=group_by)
        
        if salary_trends.empty:
            return jsonify({'success': True, 'data': []})
        
        # Convert to list of dicts
        trends_list = salary_trends.head(10).to_dict('records')
        for trend in trends_list:
            for key in trend:
                if isinstance(trend[key], (int, float)):
                    trend[key] = float(trend[key])
        
        return jsonify({'success': True, 'data': trends_list})
    
    except Exception as e:
        logging.error(f"Error getting salary trends: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get top skills
@app.route('/api/top-skills', methods=['GET'])
def get_skills():
    """Get top in-demand skills"""
    try:
        days = request.args.get('days', 30, type=int)
        top_n = request.args.get('top_n', 15, type=int)
        
        jobs_df = load_recent_jobs(days=days)
        
        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})
        
        skills = get_top_skills(jobs_df, top_n=top_n)
        
        if skills.empty:
            return jsonify({'success': True, 'data': []})
        
        skills_list = skills.to_dict('records')
        for skill in skills_list:
            skill['count'] = int(skill['count'])
        
        return jsonify({'success': True, 'data': skills_list})
    
    except Exception as e:
        logging.error(f"Error getting skills: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get role distribution
@app.route('/api/role-distribution', methods=['GET'])
def get_roles():
    """Get job role distribution"""
    try:
        days = request.args.get('days', 30, type=int)
        top_n = request.args.get('top_n', 10, type=int)
        
        jobs_df = load_recent_jobs(days=days)
        
        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})
        
        roles = get_role_distribution(jobs_df, top_n=top_n)
        
        if roles.empty:
            return jsonify({'success': True, 'data': []})
        
        roles_list = roles.to_dict('records')
        for role in roles_list:
            role['count'] = int(role['count'])
        
        return jsonify({'success': True, 'data': roles_list})
    
    except Exception as e:
        logging.error(f"Error getting roles: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get experience distribution
@app.route('/api/experience-distribution', methods=['GET'])
def get_exp_dist():
    """Get experience level distribution"""
    try:
        days = request.args.get('days', 30, type=int)
        
        jobs_df = load_recent_jobs(days=days)
        
        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data', 'data': []})
        
        exp_dist = get_experience_distribution(jobs_df)
        
        if exp_dist.empty:
            return jsonify({'success': True, 'data': []})
        
        exp_list = exp_dist.to_dict('records')
        for exp in exp_list:
            exp['count'] = int(exp['count'])
        
        return jsonify({'success': True, 'data': exp_list})
    
    except Exception as e:
        logging.error(f"Error getting experience distribution: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get location statistics
@app.route('/api/location-stats', methods=['GET'])
def get_location_stats():
    """Get job statistics by location"""
    try:
        days = request.args.get('days', 30, type=int)
        
        jobs_df = load_recent_jobs(days=days)
        
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
        
        return jsonify({'success': True, 'data': loc_list})
    
    except Exception as e:
        logging.error(f"Error getting location stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get posting trends
@app.route('/api/posting-trends', methods=['GET'])
def get_trends():
    """Get job posting trends over time"""
    try:
        days = request.args.get('days', 30, type=int)
        
        jobs_df = load_recent_jobs(days=days)
        
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
        
        return jsonify({'success': True, 'data': trends_list})
    
    except Exception as e:
        logging.error(f"Error getting posting trends: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get summary statistics
@app.route('/api/summary-stats', methods=['GET'])
def get_summary():
    """Get overall market summary statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        jobs_df = load_recent_jobs(days=days)
        
        if jobs_df.empty:
            return jsonify({'success': False, 'message': 'No data'})
        
        stats = calculate_summary_stats(jobs_df)
        
        return jsonify({'success': True, 'data': stats})
    
    except Exception as e:
        logging.error(f"Error getting summary stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Fetch latest jobs
@app.route('/api/fetch-jobs', methods=['POST'])
def fetch_jobs_api():
    """Fetch latest jobs from Adzuna API, delete old CSV/pickle, train new model"""
    try:
        app_id = os.getenv('ADZUNA_APP_ID')
        app_key = os.getenv('ADZUNA_APP_KEY')
        
        if not app_id or not app_key:
            return jsonify({
                'success': False,
                'message': 'API credentials not configured'
            }), 400
        
        # Step 1: Delete old pickle files
        pickle_file = 'models/recommendation_model.pkl'
        if os.path.exists(pickle_file):
            try:
                file_size = os.path.getsize(pickle_file) / (1024*1024)
                os.remove(pickle_file)
                logging.info("=" * 70)
                logging.info("🗑️  DELETED OLD PICKLE MODEL")
                logging.info("=" * 70)
                logging.info(f"   Path: {pickle_file}")
                logging.info(f"   Size: {file_size:.2f} MB")
                logging.info(f"   Reason: New data fetch initiated")
                logging.info("=" * 70)
            except Exception as e:
                logging.warning(f"Could not delete old pickle: {str(e)}")
        
        # Step 2: Fetch and save new jobs (this also deletes old CSVs)
        result = fetch_and_save_jobs(app_id, app_key)
        
        if result is not None and not result.empty:
            logging.info("=" * 70)
            logging.info("🔄 TRAINING NEW RECOMMENDATION MODEL")
            logging.info("=" * 70)
            
            # Step 3: Train new model on fetched data
            try:
                recommendation_engine = JobRecommendationEngine()
                recommendation_engine.train(result)
                
                # Step 4: Save new pickle model
                recommendation_engine.save_model(pickle_file)
                
                model_size = os.path.getsize(pickle_file) / (1024*1024)
                logging.info(f"✅ NEW MODEL SAVED")
                logging.info(f"   Path: {pickle_file}")
                logging.info(f"   Size: {model_size:.2f} MB")
                logging.info(f"   Trained on: {len(result)} jobs")
                logging.info("=" * 70)
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully fetched {len(result)} jobs and trained new model',
                    'count': len(result),
                    'model_trained': True,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as model_error:
                logging.error(f"Error training/saving model: {str(model_error)}")
                return jsonify({
                    'success': False,
                    'message': f'Data fetched but model training failed: {str(model_error)}',
                    'count': len(result),
                    'model_trained': False
                }), 500
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to fetch jobs from API'
            }), 400
    
    except Exception as e:
        logging.error(f"Error in fetch_jobs_api: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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
# CHATBOT ENDPOINT
# ========================

# Initialize chatbot engine
chatbot = ChatbotEngine()

# Setup Gemini API if available
if GEMINI_AVAILABLE:
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        logging.info("✅ Gemini API configured successfully")
    else:
        logging.warning("⚠️ GEMINI_API_KEY not found in .env - using fallback responses")
        GEMINI_AVAILABLE = False

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chatbot endpoint
    Handles conversation with Gemini API integration
    
    Request JSON:
    {
        "message": "user message",
        "user_profile": {
            "role": "role",
            "experience": "experience",
            "location": "location",
            "skills": ["skill1", "skill2"],
            "total_matched_jobs": 24
        },
        "conversation_history": [
            {"role": "user", "content": "message"},
            {"role": "bot", "content": "response"}
        ]
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        user_profile = data.get('user_profile', {})
        conversation_history = data.get('conversation_history', [])
        
        if not user_message:
            return jsonify({
                'success': False,
                'message': 'Message cannot be empty'
            }), 400
        
        logging.info(f"🤖 Chat request: {user_message[:100]}")
        
        # Get current job recommendations for context
        try:
            jobs = load_recent_jobs()
            recommendations = jobs.to_dict('records')[:5] if not jobs.empty else []
        except:
            recommendations = []
        
        # Generate response
        if GEMINI_AVAILABLE:
            response = chatbot.generate_response(
                user_message=user_message,
                user_profile=user_profile,
                conversation_history=conversation_history,
                recommendations=recommendations,
                gemini_api=genai
            )
        else:
            # Use fallback without Gemini API
            response = chatbot.generate_response(
                user_message=user_message,
                user_profile=user_profile,
                conversation_history=conversation_history,
                recommendations=recommendations,
                gemini_api=None
            )
        
        if response['success']:
            logging.info(f"✅ Chat response generated - Intent: {response['intent']}")
            return jsonify({
                'success': True,
                'message': response['message'],
                'intent': response['intent'],
                'category': response['category'],
                'confidence': response['confidence']
            })
        else:
            logging.error(f"Chat error: {response.get('error')}")
            return jsonify({
                'success': False,
                'message': response['message']
            }), 500
    
    except Exception as e:
        logging.error(f"Chat endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error processing chat: {str(e)}'
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
        debug=debug
    )
