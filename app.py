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
from utils.bodybuilding_metrics import (
    calculate_body_fat_percentage, 
    calculate_lean_body_mass, 
    calculate_fat_free_mass_index,
    calculate_normalized_ffmi,
    analyze_shoulder_to_waist_ratio,
    analyze_arm_symmetry,
    analyze_muscle_balance,
    analyze_bodybuilding_potential,
    formulate_bodybuilding_recommendations
)
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
    """Render the main page with the Tailwind UI"""
    return render_template('tailwind_index.html')
    
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
        'tailwind_results.html',
        analysis_id=analysis_id,
        traits=formatted_traits,
        recommendations=result['recommendations'],
        user_info=result['user_info'],
        image_data=img_b64,
        format_value=format_trait_value,  # Pass the formatter to the template
        is_3d_scan=False  # Flag to indicate this is not a 3D scan analysis
    )

@app.route('/education')
def education():
    """Display educational content about genetic traits in fitness"""
    return render_template('tailwind_education.html')
    
@app.route('/bodybuilding-metrics', methods=['GET', 'POST'])
def bodybuilding_metrics():
    """Calculate and display bodybuilding-specific metrics and analytics"""
    results = None
    
    if request.method == 'POST':
        try:
            # Extract user input from form
            gender = request.form.get('gender', 'male')
            age = int(request.form.get('age', 0))
            height = float(request.form.get('height', 0))
            weight = float(request.form.get('weight', 0))
            experience = request.form.get('experience', 'beginner')
            goal = request.form.get('goal', 'build_muscle')
            
            # Extract body measurements
            neck = float(request.form.get('neck', 0))
            shoulders = float(request.form.get('shoulders', 0))
            chest = float(request.form.get('chest', 0))
            waist = float(request.form.get('waist', 0))
            hips = float(request.form.get('hips', 0))
            left_arm = float(request.form.get('left_arm', 0))
            right_arm = float(request.form.get('right_arm', 0))
            left_forearm = float(request.form.get('left_forearm', 0))
            right_forearm = float(request.form.get('right_forearm', 0))
            left_thigh = float(request.form.get('left_thigh', 0))
            right_thigh = float(request.form.get('right_thigh', 0))
            left_calf = float(request.form.get('left_calf', 0))
            right_calf = float(request.form.get('right_calf', 0))
            wrist = float(request.form.get('wrist', 0))
            ankle = float(request.form.get('ankle', 0))
            
            # Store basic measurements in session for convenience on future visits
            session['age'] = age
            session['height'] = height
            session['weight'] = weight
            
            # Calculate body composition metrics
            body_fat_percentage = calculate_body_fat_percentage(
                weight_kg=weight, 
                height_cm=height, 
                age=age, 
                gender=gender, 
                neck_cm=neck, 
                waist_cm=waist, 
                hip_cm=hips if gender.lower() == 'female' else None
            )
            
            # If we couldn't calculate bf% with Navy method, use the simplified formula
            if body_fat_percentage is None:
                body_fat_percentage = estimate_bodyfat_from_measurements(
                    gender=gender,
                    waist_cm=waist,
                    neck_cm=neck,
                    height_cm=height,
                    hip_cm=hips if gender.lower() == 'female' else None
                )
                # If still None, provide a fallback based on gender (middle range)
                if body_fat_percentage is None:
                    body_fat_percentage = 18.0 if gender.lower() == 'male' else 25.0
            
            # Calculate lean body mass
            lbm = calculate_lean_body_mass(weight, body_fat_percentage)
            
            # Calculate FFMI (Fat-Free Mass Index)
            ffmi = calculate_fat_free_mass_index(lbm, height)
            
            # Calculate normalized FFMI (adjusted for height)
            norm_ffmi = calculate_normalized_ffmi(ffmi, height)
            
            # Determine body fat category
            if gender.lower() == 'male':
                if body_fat_percentage < 6:
                    bf_category = "Competition Ready"
                elif 6 <= body_fat_percentage < 10:
                    bf_category = "Athletic"
                elif 10 <= body_fat_percentage < 15:
                    bf_category = "Fit"
                elif 15 <= body_fat_percentage < 20:
                    bf_category = "Average"
                elif 20 <= body_fat_percentage < 25:
                    bf_category = "Above Average"
                else:
                    bf_category = "Obese"
            else:  # female
                if body_fat_percentage < 12:
                    bf_category = "Competition Ready"
                elif 12 <= body_fat_percentage < 17:
                    bf_category = "Athletic"
                elif 17 <= body_fat_percentage < 22:
                    bf_category = "Fit"
                elif 22 <= body_fat_percentage < 27:
                    bf_category = "Average"
                elif 27 <= body_fat_percentage < 32:
                    bf_category = "Above Average"
                else:
                    bf_category = "Obese"
            
            # Determine FFMI category
            if gender.lower() == 'male':
                if norm_ffmi < 18:
                    ffmi_category = "Below Average"
                elif 18 <= norm_ffmi < 20:
                    ffmi_category = "Average"
                elif 20 <= norm_ffmi < 22:
                    ffmi_category = "Above Average"
                elif 22 <= norm_ffmi < 25:
                    ffmi_category = "Excellent"
                else:
                    ffmi_category = "Exceptional"
            else:  # female
                if norm_ffmi < 15:
                    ffmi_category = "Below Average"
                elif 15 <= norm_ffmi < 17:
                    ffmi_category = "Average"
                elif 17 <= norm_ffmi < 19:
                    ffmi_category = "Above Average"
                elif 19 <= norm_ffmi < 21:
                    ffmi_category = "Excellent"
                else:
                    ffmi_category = "Exceptional"
            
            # Compile all measurements for analysis
            measurements = {
                'neck': neck,
                'shoulders': shoulders,
                'chest': chest,
                'waist': waist,
                'hips': hips,
                'left_arm': left_arm,
                'right_arm': right_arm,
                'left_forearm': left_forearm,
                'right_forearm': right_forearm,
                'left_thigh': left_thigh,
                'right_thigh': right_thigh,
                'left_calf': left_calf,
                'right_calf': right_calf,
                'wrist': wrist,
                'ankle': ankle
            }
            
            # Analyze muscle balance
            muscle_balance = analyze_muscle_balance(measurements)
            
            # Analyze arm and leg symmetry
            arm_symmetry = analyze_arm_symmetry(left_arm, right_arm)
            # Use the same function for leg symmetry
            leg_symmetry = analyze_arm_symmetry(left_thigh, right_thigh)
            
            # If we have shoulder and waist measurements, check shoulder-to-waist ratio
            if shoulders > 0 and waist > 0:
                shoulder_to_waist = analyze_shoulder_to_waist_ratio(shoulders, waist)
            else:
                shoulder_to_waist = None
            
            # Analyze genetic potential if we have wrist and ankle measurements
            if wrist > 0 and ankle > 0:
                genetic_potential = analyze_bodybuilding_potential(height, wrist, ankle, gender)
            else:
                genetic_potential = None
            
            # Create user data dictionary for recommendations
            user_data = {
                'gender': gender,
                'age': age,
                'height': height,
                'weight': weight,
                'body_fat': body_fat_percentage,
                'experience': experience,
                'goal': goal
            }
            
            # Generate recommendations
            recommendations = formulate_bodybuilding_recommendations(
                {
                    'body_fat_percentage': body_fat_percentage,
                    'muscle_balance': muscle_balance,
                    'genetic_potential': genetic_potential['genetic_potential'] if genetic_potential else {'rating': 'average'}
                }, 
                user_data
            )
            
            # Organize results
            results = {
                'body_composition': {
                    'body_fat_percentage': body_fat_percentage,
                    'body_fat_category': bf_category,
                    'lean_body_mass': lbm,
                    'ffmi': norm_ffmi,
                    'ffmi_category': ffmi_category
                },
                'muscle_balance': muscle_balance if muscle_balance else {},
                'symmetry': {
                    'arm_symmetry': arm_symmetry if arm_symmetry else {},
                    'leg_symmetry': leg_symmetry if leg_symmetry else {}
                },
                'genetic_potential': genetic_potential['genetic_potential'] if genetic_potential else {},
                'max_measurements': genetic_potential['max_measurements'] if genetic_potential and 'max_measurements' in genetic_potential else {},
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error processing bodybuilding metrics: {str(e)}")
            flash(f"Error calculating metrics: {str(e)}", "danger")
    
    return render_template('tailwind_bodybuilding_metrics.html', results=results)

@app.route('/scan3d')
def scan3d():
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
        return redirect(url_for('scan3d'))
    
    file = request.files['scan_file']
    logger.debug(f"File object: {file}, filename: {file.filename}")
    
    if file.filename == '':
        logger.error("Empty filename")
        flash('No file selected', 'danger')
        return redirect(url_for('scan3d'))
    
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
                return redirect(url_for('scan3d'))
            
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
            return redirect(url_for('scan3d'))
    else:
        flash('Invalid file type. Please upload OBJ, STL, or PLY 3D model files.', 'warning')
        return redirect(url_for('scan3d'))

@app.route('/scan3d/results/<analysis_id>')
def scan3d_results(analysis_id):
    """Display 3D scan analysis results"""
    if analysis_id not in analysis_results:
        flash('Analysis not found', 'danger')
        return redirect(url_for('scan3d'))
    
    result = analysis_results[analysis_id]
    
    # Check if this is a 3D scan analysis
    if result.get('analysis_type') != '3d_scan':
        flash('Invalid analysis type', 'danger')
        return redirect(url_for('scan3d'))
    
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
        'tailwind_results.html',
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
        if trait in result['traits']:
            trait_data = result['traits'][trait]
            # Format trait name for display
            display_name = ' '.join(word.capitalize() for word in trait.split('_'))
            chart_data['labels'].append(display_name)
            
            # Handle both dictionary trait data with 'rating' key and string trait data that directly contains the rating
            if isinstance(trait_data, dict) and 'rating' in trait_data:
                # Dictionary trait data
                rating = trait_data['rating']
            elif isinstance(trait_data, str) and trait_data in color_map:
                # String trait data that directly contains the rating
                rating = trait_data
            else:
                # Default case
                rating = 'informational'
            
            # Determine numerical value and color
            numeric_value = {
                'excellent': 90,
                'good': 75,
                'average': 50,
                'below_average': 25,
                'informational': 50  # default for informational ratings
            }.get(rating, 50)
            
            chart_data['values'].append(numeric_value)
            chart_data['colors'].append(color_map.get(rating, 'rgba(108, 117, 125, 0.7)'))
    
    # Then, add body composition metrics if they exist
    for trait in body_comp_traits:
        if trait in result['traits']:
            trait_data = result['traits'][trait]
            
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
            
            # Handle both dictionary trait data with 'rating' key and string trait data
            if isinstance(trait_data, dict) and 'rating' in trait_data:
                # Dictionary trait data
                rating = trait_data['rating']
            elif isinstance(trait_data, str) and trait_data in color_map:
                # String trait data that directly contains the rating
                rating = trait_data
            else:
                # Default case
                rating = 'informational'
            
            # Process the value based on the rating
            if rating != 'informational':
                numeric_value = {
                    'excellent': 90,
                    'good': 75,
                    'average': 50,
                    'below_average': 25
                }.get(rating, 50)
                
                chart_data['values'].append(numeric_value)
                chart_data['colors'].append(color_map.get(rating, 'rgba(108, 117, 125, 0.7)'))
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
        'tailwind_results.html',
        analysis_id=analysis_id,
        traits=formatted_traits,
        recommendations=result['recommendations'],
        user_info=result['user_info'],
        image_data=None,
        format_value=format_trait_value,  # Pass the formatter to the template
        recommendations_view=True,  # Flag to indicate this is just recommendations view
        is_3d_scan=False  # Flag to indicate this is not a 3D scan
    )

@app.route('/nutrition/<analysis_id>')
def nutrition(analysis_id):
    """Display detailed nutrition plan based on analysis results"""
    try:
        # Start with detailed logging
        logger.info(f"Accessing nutrition page for analysis_id: {analysis_id}")
        
        # Check if analysis exists
        if analysis_id not in analysis_results:
            logger.warning(f"Analysis not found with ID: {analysis_id}")
            flash('Analysis not found', 'danger')
            return redirect(url_for('profile'))
        
        # Get the result
        result = analysis_results[analysis_id]
        logger.debug(f"Retrieved analysis result for ID: {analysis_id}")
        
        # Get user's body info for calorie calculations
        height_cm = result['user_info'].get('height', 0)
        weight_kg = result['user_info'].get('weight', 0)
        gender = result['user_info'].get('gender', 'male')
        experience = result['user_info'].get('experience', 'beginner')
        
        logger.debug(f"User info - Height: {height_cm}, Weight: {weight_kg}, Gender: {gender}, Experience: {experience}")
        
        # Get body fat percentage if available
        body_fat = 15  # Default value
        if 'body_fat_percentage' in result['traits']:
            trait_data = result['traits']['body_fat_percentage']
            if isinstance(trait_data, dict) and 'value' in trait_data:
                body_fat = trait_data['value']
            elif isinstance(trait_data, (int, float)):
                body_fat = trait_data
            
        logger.debug(f"Body fat percentage for calculation: {body_fat}%")
        
        # Process traits to include their units for display
        formatted_traits = {}
        for trait_name, trait_data in result['traits'].items():
            try:
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
            except Exception as trait_error:
                logger.error(f"Error formatting trait {trait_name}: {str(trait_error)}")
                # Put a placeholder so the template doesn't break
                formatted_traits[trait_name] = trait_data
        
        # Determine body type from traits if available
        body_type_data = result['traits'].get('body_type', 'balanced')
        if isinstance(body_type_data, dict):
            body_type = body_type_data.get('value', 'balanced')
        else:
            body_type = body_type_data
        
        logger.debug(f"Determined body type: {body_type}")
        
        # Define supplements based on goals and body type
        supplements = [
            {
                'name': 'Protein Powder',
                'description': 'Supports muscle recovery and growth, especially when whole food protein sources are limited.',
                'dosage': '20-30g per serving',
                'timing': 'Post-workout or between meals'
            },
            {
                'name': 'Creatine Monohydrate',
                'description': 'Enhances strength, power output, and muscle cell volumization.',
                'dosage': '5g daily',
                'timing': 'Any time of day, consistent daily use'
            },
            {
                'name': 'Vitamin D3',
                'description': 'Supports immune function, bone health, and hormonal regulation.',
                'dosage': '1000-5000 IU daily',
                'timing': 'With a meal containing fats'
            }
        ]
        
        # Add body-type specific supplements
        if body_type.lower() in ['endomorph', 'mesomorph-endomorph']:
            supplements.append({
                'name': 'Green Tea Extract',
                'description': 'May help with fat metabolism and provide energy without excessive stimulation.',
                'dosage': '500-1000mg daily',
                'timing': 'Morning or pre-workout'
            })
        elif body_type.lower() in ['ectomorph', 'mesomorph-ectomorph']:
            supplements.append({
                'name': 'Mass Gainer',
                'description': 'Higher calorie supplement to support weight gain and muscle building.',
                'dosage': '1-2 servings daily',
                'timing': 'Between meals or before bed'
            })
        
        # Define food recommendations based on body type
        food_recommendations = {
            'protein_sources': [
                'Chicken Breast (100-150g)',
                'Lean Beef (100-150g)',
                'Egg Whites (4-6)',
                'Greek Yogurt (200-250g)',
                'White Fish (100-150g)'
            ],
            'carb_sources': [
                'Brown Rice (50-75g uncooked)',
                'Sweet Potatoes (150-200g)',
                'Oats (40-60g uncooked)',
                'Fruits (1-2 pieces)',
                'Vegetables (unlimited greens)'
            ],
            'fat_sources': [
                'Avocado (½ - 1 medium)',
                'Nuts and Seeds (30g)',
                'Olive Oil (1-2 tablespoons)',
                'Fatty Fish (100-150g, 2-3x week)',
                'Nut Butters (1-2 tablespoons)'
            ]
        }
        
        # Define meal timing recommendations
        meals = [
            {
                'name': 'Breakfast',
                'timing': '7:00 - 8:00 AM',
                'calories': '25% of daily total',
                'protein': '25-30g',
                'carbs': '30-40g',
                'fats': '10-15g'
            },
            {
                'name': 'Lunch',
                'timing': '12:00 - 1:00 PM',
                'calories': '30% of daily total',
                'protein': '30-35g',
                'carbs': '40-50g',
                'fats': '15-20g'
            },
            {
                'name': 'Pre-Workout',
                'timing': '3:00 - 4:00 PM',
                'calories': '15% of daily total',
                'protein': '20g',
                'carbs': '30-40g',
                'fats': '5-10g'
            },
            {
                'name': 'Post-Workout',
                'timing': '5:30 - 6:30 PM',
                'calories': '20% of daily total',
                'protein': '25-30g',
                'carbs': '30-40g',
                'fats': '5-10g'
            },
            {
                'name': 'Evening Snack',
                'timing': '8:00 - 9:00 PM',
                'calories': '10% of daily total',
                'protein': '15-20g',
                'carbs': '5-10g',
                'fats': '5-10g'
            }
        ]
        
        # Nutrition tips based on body type
        nutrition_tips = [
            "Prioritize protein intake with every meal to support muscle recovery and growth.",
            "Time carbohydrates around your workouts for optimal performance and recovery.",
            "Include healthy fats throughout the day to support hormone production.",
            "Stay hydrated by drinking at least 3-4 liters of water daily.",
            "Aim for 80% whole, minimally processed foods and 20% flexibility for sustainability."
        ]
        
        # Add body-type specific nutrition tips
        if body_type.lower() in ['endomorph', 'mesomorph-endomorph']:
            nutrition_tips.append("As an endomorph, be particularly mindful of carbohydrate intake and focus on fiber-rich options.")
            nutrition_tips.append("Consider intermittent fasting or time-restricted eating to help manage calorie intake.")
        elif body_type.lower() in ['ectomorph', 'mesomorph-ectomorph']:
            nutrition_tips.append("As an ectomorph, you need higher calorie intake and carbs to support muscle growth.")
            nutrition_tips.append("Consider liquid calories (smoothies, shakes) to increase your overall calorie intake.")
        else:
            nutrition_tips.append("With your balanced body type, focus on consistency and quality of nutrients.")
            nutrition_tips.append("Monitor your response to different macro ratios to find your optimal balance.")
        
        # Basic BMR calculation using the Mifflin-St Jeor Equation
        try:
            if gender.lower() == 'male':
                bmr = 10 * float(weight_kg) + 6.25 * float(height_cm) - 5 * 25 + 5  # Assuming age 25 if not available
            else:
                bmr = 10 * float(weight_kg) + 6.25 * float(height_cm) - 5 * 25 - 161  # Assuming age 25 if not available
            
            # Adjust based on activity level (experience)
            activity_multipliers = {
                'beginner': 1.375,  # Light activity
                'intermediate': 1.55,  # Moderate activity
                'advanced': 1.725,  # Very active
            }
            activity_multiplier = activity_multipliers.get(experience, 1.375)
            
            # Calculate maintenance calories
            maintenance_calories = int(bmr * activity_multiplier)
            
            # Define target calories based on body type and inferred goals
            if body_type.lower() in ['endomorph', 'mesomorph-endomorph']:
                # Slight deficit for fat loss focus
                target_calories = int(maintenance_calories * 0.9)
            elif body_type.lower() in ['ectomorph', 'mesomorph-ectomorph']:
                # Surplus for muscle gain focus
                target_calories = int(maintenance_calories * 1.1)
            else:
                # Maintenance for recomposition
                target_calories = maintenance_calories
            
            # Create calorie recommendations structure
            calories = {
                'maintenance': f"{maintenance_calories}",
                'target': f"{target_calories}"
            }
            
            logger.debug(f"Calculated calorie recommendations: {calories}")
        except Exception as calc_error:
            logger.error(f"Error calculating calories: {str(calc_error)}")
            # Provide default values if calculation fails
            calories = {
                'maintenance': "2200",
                'target': "2200"
            }
        
        # Calculate macronutrient percentages and grams
        protein_percentage = 40
        carbs_percentage = 40
        fats_percentage = 20
        
        # Adjust macros based on body type
        if body_type.lower() in ['endomorph', 'mesomorph-endomorph']:
            protein_percentage = 45
            carbs_percentage = 30
            fats_percentage = 25
        elif body_type.lower() in ['ectomorph', 'mesomorph-ectomorph']:
            protein_percentage = 35
            carbs_percentage = 50
            fats_percentage = 15
            
        # Calculate macros in grams (simple calculation)
        try:
            target_cal = int(calories['target'])
            protein_grams = int((target_cal * (protein_percentage/100)) / 4)  # Protein has 4 calories per gram
            carbs_grams = int((target_cal * (carbs_percentage/100)) / 4)      # Carbs have 4 calories per gram
            fats_grams = int((target_cal * (fats_percentage/100)) / 9)        # Fats have 9 calories per gram
            
            macros = {
                'protein': f"{protein_grams}",
                'protein_percentage': protein_percentage,
                'carbs': f"{carbs_grams}",
                'carbs_percentage': carbs_percentage,
                'fats': f"{fats_grams}",
                'fats_percentage': fats_percentage
            }
        except Exception as macro_error:
            logger.error(f"Error calculating macros: {str(macro_error)}")
            # Default values
            macros = {
                'protein': "180",
                'protein_percentage': 40,
                'carbs': "180",
                'carbs_percentage': 40,
                'fats': "40",
                'fats_percentage': 20
            }
            
        # Prepare the context for the template
        context = {
            'analysis_id': analysis_id,
            'traits': formatted_traits,
            'body_type': body_type,
            'macros': macros,
            'calories': calories,
            'supplements': supplements,
            'meals': meals,
            'food_recommendations': food_recommendations,
            'nutrition_tips': nutrition_tips
        }
        
        # Log the key parts of context for debugging
        logger.info(f"Rendering nutrition template for analysis_id: {analysis_id} with calorie recommendations")
        
        # Render the template with the context
        return render_template('tailwind_nutrition_new.html', **context)
        
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error in nutrition endpoint for analysis_id {analysis_id}: {str(e)}")
        # Return a user-friendly error message
        flash('An error occurred while generating your nutrition plan. Please try again later.', 'danger')
        # Return a fallback error page or redirect 
        return render_template('error.html', error_message="We couldn't generate your nutrition plan right now. Our team is looking into it."), 500

@app.route('/workout/<analysis_id>')
def workout(analysis_id):
    """Display detailed workout plan based on analysis results and user's weak points"""
    try:
        # Start with detailed logging
        logger.info(f"Accessing workout page for analysis_id: {analysis_id}")
        
        # Check if analysis exists
        if analysis_id not in analysis_results:
            logger.warning(f"Analysis not found with ID: {analysis_id}")
            flash('Analysis not found', 'danger')
            return redirect(url_for('profile'))
        
        # Get the result
        result = analysis_results[analysis_id]
        logger.debug(f"Retrieved analysis result for ID: {analysis_id}")
        
        # Get user info and training experience
        experience = result['user_info'].get('experience', 'beginner')
        
        # Process traits to include their units for display
        formatted_traits = {}
        for trait_name, trait_data in result['traits'].items():
            try:
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
            except Exception as trait_error:
                logger.error(f"Error formatting trait {trait_name}: {str(trait_error)}")
                formatted_traits[trait_name] = trait_data
        
        # Get user genetic traits
        logger.debug(f"Processing user genetic traits for workout planning")
        
        # Get training split from recommendations or use default push/pull/legs
        training_split = result['recommendations'].get('training_split', {
            'Monday': 'Push (Chest, Shoulders, Triceps)',
            'Tuesday': 'Pull (Back, Biceps)',
            'Wednesday': 'Legs + Core',
            'Thursday': 'Rest & Recovery',
            'Friday': 'Push (Chest, Shoulders, Triceps)',
            'Saturday': 'Pull (Back, Biceps)',
            'Sunday': 'Legs (Posterior Chain Focus)'
        })
        
        # Identify weak points from traits for targeted training
        weak_points = []
        for trait_name, trait_data in result['traits'].items():
            if isinstance(trait_data, dict) and 'rating' in trait_data:
                # Handle dictionary trait data
                if trait_data['rating'] in ['below_average', 'average']:
                    weak_points.append({
                        'name': trait_name.replace('_', ' ').title(),
                        'rating': trait_data['rating'],
                        'value': trait_data.get('value', 0)
                    })
            elif isinstance(trait_data, str) and trait_data in ['below_average', 'average']:
                # Handle string trait data that directly contains the rating
                weak_points.append({
                    'name': trait_name.replace('_', ' ').title(),
                    'rating': trait_data,
                    'value': 0  # Default value since we don't have one
                })
        
        # Create workout structure
        push_exercises = [
            {'name': 'Bench Press', 'sets': '4', 'reps': '8-10', 'focus': 'Chest', 'category': 'push'},
            {'name': 'Incline Dumbbell Press', 'sets': '3', 'reps': '10-12', 'focus': 'Upper Chest', 'category': 'push'},
            {'name': 'Seated Shoulder Press', 'sets': '3', 'reps': '8-10', 'focus': 'Shoulders', 'category': 'push'},
            {'name': 'Lateral Raises', 'sets': '3', 'reps': '12-15', 'focus': 'Side Delts', 'category': 'push'},
            {'name': 'Tricep Pushdowns', 'sets': '3', 'reps': '10-12', 'focus': 'Triceps', 'category': 'push'},
            {'name': 'Overhead Tricep Extensions', 'sets': '3', 'reps': '10-12', 'focus': 'Triceps', 'category': 'push'}
        ]
        
        pull_exercises = [
            {'name': 'Pull-Ups/Lat Pulldowns', 'sets': '4', 'reps': '8-10', 'focus': 'Back Width', 'category': 'pull'},
            {'name': 'Bent Over Rows', 'sets': '3', 'reps': '10-12', 'focus': 'Back Thickness', 'category': 'pull'},
            {'name': 'Seated Cable Rows', 'sets': '3', 'reps': '10-12', 'focus': 'Mid Back', 'category': 'pull'},
            {'name': 'Face Pulls', 'sets': '3', 'reps': '12-15', 'focus': 'Rear Delts', 'category': 'pull'},
            {'name': 'Barbell Curls', 'sets': '3', 'reps': '10-12', 'focus': 'Biceps', 'category': 'pull'},
            {'name': 'Hammer Curls', 'sets': '3', 'reps': '10-12', 'focus': 'Biceps/Forearms', 'category': 'pull'}
        ]
        
        leg_exercises = [
            {'name': 'Squats', 'sets': '4', 'reps': '8-10', 'focus': 'Quads/Overall', 'category': 'legs'},
            {'name': 'Romanian Deadlifts', 'sets': '3', 'reps': '8-10', 'focus': 'Hamstrings/Glutes', 'category': 'legs'},
            {'name': 'Walking Lunges', 'sets': '3', 'reps': '10-12 per leg', 'focus': 'Quads/Balance', 'category': 'legs'},
            {'name': 'Leg Press', 'sets': '3', 'reps': '10-12', 'focus': 'Overall Legs', 'category': 'legs'},
            {'name': 'Calf Raises', 'sets': '4', 'reps': '15-20', 'focus': 'Calves', 'category': 'legs'},
            {'name': 'Leg Curls', 'sets': '3', 'reps': '12-15', 'focus': 'Hamstrings', 'category': 'legs'}
        ]
        
        posterior_focus = [
            {'name': 'Deadlifts', 'sets': '4', 'reps': '6-8', 'focus': 'Posterior Chain', 'category': 'legs'},
            {'name': 'Good Mornings', 'sets': '3', 'reps': '10-12', 'focus': 'Hamstrings/Lower Back', 'category': 'legs'},
            {'name': 'Glute Bridges', 'sets': '3', 'reps': '12-15', 'focus': 'Glutes', 'category': 'legs'},
            {'name': 'Back Extensions', 'sets': '3', 'reps': '12-15', 'focus': 'Lower Back/Glutes', 'category': 'legs'},
            {'name': 'Standing Calf Raises', 'sets': '4', 'reps': '15-20', 'focus': 'Calves', 'category': 'legs'},
            {'name': 'Seated Calf Raises', 'sets': '3', 'reps': '15-20', 'focus': 'Calves', 'category': 'legs'}
        ]
        
        core_exercises = [
            {'name': 'Planks', 'sets': '3', 'reps': '30-60 sec', 'focus': 'Core Stability', 'category': 'core'},
            {'name': 'Russian Twists', 'sets': '3', 'reps': '15 per side', 'focus': 'Obliques', 'category': 'core'},
            {'name': 'Hanging Leg Raises', 'sets': '3', 'reps': '10-15', 'focus': 'Lower Abs', 'category': 'core'}
        ]
        
        rest_day = [
            {'name': 'Light Cardio', 'sets': '1', 'reps': '20-30 min', 'focus': 'Recovery', 'category': 'rest'},
            {'name': 'Stretching', 'sets': '1', 'reps': '15-20 min', 'focus': 'Flexibility', 'category': 'rest'},
            {'name': 'Foam Rolling', 'sets': '1', 'reps': '10-15 min', 'focus': 'Muscle Recovery', 'category': 'rest'}
        ]
        
        # Specialized exercises for weak points
        specialized_exercises = {}
        specialized_exercises['shoulder_width'] = [
            {'name': 'Wide-Grip Upright Rows', 'sets': '3', 'reps': '10-12', 'focus': 'Lateral Delts', 'category': 'push'},
            {'name': 'Lateral Raises with Hold', 'sets': '3', 'reps': '12-15', 'focus': 'Side Delts', 'category': 'push'},
            {'name': 'Cable Lateral Raises', 'sets': '3', 'reps': '12-15', 'focus': 'Side Delts', 'category': 'push'}
        ]
        
        specialized_exercises['arm_development'] = [
            {'name': 'Close-Grip Bench Press', 'sets': '3', 'reps': '8-10', 'focus': 'Triceps', 'category': 'push'},
            {'name': 'Incline Dumbbell Curls', 'sets': '3', 'reps': '10-12', 'focus': 'Biceps', 'category': 'pull'},
            {'name': 'Rope Pushdowns', 'sets': '3', 'reps': '12-15', 'focus': 'Triceps', 'category': 'push'}
        ]
        
        specialized_exercises['chest_development'] = [
            {'name': 'Cable Crossovers', 'sets': '3', 'reps': '12-15', 'focus': 'Inner Chest', 'category': 'push'},
            {'name': 'Decline Push-Ups', 'sets': '3', 'reps': '12-15', 'focus': 'Lower Chest', 'category': 'push'},
            {'name': 'Dumbbell Flyes', 'sets': '3', 'reps': '12-15', 'focus': 'Chest Stretch', 'category': 'push'}
        ]
        
        specialized_exercises['back_width'] = [
            {'name': 'Wide-Grip Pull-Ups', 'sets': '3', 'reps': '8-10', 'focus': 'Lats Width', 'category': 'pull'},
            {'name': 'Straight-Arm Pulldowns', 'sets': '3', 'reps': '12-15', 'focus': 'Lats', 'category': 'pull'},
            {'name': 'Wide-Grip Seated Rows', 'sets': '3', 'reps': '10-12', 'focus': 'Back Width', 'category': 'pull'}
        ]
        
        specialized_exercises['leg_development'] = [
            {'name': 'Front Squats', 'sets': '3', 'reps': '8-10', 'focus': 'Quads', 'category': 'legs'},
            {'name': 'Bulgarian Split Squats', 'sets': '3', 'reps': '10-12 per leg', 'focus': 'Unilateral Legs', 'category': 'legs'},
            {'name': 'Hack Squats', 'sets': '3', 'reps': '10-12', 'focus': 'Quads', 'category': 'legs'}
        ]
        
        # Generate detailed weekly workout plan
        workout_plan = {}
        for day, focus in training_split.items():
            if 'Push' in focus:
                workout_plan[day] = {
                    'focus': focus,
                    'category': 'push',
                    'exercises': push_exercises.copy()
                }
            elif 'Pull' in focus:
                workout_plan[day] = {
                    'focus': focus,
                    'category': 'pull',
                    'exercises': pull_exercises.copy()
                }
            elif 'Legs' in focus and 'Posterior' in focus:
                workout_plan[day] = {
                    'focus': focus,
                    'category': 'legs',
                    'exercises': posterior_focus.copy()
                }
            elif 'Legs' in focus:
                workout_plan[day] = {
                    'focus': focus,
                    'category': 'legs',
                    'exercises': leg_exercises.copy() + core_exercises.copy()
                }
            elif 'Rest' in focus:
                workout_plan[day] = {
                    'focus': focus,
                    'category': 'rest',
                    'exercises': rest_day.copy()
                }
            else:
                workout_plan[day] = {
                    'focus': focus,
                    'category': 'other',
                    'exercises': []
                }
        
        # Add specialized exercises for weak points
        for weak_point in weak_points:
            name = weak_point['name'].lower()
            if 'shoulder' in name:
                # Add to push days
                for day, workout in workout_plan.items():
                    if workout['category'] == 'push':
                        workout['exercises'].extend(specialized_exercises['shoulder_width'])
                        break  # Add to just one push day
            elif 'arm' in name:
                # Add arm exercises to both push and pull days
                push_added = pull_added = False
                for day, workout in workout_plan.items():
                    if workout['category'] == 'push' and not push_added:
                        workout['exercises'].append(specialized_exercises['arm_development'][0])  # Tricep focus
                        push_added = True
                    elif workout['category'] == 'pull' and not pull_added:
                        workout['exercises'].append(specialized_exercises['arm_development'][1])  # Bicep focus
                        pull_added = True
                    if push_added and pull_added:
                        break
            elif 'chest' in name:
                # Add to push days
                for day, workout in workout_plan.items():
                    if workout['category'] == 'push':
                        workout['exercises'].extend(specialized_exercises['chest_development'])
                        break
            elif 'back' in name or 'lat' in name:
                # Add to pull days
                for day, workout in workout_plan.items():
                    if workout['category'] == 'pull':
                        workout['exercises'].extend(specialized_exercises['back_width'])
                        break
            elif 'leg' in name:
                # Add to leg days
                for day, workout in workout_plan.items():
                    if workout['category'] == 'legs':
                        workout['exercises'].extend(specialized_exercises['leg_development'])
                        break
                        
        # Prepare training tips based on experience level
        training_tips = []
        if experience == 'beginner':
            training_tips = [
                "Focus on learning proper form before adding significant weight",
                "Start with 2-3 sets per exercise, gradually increasing to 3-4 sets as you adapt",
                "Rest 90-120 seconds between sets to maintain proper form",
                "Aim for progressive overload by adding small weight increments weekly",
                "Stick to the basics - master compound movements before adding isolation work"
            ]
        elif experience == 'intermediate':
            training_tips = [
                "Incorporate periodization - alternate between strength and hypertrophy phases",
                "Implement supersets for antagonistic muscle groups to increase workout density",
                "Vary rep ranges between workouts (e.g., heavy day: 6-8 reps, volume day: 10-12 reps)",
                "Rest 60-90 seconds for isolation exercises, 2-3 minutes for heavy compound lifts",
                "Track your workouts to ensure consistent progression in weight, reps, or volume"
            ]
        else:  # advanced
            training_tips = [
                "Utilize advanced techniques like drop sets, rest-pause, and mechanical drop sets",
                "Implement specialized blocks focusing on lagging body parts",
                "Consider splitting push/pull workouts into chest/shoulders and back/arms days",
                "Vary exercise selection regularly while maintaining progressive overload",
                "Carefully manage fatigue with strategic deload weeks every 6-8 weeks"
            ]
            
        # Equipment recommendations based on experience
        equipment = [
            "Barbell and weight plates",
            "Dumbbells (adjustable or fixed set)",
            "Power rack or squat stand",
            "Bench (flat, adjustable if possible)",
            "Pull-up bar",
            "Resistance bands"
        ]
        
        if experience != 'beginner':
            equipment.extend([
                "Cable machine or functional trainer",
                "Kettlebells",
                "Specialized attachments (V-bar, rope, etc.)",
                "Foam roller and mobility tools"
            ])
            
        # Progressive overload methods
        progression_methods = [
            "Increase weight while maintaining reps",
            "Increase reps with the same weight",
            "Increase sets with the same weight/reps",
            "Decrease rest periods with the same weight/reps",
            "Improve exercise form and range of motion"
        ]
        
        if experience != 'beginner':
            progression_methods.extend([
                "Add tempo variations (slower eccentric phase)",
                "Increase training frequency",
                "Add advanced techniques (drop sets, rest-pause)",
                "Increase time under tension"
            ])
            
        # Prepare the context for the template
        context = {
            'analysis_id': analysis_id,
            'traits': formatted_traits,
            'weak_points': weak_points,
            'workout_plan': workout_plan,
            'training_tips': training_tips,
            'equipment': equipment,
            'progression_methods': progression_methods,
            'experience': experience,
            'split_type': 'Push/Pull/Legs'
        }
        
        # Log the key parts of context for debugging
        logger.info(f"Rendering workout template for analysis_id: {analysis_id}")
        
        # Render the template with the context
        return render_template('tailwind_workout_direct.html', **context)
        
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Error in workout endpoint for analysis_id {analysis_id}: {str(e)}")
        # Return a user-friendly error message
        flash('An error occurred while generating your workout plan. Please try again later.', 'danger')
        # Return a fallback error page or redirect
        return render_template('error.html', error_message="We couldn't generate your workout plan right now. Our team is looking into it."), 500

@app.route('/schedule_analysis')
def schedule_analysis():
    """Schedule next analysis"""
    # In a real implementation, this would schedule an analysis
    flash('Feature coming soon: Schedule your next analysis.', 'info')
    return redirect(url_for('profile'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
