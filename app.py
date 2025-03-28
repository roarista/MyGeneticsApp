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

# Import and register blueprints
from admin import admin_bp
app.register_blueprint(admin_bp)

# Import Google auth blueprint
try:
    from google_auth import google_auth
    app.register_blueprint(google_auth)
except ImportError:
    logger.warning("Google authentication module not available")

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
    """Render the main page - redirect to analyze form"""
    return redirect(url_for('analyze_form'))
    
@app.route('/modern')
def modern_index():
    """Render the modernized UI main page"""
    return render_template('tailwind_index.html')

@app.route('/tailwind')
def tailwind_index():
    """Render the Tailwind-inspired UI main page"""
    return render_template('tailwind_index.html')

@app.route('/analyze', methods=['GET'])
def analyze_form():
    """Display the photo upload form for body analysis"""
    return render_template('tailwind_analyze.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Process uploaded image and analyze body traits"""
    logger.debug("Received analyze request")
    
    # Ensure temp directory exists
    os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
    
    if 'file' not in request.files:
        logger.error("No file in request.files")
        flash('No file selected', 'danger')
        return redirect(url_for('analyze_form'))
    
    file = request.files['file']
    logger.debug(f"File object: {file}, filename: {file.filename}")
    
    if file.filename == '':
        logger.error("Empty filename")
        flash('No file selected', 'danger')
        return redirect(url_for('analyze_form'))
    
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
                return redirect(url_for('analyze_form'))
            
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
                return redirect(url_for('analyze_form'))
            
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
            return redirect(url_for('analyze_form'))
    else:
        flash('Invalid file type. Please upload PNG or JPG images.', 'warning')
        return redirect(url_for('analyze_form'))

@app.route('/results/<analysis_id>')
def results(analysis_id):
    """Display analysis results"""
    if analysis_id not in analysis_results:
        flash('Analysis not found', 'danger')
        return redirect(url_for('analyze_form'))
    
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
        'tailwind_analysis.html',
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
    return render_template('tailwind_education.html')

@app.route('/scan3d')
def scan3d_page():
    """Display the 3D body scan upload page"""
    return render_template('tailwind_scan3d.html')

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
        'tailwind_analysis.html',
        analysis_id=analysis_id,
        traits=formatted_traits,
        recommendations=result['recommendations'],
        user_info=result['user_info'],
        image_data=img_b64,
        scan_data=result.get('scan_data', {}),
        format_value=format_trait_value,  # Pass the formatter to the template
        is_3d_scan=True  # Flag to indicate this is a 3D scan analysis
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
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Query the database for the user
        from models import User
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Login the user with Flask-Login
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('profile')
            return redirect(next_page)
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    # Default to the Tailwind template
    return render_template('tailwind_login.html')

# Route to redirect to our Google auth blueprint
@app.route('/google_login')
def google_login():
    """Redirect to Google OAuth login process"""
    try:
        return redirect(url_for('google_auth.login'))
    except Exception as e:
        logger.error(f"Error redirecting to Google login: {str(e)}")
        flash('Google login is currently unavailable. Please try again later or use email login.', 'warning')
        return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Display signup page and process signup form submissions"""
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        from models import User
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('login'))
        
        # Create new user
        new_user = User(username=fullname, email=email)
        new_user.set_password(password)
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the new user
        login_user(new_user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Default to the Tailwind template
    return render_template('tailwind_signup.html')

@app.route('/logout')
@login_required
def logout():
    """Process user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('analyze_form'))

@app.route('/profile')
@login_required
def profile():
    """Display user profile page"""
    # Get the current user and their analyses from the database
    from models import Analysis
    
    # Get user's analyses
    analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.analysis_date.desc()).all()
    
    # Format analyses for the template
    formatted_analyses = []
    for analysis in analyses:
        formatted_analyses.append({
            'id': analysis.id,
            'date': analysis.analysis_date.strftime("%b %d, %Y"),
            'type': analysis.analysis_type
        })
    
    # Construct user data for the template
    user_data = {
        'fullname': current_user.username,
        'email': current_user.email,
        'joined': current_user.created_at.strftime("%B %Y"),
        'height': current_user.height_cm or 0,
        'weight': current_user.weight_kg or 0,
        'gender': current_user.gender or 'male',
        'experience': current_user.experience_level or 'beginner',
        'analyses': formatted_analyses
    }
    
    # Use the Tailwind template version
    return render_template('tailwind_profile.html', user=user_data)

@app.route('/update_body_info', methods=['POST'])
@login_required
def update_body_info():
    """Update user body information"""
    # Get form data
    height = request.form.get('height', 0)
    weight = request.form.get('weight', 0)
    gender = request.form.get('gender', 'male')
    experience = request.form.get('experience', 'beginner')
    
    # Update user in database
    current_user.height_cm = float(height) if height else None
    current_user.weight_kg = float(weight) if weight else None
    current_user.gender = gender
    current_user.experience_level = experience
    
    db.session.commit()
    
    flash('Body information updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/account_settings')
@login_required
def account_settings():
    """Display account settings page"""
    # Get any notification or privacy settings
    from models import NotificationSetting, PrivacySetting
    
    # Get or create notification settings
    notification_settings = NotificationSetting.query.filter_by(user_id=current_user.id).first()
    if not notification_settings:
        notification_settings = NotificationSetting(user_id=current_user.id)
        db.session.add(notification_settings)
        db.session.commit()
    
    # Get or create privacy settings
    privacy_settings = PrivacySetting.query.filter_by(user_id=current_user.id).first()
    if not privacy_settings:
        privacy_settings = PrivacySetting(user_id=current_user.id)
        db.session.add(privacy_settings)
        db.session.commit()
    
    # Use the Tailwind template version
    return render_template(
        'tailwind_account_settings.html',
        user=current_user,
        notification_settings=notification_settings,
        privacy_settings=privacy_settings
    )

@app.route('/recommendations/<analysis_id>')
def recommendations(analysis_id):
    """Display personalized recommendations based on analysis results"""
    # Check if analysis exists
    if analysis_id not in analysis_results:
        flash('Analysis not found', 'danger')
        return redirect(url_for('profile'))
    
    result = analysis_results[analysis_id]
    
    # Process traits to include their units for display
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
        'tailwind_analysis.html',
        analysis_id=analysis_id,
        traits=formatted_traits,
        recommendations=result['recommendations'],
        user_info=result['user_info'],
        image_data=None,
        format_value=format_trait_value,  # Pass the formatter to the template
        recommendations_view=True  # Flag to indicate this is just recommendations view
    )

@app.route('/schedule_analysis')
def schedule_analysis():
    """Schedule next analysis"""
    # In a real implementation, this would schedule an analysis
    flash('Feature coming soon: Schedule your next analysis.', 'info')
    return redirect(url_for('profile'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
