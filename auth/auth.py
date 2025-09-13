"""
Authentication manager for Streamlit applications
Handles user signup, login, logout, and session management.
"""

import streamlit as st
import bcrypt
import re
from typing import Optional, Dict, Any, Callable
from functools import wraps
from .storage import UserDatabase


class AuthManager:
    def __init__(self, db_path: str = "users.db"):
        """Initialize the authentication manager"""
        self.db = UserDatabase(db_path)
        self.session_key = "user_session"
        self.user_key = "authenticated_user"
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def signup(self, username: str, email: str, password: str, confirm_password: str) -> Dict[str, Any]:
        """Create a new user account"""
        # Validate inputs
        if not username.strip():
            return {"success": False, "error": "Username cannot be empty"}
        
        if not email.strip():
            return {"success": False, "error": "Email cannot be empty"}
        
        if not self.validate_email(email):
            return {"success": False, "error": "Please enter a valid email address"}
        
        if password != confirm_password:
            return {"success": False, "error": "Passwords do not match"}
        
        password_validation = self.validate_password(password)
        if not password_validation["valid"]:
            return {
                "success": False, 
                "error": "Password requirements not met:\\n" + "\\n".join(password_validation["issues"])
            }
        
        # Clean inputs
        username = username.strip()
        email = email.strip().lower()
        
        # Check for existing users
        if self.db.get_user_by_username(username):
            return {"success": False, "error": "Username already exists"}
        
        if self.db.get_user_by_email(email):
            return {"success": False, "error": "Email already registered"}
        
        # Hash password and create user
        password_hash = self.hash_password(password)
        result = self.db.create_user(username, email, password_hash)
        
        return result
    
    def login(self, email_or_username: str, password: str) -> Dict[str, Any]:
        """Authenticate a user and create session"""
        if not email_or_username.strip() or not password:
            return {"success": False, "error": "Email/username and password are required"}
        
        email_or_username = email_or_username.strip().lower()
        
        # Try to find user by email first, then username
        user = self.db.get_user_by_email(email_or_username)
        if not user:
            user = self.db.get_user_by_username(email_or_username)
        
        if not user:
            return {"success": False, "error": "Invalid credentials"}
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return {"success": False, "error": "Invalid credentials"}
        
        # Create session
        session_token = self.db.create_session(user['id'])
        if not session_token:
            return {"success": False, "error": "Failed to create session"}
        
        # Store session in Streamlit session state
        st.session_state[self.session_key] = session_token
        st.session_state[self.user_key] = {
            "id": user['id'],
            "username": user['username'],
            "email": user['email']
        }
        
        return {
            "success": True,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email']
            },
            "message": f"Welcome back, {user['username']}!"
        }
    
    def logout(self) -> Dict[str, Any]:
        """Logout user and invalidate session"""
        session_token = st.session_state.get(self.session_key)
        
        if session_token:
            self.db.invalidate_session(session_token)
        
        # Clear session state
        if self.session_key in st.session_state:
            del st.session_state[self.session_key]
        if self.user_key in st.session_state:
            del st.session_state[self.user_key]
        
        # Clear other session data
        keys_to_clear = [key for key in st.session_state.keys() if key not in ['theme']]
        for key in keys_to_clear:
            if key not in [self.session_key, self.user_key]:
                del st.session_state[key]
        
        return {"success": True, "message": "Logged out successfully"}
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        session_token = st.session_state.get(self.session_key)
        
        if not session_token:
            return False
        
        # Validate session with database
        user_data = self.db.validate_session(session_token)
        
        if not user_data:
            # Session invalid, clear local session
            self.logout()
            return False
        
        # Update session state with fresh user data
        st.session_state[self.user_key] = user_data
        return True
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user data"""
        if not self.is_authenticated():
            return None
        
        return st.session_state.get(self.user_key)
    
    def require_auth(self):
        """Require authentication, redirect to login if not authenticated"""
        if not self.is_authenticated():
            st.error("🔒 Please log in to access this page.")
            self.show_login_form()
            st.stop()
    
    def show_login_form(self):
        """Display login form"""
        st.markdown("### 🔑 Login to Health Analyzer")
        
        with st.form("login_form"):
            email_or_username = st.text_input("Email or Username", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_button = st.form_submit_button("Login", type="primary")
            with col2:
                signup_button = st.form_submit_button("Need an account? Sign up")
            
            if login_button:
                result = self.login(email_or_username, password)
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["error"])
            
            elif signup_button:
                st.session_state["show_signup"] = True
                st.rerun()
    
    def show_signup_form(self):
        """Display signup form"""
        st.markdown("### 📝 Create Account")
        
        with st.form("signup_form"):
            username = st.text_input("Username", key="signup_username")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
            
            st.markdown("**Password Requirements:**")
            st.markdown("""
            - At least 8 characters long
            - At least one uppercase letter
            - At least one lowercase letter
            - At least one number
            - At least one special character (!@#$%^&*(),.?\":{}|<>)
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                signup_button = st.form_submit_button("Create Account", type="primary")
            with col2:
                login_button = st.form_submit_button("Have an account? Login")
            
            if signup_button:
                result = self.signup(username, email, password, confirm_password)
                if result["success"]:
                    st.success("Account created successfully! Please log in.")
                    st.session_state["show_signup"] = False
                    st.rerun()
                else:
                    st.error(result["error"])
            
            elif login_button:
                if "show_signup" in st.session_state:
                    del st.session_state["show_signup"]
                st.rerun()
    
    def show_auth_interface(self):
        """Show appropriate authentication interface"""
        if st.session_state.get("show_signup", False):
            self.show_signup_form()
        else:
            self.show_login_form()


def login_required(func: Callable) -> Callable:
    """Decorator to require authentication for a function"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_manager = AuthManager()
        if not auth_manager.is_authenticated():
            st.error("🔒 Please log in to access this feature.")
            auth_manager.show_auth_interface()
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def create_auth_sidebar():
    """Create authentication sidebar"""
    auth_manager = AuthManager()
    
    with st.sidebar:
        st.markdown("---")
        
        if auth_manager.is_authenticated():
            user = auth_manager.get_current_user()
            st.markdown(f"👤 **Welcome, {user['username']}!**")
            st.markdown(f"📧 {user['email']}")
            
            if st.button("🚪 Logout", key="logout_button"):
                result = auth_manager.logout()
                st.success(result["message"])
                st.rerun()
        
        else:
            st.markdown("### 🔐 Authentication")
            if st.button("🔑 Login", key="sidebar_login"):
                st.session_state["show_login"] = True
                st.rerun()
            
            if st.button("📝 Sign Up", key="sidebar_signup"):
                st.session_state["show_signup"] = True
                st.rerun()
