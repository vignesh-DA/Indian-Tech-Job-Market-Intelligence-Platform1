"""
User database management for authentication
SQLite-based user storage with OAuth integration
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List

class UserDatabase:
    """Handle user database operations"""
    
    def __init__(self, db_path: str = 'data/users.db'):
        """Initialize database connection"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Create users table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    picture TEXT,
                    google_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            conn.commit()
    
    def get_or_create_user(self, email: str, name: str = None, picture: str = None, 
                          google_id: str = None) -> Dict:
        """Get existing user or create new one"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Check if user exists
            cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                # Update last_login
                conn.execute(
                    'UPDATE users SET last_login = ? WHERE email = ?',
                    (datetime.now(), email)
                )
                conn.commit()
                return dict(user)
            else:
                # Create new user
                cursor = conn.execute(
                    '''INSERT INTO users (email, name, picture, google_id, last_login)
                       VALUES (?, ?, ?, ?, ?)''',
                    (email, name, picture, google_id, datetime.now())
                )
                conn.commit()
                
                # Return created user
                return {
                    'id': cursor.lastrowid,
                    'email': email,
                    'name': name,
                    'picture': picture,
                    'google_id': google_id,
                    'created_at': datetime.now(),
                    'last_login': datetime.now()
                }
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def update_user(self, user_id: int, **kwargs) -> Dict:
        """Update user profile"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Build update query
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in ['name', 'picture']:
                    updates.append(f'{key} = ?')
                    values.append(value)
            
            if not updates:
                return self.get_user_by_id(user_id)
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            
            conn.execute(query, values)
            conn.commit()
            
            return self.get_user_by_id(user_id)
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM users ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]


# Initialize database instance
user_db = UserDatabase()
