"""
Database Models for Health Analyzer with User Authentication

This module defines all database models including user authentication,
health sessions, and medical reports.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    health_sessions = relationship("HealthSession", back_populates="user", cascade="all, delete-orphan")
    medical_reports = relationship("MedicalReport", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert user to dictionary (excluding password_hash)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class HealthSession(Base):
    """Health analysis session model"""
    __tablename__ = 'health_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    input_symptoms = Column(Text, nullable=False)
    input_method = Column(String(50), default='text_input')
    predictions = Column(Text, nullable=True)  # JSON string of predictions
    recommendations = Column(Text, nullable=True)  # JSON string of recommendations
    top_prediction = Column(String(200), nullable=True)
    top_confidence = Column(Float, nullable=True)
    severity_level = Column(String(20), nullable=True)
    processing_time = Column(Float, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="health_sessions")
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_date': self.session_date.isoformat() if self.session_date else None,
            'input_symptoms': self.input_symptoms,
            'input_method': self.input_method,
            'top_prediction': self.top_prediction,
            'top_confidence': self.top_confidence,
            'severity_level': self.severity_level,
            'processing_time': self.processing_time
        }

class MedicalReport(Base):
    """Medical report storage model"""
    __tablename__ = 'medical_reports'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_data = Column(LargeBinary, nullable=True)  # Store file content
    extracted_text = Column(Text, nullable=True)
    analysis_results = Column(Text, nullable=True)  # JSON string of analysis
    urgency_level = Column(String(20), nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="medical_reports")
    
    def to_dict(self):
        """Convert report to dictionary (excluding binary data)"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'urgency_level': self.urgency_level,
            'confidence_score': self.confidence_score
        }

# Database configuration (kept for potential future use)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///health_analyzer.db')

def create_engine_and_session():
    """Create database engine and session factory"""
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

def create_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def drop_tables(engine):
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All database tables dropped")

# Export main components
__all__ = [
    'Base', 'create_engine_and_session', 'create_tables', 'drop_tables', 'DATABASE_URL'
]
