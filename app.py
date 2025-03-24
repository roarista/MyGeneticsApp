import os
import logging
import uuid
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import numpy as np
import cv2
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Database configuration
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import custom utility modules
from utils.image_processing import process_image, extract_body_landmarks
from utils.body_analysis import analyze_body_traits
from utils.recommendations import generate_recommendations
from utils.units import format_trait_value, get_unit
from utils.body_scan_3d import process_3d_scan, is_valid_3d_scan_file

# Configure upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_3D_EXTENSIONS = {'obj', 'stl', 'ply'}
TEMP_UPLOAD_FOLDER = tempfile.gettempdir()

# In-memory storage for analysis results (in a production app, use a database)
analysis_results = {}

def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_3d_file(filename):
    """Check if uploaded file has an allowed 3D model extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_3D_EXTENSIONS

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
            gender = request.form.get('gender', 'male')  # Default to male if not specified
            experience = request.form.get('experience', 'beginner')
            
            logger.debug(f"User inputs - Height: {height}, Weight: {weight}, Gender: {gender}, Experience: {experience}")
            
            # Extract landmarks from image
            processed_image, landmarks = extract_body_landmarks(image)
            
            if landmarks is None:
                flash('No body detected in image. Please try again with a clearer full-body image.', 'warning')
                return redirect(url_for('index'))
            
            # Analyze body traits - pass the original image for AI analysis
            traits = analyze_body_traits(
                landmarks=landmarks, 
                original_image=image,
                height_cm=float(height) if height else 0, 
                weight_kg=float(weight) if weight else 0,
                gender=gender,  # Pass gender to the analysis function
                experience=experience  # Pass training experience level
            )
            
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
                    'gender': gender,
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
    
    # Process traits to include their units
    formatted_traits = {}
    for trait_name, trait_data in result['traits'].items():
        # For traits that are dictionaries with value keys
        if isinstance(trait_data, dict) and 'value' in trait_data:
            # Copy the trait data
            formatted_trait = trait_data.copy()
            # Format the value with units
            formatted_trait['display_value'] = format_trait_value(trait_name, trait_data['value'])
            formatted_trait['unit'] = get_unit(trait_name)
            formatted_traits[trait_name] = formatted_trait
        else:
            # For other types of traits
            formatted_traits[trait_name] = trait_data
    
    return render_template(
        'analysis.html',
        analysis_id=analysis_id,
        traits=formatted_traits,
        recommendations=result['recommendations'],
        user_info=result['user_info'],
        image_data=img_b64,
        format_value=format_trait_value  # Pass the formatter to the template
    )

@app.route('/education')
def education():
    """Display educational content about genetic traits in fitness"""
    return render_template('education.html')

@app.route('/scan3d')
def scan3d_page():
    """Display the 3D body scan upload page"""
    return render_template('scan3d.html')

@app.route('/scan3d/upload', methods=['POST'])
def scan3d_upload():
    """Process uploaded 3D scan file and analyze body measurements"""
    logger.debug("Received 3D scan upload request")
    
    # Ensure temp directory exists
    os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
    
    if 'scan_file' not in request.files:
        logger.error("No scan file in request.files")
        flash('No file selected', 'danger')
        return redirect(url_for('scan3d_page'))
    
    file = request.files['scan_file']
    logger.debug(f"File object: {file}, filename: {file.filename}")
    
    if file.filename == '':
        logger.error("Empty filename")
        flash('No file selected', 'danger')
        return redirect(url_for('scan3d_page'))
    
    if file and allowed_3d_file(file.filename):
        try:
            # Create a unique ID for this analysis
            analysis_id = str(uuid.uuid4())
            logger.debug(f"Created analysis ID: {analysis_id}")
            
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(TEMP_UPLOAD_FOLDER, filename)
            logger.debug(f"Saving file to: {filepath}")
            file.save(filepath)
            
            # Get user-provided information
            height = request.form.get('height', 0)
            weight = request.form.get('weight', 0)
            gender = request.form.get('gender', 'male')  # Default to male if not specified
            experience = request.form.get('experience', 'beginner')
            
            logger.debug(f"User inputs - Height: {height}, Weight: {weight}, Gender: {gender}, Experience: {experience}")
            
            # Process the 3D scan
            scan_results = process_3d_scan(
                file_path=filepath,
                height_cm=float(height) if height else 0,
                weight_kg=float(weight) if weight else 0
            )
            
            if not scan_results:
                flash('Failed to process 3D scan. Please try again with a different file.', 'warning')
                return redirect(url_for('scan3d_page'))
            
            # Extra processing for measurements
            measurements = scan_results.get('measurements', {})
            
            # Combine measurements with body composition data
            traits = measurements.copy()
            traits.update(scan_results.get('body_composition', {}))
            
            # Generate recommendations based on the 3D scan traits
            recommendations = generate_recommendations(traits, experience)
            
            # Store results
            # For demo purposes, we'll use a placeholder image path
            image_path = os.path.join(TEMP_UPLOAD_FOLDER, f"3d_model_{analysis_id}.jpg")
            
            analysis_results[analysis_id] = {
                'image_path': image_path,
                'traits': traits,
                'recommendations': recommendations,
                'user_info': {
                    'height': height,
                    'weight': weight,
                    'gender': gender,
                    'experience': experience
                },
                'scan_data': {
                    'file_path': filepath,
                    'file_format': os.path.splitext(filepath)[1]
                },
                'analysis_type': '3d_scan'  # Flag to indicate this is a 3D scan analysis
            }
            
            # For the prototype, we won't clean up the original 3D scan file
            # in case we need to access it again
            
            return redirect(url_for('scan3d_results', analysis_id=analysis_id))
            
        except Exception as e:
            logger.error(f"Error during 3D scan analysis: {str(e)}")
            flash(f'Error during analysis: {str(e)}', 'danger')
            return redirect(url_for('scan3d_page'))
    else:
        flash('Invalid file type. Please upload OBJ, STL, or PLY 3D model files.', 'warning')
        return redirect(url_for('scan3d_page'))

@app.route('/scan3d/results/<analysis_id>')
def scan3d_results(analysis_id):
    """Display 3D scan analysis results"""
    if analysis_id not in analysis_results:
        flash('Analysis not found', 'danger')
        return redirect(url_for('scan3d_page'))
    
    result = analysis_results[analysis_id]
    
    # Check if this is a 3D scan analysis
    if result.get('analysis_type') != '3d_scan':
        flash('Invalid analysis type', 'danger')
        return redirect(url_for('scan3d_page'))
    
    # For this prototype version, we'll use a placeholder image
    # In a real implementation, we would generate a visualization of the 3D model
    img_b64 = None
    
    # Process traits to include their units
    formatted_traits = {}
    for trait_name, trait_data in result['traits'].items():
        # For traits that are dictionaries with value keys
        if isinstance(trait_data, dict) and 'value' in trait_data:
            # Copy the trait data
            formatted_trait = trait_data.copy()
            # Format the value with units
            formatted_trait['display_value'] = format_trait_value(trait_name, trait_data['value'])
            formatted_trait['unit'] = get_unit(trait_name)
            formatted_traits[trait_name] = formatted_trait
        else:
            # For other types of traits
            formatted_traits[trait_name] = trait_data
    
    return render_template(
        'scan3d_results_enhanced.html',
        analysis_id=analysis_id,
        traits=formatted_traits,
        recommendations=result['recommendations'],
        user_info=result['user_info'],
        image_data=img_b64,
        scan_data=result.get('scan_data', {}),
        format_value=format_trait_value  # Pass the formatter to the template
    )

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

# User authentication and profile routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Display login page and process login form submissions"""
    if request.method == 'POST':
        # In a real implementation, this would validate against a database
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # For demo purposes, accept any login
        flash('Login successful!', 'success')
        session['logged_in'] = True
        session['user_email'] = email
        session['user_name'] = email.split('@')[0]  # Simple name extraction from email
        return redirect(url_for('profile'))
    
    return render_template('login.html')

@app.route('/google_login')
def google_login():
    """Start Google OAuth login process"""
    # In a real implementation, this would redirect to Google OAuth
    flash('Google login would be implemented with OAuth in production.', 'info')
    session['logged_in'] = True
    session['user_email'] = 'user@example.com'
    session['user_name'] = 'Google User'
    return redirect(url_for('profile'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Display signup page and process signup form submissions"""
    if request.method == 'POST':
        # In a real implementation, this would create a user in the database
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # For demo purposes, accept any signup
        flash('Account created successfully!', 'success')
        session['logged_in'] = True
        session['user_email'] = email
        session['user_name'] = fullname
        return redirect(url_for('profile'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Process user logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    """Display user profile page"""
    # Check if user is logged in
    if not session.get('logged_in'):
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
    
    # Create a mock user for demo purposes
    user = {
        'fullname': session.get('user_name', 'John Doe'),
        'email': session.get('user_email', 'john.doe@example.com'),
        'joined': 'March 2025',
        'height': 178,
        'weight': 75,
        'gender': 'male',
        'age': 30,
        'experience': 'intermediate',
        'goal': 'gain_muscle',
        'analyses': [
            {'id': 'abc123', 'date': 'Mar 24, 2025', 'type': 'photo'},
            {'id': 'def456', 'date': 'Mar 22, 2025', 'type': '3d_scan'},
            {'id': 'ghi789', 'date': 'Mar 15, 2025', 'type': 'photo'}
        ]
    }
    
    return render_template('profile.html', user=user)

@app.route('/update_body_info', methods=['POST'])
def update_body_info():
    """Update user body information"""
    # Check if user is logged in
    if not session.get('logged_in'):
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    # In a real implementation, this would update the user in the database
    # For demo purposes, just return success
    return redirect(url_for('profile'))

@app.route('/account_settings')
def account_settings():
    """Display account settings page"""
    # Check if user is logged in
    if not session.get('logged_in'):
        flash('Please log in to view your account settings.', 'warning')
        return redirect(url_for('login'))
    
    # In a real implementation, this would retrieve the user from the database
    return render_template('account_settings.html')

@app.route('/recommendations/<analysis_id>')
def recommendations(analysis_id):
    """Display personalized recommendations based on analysis results"""
    # Check if analysis exists
    if analysis_id not in analysis_results:
        flash('Analysis not found', 'danger')
        return redirect(url_for('profile'))
    
    result = analysis_results[analysis_id]
    
    return render_template(
        'recommendations.html',
        analysis_id=analysis_id,
        traits=result['traits'],
        recommendations=result['recommendations'],
        user_info=result['user_info']
    )

@app.route('/schedule_analysis')
def schedule_analysis():
    """Schedule next analysis"""
    # In a real implementation, this would schedule an analysis
    flash('Feature coming soon: Schedule your next analysis.', 'info')
    return redirect(url_for('profile'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
