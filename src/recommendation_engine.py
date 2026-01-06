"""
Recommendation Engine Module
ML-powered job matching using TF-IDF and cosine similarity
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
import sys
from src.logger import logging
from src.exception import CustomException
from src.data_loader import normalize_location


class JobRecommendationEngine:
    """
    Job recommendation engine using TF-IDF and cosine similarity
    
    Matching weights:
    - Skills: 70%
    - Experience: 20%
    - Location: 10%
    """
    
    def __init__(self):
        self.vectorizer = None
        self.job_vectors = None
        self.jobs_df = None
        logging.info("Initialized JobRecommendationEngine")
    
    def train(self, jobs_df):
        """
        Train the recommendation model on job data
        
        Args:
            jobs_df: DataFrame with job data
        """
        try:
            if jobs_df.empty:
                logging.warning("Empty dataframe provided for training")
                return
            
            self.jobs_df = jobs_df.copy()
            
            # Create combined text for vectorization
            self.jobs_df['combined_text'] = (
                self.jobs_df['title'].fillna('') + ' ' +
                self.jobs_df['skills'].fillna('') + ' ' +
                self.jobs_df['description'].fillna('')
            )
            
            # Train TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=500,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            self.job_vectors = self.vectorizer.fit_transform(self.jobs_df['combined_text'])
            
            logging.info(f"Trained model on {len(jobs_df)} jobs")
            
        except Exception as e:
            logging.error(f"Error in train: {str(e)}")
            raise CustomException(e, sys)
    
    def calculate_match(self, user_profile, top_n=10):
        """
        Calculate job matches for user profile
        
        Args:
            user_profile: Dict with user skills, experience, location
            top_n: Number of top matches to return
            
        Returns:
            DataFrame with matched jobs and scores
        """
        try:
            if self.vectorizer is None or self.jobs_df is None:
                logging.warning("Model not trained")
                return pd.DataFrame()
            
            # Validate vectorizer state
            if not hasattr(self.vectorizer, 'idf_') or self.vectorizer.idf_ is None:
                logging.error("Vectorizer is not properly fitted")
                return pd.DataFrame()
            
            # Extract user profile info
            user_skills = user_profile.get('skills', [])
            user_experience = user_profile.get('experience', '')
            user_location = user_profile.get('location', '')
            user_role = user_profile.get('role', '')
            
            # Create user query text
            user_text = ' '.join(user_skills) + ' ' + user_role
            
            # Vectorize user query
            user_vector = self.vectorizer.transform([user_text])
            
            # Calculate cosine similarity for skills (70% weight)
            skills_similarity = cosine_similarity(user_vector, self.job_vectors).flatten()
            
            # Calculate experience match (20% weight)
            experience_match = self._calculate_experience_match(
                user_experience,
                self.jobs_df['experience']
            )
            
            # Calculate location match (10% weight)
            location_match = self._calculate_location_match(
                user_location,
                self.jobs_df['location']
            )
            
            # Combine scores with weights
            final_scores = (
                skills_similarity * 0.7 +
                experience_match * 0.2 +
                location_match * 0.1
            )
            
            # Create results dataframe
            results_df = self.jobs_df.copy()
            results_df['match_score'] = (final_scores * 100).round(2)
            results_df['skills_match'] = (skills_similarity * 100).round(2)
            results_df['experience_match'] = (experience_match * 100).round(2)
            results_df['location_match'] = (location_match * 100).round(2)
            
            # Calculate matched and missing skills
            results_df['matched_skills'] = results_df['skills'].apply(
                lambda x: self._get_matched_skills(user_skills, x)
            )
            results_df['missing_skills'] = results_df['skills'].apply(
                lambda x: self._get_missing_skills(user_skills, x)
            )
            
            # Sort by score and return top N
            results_df = results_df.sort_values('match_score', ascending=False)
            top_results = results_df.head(top_n)
            
            logging.info(f"Generated {len(top_results)} recommendations")
            return top_results
            
        except Exception as e:
            logging.error(f"Error in calculate_match: {str(e)}")
            raise CustomException(e, sys)
    
    def _calculate_experience_match(self, user_exp, job_exp_series):
        """
        Calculate experience match score
        
        Args:
            user_exp: User experience string
            job_exp_series: Series of job experience requirements
            
        Returns:
            Array of match scores (0-1)
        """
        try:
            # Parse user experience
            user_years = self._parse_experience_years(user_exp)
            
            # Calculate match for each job
            matches = []
            for job_exp in job_exp_series:
                job_years = self._parse_experience_years(str(job_exp))
                
                if job_years is None:
                    matches.append(0.5)  # Neutral score
                elif user_years >= job_years[0] and user_years <= job_years[1]:
                    matches.append(1.0)  # Perfect match
                elif user_years < job_years[0]:
                    # User has less experience
                    diff = job_years[0] - user_years
                    matches.append(max(0, 1 - (diff * 0.2)))
                else:
                    # User has more experience
                    matches.append(0.9)  # Slightly lower but still good
            
            return np.array(matches)
            
        except Exception as e:
            logging.error(f"Error calculating experience match: {str(e)}")
            return np.zeros(len(job_exp_series))
    
    def _parse_experience_years(self, exp_string):
        """
        Parse experience string to years range
        
        Args:
            exp_string: Experience string like "2-5 years"
            
        Returns:
            Tuple of (min_years, max_years) or None
        """
        try:
            if pd.isna(exp_string) or exp_string == '':
                return None
            
            exp_string = str(exp_string).lower()
            
            # Extract numbers
            import re
            numbers = re.findall(r'\d+', exp_string)
            
            if len(numbers) >= 2:
                return (int(numbers[0]), int(numbers[1]))
            elif len(numbers) == 1:
                num = int(numbers[0])
                return (num, num + 2)
            else:
                # Default ranges based on keywords
                if 'fresher' in exp_string or 'entry' in exp_string:
                    return (0, 2)
                elif 'senior' in exp_string or 'lead' in exp_string:
                    return (5, 10)
                else:
                    return (2, 5)
                    
        except Exception as e:
            return None
    
    def _calculate_location_match(self, user_location, job_location_series):
        """
        Calculate location match score using normalized locations
        
        Args:
            user_location: User preferred location (normalized)
            job_location_series: Series of raw job locations
            
        Returns:
            Array of match scores (0-1)
        """
        try:
            if not user_location or user_location.lower() == 'any':
                return np.ones(len(job_location_series))
            
            matches = []
            user_loc_lower = user_location.lower()
            
            for job_loc in job_location_series:
                # Normalize the job location
                normalized_job_loc = normalize_location(job_loc).lower()
                
                if normalized_job_loc == user_loc_lower:
                    matches.append(1.0)  # Exact match: prioritize (100%)
                elif 'remote' in normalized_job_loc:
                    matches.append(1.0)  # Remote: equal priority (100%)
                else:
                    matches.append(0.0)  # Different location: exclude completely
            
            return np.array(matches)
            
        except Exception as e:
            logging.error(f"Error calculating location match: {str(e)}")
            return np.ones(len(job_location_series)) * 0.0
    
    def _get_matched_skills(self, user_skills, job_skills_str):
        """
        Get skills that match between user and job
        
        Args:
            user_skills: List of user skills
            job_skills_str: Comma-separated job skills string
            
        Returns:
            Comma-separated string of matched skills
        """
        try:
            if pd.isna(job_skills_str):
                return ''
            
            job_skills = [s.strip().lower() for s in str(job_skills_str).split(',')]
            user_skills_lower = [s.lower() for s in user_skills]
            
            matched = [s for s in job_skills if s in user_skills_lower]
            return ', '.join(matched)
            
        except Exception as e:
            return ''
    
    def _get_missing_skills(self, user_skills, job_skills_str):
        """
        Get skills required by job that user doesn't have
        
        Args:
            user_skills: List of user skills
            job_skills_str: Comma-separated job skills string
            
        Returns:
            Comma-separated string of missing skills
        """
        try:
            if pd.isna(job_skills_str):
                return ''
            
            job_skills = [s.strip().lower() for s in str(job_skills_str).split(',')]
            user_skills_lower = [s.lower() for s in user_skills]
            
            missing = [s for s in job_skills if s not in user_skills_lower]
            return ', '.join(missing[:5])  # Limit to 5
            
        except Exception as e:
            return ''
    
    def save_model(self, filepath='models/recommendation_model.pkl'):
        """
        Save trained model to file
        
        Args:
            filepath: Path to save model
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            model_data = {
                'vectorizer': self.vectorizer,
                'job_vectors': self.job_vectors,
                'jobs_df': self.jobs_df
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            file_size = os.path.getsize(filepath)
            num_jobs = len(self.jobs_df) if self.jobs_df is not None else 0
            logging.info(f"✅ MODEL CREATED: {filepath}")
            logging.info(f"   - File size: {file_size / (1024*1024):.2f} MB")
            logging.info(f"   - Jobs trained: {num_jobs}")
            logging.info(f"   - Vectorizer features: {len(self.vectorizer.vocabulary_)}")
            
        except Exception as e:
            logging.error(f"Error saving model: {str(e)}")
            raise CustomException(e, sys)
    
    def load_model(self, filepath='models/recommendation_model.pkl'):
        """
        Load trained model from file
        
        Args:
            filepath: Path to load model from
        """
        try:
            if not os.path.exists(filepath):
                logging.warning(f"Model file not found: {filepath}")
                return False
            
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.vectorizer = model_data['vectorizer']
            self.job_vectors = model_data['job_vectors']
            self.jobs_df = model_data['jobs_df']
            
            # Validate vectorizer is properly fitted
            if not hasattr(self.vectorizer, 'idf_') or self.vectorizer.idf_ is None:
                logging.warning("Loaded vectorizer IDF is not fitted, model loading failed")
                self.vectorizer = None
                self.job_vectors = None
                self.jobs_df = None
                return False
            
            logging.info(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            # Reset state on error
            self.vectorizer = None
            self.job_vectors = None
            self.jobs_df = None
            return False


def get_learning_suggestions(missing_skills):
    """
    Get learning resource suggestions for missing skills
    
    Args:
        missing_skills: Comma-separated string of skills
        
    Returns:
        List of learning suggestions
    """
    suggestions = []
    
    if not missing_skills or missing_skills == '':
        return []
    
    skills = [s.strip().lower() for s in missing_skills.split(',')]
    
    # Map skills to learning resources
    resources = {
        'python': 'Python.org tutorials, Codecademy Python course',
        'javascript': 'freeCodeCamp, JavaScript.info',
        'react': 'React official docs, Scrimba React course',
        'node.js': 'Node.js official guides, The Odin Project',
        'aws': 'AWS Free Tier, A Cloud Guru',
        'docker': 'Docker official tutorials, Play with Docker',
        'kubernetes': 'Kubernetes docs, KodeKloud',
        'sql': 'SQLZoo, Mode Analytics SQL Tutorial',
        'machine learning': 'Coursera ML, Fast.ai',
        'data science': 'Kaggle Learn, DataCamp'
    }
    
    for skill in skills[:3]:  # Top 3 missing skills
        if skill in resources:
            suggestions.append(f"**{skill.title()}**: {resources[skill]}")
        else:
            suggestions.append(f"**{skill.title()}**: Search on Udemy, Coursera, or YouTube")
    
    return suggestions
