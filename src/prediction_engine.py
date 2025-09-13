import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import re
import pickle
import os

class HealthPredictor:
    def __init__(self, data_path='data/sample_data.csv'):
        """Initialize the Health Prediction Engine"""
        self.data_path = data_path
        self.df = None
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        self.symptom_vectors = None
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoder = LabelEncoder()
        self.load_data()
        self.prepare_models()
    
    def load_data(self):
        """Load health data from CSV file"""
        try:
            self.df = pd.read_csv(self.data_path)
            print(f"✅ Loaded {len(self.df)} diseases from dataset")
        except FileNotFoundError:
            print(f"❌ Error: Could not find {self.data_path}")
            raise
    
    def preprocess_symptoms(self, symptoms):
        """Clean and preprocess symptoms text"""
        if isinstance(symptoms, str):
            # Convert semicolon-separated symptoms to space-separated
            symptoms = symptoms.replace(';', ' ')
            # Remove special characters and normalize
            symptoms = re.sub(r'[^\w\s]', '', symptoms.lower().strip())
        return symptoms
    
    def prepare_models(self):
        """Prepare TF-IDF vectorizer and ML model"""
        # Preprocess all symptoms in dataset
        processed_symptoms = self.df['Symptoms'].apply(self.preprocess_symptoms)
        
        # Fit TF-IDF vectorizer
        self.symptom_vectors = self.vectorizer.fit_transform(processed_symptoms)
        
        # Prepare ML model
        X = self.symptom_vectors
        y = self.label_encoder.fit_transform(self.df['Disease'])
        self.model.fit(X, y)
        
        print("✅ Models prepared successfully")
    
    def calculate_similarity_scores(self, user_symptoms):
        """Calculate similarity scores using TF-IDF and cosine similarity"""
        processed_input = self.preprocess_symptoms(user_symptoms)
        user_vector = self.vectorizer.transform([processed_input])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(user_vector, self.symptom_vectors).flatten()
        
        return similarities
    
    def predict_diseases_similarity(self, user_symptoms, top_n=3):
        """Predict diseases using similarity-based matching"""
        similarities = self.calculate_similarity_scores(user_symptoms)
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        predictions = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include non-zero similarities
                disease_info = self.df.iloc[idx].copy()
                confidence = float(similarities[idx] * 100)  # Convert to percentage
                
                predictions.append({
                    'disease': disease_info['Disease'],
                    'confidence': round(confidence, 2),
                    'severity': disease_info['Severity'],
                    'precautions': disease_info['Precautions'],
                    'diet_recommendations': disease_info['Diet_Recommendations'],
                    'description': disease_info['Description'],
                    'matched_symptoms': disease_info['Symptoms']
                })
        
        return predictions
    
    def predict_diseases_ml(self, user_symptoms, top_n=3):
        """Predict diseases using Machine Learning model"""
        processed_input = self.preprocess_symptoms(user_symptoms)
        user_vector = self.vectorizer.transform([processed_input])
        
        # Get prediction probabilities
        probabilities = self.model.predict_proba(user_vector)[0]
        
        # Get top predictions
        top_indices = np.argsort(probabilities)[::-1][:top_n]
        
        predictions = []
        for idx in top_indices:
            if probabilities[idx] > 0.01:  # Only include predictions with >1% confidence
                disease_name = self.label_encoder.inverse_transform([idx])[0]
                disease_info = self.df[self.df['Disease'] == disease_name].iloc[0]
                confidence = float(probabilities[idx] * 100)
                
                predictions.append({
                    'disease': disease_name,
                    'confidence': round(confidence, 2),
                    'severity': disease_info['Severity'],
                    'precautions': disease_info['Precautions'],
                    'diet_recommendations': disease_info['Diet_Recommendations'],
                    'description': disease_info['Description'],
                    'matched_symptoms': disease_info['Symptoms']
                })
        
        return predictions
    
    def hybrid_prediction(self, user_symptoms, top_n=3):
        """Combine similarity-based and ML predictions for better results"""
        # Get predictions from both methods
        similarity_predictions = self.predict_diseases_similarity(user_symptoms, top_n)
        ml_predictions = self.predict_diseases_ml(user_symptoms, top_n)
        
        # Combine and weight the predictions
        combined_scores = {}
        
        # Weight similarity-based predictions (60% weight)
        for pred in similarity_predictions:
            disease = pred['disease']
            combined_scores[disease] = {
                'info': pred,
                'score': pred['confidence'] * 0.6
            }
        
        # Weight ML-based predictions (40% weight)
        for pred in ml_predictions:
            disease = pred['disease']
            if disease in combined_scores:
                combined_scores[disease]['score'] += pred['confidence'] * 0.4
            else:
                combined_scores[disease] = {
                    'info': pred,
                    'score': pred['confidence'] * 0.4
                }
        
        # Sort by combined score and return top predictions
        sorted_predictions = sorted(combined_scores.items(), 
                                  key=lambda x: x[1]['score'], 
                                  reverse=True)[:top_n]
        
        final_predictions = []
        for disease, data in sorted_predictions:
            prediction = data['info'].copy()
            prediction['confidence'] = round(data['score'], 2)
            final_predictions.append(prediction)
        
        return final_predictions
    
    def get_severity_warning(self, predictions):
        """Generate severity-based warnings"""
        if not predictions:
            return "No matching conditions found."
        
        highest_severity = predictions[0]['severity']
        
        warnings = {
            'Mild': "💚 Low concern - Monitor symptoms and consider self-care measures.",
            'Moderate': "🟡 Moderate concern - Consider consulting a healthcare provider if symptoms persist or worsen.",
            'Severe': "🔴 HIGH CONCERN - Seek immediate medical attention. This could be a serious condition."
        }
        
        return warnings.get(highest_severity, "Please monitor your symptoms carefully.")
    
    def save_model(self, model_path='models/'):
        """Save trained models"""
        os.makedirs(model_path, exist_ok=True)
        
        with open(f'{model_path}/vectorizer.pkl', 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        with open(f'{model_path}/rf_model.pkl', 'wb') as f:
            pickle.dump(self.model, f)
        
        with open(f'{model_path}/label_encoder.pkl', 'wb') as f:
            pickle.dump(self.label_encoder, f)
        
        print("✅ Models saved successfully")
    
    def load_model(self, model_path='models/'):
        """Load pre-trained models"""
        try:
            with open(f'{model_path}/vectorizer.pkl', 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            with open(f'{model_path}/rf_model.pkl', 'rb') as f:
                self.model = pickle.load(f)
            
            with open(f'{model_path}/label_encoder.pkl', 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            print("✅ Models loaded successfully")
        except FileNotFoundError:
            print("⚠️ Pre-trained models not found. Using freshly trained models.")

def test_prediction_engine():
    """Test the prediction engine with sample symptoms"""
    print("🧪 Testing Health Prediction Engine\n")
    
    predictor = HealthPredictor()
    
    test_cases = [
        "fever, cough, chills",
        "headache, nausea, sensitivity to light",
        "chest pain, difficulty breathing, fatigue",
        "stomach pain, diarrhea, vomiting"
    ]
    
    for symptoms in test_cases:
        print(f"🔍 Testing symptoms: {symptoms}")
        predictions = predictor.hybrid_prediction(symptoms)
        warning = predictor.get_severity_warning(predictions)
        
        print("📋 Top Predictions:")
        for i, pred in enumerate(predictions, 1):
            print(f"{i}. {pred['disease']} ({pred['confidence']}% confidence)")
            print(f"   Severity: {pred['severity']}")
        
        print(f"⚠️ Warning: {warning}")
        print("-" * 50)

if __name__ == "__main__":
    test_prediction_engine()
