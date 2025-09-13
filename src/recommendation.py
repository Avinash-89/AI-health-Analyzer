import pandas as pd
from datetime import datetime
import re

class HealthRecommendationSystem:
    def __init__(self):
        """Initialize the Health Recommendation System"""
        self.severity_actions = {
            'Mild': {
                'urgency': 'Low Priority',
                'action': 'Monitor symptoms and try self-care measures',
                'timeframe': 'If symptoms persist for more than 3-5 days',
                'color': '🟢'
            },
            'Moderate': {
                'urgency': 'Medium Priority',
                'action': 'Consider scheduling an appointment with healthcare provider',
                'timeframe': 'If symptoms persist for more than 24-48 hours or worsen',
                'color': '🟡'
            },
            'Severe': {
                'urgency': 'HIGH PRIORITY',
                'action': 'Seek immediate medical attention',
                'timeframe': 'Contact healthcare provider immediately or visit emergency room',
                'color': '🔴'
            }
        }
        
        self.general_health_tips = [
            "💧 Stay well-hydrated by drinking plenty of water throughout the day",
            "😴 Ensure adequate rest and sleep (7-9 hours for adults)",
            "🏃‍♂️ Maintain light physical activity as tolerated",
            "🧘‍♀️ Practice stress management techniques like meditation or deep breathing",
            "🚭 Avoid smoking and limit alcohol consumption",
            "🧼 Maintain good hygiene practices",
            "🌡️ Monitor your symptoms and track any changes",
            "📱 Keep emergency contacts readily available"
        ]
    
    def generate_severity_assessment(self, predictions):
        """Generate detailed severity assessment and recommendations"""
        if not predictions:
            return {
                'overall_severity': 'Unknown',
                'recommendation': 'Unable to assess. Please consult a healthcare provider.',
                'urgency': 'Consult healthcare provider',
                'color': '⚪'
            }
        
        # Get the highest severity from predictions
        severities = [pred['severity'] for pred in predictions]
        severity_priority = {'Severe': 3, 'Moderate': 2, 'Mild': 1}
        
        highest_severity = max(severities, key=lambda x: severity_priority.get(x, 0))
        severity_info = self.severity_actions[highest_severity]
        
        return {
            'overall_severity': highest_severity,
            'recommendation': severity_info['action'],
            'urgency': severity_info['urgency'],
            'timeframe': severity_info['timeframe'],
            'color': severity_info['color']
        }
    
    def parse_recommendations(self, recommendation_text):
        """Parse comma-separated recommendations into a list"""
        if pd.isna(recommendation_text) or not recommendation_text:
            return []
        
        # Split by comma and clean up
        recommendations = [rec.strip() for rec in recommendation_text.split(',')]
        return [rec for rec in recommendations if rec]  # Remove empty strings
    
    def generate_lifestyle_recommendations(self, predictions):
        """Generate comprehensive lifestyle recommendations"""
        if not predictions:
            return []
        
        lifestyle_recs = []
        
        # Collect all precautions from predictions
        for pred in predictions:
            precautions = self.parse_recommendations(pred.get('precautions', ''))
            for precaution in precautions:
                if precaution not in lifestyle_recs:
                    lifestyle_recs.append(f"⚠️ {precaution}")
        
        # Add general health tips based on severity
        severity_assessment = self.generate_severity_assessment(predictions)
        
        if severity_assessment['overall_severity'] in ['Mild', 'Moderate']:
            lifestyle_recs.extend(self.general_health_tips[:4])
        else:
            lifestyle_recs.extend(self.general_health_tips[:2])
        
        return lifestyle_recs
    
    def generate_dietary_recommendations(self, predictions):
        """Generate comprehensive dietary recommendations"""
        if not predictions:
            return []
        
        dietary_recs = []
        
        # Collect all diet recommendations from predictions
        for pred in predictions:
            diet_recommendations = self.parse_recommendations(pred.get('diet_recommendations', ''))
            for rec in diet_recommendations:
                if rec not in dietary_recs:
                    dietary_recs.append(f"🍽️ {rec}")
        
        # Add general dietary advice
        general_dietary_tips = [
            "🥗 Eat a balanced diet rich in fruits and vegetables",
            "💊 Consider appropriate vitamin supplements if recommended",
            "🍯 Natural remedies like honey and ginger may help with some symptoms",
            "🚫 Avoid foods that may worsen your condition"
        ]
        
        # Add general tips if we don't have many specific recommendations
        if len(dietary_recs) < 3:
            dietary_recs.extend(general_dietary_tips[:2])
        
        return dietary_recs
    
    def generate_warning_signs(self, predictions):
        """Generate warning signs that require immediate medical attention"""
        if not predictions:
            return []
        
        general_warning_signs = [
            "🚨 Difficulty breathing or shortness of breath",
            "🚨 Chest pain or pressure",
            "🚨 High fever (>103°F/39.4°C)",
            "🚨 Severe dehydration",
            "🚨 Persistent vomiting",
            "🚨 Severe abdominal pain",
            "🚨 Signs of infection (spreading redness, pus)",
            "🚨 Loss of consciousness or confusion"
        ]
        
        # Add specific warning signs based on predicted conditions
        specific_warnings = []
        for pred in predictions:
            disease = pred['disease'].lower()
            
            if 'heart' in disease or 'cardiac' in disease:
                specific_warnings.append("🚨 Chest pain radiating to arm, jaw, or back")
            elif 'stroke' in disease:
                specific_warnings.append("🚨 Sudden weakness, speech difficulty, or vision problems")
            elif 'asthma' in disease:
                specific_warnings.append("🚨 Severe difficulty breathing or wheezing")
            elif 'diabetes' in disease:
                specific_warnings.append("🚨 Extremely high or low blood sugar levels")
        
        # Combine and return unique warnings
        all_warnings = specific_warnings + general_warning_signs[:5]
        return list(dict.fromkeys(all_warnings))  # Remove duplicates while preserving order
    
    def generate_self_care_tips(self, predictions):
        """Generate self-care tips based on predicted conditions"""
        if not predictions:
            return []
        
        self_care_tips = []
        
        for pred in predictions:
            disease = pred['disease'].lower()
            severity = pred['severity']
            
            # Add condition-specific self-care tips
            if 'cold' in disease or 'flu' in disease:
                self_care_tips.extend([
                    "🤧 Use a humidifier or breathe steam from a hot shower",
                    "🍵 Drink warm beverages like tea with honey",
                    "🧊 Gargle with warm salt water for sore throat"
                ])
            elif 'headache' in disease or 'migraine' in disease:
                self_care_tips.extend([
                    "🌑 Rest in a dark, quiet room",
                    "❄️ Apply cold or warm compress to head/neck",
                    "💆‍♀️ Try gentle neck and shoulder massage"
                ])
            elif 'stomach' in disease or 'gastro' in disease:
                self_care_tips.extend([
                    "🍚 Follow BRAT diet (Bananas, Rice, Applesauce, Toast)",
                    "💧 Sip clear fluids frequently",
                    "🌡️ Use heating pad on stomach for comfort"
                ])
            
            # Only include self-care for mild to moderate conditions
            if severity == 'Severe':
                self_care_tips = ["⚠️ Seek immediate medical attention - self-care not appropriate for severe conditions"]
                break
        
        # Remove duplicates
        return list(dict.fromkeys(self_care_tips))
    
    def generate_followup_recommendations(self, predictions):
        """Generate follow-up care recommendations"""
        followup_recs = []
        
        severity_assessment = self.generate_severity_assessment(predictions)
        
        if severity_assessment['overall_severity'] == 'Severe':
            followup_recs = [
                "🏥 Seek immediate emergency medical care",
                "📞 Call emergency services if symptoms are life-threatening",
                "👨‍⚕️ Follow up with specialists as recommended"
            ]
        elif severity_assessment['overall_severity'] == 'Moderate':
            followup_recs = [
                "📅 Schedule appointment with primary care physician within 24-48 hours",
                "📊 Consider getting relevant tests or screenings",
                "📝 Keep a symptom diary to track changes",
                "💊 Follow prescribed treatment plan if applicable"
            ]
        else:  # Mild
            followup_recs = [
                "📋 Monitor symptoms for 3-5 days",
                "📅 Schedule routine check-up if symptoms persist",
                "📱 Consider telehealth consultation if available",
                "📖 Research reputable health information sources"
            ]
        
        return followup_recs
    
    def generate_comprehensive_recommendations(self, predictions, user_symptoms):
        """Generate comprehensive health recommendations"""
        if not predictions:
            return {
                'error': 'No predictions available to generate recommendations',
                'general_advice': 'Please consult with a healthcare provider for proper evaluation.'
            }
        
        severity_assessment = self.generate_severity_assessment(predictions)
        
        recommendations = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'input_symptoms': user_symptoms,
            'severity_assessment': severity_assessment,
            'lifestyle_recommendations': self.generate_lifestyle_recommendations(predictions),
            'dietary_recommendations': self.generate_dietary_recommendations(predictions),
            'self_care_tips': self.generate_self_care_tips(predictions),
            'warning_signs': self.generate_warning_signs(predictions),
            'followup_recommendations': self.generate_followup_recommendations(predictions),
            'disclaimer': self._generate_disclaimer()
        }
        
        return recommendations
    
    def _generate_disclaimer(self):
        """Generate medical disclaimer"""
        return {
            'title': '⚠️ IMPORTANT MEDICAL DISCLAIMER',
            'content': [
                "This system is for informational purposes only and does not constitute medical advice.",
                "Always consult with qualified healthcare professionals for proper diagnosis and treatment.",
                "In case of medical emergency, call your local emergency services immediately.",
                "This tool should not replace professional medical consultation, examination, or treatment."
            ]
        }
    
    def format_recommendations_for_display(self, recommendations):
        """Format recommendations for clean display"""
        if 'error' in recommendations:
            return recommendations
        
        formatted = []
        
        # Severity Assessment
        severity = recommendations['severity_assessment']
        formatted.append(f"\n{severity['color']} **SEVERITY ASSESSMENT: {severity['overall_severity'].upper()}**")
        formatted.append(f"📋 **Recommendation:** {severity['recommendation']}")
        formatted.append(f"⏰ **Timeframe:** {severity['timeframe']}")
        
        # Lifestyle Recommendations
        if recommendations['lifestyle_recommendations']:
            formatted.append(f"\n🏃‍♂️ **LIFESTYLE RECOMMENDATIONS:**")
            for rec in recommendations['lifestyle_recommendations'][:6]:
                formatted.append(f"  • {rec}")
        
        # Dietary Recommendations
        if recommendations['dietary_recommendations']:
            formatted.append(f"\n🍽️ **DIETARY RECOMMENDATIONS:**")
            for rec in recommendations['dietary_recommendations'][:5]:
                formatted.append(f"  • {rec}")
        
        # Self-Care Tips
        if recommendations['self_care_tips']:
            formatted.append(f"\n💆‍♀️ **SELF-CARE TIPS:**")
            for tip in recommendations['self_care_tips'][:4]:
                formatted.append(f"  • {tip}")
        
        # Warning Signs
        if recommendations['warning_signs']:
            formatted.append(f"\n🚨 **SEEK IMMEDIATE MEDICAL ATTENTION IF:**")
            for warning in recommendations['warning_signs'][:5]:
                formatted.append(f"  • {warning}")
        
        # Follow-up Recommendations
        if recommendations['followup_recommendations']:
            formatted.append(f"\n📅 **FOLLOW-UP CARE:**")
            for followup in recommendations['followup_recommendations']:
                formatted.append(f"  • {followup}")
        
        # Disclaimer
        disclaimer = recommendations['disclaimer']
        formatted.append(f"\n{disclaimer['title']}")
        for content in disclaimer['content']:
            formatted.append(f"• {content}")
        
        return "\n".join(formatted)

def test_recommendation_system():
    """Test the recommendation system"""
    print("🧪 Testing Health Recommendation System\n")
    
    # Sample predictions from prediction engine
    sample_predictions = [
        {
            'disease': 'Flu',
            'confidence': 75.5,
            'severity': 'Moderate',
            'precautions': 'Bed rest, antiviral medication if severe, avoid contact with others',
            'diet_recommendations': 'Light meals, plenty of fluids, chicken soup',
            'description': 'Viral infection causing systemic symptoms'
        },
        {
            'disease': 'Common Cold',
            'confidence': 45.2,
            'severity': 'Mild',
            'precautions': 'Rest, stay hydrated, avoid cold exposure',
            'diet_recommendations': 'Warm fluids, vitamin C rich foods, ginger tea',
            'description': 'Viral infection affecting upper respiratory tract'
        }
    ]
    
    rec_system = HealthRecommendationSystem()
    recommendations = rec_system.generate_comprehensive_recommendations(
        sample_predictions, 
        "fever, cough, chills"
    )
    
    formatted_output = rec_system.format_recommendations_for_display(recommendations)
    print(formatted_output)

if __name__ == "__main__":
    test_recommendation_system()
