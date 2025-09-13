"""
Authentication module for Health Analyzer
Provides user authentication, session management, and database utilities.
"""

from .auth import AuthManager, login_required
from .storage import UserDatabase

__all__ = ['AuthManager', 'UserDatabase', 'login_required']
