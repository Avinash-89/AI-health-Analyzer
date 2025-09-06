import streamlit as st
import sys
import os
import time
from datetime import datetime
import pandas as pd
import plotly.express as px

# Add src and auth directories to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'auth'))

# Import authentication system
from auth.auth import AuthManager, create_auth_sidebar

from prediction_engine import HealthPredictor
from recommendation_system import HealthRecommendationSystem
from visualization import HealthVisualization
from pdf_generator import HealthReportGenerator
from report_analyzer import create_report_upload_interface, display_report_analysis_results, MedicalReportAnalyzer

# Remove authentication imports - keeping only health_trends for dashboard
from health_trends import HealthTrendsDashboard

# Page configuration
st.set_page_config(
    page_title="AI Health Analyzer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .severe-warning {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .mild-info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .footer {
        text-align: center;
        color: #6c757d;
        font-style: italic;
        margin-top: 3rem;
        padding: 2rem;
        border-top: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'predictions' not in st.session_state:
    st.session_state.predictions = None
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'user_symptoms' not in st.session_state:
    st.session_state.user_symptoms = ""

@st.cache_resource
def load_models():
    """Load the prediction models and systems"""
    try:
        predictor = HealthPredictor()
        rec_system = HealthRecommendationSystem()
        viz_system = HealthVisualization()
        return predictor, rec_system, viz_system
    except Exception as e:
        st.error(f"Error loading models: {str(e)}")
        return None, None, None

def main():
    # Initialize authentication manager
    auth_manager = AuthManager()
    
    # Check authentication
    if not auth_manager.is_authenticated():
        # Show authentication interface
        st.markdown('<div class="main-header">🏥 AI-Powered Health Analyzer</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; color: #6c757d; margin-bottom: 2rem;">
            <p><strong>Intelligent Symptom Analysis & Health Recommendations</strong></p>
            <p>🔒 <em>Please log in to access the health analyzer.</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        auth_manager.show_auth_interface()
        return
    
    # Load models
    predictor, rec_system, viz_system = load_models()
    
    if not all([predictor, rec_system, viz_system]):
        st.error("Failed to load the health analysis system. Please check the configuration.")
        return
    
    # Main header
    st.markdown('<div class="main-header">🏥 AI-Powered Health Analyzer</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; color: #6c757d; margin-bottom: 2rem;">
        <p><strong>Intelligent Symptom Analysis & Health Recommendations</strong></p>
        <p>⚠️ <em>This tool is for informational purposes only and does not replace professional medical advice.</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication sidebar
    create_auth_sidebar()
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 Health Analysis")
        
        # Symptom input methods
        input_method = st.selectbox(
            "Choose input method:",
            ["Text Input", "Symptom Checklist", "Voice Input (Experimental)"]
        )
        
        if input_method == "Text Input":
            user_symptoms = st.text_area(
                "Enter your symptoms (separated by commas):",
                placeholder="e.g., fever, cough, headache, fatigue",
                height=100,
                value=st.session_state.user_symptoms
            )
        
        elif input_method == "Symptom Checklist":
            st.write("**Common Symptoms:**")
            symptom_options = [
                "fever", "cough", "headache", "fatigue", "sore throat",
                "runny nose", "body ache", "chills", "nausea", "vomiting",
                "diarrhea", "stomach pain", "chest pain", "difficulty breathing",
                "dizziness", "joint pain", "muscle pain", "skin rash"
            ]
            
            selected_symptoms = []
            for symptom in symptom_options:
                if st.checkbox(symptom.title()):
                    selected_symptoms.append(symptom)
            
            user_symptoms = ", ".join(selected_symptoms)
        
        else:  # Voice Input
            st.write("**Voice Input (Experimental)**")
            if st.button("🎤 Record Symptoms"):
                st.info("Voice input feature coming soon!")
                user_symptoms = st.text_input("For now, please type your symptoms:")
            else:
                user_symptoms = ""
        
        # Analysis button
        if st.button("🔬 Analyze Symptoms", type="primary"):
            if (user_symptoms or "").strip():
                st.session_state.user_symptoms = user_symptoms
                
                with st.spinner("Analyzing your symptoms..."):
                    # Get predictions
                    if predictor is not None:
                        predictions = predictor.hybrid_prediction(user_symptoms, top_n=3)
                        st.session_state.predictions = predictions
                    else:
                        st.error("Prediction engine is not available. Please reload the page or check the configuration.")
                        st.session_state.predictions = None
                    
                    # Generate recommendations
                    if rec_system is not None and st.session_state.predictions is not None:
                        recommendations = rec_system.generate_comprehensive_recommendations(
                            st.session_state.predictions, user_symptoms
                        )
                        st.session_state.recommendations = recommendations
                    else:
                        st.session_state.recommendations = None
                
                st.success("Analysis complete!")
            else:
                st.error("Please enter your symptoms first.")
        
        # Clear results button
        if st.button("🗑️ Clear Results"):
            st.session_state.predictions = None
            st.session_state.recommendations = None
            st.session_state.user_symptoms = ""
            st.rerun()
    
    # Main content area
    if st.session_state.predictions and st.session_state.recommendations:
        predictions = st.session_state.predictions
        recommendations = st.session_state.recommendations
        
        # Display results in tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🎯 Predictions", "📋 Recommendations", "📊 Analysis", "📈 Insights", "📄 Report", "📋 Report Upload"
        ])
        
        with tab1:
            st.markdown('<div class="sub-header">Disease Predictions</div>', unsafe_allow_html=True)
            
            if predictions:
                # Display top prediction prominently
                top_pred = predictions[0]
                severity = top_pred['severity']
                
                # Choose styling based on severity
                if severity == 'Severe':
                    st.markdown(f'<div class="severe-warning">', unsafe_allow_html=True)
                    st.error(f"🔴 **TOP PREDICTION: {top_pred['disease']}** ({top_pred['confidence']:.1f}% confidence)")
                elif severity == 'Moderate':
                    st.markdown(f'<div class="warning-box">', unsafe_allow_html=True)
                    st.warning(f"🟡 **TOP PREDICTION: {top_pred['disease']}** ({top_pred['confidence']:.1f}% confidence)")
                else:
                    st.markdown(f'<div class="mild-info">', unsafe_allow_html=True)
                    st.info(f"🟢 **TOP PREDICTION: {top_pred['disease']}** ({top_pred['confidence']:.1f}% confidence)")
                
                st.write(f"**Description:** {top_pred['description']}")
                st.write(f"**Severity Level:** {severity}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Display all predictions in columns
                st.markdown("### All Predictions:")
                cols = st.columns(len(predictions))
                
                for i, (pred, col) in enumerate(zip(predictions, cols)):
                    with col:
                        st.markdown(f"**{i+1}. {pred['disease']}**")
                        st.metric("Confidence", f"{pred['confidence']:.1f}%")
                        st.write(f"Severity: {pred['severity']}")
                        st.write(f"*{pred['description']}*")
            else:
                st.warning("No predictions available.")
        
        with tab2:
            st.markdown('<div class="sub-header">Health Recommendations</div>', unsafe_allow_html=True)
            
            if recommendations and 'error' not in recommendations:
                # Severity assessment
                severity_info = recommendations['severity_assessment']
                severity_level = severity_info['overall_severity']
                
                if severity_level == 'Severe':
                    st.error(f"🔴 **{severity_info['urgency']}**")
                elif severity_level == 'Moderate':
                    st.warning(f"🟡 **{severity_info['urgency']}**")
                else:
                    st.success(f"🟢 **{severity_info['urgency']}**")
                
                st.write(f"**Recommendation:** {severity_info['recommendation']}")
                st.write(f"**Timeframe:** {severity_info['timeframe']}")
                
                # Organize recommendations in columns
                col1, col2 = st.columns(2)
                
                with col1:
                    # Lifestyle recommendations
                    if recommendations.get('lifestyle_recommendations'):
                        st.markdown("### 🏃‍♂️ Lifestyle Recommendations")
                        for rec in recommendations['lifestyle_recommendations'][:6]:
                            st.write(f"• {rec}")
                    
                    # Self-care tips
                    if recommendations.get('self_care_tips'):
                        st.markdown("### 💆‍♀️ Self-Care Tips")
                        for tip in recommendations['self_care_tips'][:4]:
                            st.write(f"• {tip}")
                
                with col2:
                    # Dietary recommendations
                    if recommendations.get('dietary_recommendations'):
                        st.markdown("### 🍽️ Dietary Recommendations")
                        for rec in recommendations['dietary_recommendations'][:5]:
                            st.write(f"• {rec}")
                    
                    # Follow-up care
                    if recommendations.get('followup_recommendations'):
                        st.markdown("### 📅 Follow-up Care")
                        for followup in recommendations['followup_recommendations']:
                            st.write(f"• {followup}")
                
                # Warning signs
                if recommendations.get('warning_signs'):
                    st.markdown("### 🚨 Seek Immediate Medical Attention If:")
                    warning_cols = st.columns(2)
                    for i, warning in enumerate(recommendations['warning_signs'][:6]):
                        with warning_cols[i % 2]:
                            st.write(f"• {warning}")
                
                # Medical disclaimer
                disclaimer = recommendations.get('disclaimer', {})
                st.markdown("---")
                st.markdown(f"### {disclaimer.get('title', '⚠️ Medical Disclaimer')}")
                for content in disclaimer.get('content', []):
                    st.write(f"• {content}")
        
        with tab3:
            st.markdown('<div class="sub-header">Visual Analysis</div>', unsafe_allow_html=True)
            
            # Create visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Confidence bar chart
                st.markdown("#### Disease Confidence Levels")
                bar_fig = viz_system.create_confidence_bar_chart(predictions)
                if bar_fig:
                    st.pyplot(bar_fig)
                
                # Pie chart
                st.markdown("#### Probability Distribution")
                pie_fig = viz_system.create_confidence_pie_chart(predictions)
                if pie_fig:
                    st.pyplot(pie_fig)
            
            with col2:
                # Interactive gauge for top prediction
                st.markdown("#### Top Prediction Confidence")
                gauge_fig = viz_system.create_confidence_gauge(predictions[0])
                if gauge_fig:
                    st.plotly_chart(gauge_fig, use_container_width=True)
                
                # Severity distribution
                st.markdown("#### Severity Analysis")
                severity_fig = viz_system.create_severity_distribution_chart(predictions)
                if severity_fig:
                    st.pyplot(severity_fig)
            
            # Symptom Analysis Overview
            st.markdown("#### Your Symptoms Analysis")
            
            # Create symptom display
            all_symptoms = set()
            
            # Add user symptoms
            if st.session_state.user_symptoms:
                for symptom in st.session_state.user_symptoms.replace(',', ' ').split():
                    clean = symptom.strip().title()
                    if clean and len(clean) > 2:
                        all_symptoms.add(clean)
            
            # Add symptoms from predictions
            for pred in predictions:
                if 'matched_symptoms' in pred:
                    for symptom in pred['matched_symptoms'].split(';'):
                        clean = symptom.strip().title()
                        if clean and len(clean) > 2:
                            all_symptoms.add(clean)
            
            symptoms_list = sorted(list(all_symptoms))
            
            if symptoms_list:
                # Display in a colorful grid
                cols_per_row = 3
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
                
                for i in range(0, len(symptoms_list), cols_per_row):
                    cols = st.columns(cols_per_row)
                    row_symptoms = symptoms_list[i:i+cols_per_row]
                    for j, symptom in enumerate(row_symptoms):
                        with cols[j]:
                            color = colors[(i + j) % len(colors)]
                            st.markdown(f'''
                            <div style="background: {color}; color: white; padding: 15px; 
                                        border-radius: 10px; text-align: center; margin: 5px; 
                                        font-weight: bold; font-size: 14px;
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                {symptom}
                            </div>''', unsafe_allow_html=True)
            else:
                st.info("Enter symptoms above to see your symptom analysis")
        
        with tab4:
            st.markdown('<div class="sub-header">Detailed Insights</div>', unsafe_allow_html=True)
            
            # Interactive confidence chart
            interactive_fig = viz_system.create_interactive_confidence_chart(predictions)
            if interactive_fig:
                st.plotly_chart(interactive_fig, use_container_width=True)
            
            # Comparison chart
            comparison_fig = viz_system.create_prediction_comparison_chart(predictions)
            if comparison_fig:
                st.plotly_chart(comparison_fig, use_container_width=True)
            
            # Detailed prediction information
            st.markdown("### 📋 Detailed Prediction Information")
            for i, pred in enumerate(predictions, 1):
                with st.expander(f"{i}. {pred['disease']} - {pred['confidence']:.1f}% confidence"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Severity:** {pred['severity']}")
                        st.write(f"**Description:** {pred['description']}")
                    with col2:
                        st.write(f"**Precautions:** {pred['precautions']}")
                        st.write(f"**Diet Recommendations:** {pred['diet_recommendations']}")
        
        with tab5:
            st.markdown('<div class="sub-header">Health Report</div>', unsafe_allow_html=True)
            
            # Report summary
            report_data = {
                "Analysis Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Input Symptoms": st.session_state.user_symptoms,
                "Top Prediction": f"{predictions[0]['disease']} ({predictions[0]['confidence']:.1f}%)",
                "Severity Level": predictions[0]['severity'],
                "Urgency": recommendations['severity_assessment']['urgency']
            }
            
            st.markdown("### 📊 Report Summary")
            for key, value in report_data.items():
                st.write(f"**{key}:** {value}")
            
            # Export functionality
            st.markdown("### 📥 Export Options")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Generate PDF Report"):
                    with st.spinner("Generating PDF report..."):
                        try:
                            pdf_generator = HealthReportGenerator()
                            pdf_buffer = pdf_generator.generate_pdf_buffer(
                                st.session_state.user_symptoms, 
                                predictions, 
                                recommendations
                            )
                            
                            st.download_button(
                                label="⬇️ Download PDF Report",
                                data=pdf_buffer.getvalue(),
                                file_name=f"health_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            )
                            st.success("PDF report generated successfully!")
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")
            
            with col2:
                if st.button("📧 Email Report"):
                    st.info("Email functionality coming soon!")
            
            with col3:
                # CSV export of predictions
                df = pd.DataFrame(predictions)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📊 Download CSV",
                    data=csv,
                    file_name=f"health_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with tab6:
            # Medical Report Upload and Analysis
            create_report_upload_interface()
    
    else:
        # Welcome screen with option to access report upload
        st.markdown("## 👋 Welcome to AI Health Analyzer")
        
        # Main feature tabs on welcome screen
        welcome_tab1, welcome_tab2 = st.tabs([
            "🎯 Symptom Analysis", "📋 Medical Report Upload"
        ])
        
        with welcome_tab1:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                ### 🎯 **Symptom Analysis**
                - Advanced AI-powered symptom matching
                - Multiple prediction algorithms
                - Confidence scoring for each diagnosis
                """)
            
            with col2:
                st.markdown("""
                ### 📋 **Health Recommendations**
                - Personalized lifestyle advice
                - Dietary recommendations
                - Self-care tips and precautions
                """)
            
            with col3:
                st.markdown("""
                ### 📊 **Visual Insights**
                - Interactive charts and graphs
                - Severity analysis
                - Comprehensive health reports
                """)
        
        with welcome_tab2:
            # Medical Report Upload Feature
            create_report_upload_interface()
        
        st.markdown("---")
        st.markdown("""
        ### 🚀 **Key Features:**
        
        - **Multi-disease Prediction**: Get top 2-3 possible diagnoses with confidence scores
        - **Severity Assessment**: Understand urgency levels (Mild, Moderate, Severe)
        - **Medical Report Analysis**: Upload and analyze PDF or image medical reports with AI
        - **Comprehensive Recommendations**: Lifestyle, diet, and self-care suggestions
        - **Visual Analytics**: Charts showing disease probability and risk factors
        - **Professional Disclaimer**: Clear guidance on when to seek medical care
        
        ### 📝 **How to Use:**
        
        **For Symptom Analysis:**
        1. Enter your symptoms in the sidebar
        2. Choose between text input or symptom checklist
        3. Click "Analyze Symptoms" to get predictions
        4. Review results across different tabs
        5. Export your health report for records
        
        **For Medical Report Analysis:**
        1. Go to the "Medical Report Upload" tab
        2. Upload your medical report (PDF or image)
        3. Click "Analyze Report" to get AI-powered insights
        4. Review the comprehensive analysis and recommendations
        """)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>🏥 <strong>AI Health Analyzer</strong> | Powered by Machine Learning & Medical Knowledge</p>
        <p>⚠️ <strong>Important:</strong> This system is for educational and informational purposes only. 
        Always consult with qualified healthcare professionals for proper medical advice and treatment.</p>
        <p>🔬 Built with Streamlit, scikit-learn, and advanced NLP techniques</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
