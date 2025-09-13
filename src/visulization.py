import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import io
import base64

class HealthVisualization:
    def __init__(self):
        """Initialize the Health Visualization System"""
        # Set styling for matplotlib/seaborn
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Color schemes for different severity levels
        self.severity_colors = {
            'Mild': '#28a745',     # Green
            'Moderate': '#ffc107', # Yellow/Orange
            'Severe': '#dc3545'    # Red
        }
        
        self.confidence_colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
    
    def create_confidence_bar_chart(self, predictions, title="Disease Prediction Confidence"):
        """Create horizontal bar chart showing disease confidence levels"""
        if not predictions:
            return None
        
        diseases = [pred['disease'] for pred in predictions]
        confidences = [pred['confidence'] for pred in predictions]
        severities = [pred['severity'] for pred in predictions]
        
        # Create colors based on severity
        colors = [self.severity_colors.get(severity, '#6c757d') for severity in severities]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create horizontal bar chart
        bars = ax.barh(diseases, confidences, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
        
        # Customize the chart
        ax.set_xlabel('Confidence (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Predicted Diseases', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Add confidence values on bars
        for i, (bar, conf) in enumerate(zip(bars, confidences)):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                   f'{conf:.1f}%', va='center', fontweight='bold')
        
        # Add severity legend
        severity_handles = []
        for severity, color in self.severity_colors.items():
            if severity in severities:
                severity_handles.append(plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.7, label=severity))
        
        if severity_handles:
            ax.legend(handles=severity_handles, title='Severity Level', 
                     loc='lower right', frameon=True, fancybox=True, shadow=True)
        
        # Customize grid and spines
        ax.grid(True, alpha=0.3, axis='x')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Set x-axis limit
        ax.set_xlim(0, max(confidences) * 1.2)
        
        plt.tight_layout()
        return fig
    
    def create_confidence_pie_chart(self, predictions, title="Disease Probability Distribution"):
        """Create pie chart showing disease probability distribution"""
        if not predictions:
            return None
        
        diseases = [pred['disease'] for pred in predictions]
        confidences = [pred['confidence'] for pred in predictions]
        severities = [pred['severity'] for pred in predictions]
        
        # Create colors based on severity
        colors = [self.severity_colors.get(severity, '#6c757d') for severity in severities]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(confidences, labels=diseases, colors=colors, 
                                         autopct='%1.1f%%', startangle=90,
                                         explode=[0.1 if i == 0 else 0 for i in range(len(diseases))],
                                         shadow=True)
        
        # Customize text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        for text in texts:
            text.set_fontsize(12)
            text.set_fontweight('bold')
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Add severity information in legend
        legend_labels = [f"{disease} ({severity})" for disease, severity in zip(diseases, severities)]
        ax.legend(wedges, legend_labels, title="Diseases (Severity)", 
                 loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        return fig
    
    def create_interactive_confidence_chart(self, predictions):
        """Create interactive Plotly chart for disease confidence"""
        if not predictions:
            return None
        
        diseases = [pred['disease'] for pred in predictions]
        confidences = [pred['confidence'] for pred in predictions]
        severities = [pred['severity'] for pred in predictions]
        descriptions = [pred.get('description', 'No description available') for pred in predictions]
        
        # Create color mapping for severities
        color_map = {'Mild': 'green', 'Moderate': 'orange', 'Severe': 'red'}
        colors = [color_map.get(severity, 'gray') for severity in severities]
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=diseases,
            y=confidences,
            marker_color=colors,
            text=[f'{conf:.1f}%' for conf in confidences],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>' +
                         'Confidence: %{y:.1f}%<br>' +
                         'Severity: %{customdata[0]}<br>' +
                         'Description: %{customdata[1]}<br>' +
                         '<extra></extra>',
            customdata=list(zip(severities, descriptions))
        ))
        
        fig.update_layout(
            title={
                'text': 'Disease Prediction Confidence Levels',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'family': 'Arial, sans-serif'}
            },
            xaxis_title='Predicted Diseases',
            yaxis_title='Confidence (%)',
            font=dict(size=12),
            showlegend=False,
            height=500,
            margin=dict(t=80, b=100, l=60, r=60)
        )
        
        # Add severity color legend manually
        for severity, color in color_map.items():
            if severity in severities:
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(size=10, color=color),
                    name=f'{severity} Severity',
                    showlegend=True
                ))
        
        return fig
    
    def create_severity_distribution_chart(self, predictions):
        """Create chart showing severity distribution of predictions"""
        if not predictions:
            return None
        
        severities = [pred['severity'] for pred in predictions]
        severity_counts = pd.Series(severities).value_counts()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Pie chart
        colors = [self.severity_colors.get(severity, '#6c757d') for severity in severity_counts.index]
        wedges, texts, autotexts = ax1.pie(severity_counts.values, labels=severity_counts.index, 
                                          colors=colors, autopct='%1.0f%%', startangle=90, shadow=True)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax1.set_title('Severity Distribution', fontsize=14, fontweight='bold')
        
        # Bar chart
        bars = ax2.bar(severity_counts.index, severity_counts.values, 
                      color=colors, alpha=0.7, edgecolor='black', linewidth=1)
        ax2.set_title('Severity Count', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Severity Level', fontweight='bold')
        ax2.set_ylabel('Number of Predictions', fontweight='bold')
        
        # Add count values on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        plt.tight_layout()
        return fig
    
    def create_symptom_word_cloud(self, predictions, user_symptoms=""):
        """Create word cloud from symptoms"""
        if not predictions and not user_symptoms:
            return None
        
        # Combine all symptoms
        all_symptoms = user_symptoms + " "
        for pred in predictions:
            if 'matched_symptoms' in pred:
                all_symptoms += pred['matched_symptoms'].replace(';', ' ') + " "
        
        if not all_symptoms.strip():
            return None
        
        # Create word cloud
        wordcloud = WordCloud(width=1200, height=600, 
                             min_font_size=16,
                             max_font_size=80,
                             prefer_horizontal=0.8,
                             collocations=False,
                             margin=20,
                             random_state=42,
                             background_color='white',
                             colormap="Set3",
                             max_words=25,
                             relative_scaling=0.8).generate(all_symptoms)
        
        fig, ax = plt.subplots(figsize=(15, 8))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title('Symptom Analysis Word Cloud', fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        return fig
    
    def create_confidence_gauge(self, top_prediction):
        """Create gauge chart for top prediction confidence"""
        if not top_prediction:
            return None
        
        confidence = top_prediction['confidence']
        disease = top_prediction['disease']
        severity = top_prediction['severity']
        
        # Determine gauge color based on confidence and severity
        if confidence >= 70:
            gauge_color = '#28a745'  # Green
        elif confidence >= 40:
            gauge_color = '#ffc107'  # Yellow
        else:
            gauge_color = '#dc3545'  # Red
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=confidence,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Confidence: {disease}<br><span style='font-size:0.8em;color:gray'>Severity: {severity}</span>"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': gauge_color},
                'steps': [
                    {'range': [0, 25], 'color': "lightgray"},
                    {'range': [25, 50], 'color': "gray"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            font={'color': "darkblue", 'family': "Arial"},
            height=400,
            margin=dict(t=80, b=20, l=20, r=20)
        )
        
        return fig
    
    def create_prediction_comparison_chart(self, predictions):
        """Create comparison chart showing multiple prediction metrics"""
        if not predictions:
            return None
        
        diseases = [pred['disease'] for pred in predictions]
        confidences = [pred['confidence'] for pred in predictions]
        severities = [pred['severity'] for pred in predictions]
        
        # Create subplot figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Confidence Levels', 'Severity Distribution', 
                          'Confidence vs Disease', 'Risk Assessment'),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )
        
        # Bar chart of confidences
        fig.add_trace(
            go.Bar(x=diseases, y=confidences, name='Confidence',
                  marker_color='lightblue'),
            row=1, col=1
        )
        
        # Pie chart of severities
        severity_counts = pd.Series(severities).value_counts()
        fig.add_trace(
            go.Pie(labels=severity_counts.index, values=severity_counts.values,
                  name="Severity"),
            row=1, col=2
        )
        
        # Scatter plot
        fig.add_trace(
            go.Scatter(x=diseases, y=confidences, mode='markers+text',
                      text=[f'{c:.1f}%' for c in confidences],
                      textposition="top center",
                      marker=dict(size=[c/2 for c in confidences], 
                                color=[self.severity_colors.get(s, 'gray') for s in severities]),
                      name='Confidence-Severity'),
            row=2, col=1
        )
        
        # Risk assessment bar
        risk_scores = [c * (3 if s == 'Severe' else 2 if s == 'Moderate' else 1) 
                      for c, s in zip(confidences, severities)]
        fig.add_trace(
            go.Bar(x=diseases, y=risk_scores, name='Risk Score',
                  marker_color='salmon'),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=False,
                         title_text="Comprehensive Health Prediction Analysis")
        
        return fig
    
    def save_plot_as_base64(self, fig):
        """Convert matplotlib figure to base64 string for embedding"""
        if fig is None:
            return None
        
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)  # Close figure to free memory
        return img_base64

def test_visualization():
    """Test the visualization system"""
    print("🧪 Testing Health Visualization System\n")
    
    # Sample predictions
    sample_predictions = [
        {
            'disease': 'Flu',
            'confidence': 75.5,
            'severity': 'Moderate',
            'description': 'Viral infection causing systemic symptoms',
            'matched_symptoms': 'fever;cough;chills;fatigue'
        },
        {
            'disease': 'Common Cold',
            'confidence': 45.2,
            'severity': 'Mild',
            'description': 'Viral infection affecting upper respiratory tract',
            'matched_symptoms': 'fever;runny nose;cough'
        },
        {
            'disease': 'Pneumonia',
            'confidence': 32.1,
            'severity': 'Severe',
            'description': 'Serious lung infection',
            'matched_symptoms': 'fever;chest pain;difficulty breathing'
        }
    ]
    
    viz = HealthVisualization()
    
    # Test bar chart
    print("📊 Creating confidence bar chart...")
    bar_fig = viz.create_confidence_bar_chart(sample_predictions)
    if bar_fig:
        plt.show()
        plt.close()
    
    # Test pie chart
    print("🥧 Creating confidence pie chart...")
    pie_fig = viz.create_confidence_pie_chart(sample_predictions)
    if pie_fig:
        plt.show()
        plt.close()
    
    # Test severity distribution
    print("📈 Creating severity distribution chart...")
    severity_fig = viz.create_severity_distribution_chart(sample_predictions)
    if severity_fig:
        plt.show()
        plt.close()
    
    # Test word cloud
    print("☁️ Creating symptom word cloud...")
    wordcloud_fig = viz.create_symptom_word_cloud(sample_predictions, "fever cough chills")
    if wordcloud_fig:
        plt.show()
        plt.close()
    
    # Test interactive charts
    print("🎯 Creating interactive gauge chart...")
    gauge_fig = viz.create_confidence_gauge(sample_predictions[0])
    if gauge_fig:
        print("✅ Interactive gauge chart created successfully")
    
    print("📊 Creating interactive confidence chart...")
    interactive_fig = viz.create_interactive_confidence_chart(sample_predictions)
    if interactive_fig:
        print("✅ Interactive confidence chart created successfully")
    
    print("\n✅ All visualization tests completed!")

if __name__ == "__main__":
    test_visualization()
