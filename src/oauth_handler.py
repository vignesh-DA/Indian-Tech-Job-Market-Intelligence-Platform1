"""
Google OAuth 2.0 Authentication Handler
Handles login flow and session management
"""

import os
import json
import requests
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
from src.user_db import user_db
from src.logger import logging

load_dotenv()

class GoogleOAuth:
    """Handle Google OAuth 2.0 authentication"""
    
    def __init__(self):
        """Initialize OAuth with credentials from .env"""
        self.client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_OAUTH_REDIRECT_URI', 'http://localhost:5000/api/auth/callback')
        
        # Google OAuth endpoints
        self.auth_uri = 'https://accounts.google.com/o/oauth2/v2/auth'
        self.token_uri = 'https://www.googleapis.com/oauth2/v4/token'
        self.userinfo_uri = 'https://www.googleapis.com/oauth2/v1/userinfo'
        
        if not self.client_id or not self.client_secret:
            logging.warning("⚠️ Google OAuth credentials not configured in .env")
    
    def get_authorization_url(self) -> str:
        """
        Generate Google OAuth authorization URL
        User clicks this link to sign in
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{self.auth_uri}?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """
        Exchange authorization code for access token
        Called on /api/auth/callback
        """
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            response = requests.post(self.token_uri, data=data)
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logging.error(f"❌ Token exchange failed: {str(e)}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user info from Google using access token"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(self.userinfo_uri, headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            return {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'google_id': user_info.get('id')
            }
        
        except Exception as e:
            logging.error(f"❌ Failed to get user info: {str(e)}")
            return None
    
    def handle_oauth_callback(self, code: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Handle OAuth callback from Google
        Returns: (success, user_data, error_message)
        """
        # Exchange code for token
        token_response = self.exchange_code_for_token(code)
        if not token_response:
            return False, None, "Failed to exchange authorization code"
        
        access_token = token_response.get('access_token')
        if not access_token:
            return False, None, "No access token received"
        
        # Get user info
        user_info = self.get_user_info(access_token)
        if not user_info:
            return False, None, "Failed to retrieve user information"
        
        # Create or get user in database
        user = user_db.get_or_create_user(
            email=user_info['email'],
            name=user_info['name'],
            picture=user_info['picture'],
            google_id=user_info['google_id']
        )
        
        logging.info(f"✅ OAuth successful for user: {user['email']}")
        return True, user, None


# Initialize OAuth instance
oauth = GoogleOAuth()
