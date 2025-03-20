import os
import logging
import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import tempfile
import numpy as np
import cv2
from werkzeug.utils import secure_filename

# Import custom utility modules
from utils.image_processing import process_image, extract_body_landmarks
from utils.body_analysis import analyze_body_traits
from utils.recommendations import generate_recommendations

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
TEMP_UPLOAD_FOLDER = tempfile.gettempdir()

# In-memory storage for analysis results (in a production app, use a database)
analysis_results = {}

def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Process uploaded image and analyze body traits"""
    logger.debug("Received analyze request")
    
    # Ensure temp directory exists
    os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
    
    if 'file' not in request.files:
        logger.error("No file in request.files")
        flash('No file selected', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['file']
    logger.debug(f"File object: {file}, filename: {file.filename}")
    
    if file.filename == '':
        logger.error("Empty filename")
        flash('No file selected', 'danger')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        try:
            # Create a unique ID for this analysis
            analysis_id = str(uuid.uuid4())
            logger.debug(f"Created analysis ID: {analysis_id}")
            
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(TEMP_UPLOAD_FOLDER, filename)
            logger.debug(f"Saving file to: {filepath}")
            file.save(filepath)
            
            # Process image to get landmarks
            image = cv2.imread(filepath)
            if image is None:
                flash('Failed to process image', 'danger')
                return redirect(url_for('index'))
            
            # Get user-provided information
            height = request.form.get('height', 0)
            weight = request.form.get('weight', 0)
            experience = request.form.get('experience', 'beginner')
            
            # Extract landmarks from image
            processed_image, landmarks = extract_body_landmarks(image)
            
            if landmarks is None:
                flash('No body detected in image. Please try again with a clearer full-body image.', 'warning')
                return redirect(url_for('index'))
            
            # Analyze body traits
            traits = analyze_body_traits(landmarks, float(height) if height else 0, float(weight) if weight else 0)
            
            # Generate recommendations
            recommendations = generate_recommendations(traits, experience)
            
            # Store results
            image_path = os.path.join(TEMP_UPLOAD_FOLDER, f"processed_{analysis_id}.jpg")
            cv2.imwrite(image_path, processed_image)
            
            analysis_results[analysis_id] = {
                'image_path': image_path,
                'traits': traits,
                'recommendations': recommendations,
                'user_info': {
                    'height': height,
                    'weight': weight,
                    'experience': experience
                }
            }
            
            # Clean up original upload
            os.remove(filepath)
            
            return redirect(url_for('results', analysis_id=analysis_id))
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            flash(f'Error during analysis: {str(e)}', 'danger')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload PNG or JPG images.', 'warning')
        return redirect(url_for('index'))

@app.route('/results/<analysis_id>')
def results(analysis_id):
    """Display analysis results"""
    if analysis_id not in analysis_results:
        flash('Analysis not found', 'danger')
        return redirect(url_for('index'))
    
    result = analysis_results[analysis_id]
    
    # Read the processed image for display
    with open(result['image_path'], 'rb') as f:
        img_data = f.read()
    
    # Convert image to base64 for embedding in HTML
    import base64
    img_b64 = base64.b64encode(img_data).decode('utf-8')
    
    return render_template(
        'analysis.html',
        analysis_id=analysis_id,
        traits=result['traits'],
        recommendations=result['recommendations'],
        user_info=result['user_info'],
        image_data=img_b64
    )

@app.route('/education')
def education():
    """Display educational content about genetic traits in fitness"""
    return render_template('education.html')

@app.route('/api/traits/<analysis_id>')
def get_traits_data(analysis_id):
    """API endpoint to get trait data for charts"""
    if analysis_id not in analysis_results:
        return jsonify({'error': 'Analysis not found'}), 404
    
    result = analysis_results[analysis_id]
    
    # Format trait data for charts
    chart_data = {
        'labels': [],
        'values': [],
        'colors': []
    }
    
    color_map = {
        'excellent': 'rgba(40, 167, 69, 0.7)',  # green
        'good': 'rgba(23, 162, 184, 0.7)',      # blue
        'average': 'rgba(255, 193, 7, 0.7)',    # yellow
        'below_average': 'rgba(220, 53, 69, 0.7)',  # red
        'informational': 'rgba(108, 117, 125, 0.7)'  # gray
    }
    
    # Define traits for the main radar chart (genetic structure)
    primary_traits = [
        'shoulder_width', 'shoulder_hip_ratio', 'arm_length', 
        'leg_length', 'arm_torso_ratio', 'torso_length', 'waist_hip_ratio'
    ]
    
    # Define body composition traits for the optional second chart
    body_comp_traits = [
        'bmi', 'body_fat_percentage', 'muscle_potential'
    ]
    
    # First, add the primary genetic structure traits
    for trait in primary_traits:
        if trait in result['traits'] and isinstance(result['traits'][trait], dict) and 'rating' in result['traits'][trait]:
            # Format trait name for display
            display_name = ' '.join(word.capitalize() for word in trait.split('_'))
            chart_data['labels'].append(display_name)
            
            # Determine numerical value and color
            trait_data = result['traits'][trait]
            numeric_value = {
                'excellent': 90,
                'good': 75,
                'average': 50,
                'below_average': 25,
                'informational': 50  # default for informational ratings
            }.get(trait_data['rating'], 50)
            
            chart_data['values'].append(numeric_value)
            chart_data['colors'].append(color_map.get(trait_data['rating'], 'rgba(108, 117, 125, 0.7)'))
    
    # Then, add body composition metrics if they exist
    for trait in body_comp_traits:
        if trait in result['traits'] and isinstance(result['traits'][trait], dict) and 'rating' in result['traits'][trait]:
            # Format trait name for display
            if trait == 'bmi':
                display_name = 'BMI'
            elif trait == 'body_fat_percentage':
                display_name = 'Body Fat %'
            elif trait == 'muscle_potential':
                display_name = 'Muscle Potential'
            else:
                display_name = ' '.join(word.capitalize() for word in trait.split('_'))
            
            chart_data['labels'].append(display_name)
            
            # Determine numerical value and color
            trait_data = result['traits'][trait]
            if trait_data['rating'] != 'informational':
                numeric_value = {
                    'excellent': 90,
                    'good': 75,
                    'average': 50,
                    'below_average': 25
                }.get(trait_data['rating'], 50)
                
                chart_data['values'].append(numeric_value)
                chart_data['colors'].append(color_map.get(trait_data['rating'], 'rgba(108, 117, 125, 0.7)'))
            else:
                # For informational values, use a neutral value
                chart_data['values'].append(50)
                chart_data['colors'].append('rgba(108, 117, 125, 0.7)')
    
    return jsonify(chart_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
