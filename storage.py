"""
SQLite database utilities for user authentication
Handles user storage, retrieval, and database operations.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib
import secrets


class UserDatabase:
    def __init__(self, db_path: str = "users.db"):
        """Initialize the user database"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the users table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create sessions table for session management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username: str, email: str, password_hash: str) -> Dict[str, Any]:
        """Create a new user in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "error": "Username or email already exists"}
            
            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "success": True, 
                "user_id": user_id,
                "message": "User created successfully"
            }
        
        except sqlite3.Error as e:
            return {"success": False, "error": f"Database error: {str(e)}"}
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, created_at
                FROM users WHERE email = ?
            ''', (email,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "password_hash": row[3],
                    "created_at": row[4]
                }
            return None
        
        except sqlite3.Error:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by username"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, created_at
                FROM users WHERE username = ?
            ''', (username,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "password_hash": row[3],
                    "created_at": row[4]
                }
            return None
        
        except sqlite3.Error:
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, created_at
                FROM users WHERE id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "created_at": row[3]
                }
            return None
        
        except sqlite3.Error:
            return None
    
    def create_session(self, user_id: int, expires_hours: int = 24) -> str:
        """Create a session token for a user"""
        session_token = secrets.token_urlsafe(32)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate expiration time
            expires_at = datetime.now().timestamp() + (expires_hours * 3600)
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, session_token, expires_at))
            
            conn.commit()
            conn.close()
            
            return session_token
        
        except sqlite3.Error:
            return None
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate a session token and return user info"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.email, s.expires_at
                FROM users u
                JOIN user_sessions s ON u.id = s.user_id
                WHERE s.session_token = ? AND s.is_active = TRUE
            ''', (session_token,))
            
            row = cursor.fetchone()
            
            if row:
                user_id, username, email, expires_at = row
                
                # Check if session is expired
                if datetime.now().timestamp() > expires_at:
                    # Deactivate expired session
                    cursor.execute('''
                        UPDATE user_sessions 
                        SET is_active = FALSE 
                        WHERE session_token = ?
                    ''', (session_token,))
                    conn.commit()
                    conn.close()
                    return None
                
                conn.close()
                return {
                    "id": user_id,
                    "username": username,
                    "email": email
                }
            
            conn.close()
            return None
        
        except sqlite3.Error:
            return None
    
    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE session_token = ?
            ''', (session_token,))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
        
        except sqlite3.Error:
            return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().timestamp()
            cursor.execute('''
                DELETE FROM user_sessions 
                WHERE expires_at < ? OR is_active = FALSE
            ''', (current_time,))
            
            conn.commit()
            conn.close()
            return True
        
        except sqlite3.Error:
            return False
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        
        except sqlite3.Error:
            return 0
