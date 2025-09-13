"""
Medical Report Analysis Module

This module handles the analysis of uploaded medical reports including:
- Text extraction from PDFs and images
- AI-powered medical report summarization
- Key finding extraction
- Recommendation generation based on report content
"""

import io
import re
import os
import streamlit as st
from typing import Dict, List, Optional, Tuple
import base64
from datetime import datetime

# For PDF processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# For image processing and OCR
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# For advanced NLP
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class MedicalReportAnalyzer:
    """
    Comprehensive medical report analysis system
    """
    
    def __init__(self):
        """Initialize the medical report analyzer"""
        self.medical_keywords = self._load_medical_keywords()
        self.critical_findings = self._load_critical_findings()
        
        # Initialize NLTK components if available
        if NLTK_AVAILABLE:
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                self.lemmatizer = WordNetLemmatizer()
                self.stop_words = set(stopwords.words('english'))
            except:
                self.lemmatizer = None
                self.stop_words = set()
        else:
            self.lemmatizer = None
            self.stop_words = set()
    
    def _load_medical_keywords(self) -> Dict[str, List[str]]:
        """Load medical keywords for different categories"""
        return {
            'vital_signs': [
                'blood pressure', 'heart rate', 'temperature', 'respiratory rate',
                'oxygen saturation', 'pulse', 'bp', 'hr', 'temp', 'rr', 'spo2'
            ],
            'lab_values': [
                'hemoglobin', 'hematocrit', 'white blood cell', 'platelet', 'glucose',
                'cholesterol', 'triglycerides', 'creatinine', 'bun', 'sodium',
                'potassium', 'chloride', 'co2', 'albumin', 'protein', 'ast', 'alt',
                'bilirubin', 'alkaline phosphatase', 'troponin', 'bnp', 'psa'
            ],
            'symptoms': [
                'pain', 'fever', 'cough', 'shortness of breath', 'chest pain',
                'abdominal pain', 'headache', 'dizziness', 'nausea', 'vomiting',
                'diarrhea', 'constipation', 'fatigue', 'weakness', 'swelling'
            ],
            'conditions': [
                'diabetes', 'hypertension', 'heart disease', 'cancer', 'arthritis',
                'asthma', 'copd', 'depression', 'anxiety', 'obesity', 'anemia',
                'infection', 'inflammation', 'tumor', 'mass', 'lesion'
            ],
            'medications': [
                'aspirin', 'metformin', 'lisinopril', 'amlodipine', 'atorvastatin',
                'metoprolol', 'omeprazole', 'albuterol', 'insulin', 'warfarin',
                'antibiotic', 'steroid', 'nsaid', 'beta blocker', 'ace inhibitor'
            ],
            'procedures': [
                'surgery', 'biopsy', 'endoscopy', 'colonoscopy', 'ct scan',
                'mri', 'x-ray', 'ultrasound', 'ecg', 'ekg', 'echo', 'stress test'
            ]
        }
    
    def _load_critical_findings(self) -> List[str]:
        """Load patterns that indicate critical findings"""
        return [
            'acute', 'severe', 'critical', 'emergency', 'urgent', 'immediate',
            'malignant', 'cancer', 'tumor', 'mass', 'abnormal', 'elevated',
            'decreased', 'low', 'high', 'positive', 'negative', 'present',
            'absent', 'significant', 'concerning', 'suspicious'
        ]
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from uploaded PDF file"""
        if not PDF_AVAILABLE:
            return "PDF processing not available. Please install PyPDF2."
        
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\\n"
            
            return text.strip()
        
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"
    
    def extract_text_from_image(self, image_file) -> str:
        """Extract text from uploaded image file using OCR"""
        if not OCR_AVAILABLE:
            return "OCR processing not available. Please install PIL and pytesseract."
        
        try:
            image = Image.open(image_file)
            text = pytesseract.image_to_string(image)
            return text.strip()
        
        except Exception as e:
            return f"Error extracting text from image: {str(e)}"
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess the extracted text"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\\s+', ' ', text)
        text = text.strip()
        
        # Remove special characters but keep medical notation
        text = re.sub(r'[^a-zA-Z0-9\\s\\.,;:()/%-]', '', text)
        
        return text
    
    def extract_key_information(self, text: str) -> Dict[str, List[str]]:
        """Extract key medical information from the text"""
        extracted_info = {
            'vital_signs': [],
            'lab_values': [],
            'symptoms': [],
            'conditions': [],
            'medications': [],
            'procedures': [],
            'critical_findings': []
        }
        
        text_lower = text.lower()
        
        # Extract information for each category
        for category, keywords in self.medical_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Extract the sentence containing the keyword
                    sentences = text.split('.')
                    for sentence in sentences:
                        if keyword.lower() in sentence.lower():
                            extracted_info[category].append(sentence.strip())
                            break
        
        # Look for critical findings
        for critical_word in self.critical_findings:
            if critical_word in text_lower:
                # Find sentences with critical findings
                sentences = text.split('.')
                for sentence in sentences:
                    if critical_word.lower() in sentence.lower():
                        extracted_info['critical_findings'].append(sentence.strip())
        
        # Remove duplicates
        for key in extracted_info:
            extracted_info[key] = list(set(extracted_info[key]))
        
        return extracted_info
    
    def extract_numerical_values(self, text: str) -> Dict[str, str]:
        """Extract numerical values from medical reports"""
        numerical_data = {}
        
        # Common lab value patterns
        patterns = {
            'blood_pressure': r'bp:?\\s*(\\d{2,3})/?(\\d{2,3})',
            'heart_rate': r'hr:?\\s*(\\d{2,3})\\s*bpm',
            'temperature': r'temp:?\\s*(\\d{2,3}\\.?\\d*)\\s*[cf]',
            'glucose': r'glucose:?\\s*(\\d{2,4})\\s*mg/dl',
            'hemoglobin': r'h[bg]:?\\s*(\\d{1,2}\\.?\\d*)\\s*g/dl',
            'cholesterol': r'cholesterol:?\\s*(\\d{2,4})\\s*mg/dl'
        }
        
        text_lower = text.lower()
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text_lower)
            if matches:
                if key == 'blood_pressure' and len(matches[0]) == 2:
                    numerical_data[key] = f"{matches[0][0]}/{matches[0][1]}"
                elif isinstance(matches[0], tuple):
                    numerical_data[key] = matches[0][0]
                else:
                    numerical_data[key] = matches[0]
        
        return numerical_data
    
    def generate_report_summary(self, extracted_info: Dict, numerical_data: Dict) -> Dict[str, any]:
        """Generate AI-powered summary of the medical report"""
        
        summary = {
            'overall_assessment': '',
            'key_findings': [],
            'recommendations': [],
            'follow_up_needed': False,
            'urgency_level': 'Low',
            'extracted_data': {
                'vitals': numerical_data,
                'findings': extracted_info
            }
        }
        
        # Analyze critical findings
        critical_count = len(extracted_info.get('critical_findings', []))
        
        if critical_count > 0:
            summary['urgency_level'] = 'High'
            summary['follow_up_needed'] = True
            summary['overall_assessment'] = 'The report contains findings that require immediate medical attention.'
        elif len(extracted_info.get('conditions', [])) > 2:
            summary['urgency_level'] = 'Medium'
            summary['follow_up_needed'] = True
            summary['overall_assessment'] = 'The report shows multiple conditions that need ongoing monitoring.'
        else:
            summary['urgency_level'] = 'Low'
            summary['overall_assessment'] = 'The report appears to show routine findings.'
        
        # Generate key findings
        all_findings = []
        for category, findings in extracted_info.items():
            if findings and category != 'critical_findings':
                all_findings.extend([f"{category.replace('_', ' ').title()}: {finding}" 
                                   for finding in findings[:2]])  # Limit to 2 per category
        
        summary['key_findings'] = all_findings[:10]  # Limit to top 10 findings
        
        # Generate recommendations
        recommendations = []
        
        if extracted_info.get('critical_findings'):
            recommendations.append("Immediate consultation with healthcare provider recommended")
        
        if extracted_info.get('conditions'):
            recommendations.append("Continue monitoring of identified conditions")
        
        if extracted_info.get('medications'):
            recommendations.append("Review current medications with healthcare provider")
        
        if numerical_data:
            recommendations.append("Discuss laboratory results and vital signs with physician")
        
        recommendations.extend([
            "Maintain regular follow-up appointments",
            "Keep a record of symptoms and changes",
            "Follow prescribed treatment plans"
        ])
        
        summary['recommendations'] = recommendations[:8]  # Limit recommendations
        
        return summary
    
    def analyze_uploaded_report(self, uploaded_file) -> Dict[str, any]:
        """
        Main function to analyze an uploaded medical report
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Dictionary containing analysis results
        """
        
        if uploaded_file is None:
            return {'error': 'No file uploaded'}
        
        file_type = uploaded_file.type
        file_name = uploaded_file.name
        
        # Extract text based on file type
        if file_type == 'application/pdf':
            if not PDF_AVAILABLE:
                return {'error': 'PDF processing not available. Please install PyPDF2.'}
            extracted_text = self.extract_text_from_pdf(uploaded_file)
        elif file_type.startswith('image/'):
            if not OCR_AVAILABLE:
                return {'error': 'Image processing not available. Please install PIL and pytesseract.'}
            extracted_text = self.extract_text_from_image(uploaded_file)
        else:
            return {'error': f'Unsupported file type: {file_type}'}
        
        # Check if text extraction was successful
        if extracted_text.startswith('Error'):
            return {'error': extracted_text}
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            return {'error': 'Unable to extract sufficient text from the file'}
        
        # Preprocess the text
        clean_text = self.preprocess_text(extracted_text)
        
        # Extract key information
        extracted_info = self.extract_key_information(clean_text)
        
        # Extract numerical values
        numerical_data = self.extract_numerical_values(clean_text)
        
        # Generate summary
        summary = self.generate_report_summary(extracted_info, numerical_data)
        
        # Compile final analysis
        analysis_result = {
            'file_info': {
                'name': file_name,
                'type': file_type,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'extracted_text': clean_text[:1000] + '...' if len(clean_text) > 1000 else clean_text,
            'summary': summary,
            'confidence_score': self._calculate_confidence_score(extracted_info, clean_text)
        }
        
        return analysis_result
    
    def _calculate_confidence_score(self, extracted_info: Dict, text: str) -> float:
        """Calculate confidence score for the analysis"""
        score = 0.0
        
        # Base score for text length
        if len(text) > 100:
            score += 0.3
        
        # Score for extracted information
        for category, items in extracted_info.items():
            if items:
                score += 0.1
        
        # Cap at 1.0
        return min(1.0, score)
    
    def generate_health_insights(self, analysis_result: Dict) -> Dict[str, any]:
        """Generate health insights based on the report analysis"""
        
        if 'error' in analysis_result:
            return {'error': analysis_result['error']}
        
        insights = {
            'health_status_overview': '',
            'areas_of_concern': [],
            'positive_indicators': [],
            'lifestyle_recommendations': [],
            'follow_up_suggestions': [],
            'preventive_measures': []
        }
        
        summary = analysis_result.get('summary', {})
        urgency = summary.get('urgency_level', 'Low')
        
        # Generate health status overview
        if urgency == 'High':
            insights['health_status_overview'] = "Your report contains findings that require prompt medical attention. Please consult with your healthcare provider immediately."
        elif urgency == 'Medium':
            insights['health_status_overview'] = "Your report shows some conditions that need ongoing monitoring and management."
        else:
            insights['health_status_overview'] = "Your report appears to show routine findings, but regular monitoring is still important."
        
        # Analyze findings for concerns and positive indicators
        findings = summary.get('extracted_data', {}).get('findings', {})
        
        # Areas of concern
        if findings.get('critical_findings'):
            insights['areas_of_concern'].extend(findings['critical_findings'])
        
        if findings.get('conditions'):
            insights['areas_of_concern'].extend([f"Diagnosed condition: {cond}" for cond in findings['conditions']])
        
        # Positive indicators (if minimal concerning findings)
        if len(insights['areas_of_concern']) == 0:
            insights['positive_indicators'] = [
                "No immediate concerning findings identified",
                "Report suggests stable health status",
                "Continue current health maintenance practices"
            ]
        
        # Lifestyle recommendations
        insights['lifestyle_recommendations'] = [
            "Maintain a balanced, nutritious diet",
            "Engage in regular physical activity as appropriate",
            "Ensure adequate sleep and stress management",
            "Stay hydrated and avoid harmful substances",
            "Follow prescribed medication regimens"
        ]
        
        # Follow-up suggestions
        insights['follow_up_suggestions'] = [
            "Schedule regular check-ups with your primary care physician",
            "Monitor and track any symptoms or changes",
            "Keep all medical reports organized for future reference",
            "Discuss any concerns with your healthcare team"
        ]
        
        # Preventive measures
        insights['preventive_measures'] = [
            "Maintain healthy lifestyle habits",
            "Stay up to date with recommended screenings",
            "Practice good hygiene and infection prevention",
            "Monitor vital signs regularly if advised",
            "Follow vaccination schedules as recommended"
        ]
        
        return insights
    
    def create_report_visualization_data(self, analysis_result: Dict) -> Dict[str, any]:
        """Create data for visualizing the report analysis"""
        
        if 'error' in analysis_result:
            return {'error': analysis_result['error']}
        
        viz_data = {
            'urgency_gauge': 0,
            'findings_count': {},
            'confidence_score': 0,
            'timeline_data': []
        }
        
        summary = analysis_result.get('summary', {})
        
        # Urgency gauge data
        urgency_mapping = {'Low': 25, 'Medium': 65, 'High': 90}
        viz_data['urgency_gauge'] = urgency_mapping.get(summary.get('urgency_level', 'Low'), 25)
        
        # Findings count
        findings = summary.get('extracted_data', {}).get('findings', {})
        for category, items in findings.items():
            if items:
                viz_data['findings_count'][category.replace('_', ' ').title()] = len(items)
        
        # Confidence score
        viz_data['confidence_score'] = analysis_result.get('confidence_score', 0) * 100
        
        return viz_data


def create_report_upload_interface():
    """Create the Streamlit interface for medical report upload and analysis"""
    
    st.markdown('<div class="sub-header">📋 Medical Report Analysis</div>', unsafe_allow_html=True)
    
    st.markdown("""
    **Upload your medical reports to get AI-powered analysis and insights.**
    
    Supported formats:
    - PDF documents
    - Image files (JPG, PNG, TIFF)
    
    ⚠️ **Privacy Notice**: Reports are processed locally and not stored permanently.
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a medical report file",
        type=['pdf', 'jpg', 'jpeg', 'png', 'tiff'],
        help="Upload a PDF or image file containing your medical report"
    )
    
    if uploaded_file is not None:
        # Display file information
        st.info(f"📄 **File:** {uploaded_file.name} ({uploaded_file.type})")
        
        # Analyze button
        if st.button("🔬 Analyze Report", type="primary"):
            with st.spinner("Analyzing your medical report..."):
                
                # Initialize analyzer
                analyzer = MedicalReportAnalyzer()
                
                # Analyze the report
                analysis_result = analyzer.analyze_uploaded_report(uploaded_file)
                
                if 'error' in analysis_result:
                    st.error(f"❌ Analysis Error: {analysis_result['error']}")
                    return
                
                # Generate insights
                insights = analyzer.generate_health_insights(analysis_result)
                
                # Create visualization data
                viz_data = analyzer.create_report_visualization_data(analysis_result)
                
                # Store results in session state
                st.session_state['report_analysis'] = analysis_result
                st.session_state['report_insights'] = insights
                st.session_state['report_viz_data'] = viz_data
            
            st.success("✅ Report analysis completed!")
            
            # Display results immediately
            display_report_analysis_results()
    
    # Display existing results if available
    elif 'report_analysis' in st.session_state:
        st.info("📊 Previous analysis results available below")
        display_report_analysis_results()


def display_report_analysis_results():
    """Display the analysis results in organized tabs"""
    
    if 'report_analysis' not in st.session_state:
        return
    
    analysis_result = st.session_state['report_analysis']
    insights = st.session_state.get('report_insights', {})
    viz_data = st.session_state.get('report_viz_data', {})
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Summary", "🔍 Detailed Analysis", "📊 Visual Insights", "💡 Health Recommendations"
    ])
    
    with tab1:
        st.markdown("### 📊 Report Summary")
        
        # File information
        file_info = analysis_result.get('file_info', {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("File Name", file_info.get('name', 'Unknown'))
        with col2:
            st.metric("Analysis Date", file_info.get('analysis_date', 'Unknown'))
        with col3:
            confidence = analysis_result.get('confidence_score', 0) * 100
            st.metric("Confidence Score", f"{confidence:.1f}%")
        
        # Urgency assessment
        summary = analysis_result.get('summary', {})
        urgency = summary.get('urgency_level', 'Low')
        
        if urgency == 'High':
            st.error(f"🔴 **Urgency Level: {urgency}**")
        elif urgency == 'Medium':
            st.warning(f"🟡 **Urgency Level: {urgency}**")
        else:
            st.success(f"🟢 **Urgency Level: {urgency}**")
        
        st.write(f"**Assessment:** {summary.get('overall_assessment', 'No assessment available')}")
        
        # Key findings
        key_findings = summary.get('key_findings', [])
        if key_findings:
            st.markdown("### 🔍 Key Findings")
            for i, finding in enumerate(key_findings[:5], 1):
                st.write(f"{i}. {finding}")
    
    with tab2:
        st.markdown("### 🔍 Detailed Analysis")
        
        # Extracted text preview
        with st.expander("📄 Extracted Text Preview"):
            extracted_text = analysis_result.get('extracted_text', '')
            st.text_area("Report Content", extracted_text, height=200, disabled=True)
        
        # Categorized findings
        findings = summary.get('extracted_data', {}).get('findings', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🩺 Medical Information")
            
            for category in ['vital_signs', 'lab_values', 'procedures']:
                if findings.get(category):
                    st.markdown(f"**{category.replace('_', ' ').title()}:**")
                    for item in findings[category][:3]:
                        st.write(f"• {item}")
        
        with col2:
            st.markdown("#### 🏥 Clinical Information")
            
            for category in ['symptoms', 'conditions', 'medications']:
                if findings.get(category):
                    st.markdown(f"**{category.replace('_', ' ').title()}:**")
                    for item in findings[category][:3]:
                        st.write(f"• {item}")
        
        # Critical findings
        if findings.get('critical_findings'):
            st.markdown("### 🚨 Critical Findings")
            for finding in findings['critical_findings']:
                st.error(f"⚠️ {finding}")
        
        # Numerical data
        numerical_data = summary.get('extracted_data', {}).get('vitals', {})
        if numerical_data:
            st.markdown("### 📊 Numerical Values")
            cols = st.columns(min(len(numerical_data), 4))
            for i, (key, value) in enumerate(numerical_data.items()):
                with cols[i % 4]:
                    st.metric(key.replace('_', ' ').title(), value)
    
    with tab3:
        st.markdown("### 📊 Visual Insights")
        
        if viz_data and 'error' not in viz_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # Urgency gauge
                st.markdown("#### 🚨 Urgency Level")
                urgency_score = viz_data.get('urgency_gauge', 0)
                st.progress(urgency_score / 100)
                
                # Confidence score
                st.markdown("#### 🎯 Analysis Confidence")
                confidence = viz_data.get('confidence_score', 0)
                st.progress(confidence / 100)
            
            with col2:
                # Findings distribution
                findings_count = viz_data.get('findings_count', {})
                if findings_count:
                    st.markdown("#### 📋 Findings Distribution")
                    for category, count in findings_count.items():
                        st.write(f"**{category}:** {count} items")
        else:
            st.info("Visual insights will appear here after successful report analysis.")
    
    with tab4:
        st.markdown("### 💡 Health Recommendations")
        
        if insights and 'error' not in insights:
            # Health status overview
            st.markdown("#### 🏥 Health Status Overview")
            st.info(insights.get('health_status_overview', 'No overview available'))
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Areas of concern
                concerns = insights.get('areas_of_concern', [])
                if concerns:
                    st.markdown("#### ⚠️ Areas of Concern")
                    for concern in concerns[:5]:
                        st.warning(f"• {concern}")
                
                # Positive indicators
                positives = insights.get('positive_indicators', [])
                if positives:
                    st.markdown("#### ✅ Positive Indicators")
                    for positive in positives:
                        st.success(f"• {positive}")
            
            with col2:
                # Lifestyle recommendations
                lifestyle_recs = insights.get('lifestyle_recommendations', [])
                if lifestyle_recs:
                    st.markdown("#### 🏃‍♂️ Lifestyle Recommendations")
                    for rec in lifestyle_recs:
                        st.write(f"• {rec}")
                
                # Follow-up suggestions
                followup = insights.get('follow_up_suggestions', [])
                if followup:
                    st.markdown("#### 📅 Follow-up Suggestions")
                    for suggestion in followup[:4]:
                        st.write(f"• {suggestion}")
            
            # Preventive measures
            preventive = insights.get('preventive_measures', [])
            if preventive:
                st.markdown("#### 🛡️ Preventive Measures")
                for measure in preventive:
                    st.write(f"• {measure}")
        
        # Medical disclaimer
        st.markdown("---")
        st.markdown("### ⚠️ Important Medical Disclaimer")
        st.warning("""
        **This analysis is for informational purposes only and should not replace professional medical advice.**
        
        - Always consult with qualified healthcare professionals for medical decisions
        - This tool cannot diagnose medical conditions
        - Emergency situations require immediate medical attention
        - Keep original reports for your healthcare providers
        """)


# Export the main functions
__all__ = ['MedicalReportAnalyzer', 'create_report_upload_interface', 'display_report_analysis_results']
