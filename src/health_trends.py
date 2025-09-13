"""
Health Trends Dashboard for Health Analyzer

Simplified version without user authentication.
This module provides basic trend visualization capabilities.
"""

import streamlit as st


class HealthTrendsDashboard:
    """Simplified health trends dashboard without user authentication"""
    
    def __init__(self):
        """Initialize health trends dashboard"""
        pass
    
    def show_health_trends_dashboard(self):
        """Display simplified health trends dashboard"""
        st.markdown("## 📈 Health Trends Dashboard")
        st.info("📊 **Health trends tracking is currently disabled.** The app now focuses on symptom analysis without user accounts.")
        
        st.markdown("""
        ### 🔧 **What Changed:**
        - Removed user authentication system
        - Disabled historical data tracking
        - Focus on individual symptom analysis sessions
        
        ### 🎯 **Current Features:**
        - Real-time symptom analysis
        - Disease prediction with confidence scores
        - Personalized health recommendations
        - Medical report upload and analysis
        - Visual analysis charts
        - PDF report generation
        
        ### 💡 **How to Use:**
        1. Use the sidebar to enter your symptoms
        2. Get instant AI-powered analysis
        3. Review recommendations and insights
        4. Export your results for personal records
        """)


# Export main components
__all__ = ['HealthTrendsDashboard']
