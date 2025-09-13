from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, black, red, orange, green
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib import colors
import io
import base64
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import tempfile
import os

class HealthReportGenerator:
    def __init__(self):
        """Initialize the PDF Health Report Generator"""
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
        # Color scheme
        self.colors = {
            'primary': HexColor('#1f77b4'),
            'severe': HexColor('#dc3545'),
            'moderate': HexColor('#ffc107'),
            'mild': HexColor('#28a745'),
            'light_gray': HexColor('#f8f9fa'),
            'dark_gray': HexColor('#6c757d')
        }
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Main title style
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#1f77b4'),
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=HexColor('#34495e'),
            fontName='Helvetica-Bold'
        ))
        
        # Warning style
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            textColor=HexColor('#dc3545'),
            fontName='Helvetica-Bold'
        ))
        
        # Info style
        self.styles.add(ParagraphStyle(
            name='Info',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            textColor=HexColor('#6c757d'),
            fontName='Helvetica'
        ))
    
    def create_header_section(self, story):
        """Create the header section of the report"""
        # Main title
        title = Paragraph("AI Health Analysis Report", self.styles['MainTitle'])
        story.append(title)
        
        # Subtitle
        subtitle = Paragraph("Intelligent Symptom Analysis & Health Recommendations", self.styles['Info'])
        story.append(subtitle)
        
        # Horizontal line
        line = HRFlowable(width="100%", thickness=2, color=self.colors['primary'])
        story.append(line)
        story.append(Spacer(1, 20))
    
    def create_summary_section(self, story, user_symptoms, predictions, recommendations):
        """Create the executive summary section"""
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Generate current date
        current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # Summary data
        summary_data = [
            ["Report Generated:", current_date],
            ["Symptoms Analyzed:", user_symptoms],
        ]
        
        if predictions:
            top_prediction = predictions[0]
            summary_data.extend([
                ["Top Prediction:", f"{top_prediction['disease']} ({top_prediction['confidence']:.1f}% confidence)"],
                ["Severity Level:", top_prediction['severity']],
                ["Urgency:", recommendations['severity_assessment']['urgency'] if recommendations else "N/A"]
            ])
        
        # Create table
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, self.colors['light_gray']]),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
    
    def create_predictions_section(self, story, predictions):
        """Create the disease predictions section"""
        if not predictions:
            story.append(Paragraph("Disease Predictions", self.styles['SectionHeader']))
            story.append(Paragraph("No predictions available.", self.styles['Normal']))
            return
        
        story.append(Paragraph("Disease Predictions", self.styles['SectionHeader']))
        
        # Top prediction highlight
        top_pred = predictions[0]
        severity_color = self.colors['severe'] if top_pred['severity'] == 'Severe' else \
                        self.colors['moderate'] if top_pred['severity'] == 'Moderate' else \
                        self.colors['mild']
        
        top_prediction_style = ParagraphStyle(
            'TopPrediction',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=severity_color,
            fontName='Helvetica-Bold',
            spaceAfter=12
        )
        
        story.append(Paragraph(
            f"🎯 Primary Diagnosis: {top_pred['disease']} ({top_pred['confidence']:.1f}% confidence)",
            top_prediction_style
        ))
        
        story.append(Paragraph(f"Description: {top_pred['description']}", self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # All predictions table
        story.append(Paragraph("Complete Analysis Results:", self.styles['SubsectionHeader']))
        
        pred_data = [["Rank", "Disease", "Confidence", "Severity", "Description"]]
        
        for i, pred in enumerate(predictions, 1):
            pred_data.append([
                str(i),
                pred['disease'],
                f"{pred['confidence']:.1f}%",
                pred['severity'],
                pred['description'][:50] + "..." if len(pred['description']) > 50 else pred['description']
            ])
        
        pred_table = Table(pred_data, colWidths=[0.5*inch, 1.5*inch, 1*inch, 1*inch, 2.5*inch])
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors['light_gray']]),
        ]))
        
        story.append(pred_table)
        story.append(Spacer(1, 20))
    
    def create_recommendations_section(self, story, recommendations):
        """Create the health recommendations section"""
        if not recommendations or 'error' in recommendations:
            story.append(Paragraph("Health Recommendations", self.styles['SectionHeader']))
            story.append(Paragraph("No recommendations available.", self.styles['Normal']))
            return
        
        story.append(Paragraph("Health Recommendations", self.styles['SectionHeader']))
        
        # Severity assessment
        severity_info = recommendations['severity_assessment']
        severity_style = ParagraphStyle(
            'SeverityWarning',
            parent=self.styles['Warning'],
            fontSize=13,
            spaceAfter=15
        )
        
        severity_text = f"⚠️ {severity_info['urgency']}: {severity_info['recommendation']}"
        story.append(Paragraph(severity_text, severity_style))
        story.append(Paragraph(f"Timeframe: {severity_info['timeframe']}", self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Lifestyle recommendations
        if recommendations.get('lifestyle_recommendations'):
            story.append(Paragraph("Lifestyle Recommendations:", self.styles['SubsectionHeader']))
            for rec in recommendations['lifestyle_recommendations'][:8]:
                story.append(Paragraph(f"• {rec.replace('⚠️', '').strip()}", self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Dietary recommendations
        if recommendations.get('dietary_recommendations'):
            story.append(Paragraph("Dietary Recommendations:", self.styles['SubsectionHeader']))
            for rec in recommendations['dietary_recommendations'][:6]:
                story.append(Paragraph(f"• {rec.replace('🍽️', '').strip()}", self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Self-care tips
        if recommendations.get('self_care_tips'):
            story.append(Paragraph("Self-Care Tips:", self.styles['SubsectionHeader']))
            for tip in recommendations['self_care_tips'][:5]:
                story.append(Paragraph(f"• {tip}", self.styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Warning signs
        if recommendations.get('warning_signs'):
            story.append(Paragraph("Seek Immediate Medical Attention If:", self.styles['SubsectionHeader']))
            warning_style = ParagraphStyle(
                'WarningList',
                parent=self.styles['Normal'],
                textColor=self.colors['severe'],
                fontSize=11
            )
            for warning in recommendations['warning_signs'][:6]:
                story.append(Paragraph(f"• {warning.replace('🚨', '').strip()}", warning_style))
            story.append(Spacer(1, 12))
        
        # Follow-up care
        if recommendations.get('followup_recommendations'):
            story.append(Paragraph("Follow-up Care:", self.styles['SubsectionHeader']))
            for followup in recommendations['followup_recommendations']:
                story.append(Paragraph(f"• {followup}", self.styles['Normal']))
            story.append(Spacer(1, 20))
    
    def create_chart_section(self, story, predictions):
        """Create a text-based analysis section"""
        if not predictions:
            return
        
        story.append(Paragraph("Confidence Analysis", self.styles['SectionHeader']))
        
        # Create a text-based confidence analysis table
        analysis_data = [["Disease", "Confidence", "Severity", "Risk Level"]]
        
        for pred in predictions:
            confidence = pred['confidence']
            severity = pred['severity']
            
            # Determine risk level based on confidence and severity
            if severity == 'Severe' and confidence > 30:
                risk_level = "High"
            elif severity == 'Moderate' and confidence > 50:
                risk_level = "Medium-High"
            elif confidence > 60:
                risk_level = "Medium"
            else:
                risk_level = "Low-Medium"
            
            analysis_data.append([
                pred['disease'],
                f"{confidence:.1f}%",
                severity,
                risk_level
            ])
        
        # Create analysis table
        analysis_table = Table(analysis_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        analysis_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors['light_gray']]),
        ]))
        
        story.append(analysis_table)
        story.append(Spacer(1, 20))
    
    def create_disclaimer_section(self, story, recommendations):
        """Create the medical disclaimer section"""
        story.append(Paragraph("Important Medical Disclaimer", self.styles['SectionHeader']))
        
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.colors['severe'],
            spaceAfter=8
        )
        
        disclaimer_content = [
            "This AI Health Analysis Report is for informational and educational purposes only.",
            "The predictions and recommendations provided are based on algorithmic analysis and should not be considered as professional medical advice, diagnosis, or treatment.",
            "Always consult with qualified healthcare professionals for proper medical evaluation, diagnosis, and treatment.",
            "In case of medical emergency, contact your local emergency services immediately.",
            "This system should not replace professional medical consultation, examination, or treatment.",
            "The accuracy of predictions depends on the quality of input symptoms and the limitations of the AI model.",
            "Users are responsible for seeking appropriate medical care based on their individual circumstances."
        ]
        
        for content in disclaimer_content:
            story.append(Paragraph(f"• {content}", disclaimer_style))
        
        story.append(Spacer(1, 20))
    
    def create_footer_section(self, story):
        """Create the footer section"""
        footer_line = HRFlowable(width="100%", thickness=1, color=self.colors['dark_gray'])
        story.append(footer_line)
        story.append(Spacer(1, 10))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Info'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=self.colors['dark_gray']
        )
        
        footer_text = (
            "AI Health Analyzer | Powered by Machine Learning & Medical Knowledge<br/>"
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            "For questions or concerns, please consult your healthcare provider."
        )
        
        story.append(Paragraph(footer_text, footer_style))
    
    def generate_pdf_report(self, user_symptoms, predictions, recommendations, filename=None):
        """Generate the complete PDF health report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.pdf"
        
        # Create document
        doc = SimpleDocTemplate(filename, pagesize=A4, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Build story
        story = []
        
        # Add sections
        self.create_header_section(story)
        self.create_summary_section(story, user_symptoms, predictions, recommendations)
        self.create_predictions_section(story, predictions)
        self.create_recommendations_section(story, recommendations)
        self.create_chart_section(story, predictions)
        self.create_disclaimer_section(story, recommendations)
        self.create_footer_section(story)
        
        # Build PDF
        doc.build(story)
        
        return filename
    
    def generate_pdf_buffer(self, user_symptoms, predictions, recommendations):
        """Generate PDF report in memory and return as bytes buffer"""
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        story = []
        self.create_header_section(story)
        self.create_summary_section(story, user_symptoms, predictions, recommendations)
        self.create_predictions_section(story, predictions)
        self.create_recommendations_section(story, recommendations)
        self.create_chart_section(story, predictions)
        self.create_disclaimer_section(story, recommendations)
        self.create_footer_section(story)
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer

def test_pdf_generator():
    """Test the PDF generator with sample data"""
    print("🧪 Testing PDF Report Generator\n")
    
    # Sample data
    user_symptoms = "fever, cough, chills, fatigue"
    
    sample_predictions = [
        {
            'disease': 'Flu',
            'confidence': 75.5,
            'severity': 'Moderate',
            'description': 'Viral infection causing systemic symptoms',
            'precautions': 'Bed rest, antiviral medication if severe',
            'diet_recommendations': 'Light meals, plenty of fluids, chicken soup'
        },
        {
            'disease': 'Common Cold',
            'confidence': 45.2,
            'severity': 'Mild',
            'description': 'Viral infection affecting upper respiratory tract',
            'precautions': 'Rest, stay hydrated, avoid cold exposure',
            'diet_recommendations': 'Warm fluids, vitamin C rich foods, ginger tea'
        },
        {
            'disease': 'Pneumonia',
            'confidence': 32.1,
            'severity': 'Severe',
            'description': 'Serious lung infection requiring medical care',
            'precautions': 'Immediate medical attention, antibiotics',
            'diet_recommendations': 'Nutritious meals, increased fluid intake'
        }
    ]
    
    sample_recommendations = {
        'severity_assessment': {
            'overall_severity': 'Moderate',
            'urgency': 'Medium Priority',
            'recommendation': 'Consider scheduling appointment with healthcare provider',
            'timeframe': 'If symptoms persist for more than 24-48 hours or worsen'
        },
        'lifestyle_recommendations': [
            'Bed rest and adequate sleep',
            'Stay well-hydrated',
            'Avoid strenuous physical activity',
            'Practice good hygiene'
        ],
        'dietary_recommendations': [
            'Light meals and plenty of fluids',
            'Chicken soup and warm beverages',
            'Vitamin C rich foods',
            'Avoid alcohol and caffeine'
        ],
        'self_care_tips': [
            'Use humidifier or steam inhalation',
            'Gargle with warm salt water',
            'Apply warm compress to chest'
        ],
        'warning_signs': [
            'Difficulty breathing or shortness of breath',
            'High fever (>103°F/39.4°C)',
            'Persistent vomiting',
            'Chest pain or pressure'
        ],
        'followup_recommendations': [
            'Schedule appointment with primary care physician within 24-48 hours',
            'Keep symptom diary to track changes',
            'Follow prescribed treatment plan'
        ]
    }
    
    # Generate PDF
    generator = HealthReportGenerator()
    
    try:
        filename = generator.generate_pdf_report(user_symptoms, sample_predictions, sample_recommendations)
        print(f"✅ PDF report generated successfully: {filename}")
        
        # Test buffer generation
        buffer = generator.generate_pdf_buffer(user_symptoms, sample_predictions, sample_recommendations)
        print(f"✅ PDF buffer generated successfully: {len(buffer.getvalue())} bytes")
        
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")

if __name__ == "__main__":
    test_pdf_generator()
