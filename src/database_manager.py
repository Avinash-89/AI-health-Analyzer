"""
Database Manager for Health Analyzer with Authentication

This module provides functions for database operations, including:
- User authentication (signup, login, profile management)
- Health sessions management
- Medical reports storage
"""

import json
import streamlit as st
import bcrypt
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database_models import (
    create_engine_and_session, create_tables, 
    User, HealthSession, MedicalReport
)


class DatabaseManager:
    """Database management class for authentication and data operations"""
    
    def __init__(self):
        """Initialize database manager"""
        self.engine, self.SessionLocal = create_engine_and_session()
        self.init_database()
    
    def init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            create_tables(self.engine)
        except Exception as e:
            print(f"⚠️ Database initialization error: {e}")
    
    def get_db_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    # ---- User Authentication ----
    
    def create_user(self, username: str, email: str, password: str) -> Optional[User]:
        """Create a new user with hashed password"""
        db = self.get_db_session()
        try:
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create new user
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash.decode('utf-8'),
                created_at=datetime.utcnow()
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        except IntegrityError:
            db.rollback()
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db = self.get_db_session()
        try:
            user = db.query(User).filter(User.email == email).first()
            return user
        finally:
            db.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        db = self.get_db_session()
        try:
            user = db.query(User).filter(User.username == username).first()
            return user
        finally:
            db.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        db = self.get_db_session()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
        finally:
            db.close()
    
    def verify_password(self, user: User, password: str) -> bool:
        """Verify password against stored hash"""
        if not user or not user.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user or not self.verify_password(user, password):
            return None
        
        # Update last login time
        db = self.get_db_session()
        try:
            user.last_login = datetime.utcnow()
            db.add(user)
            db.commit()
        except Exception as e:
            print(f"Error updating last login: {e}")
            db.rollback()
        finally:
            db.close()
        
        return user
    
    def update_user_profile(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Update user profile information"""
        db = self.get_db_session()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Update fields
            for key, value in data.items():
                if hasattr(user, key) and key != 'id' and key != 'password_hash':
                    setattr(user, key, value)
            
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password"""
        db = self.get_db_session()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not self.verify_password(user, current_password):
                return False
            
            # Hash and set new password
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            user.password_hash = password_hash.decode('utf-8')
            
            db.commit()
            return True
        except Exception as e:
            print(f"Error changing password: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    # ---- Health Sessions ----
    
    def create_health_session(
        self, user_id: int, input_symptoms: str, input_method: str,
        predictions: List[Dict], recommendations: Dict, processing_time: float
    ) -> Optional[HealthSession]:
        """Create a new health analysis session"""
        db = self.get_db_session()
        try:
            # Extract key information
            top_prediction = predictions[0]['disease'] if predictions else None
            top_confidence = predictions[0]['confidence'] if predictions else None
            severity_level = predictions[0]['severity'] if predictions else None
            
            # Create new session
            new_session = HealthSession(
                user_id=user_id,
                session_date=datetime.utcnow(),
                input_symptoms=input_symptoms,
                input_method=input_method,
                predictions=json.dumps(predictions),
                recommendations=json.dumps(recommendations),
                top_prediction=top_prediction,
                top_confidence=top_confidence,
                severity_level=severity_level,
                processing_time=processing_time
            )
            
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            return new_session
        except Exception as e:
            print(f"Error creating health session: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_user_health_sessions(self, user_id: int, limit: int = 10) -> List[HealthSession]:
        """Get user's health analysis sessions"""
        db = self.get_db_session()
        try:
            sessions = db.query(HealthSession).filter(
                HealthSession.user_id == user_id
            ).order_by(HealthSession.session_date.desc()).limit(limit).all()
            
            return sessions
        finally:
            db.close()
    
    # ---- Medical Reports ----
    
    def store_medical_report(
        self, user_id: int, filename: str, file_type: str, file_data: bytes,
        analysis_results: Dict, extracted_text: str
    ) -> Optional[MedicalReport]:
        """Store a medical report and its analysis"""
        db = self.get_db_session()
        try:
            # Extract key information
            summary = analysis_results.get('summary', {})
            urgency_level = summary.get('urgency_level', 'Low')
            confidence_score = analysis_results.get('confidence_score', 0.0)
            
            # Create new report
            new_report = MedicalReport(
                user_id=user_id,
                uploaded_at=datetime.utcnow(),
                original_filename=filename,
                file_type=file_type,
                file_data=file_data,
                extracted_text=extracted_text,
                analysis_results=json.dumps(analysis_results),
                urgency_level=urgency_level,
                confidence_score=confidence_score
            )
            
            db.add(new_report)
            db.commit()
            db.refresh(new_report)
            return new_report
        except Exception as e:
            print(f"Error storing medical report: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def get_user_medical_reports(self, user_id: int) -> List[MedicalReport]:
        """Get user's medical reports"""
        db = self.get_db_session()
        try:
            reports = db.query(MedicalReport).filter(
                MedicalReport.user_id == user_id
            ).order_by(MedicalReport.uploaded_at.desc()).all()
            
            return reports
        finally:
            db.close()
    
    # ---- User Health Summary ----
    
    def get_user_health_summary(self, user_id: int) -> Dict[str, Any]:
        """Get a summary of user's health data"""
        db = self.get_db_session()
        try:
            # Count sessions and reports
            total_sessions = db.query(HealthSession).filter(HealthSession.user_id == user_id).count()
            total_reports = db.query(MedicalReport).filter(MedicalReport.user_id == user_id).count()
            
            # Get last analysis date
            last_session = db.query(HealthSession).filter(
                HealthSession.user_id == user_id
            ).order_by(HealthSession.session_date.desc()).first()
            
            last_analysis = last_session.session_date.isoformat() if last_session else None
            
            # Calculate average confidence
            sessions = db.query(HealthSession).filter(HealthSession.user_id == user_id).all()
            confidence_values = [s.top_confidence for s in sessions if s.top_confidence is not None]
            avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
            
            # Count severity distribution
            severity_distribution = {}
            for s in sessions:
                if s.severity_level:
                    severity_distribution[s.severity_level] = severity_distribution.get(s.severity_level, 0) + 1
            
            # Extract top symptoms (basic implementation)
            all_symptoms = []
            for s in sessions:
                symptoms = s.input_symptoms.split(',') if s.input_symptoms else []
                all_symptoms.extend([sym.strip().lower() for sym in symptoms if sym.strip()])
            
            symptom_counter = {}
            for symptom in all_symptoms:
                symptom_counter[symptom] = symptom_counter.get(symptom, 0) + 1
            
            top_symptoms = sorted(symptom_counter.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_sessions': total_sessions,
                'total_reports': total_reports,
                'last_analysis': last_analysis,
                'avg_confidence': avg_confidence,
                'severity_distribution': severity_distribution,
                'top_symptoms': top_symptoms
            }
        finally:
            db.close()
    
    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """Export all user data for GDPR compliance"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        user_data = user.to_dict()
        
        # Get sessions and reports
        sessions = self.get_user_health_sessions(user_id, limit=1000)
        reports = self.get_user_medical_reports(user_id)
        
        # Convert to dict (excluding binary data)
        sessions_data = [session.to_dict() for session in sessions]
        reports_data = [report.to_dict() for report in reports]
        
        return {
            'user': user_data,
            'sessions': sessions_data,
            'reports': reports_data,
            'export_date': datetime.utcnow().isoformat()
        }


# Singleton instance
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get singleton database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# ---- Session Management ----

def init_session_state():
    """Initialize Streamlit session state for authentication"""
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'page' not in st.session_state:
        st.session_state.page = None

def is_user_logged_in() -> bool:
    """Check if user is currently logged in"""
    return st.session_state.get('is_authenticated', False)

def get_current_user() -> Dict[str, Any]:
    """Get currently logged in user profile"""
    if not is_user_logged_in():
        return {}
    
    user_id = st.session_state.get('user_id')
    if not user_id:
        return {}
    
    user = get_database_manager().get_user_by_id(user_id)
    if not user:
        return {}
    
    return user.to_dict()


# Export main components
__all__ = [
    'DatabaseManager', 'get_database_manager', 
    'init_session_state', 'is_user_logged_in', 'get_current_user'
]
