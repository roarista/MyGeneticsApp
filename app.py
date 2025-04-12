import os
import logging
import uuid
import tempfile
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import numpy as np
import cv2
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from replit import web
from replit.web import auth  # Import Replit Web Authentication

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Make Replit Auth available to templates
@app.context_processor
def inject_auth():
    return {'auth': auth, 'is_authenticated': is_authenticated}

# Add min and max functions to be available in templates
@app.context_processor
def utility_functions():
    def min_value(a, b):
        return min(a, b)
    
    def max_value(a, b):
        return max(a, b)
    
    def calculate_shoulder_to_waist_ratio(measurements):
        """Calculate shoulder-to-waist ratio from measurements"""
        if not measurements:
            return 1.6  # Default value
            
        sw = measurements.get('shoulder_width_cm')
        wc = measurements.get('waist_circumference_cm')
            
        if sw and wc and wc > 0:
            # Convert waist circumference to width (approximate)
            waist_width = wc / 3.14
            ratio = sw / waist_width
            return round(ratio, 2)
        return 1.6  # Default value if measurements aren't available
    
    return {'min': min_value, 'max': max_value, 'calculate_shoulder_to_waist_ratio': calculate_shoulder_to_waist_ratio}

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

# Initialize Replit Authentication
# The traditional Flask-Login is being replaced with Replit Auth

# Define a function to check if user is authenticated with Replit Auth
def is_authenticated():
    return auth.is_authenticated

# Define our own login_required decorator using Replit Auth
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth.is_authenticated:
            # Correct way to redirect to Replit login
            return redirect(f"https://replit.com/auth_with_repl_site?domain={web.get_origin()}")
        return f(*args, **kwargs)
    return decorated_function

# Import custom utility modules
from utils.image_processing import process_image, extract_body_landmarks
from utils.body_analysis import analyze_body_traits
from utils.recommendations import generate_recommendations
from utils.measurement_validator import MeasurementValidator

# Define upload folder
TEMP_UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
from utils.units import format_trait_value, get_unit
from utils.measurement_estimator import estimate_measurements
from utils.bodybuilding_metrics import complete_bodybuilding_analysis
from utils.bodybuilding_metrics import (
    calculate_body_fat_percentage, 
    calculate_lean_body_mass, 
    calculate_fat_free_mass_index,
    calculate_normalized_ffmi,
    analyze_shoulder_to_waist_ratio,
    analyze_arm_symmetry,
    analyze_muscle_balance,
    analyze_bodybuilding_potential,
    formulate_bodybuilding_recommendations,
    estimate_bodyfat_from_measurements
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

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Process uploaded front and back photos for comprehensive body analysis including 50 bodybuilding measurements"""
    # If it's a GET request, redirect to the homepage
    if request.method == 'GET':
        return redirect(url_for('index'))
    
    # Initialize variables to store file paths (for cleanup in case of error)
    front_filepath = None
    back_filepath = None
    
    try:
        logger.debug("Received analyze request")
        
        # Ensure temp directory exists
        os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
        
        # Check if required files are present
        if 'front_photo' not in request.files or 'back_photo' not in request.files:
            logger.error("Missing front or back photo in request.files")
            flash('Both front and back photos are required', 'danger')
            return redirect(url_for('index'))
        
        front_file = request.files['front_photo']
        back_file = request.files['back_photo']
        
        logger.debug(f"Front file: {front_file.filename}, Back file: {back_file.filename}")
        
        # Check for empty file names
        if front_file.filename == '' or back_file.filename == '':
            logger.error("Empty filename for one or both photos")
            flash('Both front and back photos are required', 'danger')
            return redirect(url_for('index'))
            
        # Validate file types
        if not (allowed_file(front_file.filename) and allowed_file(back_file.filename)):
            flash('Invalid file type. Please upload PNG or JPG images.', 'warning')
            return redirect(url_for('index'))
        
        # Create a unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        logger.debug(f"Created analysis ID: {analysis_id}")
        
        # Save files temporarily with error handling
        try:
            front_filename = secure_filename(front_file.filename)
            front_filepath = os.path.join(TEMP_UPLOAD_FOLDER, f"front_{analysis_id}_{front_filename}")
            logger.debug(f"Saving front photo to: {front_filepath}")
            front_file.save(front_filepath)
            
            back_filename = secure_filename(back_file.filename)
            back_filepath = os.path.join(TEMP_UPLOAD_FOLDER, f"back_{analysis_id}_{back_filename}")
            logger.debug(f"Saving back photo to: {back_filepath}")
            back_file.save(back_filepath)
        except Exception as e:
            logger.error(f"Failed to save uploaded files: {str(e)}")
            flash('Failed to process uploaded files', 'danger')
            return redirect(url_for('index'))
        
        # Process front image to get landmarks with error handling
        try:
            front_image = cv2.imread(front_filepath)
            if front_image is None:
                raise ValueError("Failed to read front image")
            
            # Process back image to get landmarks
            back_image = cv2.imread(back_filepath)
            if back_image is None:
                raise ValueError("Failed to read back image")
        except Exception as e:
            logger.error(f"Failed to process images: {str(e)}")
            flash('Failed to process uploaded images. Please try again with different photos.', 'danger')
            return redirect(url_for('index'))
        
        # Get user-provided information with validation
        try:
            height = request.form.get('height', 0)
            weight = request.form.get('weight', 0)
            age = request.form.get('age', 25)  # Default age if not provided
            gender = request.form.get('gender', 'male')  # Default to male if not specified
            experience = request.form.get('experience', 'beginner')
            
            # Convert to appropriate types with validation
            height_cm = float(height) if height else 0
            weight_kg = float(weight) if weight else 0
            age_years = int(age) if age else 25
            
            if not all([height_cm > 0, weight_kg > 0, age_years > 0]):
                flash('Height, weight, and age are required and must be positive values', 'danger')
                return redirect(url_for('index'))
                
            if height_cm < 100 or height_cm > 250:  # Reasonable height range in cm
                flash('Please enter a valid height between 100cm and 250cm', 'danger')
                return redirect(url_for('index'))
                
            if weight_kg < 30 or weight_kg > 300:  # Reasonable weight range in kg
                flash('Please enter a valid weight between 30kg and 300kg', 'danger')
                return redirect(url_for('index'))
                
            if age_years < 16 or age_years > 100:  # Reasonable age range
                flash('Please enter a valid age between 16 and 100 years', 'danger')
                return redirect(url_for('index'))
                
        except ValueError as e:
            logger.error(f"Invalid input values: {str(e)}")
            flash('Invalid height, weight, or age values', 'danger')
            return redirect(url_for('index'))
        
        logger.debug(f"User inputs - Height: {height_cm}, Weight: {weight_kg}, Age: {age_years}, Gender: {gender}, Experience: {experience}")
        
        # Extract landmarks from front image with error handling
        try:
            processed_front_image, front_landmarks, front_confidence_scores = extract_body_landmarks(
                image=front_image,
                height_cm=int(height_cm)
            )
            
            if front_landmarks is None:
                flash('No body detected in front image. Please try again with a clearer full-body image.', 'warning')
                return redirect(url_for('index'))
            
            # Extract landmarks from back image
            processed_back_image, back_landmarks, back_confidence_scores = extract_body_landmarks(
                image=back_image,
                height_cm=int(height_cm)
            )
            
            if back_landmarks is None:
                flash('No body detected in back image. Please try again with a clearer full-body image.', 'warning')
                return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Failed to extract body landmarks: {str(e)}")
            flash('Failed to analyze body landmarks. Please try again with clearer photos.', 'danger')
            return redirect(url_for('index'))
        
        # Create an analysis metadata to store confidence information
        analysis_metadata = {
            'front_confidence_scores': front_confidence_scores,
            'back_confidence_scores': back_confidence_scores,
            'measurement_system': 'metric',
            'processing_timestamp': datetime.now().isoformat(),
            'dual_photo_analysis': True
        }
        
        # Analyze body traits with error handling
        try:
            # Analyze body traits from front image
            front_traits = analyze_body_traits(
                landmarks=front_landmarks, 
                original_image=front_image,
                height_cm=height_cm, 
                weight_kg=weight_kg,
                gender=gender,  
                experience=experience,
                is_back_view=False
            )
            
            # Analyze body traits from back image
            back_traits = analyze_body_traits(
                landmarks=back_landmarks, 
                original_image=back_image,
                height_cm=height_cm, 
                weight_kg=weight_kg,
                gender=gender,  
                experience=experience,
                is_back_view=True
            )
        except Exception as e:
            logger.error(f"Failed to analyze body traits: {str(e)}")
            flash('Failed to analyze body traits. Please try again.', 'danger')
            return redirect(url_for('index'))
        
        # Combine traits from both views
        combined_traits = {**front_traits}
        for key, value in back_traits.items():
            if key in combined_traits:
                # If the same trait exists in both, take the one with higher confidence or average them
                if isinstance(value, dict) and isinstance(combined_traits[key], dict):
                    if 'confidence' in value and 'confidence' in combined_traits[key]:
                        if value['confidence'] > combined_traits[key]['confidence']:
                            combined_traits[key] = value
                    else:
                        # If no confidence scores, average the values if they are numeric
                        if 'value' in value and 'value' in combined_traits[key]:
                            try:
                                combined_value = (float(value['value']) + float(combined_traits[key]['value'])) / 2
                                combined_traits[key]['value'] = combined_value
                            except (ValueError, TypeError):
                                # Not numeric, keep the front view value
                                pass
            else:
                # Unique trait from back view
                combined_traits[key] = value
        
        # Add metadata to traits for display
        combined_traits['metadata'] = analysis_metadata
        
        # Generate recommendations based on combined traits
        recommendations = generate_recommendations(combined_traits, experience)
        
        # Store the processed images
        front_image_path = os.path.join(TEMP_UPLOAD_FOLDER, f"processed_front_{analysis_id}.jpg")
        cv2.imwrite(front_image_path, processed_front_image)
        
        back_image_path = os.path.join(TEMP_UPLOAD_FOLDER, f"processed_back_{analysis_id}.jpg")
        cv2.imwrite(back_image_path, processed_back_image)
        
        # Prepare base64 images for processing
        with open(front_filepath, "rb") as image_file:
            front_image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        with open(back_filepath, "rb") as image_file:
            back_image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Estimate body measurements from both images
        logger.debug("Estimating body measurements from front and back images...")
        front_measurements = estimate_measurements(
            image_data=front_image_data, 
            height_cm=height_cm, 
            weight_kg=weight_kg, 
            gender=gender, 
            experience=experience,
            view='front'
        )
        
        back_measurements = estimate_measurements(
            image_data=back_image_data, 
            height_cm=height_cm, 
            weight_kg=weight_kg, 
            gender=gender, 
            experience=experience,
            view='back'
        )
        
        # Combine measurements
        combined_measurements = {**front_measurements}
        for key, value in back_measurements.items():
            if key in combined_measurements:
                # For measurements that appear in both, use the more confident one or average
                if isinstance(value, dict) and isinstance(combined_measurements[key], dict):
                    if 'confidence' in value and 'confidence' in combined_measurements[key]:
                        if value['confidence'] > combined_measurements[key]['confidence']:
                            combined_measurements[key] = value
                    else:
                        # Average the values
                        if 'value' in value and 'value' in combined_measurements[key]:
                            try:
                                combined_value = (float(value['value']) + float(combined_measurements[key]['value'])) / 2
                                combined_measurements[key]['value'] = combined_value
                            except (ValueError, TypeError):
                                pass
            else:
                # Measurements only in back view
                combined_measurements[key] = value
        
        logger.debug(f"Combined measurements: {combined_measurements}")
        
        # Prepare user data for bodybuilding analysis
        user_data = {
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "gender": gender,
            "experience": experience
        }
        
        # Add estimated measurements to user data
        if combined_measurements:
            for key, value in combined_measurements.items():
                if isinstance(value, dict) and 'value' in value:
                    user_data[key] = value['value']
                else:
                    user_data[key] = value
        
        # Complete bodybuilding analysis
        logger.debug("Performing bodybuilding analysis...")
        bodybuilding_analysis = complete_bodybuilding_analysis(user_data)
        logger.debug("Bodybuilding analysis completed")
        
        # Initialize enhanced measurements variables
        enhanced_measurements = {}
        categorized_measurements = {}
        
        # Perform enhanced 50-measurements analysis
        logger.debug("Performing enhanced 50-measurements bodybuilding analysis...")
        try:
            from utils.enhanced_measurements import EnhancedMeasurementAnalyzer, categorize_measurements
            
            # Initialize the enhanced measurement analyzer
            enhanced_analyzer = EnhancedMeasurementAnalyzer()
            
            # Process enhanced measurements
            enhanced_measurements = enhanced_analyzer.analyze_photos(
                front_image=front_image,
                back_image=back_image,
                height_cm=height_cm,
                weight_kg=weight_kg,
                age=age_years,
                gender=gender
            )
            
            # Categorize the measurements for better display
            categorized_measurements = categorize_measurements(enhanced_measurements)
            
            logger.debug("Enhanced 50-measurements analysis completed successfully.")
            
        except Exception as e:
            logger.error(f"Error during enhanced measurements analysis: {str(e)}")
            flash('Note: Some advanced bodybuilding measurements could not be calculated.', 'warning')
            # enhanced_measurements and categorized_measurements are already initialized to empty dicts
        
        # Store all results
        analysis_results[analysis_id] = {
            'front_image_path': front_image_path,
            'back_image_path': back_image_path,
            'traits': combined_traits,
            'recommendations': recommendations,
            'user_info': {
                'height': height_cm,
                'weight': weight_kg,
                'age': age_years,
                'gender': gender,
                'experience': experience
            },
            'front_measurements': front_measurements,
            'back_measurements': back_measurements,
            'combined_measurements': combined_measurements,
            'enhanced_measurements': enhanced_measurements,        # Add enhanced 50 measurements
            'categorized_measurements': categorized_measurements,  # Add categorized measurements
            'bodybuilding_analysis': bodybuilding_analysis,
            'analysis_type': 'dual_photo'  # Flag to indicate this is a dual photo analysis
        }
        
        # Clean up original uploads
        if os.path.exists(front_filepath):
            os.remove(front_filepath)
        if os.path.exists(back_filepath):
            os.remove(back_filepath)
        
        return redirect(url_for('results', analysis_id=analysis_id))
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        # Clean up any remaining files
        try:
            for filepath in [front_filepath, back_filepath]:
                if os.path.exists(filepath):
                    os.remove(filepath)
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up files after error: {str(cleanup_error)}")
        
        flash(f'Error during analysis: {str(e)}', 'danger')
        
        # Clean up any files that might have been created
        try:
            if front_filepath and os.path.exists(front_filepath):
                os.remove(front_filepath)
            if back_filepath and os.path.exists(back_filepath):
                os.remove(back_filepath)
        except Exception as cleanup_error:
            logger.error(f"Error during file cleanup: {str(cleanup_error)}")
        
        return redirect(url_for('index'))

@app.route('/results/<analysis_id>')
def results(analysis_id):
    """Display analysis results"""
    try:
        if analysis_id not in analysis_results:
            flash('Analysis not found', 'danger')
            return redirect(url_for('index'))
        
        result = analysis_results[analysis_id]
        
        # Check what type of analysis this is
        analysis_type = result.get('analysis_type', 'single_photo')
        
        # Initialize image variables
        front_img_b64 = None
        back_img_b64 = None
        img_b64 = None
        
        # Create a default bodybuilding_analysis object with fallback values if not present
        if 'bodybuilding_analysis' not in result or not result['bodybuilding_analysis']:
            result['bodybuilding_analysis'] = {
                'body_fat_percentage': 0.0,
                'lean_body_mass': 0.0,
                'body_fat_mass': 0.0,
                'ffmi': 0.0,
                'body_type': 'Unknown',
                'muscle_building_potential': 0.0,
                'body_fat_confidence': 0.5,
                'muscle_building_confidence': 0.5
            }
            logger.warning("Missing bodybuilding_analysis object - using defaults")
        
        # Handle different types of analysis
        if analysis_type == 'dual_photo':
            try:
                # Read the processed front image if it exists
                if os.path.exists(result.get('front_image_path', '')):
                    with open(result['front_image_path'], 'rb') as f:
                        front_img_data = f.read()
                    front_img_b64 = base64.b64encode(front_img_data).decode('utf-8')
                
                # Read the processed back image if it exists
                if os.path.exists(result.get('back_image_path', '')):
                    with open(result['back_image_path'], 'rb') as f:
                        back_img_data = f.read()
                    back_img_b64 = base64.b64encode(back_img_data).decode('utf-8')
                
                # Use front image as main image, provide back image separately
                img_b64 = front_img_b64 if front_img_b64 else None
            except Exception as e:
                logger.error(f"Error reading image files: {str(e)}")
                # Continue without images
        
        # Process traits to include their units
        formatted_traits = {}
        for trait_name, trait_data in result.get('traits', {}).items():
            # Skip metadata
            if trait_name == 'metadata':
                formatted_traits[trait_name] = trait_data
                continue
                
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
        
        # Get measurements for display
        measurements = result.get('combined_measurements', {})
        
        # Create analysis object for template compatibility
        analysis = {
            'id': analysis_id,
            'body_fat_percentage': result['bodybuilding_analysis'].get('body_fat_percentage', 0),
            'body_type': result['bodybuilding_analysis'].get('body_type', 'Unknown'),
            'muscle_building_potential': result['bodybuilding_analysis'].get('muscle_building_potential', 0)
        }
        
        # Extract measurements from traits if available
        measurements = {}
        for trait_name, trait_data in result['traits'].items():
            if isinstance(trait_data, dict) and 'value' in trait_data:
                measurements[trait_name] = trait_data
                
        # Create basic measurements for display
        basic_measurements = {}
        if measurements:
            # Extract key measurements for the basic measurements panel
            basic_keys = ['height', 'weight', 'chest', 'waist', 'hips', 'shoulders']
            for key in basic_keys:
                if key in measurements:
                    basic_measurements[key.capitalize()] = measurements[key]
        
        # Get proportion measurements for the proportions panel
        proportion_measurements = {}
        if measurements:
            # Extract proportion metrics for display
            proportion_keys = ['shoulder_hip_ratio', 'waist_hip_ratio', 'arm_torso_ratio', 'leg_torso_ratio']
            for key in proportion_keys:
                if key in measurements:
                    proportion_measurements[key.replace('_', ' ').title()] = measurements[key]
        
        # Prepare circumference measurements (left and right)
        circumference_measurements_left = {}
        circumference_measurements_right = {}
        if measurements:
            # Left side measurements
            left_keys = ['left_arm_cm', 'left_thigh_cm', 'left_calf_cm']
            for key in left_keys:
                if key in measurements:
                    display_key = key.replace('left_', '').replace('_cm', '').capitalize()
                    circumference_measurements_left[display_key] = measurements[key]
            
            # Right side measurements
            right_keys = ['right_arm_cm', 'right_thigh_cm', 'right_calf_cm']
            for key in right_keys:
                if key in measurements:
                    display_key = key.replace('right_', '').replace('_cm', '').capitalize()
                    circumference_measurements_right[display_key] = measurements[key]
        
        # Template data
        template_data = {
            'analysis_id': analysis_id,
            'analysis': analysis,
            'traits': formatted_traits,
            'recommendations': result.get('recommendations', {}),
            'user_info': result.get('user_info', {}),
            'image_data': img_b64,
            'front_image': front_img_b64,  # Add front image
            'back_image': back_img_b64,    # Add back image
            'format_value': format_trait_value,
            'is_3d_scan': analysis_type == '3d_scan',
            'is_dual_photo': analysis_type == 'dual_photo',
            'bodybuilding_analysis': result['bodybuilding_analysis'],
            'estimated_measurements': measurements,
            'basic_measurements': basic_measurements,
            'proportion_measurements': proportion_measurements,
            'circumference_measurements_left': circumference_measurements_left,
            'circumference_measurements_right': circumference_measurements_right,
            'enhanced_measurements': result.get('enhanced_measurements', {}),
            'categorized_measurements': result.get('categorized_measurements', {}),
            'has_enhanced_measurements': bool(result.get('enhanced_measurements')),
            'top_advantages': result.get('recommendations', {}).get('top_advantages', [])[:5],
            
            # Calculate recovery capacity from user metrics
            'recovery_capacity': result.get('enhanced_measurements', {}).get('recovery_capacity', 5.0),
            'metabolic_efficiency': result.get('enhanced_measurements', {}).get('metabolic_efficiency', 5.0),
            
            # For Fitness Age Estimation chart
            'gender': result.get('user_info', {}).get('gender', 'male'),
            'position': result['bodybuilding_analysis'].get('body_type_position', 50),
            'body_type': result['bodybuilding_analysis'].get('body_type', 'balanced'),
            
            # Calculate shoulder-to-waist ratio with default fallback
            'shoulder_to_waist_ratio': utility_functions()['calculate_shoulder_to_waist_ratio'](result.get('enhanced_measurements', {}))
        }
        
        return render_template('tailwind_results_charts.html', **template_data)
        
    except Exception as e:
        logger.error(f"Error displaying results: {str(e)}")
        flash('Error displaying analysis results. Please try again.', 'danger')
        return redirect(url_for('index'))
    
@app.route('/education')
def education():
    """Display educational content about genetic traits in fitness"""
    return render_template('tailwind_education.html')

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
    
    # Create analysis object for template compatibility
    analysis = {
        'id': analysis_id,
        'body_fat_percentage': result.get('traits', {}).get('body_fat_percentage', 0),
        'body_type': result.get('traits', {}).get('body_type', 'Unknown'),
        'muscle_building_potential': result.get('traits', {}).get('muscle_building_potential', 0)
    }
    
    # Also create a bodybuilding object for the left panel
    bodybuilding = {
        'body_fat_percentage': analysis['body_fat_percentage'],
        'body_type': analysis['body_type'],
        'muscle_building_potential': analysis['muscle_building_potential']
    }
    
    # Extract measurements for display in the basic measurements panel
    measurements = result['traits']
    basic_measurements = {}
    if measurements:
        confidence_scores = measurements.get('confidence_scores', {})
        
        # Extract key measurements for the basic measurements panel
        basic_keys = ['height', 'weight', 'chest', 'waist', 'hips', 'shoulders']
        for key in basic_keys:
            if key in measurements:
                confidence_key = key.replace('_cm', '')
                
                # Get confidence level based on score
                score = confidence_scores.get(confidence_key, 0.6)
                if score >= 0.7:
                    confidence = 'high'
                elif score >= 0.4:
                    confidence = 'medium'
                else:
                    confidence = 'low'
                
                # Format with proper unit based on measurement type
                if key == 'height' or key == 'weight':
                    unit = 'cm' if key == 'height' else 'kg'
                    value_str = f"{measurements[key]:.1f} {unit}"
                else:
                    value_str = f"{measurements[key]:.1f} cm"
                
                basic_measurements[key.capitalize()] = {
                    'value': value_str,
                    'confidence': confidence
                }
    
    # Get proportion measurements for the proportions panel
    proportion_measurements = {}
    if measurements:
        confidence_scores = measurements.get('confidence_scores', {})
        
        # Extract proportion metrics for display
        proportion_keys = ['shoulder_hip_ratio', 'waist_hip_ratio', 'arm_torso_ratio', 'leg_torso_ratio']
        for key in proportion_keys:
            if key in measurements:
                confidence_key = key.replace('_ratio', '')
                
                # Get confidence level based on score
                score = confidence_scores.get(confidence_key, 0.6)
                if score >= 0.7:
                    confidence = 'high'
                elif score >= 0.4:
                    confidence = 'medium'
                else:
                    confidence = 'low'
                
                # Format ratio without unit
                value_str = f"{measurements[key]:.2f}"
                
                proportion_measurements[key.replace('_', ' ').title()] = {
                    'value': value_str,
                    'confidence': confidence
                }
    
    # Prepare circumference measurements (left and right)
    circumference_measurements_left = {}
    circumference_measurements_right = {}
    if measurements:
        # Use confidence scores from measurements or default to medium confidence
        confidence_scores = measurements.get('confidence_scores', {})
        
        # Left side measurements
        left_keys = ['left_arm_cm', 'left_thigh_cm', 'left_calf_cm']
        for key in left_keys:
            if key in measurements:
                display_key = key.replace('left_', '').replace('_cm', '').capitalize()
                confidence_key = key.replace('left_', '').replace('right_', '').replace('_cm', '')
                
                # Get confidence level based on score
                score = confidence_scores.get(confidence_key, 0.5)
                if score >= 0.7:
                    confidence = 'high'
                elif score >= 0.4:
                    confidence = 'medium'
                else:
                    confidence = 'low'
                
                # Format with value and confidence level
                circumference_measurements_left[display_key] = {
                    'value': f"{measurements[key]:.1f} cm",
                    'confidence': confidence
                }
                
        # Right side measurements
        right_keys = ['right_arm_cm', 'right_thigh_cm', 'right_calf_cm']
        for key in right_keys:
            if key in measurements:
                display_key = key.replace('right_', '').replace('_cm', '').capitalize()
                confidence_key = key.replace('left_', '').replace('right_', '').replace('_cm', '')
                
                # Get confidence level based on score
                score = confidence_scores.get(confidence_key, 0.5)
                if score >= 0.7:
                    confidence = 'high'
                elif score >= 0.4:
                    confidence = 'medium'
                else:
                    confidence = 'low'
                
                # Format with value and confidence level
                circumference_measurements_right[display_key] = {
                    'value': f"{measurements[key]:.1f} cm",
                    'confidence': confidence
                }
    
    return render_template(
        'tailwind_results_charts.html',
        analysis_id=analysis_id,
        analysis=analysis,  # Add analysis object for template compatibility
        traits=formatted_traits,
        recommendations=result['recommendations'],
        user_info=result['user_info'],
        image_data=img_b64,
        scan_data=result.get('scan_data', {}),
        format_value=format_trait_value,  # Pass the formatter to the template
        is_3d_scan=True,  # Flag to indicate this is a 3D scan analysis
        bodybuilding=bodybuilding,  # Bodybuilding metrics for left panel
        basic_measurements=basic_measurements,  # Basic measurements for the template
        estimated_measurements=measurements,  # All measurements
        proportion_measurements=proportion_measurements,  # Proportion measurements for the template
        circumference_measurements_left=circumference_measurements_left,  # Left side measurements
        circumference_measurements_right=circumference_measurements_right  # Right side measurements
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
@app.route('/login')
def login():
    """Redirect to Replit Auth login"""
    return redirect(f"https://replit.com/auth_with_repl_site?domain={web.get_origin()}")


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

@app.route('/signup')
def signup():
    """Redirect to Replit Auth login (same as login for Replit Auth)"""
    return redirect(f"https://replit.com/auth_with_repl_site?domain={web.get_origin()}")

@app.route('/logout')
def logout():
    """Redirect to Replit Auth logout"""
    return redirect("https://replit.com/logout")

@app.route('/profile')
@login_required
def profile():
    """Display user profile page"""
    # Get the current user and their analyses from the database
    from models import Analysis, User
    
    # Get the Replit Auth user ID
    replit_user_id = auth.user.id if auth.user else None
    
    # Find or create user in our database
    user = User.query.filter_by(username=f"replit_{replit_user_id}").first()
    if not user and replit_user_id:
        # Create a new user record for this Replit user
        user = User(
            username=f"replit_{replit_user_id}",
            email=auth.user.email or f"{replit_user_id}@replit.user"
        )
        db.session.add(user)
        db.session.commit()
    
    if not user:
        flash('User not found. Please log in again.', 'danger')
        return redirect(f"https://replit.com/auth_with_repl_site?domain={web.get_origin()}")
    
    # Get user's analyses
    analyses = Analysis.query.filter_by(user_id=user.id).order_by(Analysis.analysis_date.desc()).all()
    
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
        'fullname': auth.user.name if auth.user else user.username,
        'email': auth.user.email if auth.user else user.email,
        'joined': user.created_at.strftime("%B %Y") if user.created_at else 'N/A',
        'height': user.height_cm or 0,
        'weight': user.weight_kg or 0,
        'gender': user.gender or 'male',
        'experience': user.experience_level or 'beginner',
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
    
    # Get the Replit Auth user ID
    from models import User
    replit_user_id = auth.user.id if auth.user else None
    
    # Find the user in our database
    user = User.query.filter_by(username=f"replit_{replit_user_id}").first()
    if not user and replit_user_id:
        # Create a new user record for this Replit user
        user = User(
            username=f"replit_{replit_user_id}",
            email=auth.user.email or f"{replit_user_id}@replit.user"
        )
        db.session.add(user)
    
    if user:
        # Update user in database
        user.height_cm = float(height) if height else None
        user.weight_kg = float(weight) if weight else None
        user.gender = gender
        user.experience_level = experience
        
        db.session.commit()
        
        flash('Body information updated successfully!', 'success')
    else:
        flash('User not found. Please log in again.', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/account_settings')
@login_required
def account_settings():
    """Display account settings page"""
    # Get any notification or privacy settings
    from models import NotificationSetting, PrivacySetting, User
    
    # Get the Replit Auth user ID
    replit_user_id = auth.user.id if auth.user else None
    
    # Find or create user in our database
    user = User.query.filter_by(username=f"replit_{replit_user_id}").first()
    if not user and replit_user_id:
        # Create a new user record for this Replit user
        user = User(
            username=f"replit_{replit_user_id}",
            email=auth.user.email or f"{replit_user_id}@replit.user"
        )
        db.session.add(user)
        db.session.commit()
        
    if not user:
        flash('User not found. Please log in again.', 'danger')
        return redirect(f"https://replit.com/auth_with_repl_site?domain={web.get_origin()}")
    
    # Get or create notification settings
    notification_settings = NotificationSetting.query.filter_by(user_id=user.id).first()
    if not notification_settings:
        notification_settings = NotificationSetting(user_id=user.id)
        db.session.add(notification_settings)
        db.session.commit()
    
    # Get or create privacy settings
    privacy_settings = PrivacySetting.query.filter_by(user_id=user.id).first()
    if not privacy_settings:
        privacy_settings = PrivacySetting(user_id=user.id)
        db.session.add(privacy_settings)
        db.session.commit()
    
    # Construct user data for the template
    user_data = {
        'fullname': auth.user.name if auth.user else user.username,
        'email': auth.user.email if auth.user else user.email,
        'joined': user.created_at.strftime("%B %Y") if user.created_at else 'N/A',
        'height': user.height_cm or 0,
        'weight': user.weight_kg or 0,
        'gender': user.gender or 'male',
        'experience': user.experience_level or 'beginner',
        'id': user.id
    }
    
    # Use the Tailwind template version
    return render_template(
        'tailwind_account_settings.html',
        user=user_data,
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
    
    # Create analysis object for template compatibility
    analysis = {
        'id': analysis_id,
        'body_fat_percentage': result['bodybuilding_analysis'].get('body_fat_percentage', 0),
        'body_type': result['bodybuilding_analysis'].get('body_type', 'Unknown'),
        'muscle_building_potential': result['bodybuilding_analysis'].get('muscle_building_potential', 0)
    }
    
    # Also create a bodybuilding object for the left panel
    bodybuilding = {
        'body_fat_percentage': analysis['body_fat_percentage'],
        'body_type': analysis['body_type'],
        'muscle_building_potential': analysis['muscle_building_potential']
    }
    
    # Extract measurements from traits if available
    measurements = {}
    for trait_name, trait_data in result['traits'].items():
        if isinstance(trait_data, dict) and 'value' in trait_data:
            measurements[trait_name] = trait_data
            
    # Create basic measurements for display
    basic_measurements = {}
    if measurements:
        # Extract key measurements for the basic measurements panel
        basic_keys = ['height', 'weight', 'chest', 'waist', 'hips', 'shoulders']
        for key in basic_keys:
            if key in measurements:
                basic_measurements[key.capitalize()] = measurements[key]
    
    # Get proportion measurements for the proportions panel
    proportion_measurements = {}
    if measurements:
        # Extract proportion metrics for display
        proportion_keys = ['shoulder_hip_ratio', 'waist_hip_ratio', 'arm_torso_ratio', 'leg_torso_ratio']
        for key in proportion_keys:
            if key in measurements:
                proportion_measurements[key.replace('_', ' ').title()] = measurements[key]
    
    # Prepare circumference measurements (left and right)
    circumference_measurements_left = {}
    circumference_measurements_right = {}
    if measurements:
        # Left side measurements
        left_keys = ['left_arm_cm', 'left_thigh_cm', 'left_calf_cm']
        for key in left_keys:
            if key in measurements:
                display_key = key.replace('left_', '').replace('_cm', '').capitalize()
                circumference_measurements_left[display_key] = measurements[key]
        
        # Right side measurements
        right_keys = ['right_arm_cm', 'right_thigh_cm', 'right_calf_cm']
        for key in right_keys:
            if key in measurements:
                display_key = key.replace('right_', '').replace('_cm', '').capitalize()
                circumference_measurements_right[display_key] = measurements[key]
    
    return render_template(
        'tailwind_results_charts.html',
        analysis_id=analysis_id,
        analysis=analysis,  # Add analysis object for template compatibility
        bodybuilding=bodybuilding,  # Bodybuilding metrics for left panel
        traits=formatted_traits,
        recommendations=result['recommendations'],
        user_info=result['user_info'],
        image_data=None,
        format_value=format_trait_value,  # Pass the formatter to the template
        recommendations_view=True,  # Flag to indicate this is just recommendations view
        is_3d_scan=False,  # Flag to indicate this is not a 3D scan
        basic_measurements=basic_measurements,  # Basic measurements for the template
        estimated_measurements=measurements,  # All measurements
        proportion_measurements=proportion_measurements,  # Proportion measurements for the template
        circumference_measurements_left=circumference_measurements_left,  # Left side measurements
        circumference_measurements_right=circumference_measurements_right  # Right side measurements
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
            
        # Create analysis object for template compatibility
        analysis = {
            'id': analysis_id,
            'body_fat_percentage': body_fat,
            'body_type': body_type,
            'muscle_building_potential': result.get('bodybuilding_analysis', {}).get('muscle_building_potential', 0)
        }
        
        # Extract measurements from traits if available
        measurements = {}
        for trait_name, trait_data in result['traits'].items():
            if isinstance(trait_data, dict) and 'value' in trait_data:
                measurements[trait_name] = trait_data
        
        # Create basic measurements for display
        basic_measurements = {}
        if measurements:
            # Extract key measurements for the basic measurements panel
            basic_keys = ['height', 'weight', 'chest', 'waist', 'hips', 'shoulders']
            for key in basic_keys:
                if key in measurements:
                    basic_measurements[key.capitalize()] = measurements[key]
                    
        # Get proportion measurements for the proportions panel
        proportion_measurements = {}
        if measurements:
            # Extract proportion metrics for display
            proportion_keys = ['shoulder_hip_ratio', 'waist_hip_ratio', 'arm_torso_ratio', 'leg_torso_ratio']
            for key in proportion_keys:
                if key in measurements:
                    proportion_measurements[key.replace('_', ' ').title()] = measurements[key]
        
        # Prepare the context for the template
        # Prepare circumference measurements (left and right)
        circumference_measurements_left = {}
        circumference_measurements_right = {}
        if measurements:
            # Left side measurements
            left_keys = ['left_arm_cm', 'left_thigh_cm', 'left_calf_cm']
            for key in left_keys:
                if key in measurements:
                    display_key = key.replace('left_', '').replace('_cm', '').capitalize()
                    circumference_measurements_left[display_key] = measurements[key]
            
            # Right side measurements
            right_keys = ['right_arm_cm', 'right_thigh_cm', 'right_calf_cm']
            for key in right_keys:
                if key in measurements:
                    display_key = key.replace('right_', '').replace('_cm', '').capitalize()
                    circumference_measurements_right[display_key] = measurements[key]

        context = {
            'analysis_id': analysis_id,
            'analysis': analysis,  # Add analysis object for template compatibility
            'traits': formatted_traits,
            'body_type': body_type,
            'macros': macros,
            'calories': calories,
            'supplements': supplements,
            'meals': meals,
            'food_recommendations': food_recommendations,
            'nutrition_tips': nutrition_tips,
            'basic_measurements': basic_measurements,  # Basic measurements for the template
            'estimated_measurements': measurements,  # All measurements
            'proportion_measurements': proportion_measurements,  # Proportion measurements for the template
            'circumference_measurements_left': circumference_measurements_left,  # Left side measurements
            'circumference_measurements_right': circumference_measurements_right  # Right side measurements
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
        
        # Import our new smart workout generator
        from utils.workout_generator import generate_complete_workout_plan
        
        # Extract the body analysis data
        bodybuilding_analysis = {}
        
        # Try to extract muscle development data
        if 'bodybuilding_metrics' in result:
            bodybuilding_analysis = result['bodybuilding_metrics']
            logger.debug(f"Found bodybuilding metrics data")
        
        # Fallback to traits data if needed
        elif 'traits' in result:
            # Map traits to muscle development assessment
            traits = result['traits']
            muscle_traits = {
                'arm_development': traits.get('arm_strength', {}).get('value', 'Average') if isinstance(traits.get('arm_strength', {}), dict) else 'Average',
                'chest_development': traits.get('chest_development', {}).get('value', 'Average') if isinstance(traits.get('chest_development', {}), dict) else 'Average',
                'back_development': traits.get('back_strength', {}).get('value', 'Average') if isinstance(traits.get('back_strength', {}), dict) else 'Average',
                'shoulder_development': traits.get('shoulder_width', {}).get('value', 'Average') if isinstance(traits.get('shoulder_width', {}), dict) else 'Average',
                'legs_development': traits.get('leg_strength', {}).get('value', 'Average') if isinstance(traits.get('leg_strength', {}), dict) else 'Average',
                'core_development': traits.get('core_strength', {}).get('value', 'Average') if isinstance(traits.get('core_strength', {}), dict) else 'Average',
            }
            
            # Convert trait values to development levels
            muscle_development = {}
            for muscle, value in muscle_traits.items():
                level = "Average"  # Default
                if isinstance(value, (int, float)):
                    if value < 0.3:
                        level = "Needs Growth"
                    elif value > 0.7:
                        level = "Well Developed"
                    else:
                        level = "Average"
                elif isinstance(value, str):
                    if value.lower() in ["low", "poor", "below average"]:
                        level = "Needs Growth"
                    elif value.lower() in ["high", "excellent", "above average", "good"]:
                        level = "Well Developed"
                    else:
                        level = "Average"
                
                # Store in the proper format
                muscle_key = muscle.split('_')[0].capitalize()
                muscle_development[muscle_key] = level
            
            bodybuilding_analysis['muscle_development'] = muscle_development
            logger.debug(f"Created muscle development assessment from traits")
        
        # Get user info for experience level
        user_info = result.get('user_info', {})
        experience_level = user_info.get('experience', 'beginner')
        
        # Determine the user's primary goal
        goal = "muscle_gain"  # Default
        body_fat_percentage = result.get('body_fat_percentage', 20)
        
        # If high body fat, suggest fat loss as primary goal
        if body_fat_percentage > 25 and user_info.get('gender') == 'male':
            goal = "fat_loss"
        elif body_fat_percentage > 32 and user_info.get('gender') == 'female':
            goal = "fat_loss"
        
        # Generate the personalized workout plan
        logger.debug(f"Generating dynamic workout plan based on muscle development analysis")
        workout_plan = generate_complete_workout_plan(
            bodybuilding_analysis=bodybuilding_analysis,
            experience=experience_level,
            goal=goal
        )
        
        # Store the workout data in the session for use in the API
        if 'workout_data' not in session:
            session['workout_data'] = {}
        session['workout_data'][analysis_id] = workout_plan
        
        # For compatibility with the existing code
        analysis = {
            'weak_points': workout_plan['muscle_focus']['primary'],
            'average_points': workout_plan['muscle_focus']['secondary'], 
            'strong_points': workout_plan['muscle_focus']['maintenance']
        }
        
        # Training tips based on experience level
        training_tips = []
        if experience_level == 'beginner':
            training_tips = [
                "Focus on form before increasing weight",
                "Rest at least 48 hours between training the same muscle group",
                "Aim for progressive overload by adding weight or reps each week",
                "Start with compound exercises at the beginning of your workout",
                "Don't skip your warm-up sets"
            ]
        elif experience_level == 'intermediate':
            training_tips = [
                "Consider varying rep ranges (5-8, 8-12, 12-15) for different stimuli",
                "Track your workouts to ensure progressive overload",
                "Add intensity techniques like drop sets on your final set",
                "Focus more volume on lagging muscle groups",
                "Include deload weeks every 4-6 weeks of training"
            ]
        else:  # advanced
            training_tips = [
                "Implement periodization to avoid plateaus",
                "Consider specialized techniques like rest-pause, cluster sets, and mechanical drop sets",
                "Evaluate recovery markers (sleep quality, resting heart rate, motivation)",
                "Cycle intensity by alternating focus on volume, intensity and frequency",
                "Target specific portions of muscle groups (upper/lower chest, etc.)"
            ]
        
        # Equipment and progression methods
        equipment = ["Barbell", "Dumbbells", "Cable Machine", "Resistance Bands", "Body Weight"]
        progression_methods = ["Add weight", "Add reps", "Reduce rest time", "Increase volume", "Change tempo"]
        
        # Get muscle assessment results from our generated plan
        muscle_assessment = {
            'primary_focus': workout_plan['muscle_focus']['primary'],
            'secondary_focus': workout_plan['muscle_focus']['secondary'],
            'maintenance': workout_plan['muscle_focus']['maintenance']
        }
        
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
        
        # Get user genetic traits and experience
        logger.debug(f"Processing user genetic traits for workout planning")
        experience = experience_level  # Use the experience level variable we already defined
        
        # Use weak points identified by the workout planner
        weak_points = analysis['weak_points']
        
        # Create the basic measurements for the left panel
        basic_measurements = {}
        measurements = result.get('measurements', {})
        
        # Extract main measurements for display
        if measurements:
            basic_measurements = {
                'shoulder_width': measurements.get('shoulder_width_cm', 0),
                'chest_circumference': measurements.get('chest_circumference_cm', 0),
                'arm_circumference': measurements.get('arm_circumference_cm', 0),
                'waist_circumference': measurements.get('waist_circumference_cm', 0),
                'thigh_circumference': measurements.get('thigh_circumference_cm', 0),
                'calf_circumference': measurements.get('calf_circumference_cm', 0)
            }
        
        # Parse proportion measurements for display
        proportion_measurements = {}
        for key, value in measurements.items():
            if 'ratio' in key or 'proportion' in key:
                proportion_measurements[key] = value
        
        # Separate left and right side measurements for comparison
        circumference_measurements_left = {}
        circumference_measurements_right = {}
        
        for key, value in measurements.items():
            if 'left' in key and 'circumference' in key:
                # Clean up the key name for display
                display_key = key.replace('left_', '').replace('_cm', '').replace('_', ' ').title()
                circumference_measurements_left[display_key] = value
            elif 'right' in key and 'circumference' in key:
                # Clean up the key name for display
                display_key = key.replace('right_', '').replace('_cm', '').replace('_', ' ').title()
                circumference_measurements_right[display_key] = value
        
        # Template context with all required data
        context = {
            'analysis_id': analysis_id,
            'traits': formatted_traits,
            'weak_points': weak_points,
            'workout_plan': workout_plan,
            'training_tips': training_tips,
            'equipment': equipment,
            'progression_methods': progression_methods,
            'experience': experience,
            'split_type': 'Push/Pull/Legs',
            'muscle_assessment': muscle_assessment,  # Muscle development assessment
            'basic_measurements': basic_measurements,  # Basic measurements for the template
            'estimated_measurements': measurements,  # All measurements
            'proportion_measurements': proportion_measurements,  # Proportion measurements for the template
            'circumference_measurements_left': circumference_measurements_left,  # Left side measurements
            'circumference_measurements_right': circumference_measurements_right  # Right side measurements
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
        
@app.route('/api/workout/<analysis_id>/<day>')
def get_workout(analysis_id, day):
    """API endpoint to get a specific day's workout"""
    try:
        # Check if analysis exists
        if analysis_id not in analysis_results:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Get the workout plan from session if available
        if 'workout_data' in session and analysis_id in session['workout_data']:
            workout_plan = session['workout_data'][analysis_id]
            logger.debug(f"Retrieved workout plan from session for analysis_id {analysis_id}")
        else:
            # Generate a new workout plan
            # Import our workout generator
            from utils.workout_generator import generate_complete_workout_plan
            
            # Get the analysis result
            result = analysis_results[analysis_id]
            
            # Create bodybuilding analysis
            bodybuilding_analysis = {}
            
            # Try to extract muscle development data
            if 'bodybuilding_metrics' in result:
                bodybuilding_analysis = result['bodybuilding_metrics']
            elif 'traits' in result:
                # Map traits to muscle development assessment
                traits = result['traits']
                muscle_traits = {
                    'arm_development': traits.get('arm_strength', {}).get('value', 'Average') if isinstance(traits.get('arm_strength', {}), dict) else 'Average',
                    'chest_development': traits.get('chest_development', {}).get('value', 'Average') if isinstance(traits.get('chest_development', {}), dict) else 'Average',
                    'back_development': traits.get('back_strength', {}).get('value', 'Average') if isinstance(traits.get('back_strength', {}), dict) else 'Average',
                    'shoulder_development': traits.get('shoulder_width', {}).get('value', 'Average') if isinstance(traits.get('shoulder_width', {}), dict) else 'Average',
                    'legs_development': traits.get('leg_strength', {}).get('value', 'Average') if isinstance(traits.get('leg_strength', {}), dict) else 'Average',
                    'core_development': traits.get('core_strength', {}).get('value', 'Average') if isinstance(traits.get('core_strength', {}), dict) else 'Average',
                }
                
                # Convert trait values to development levels
                muscle_development = {}
                for muscle, value in muscle_traits.items():
                    level = "Average"  # Default
                    if isinstance(value, (int, float)):
                        if value < 0.3:
                            level = "Needs Growth"
                        elif value > 0.7:
                            level = "Well Developed"
                        else:
                            level = "Average"
                    elif isinstance(value, str):
                        if value.lower() in ["low", "poor", "below average"]:
                            level = "Needs Growth"
                        elif value.lower() in ["high", "excellent", "above average", "good"]:
                            level = "Well Developed"
                        else:
                            level = "Average"
                    
                    # Store in the proper format
                    muscle_key = muscle.split('_')[0].capitalize()
                    muscle_development[muscle_key] = level
                
                bodybuilding_analysis['muscle_development'] = muscle_development
            
            # Get user info for experience level
            user_info = result.get('user_info', {})
            experience_level = user_info.get('experience', 'beginner')
            
            # Determine the user's primary goal
            goal = "muscle_gain"
            body_fat_percentage = result.get('body_fat_percentage', 20)
            
            # Generate the workout plan
            workout_plan = generate_complete_workout_plan(
                bodybuilding_analysis=bodybuilding_analysis,
                experience=experience_level,
                goal=goal
            )
            
            # Store in session
            if 'workout_data' not in session:
                session['workout_data'] = {}
            session['workout_data'][analysis_id] = workout_plan
        
        # Try to get the requested day
        try:
            # Convert day number to index (1-based to 0-based)
            day_index = 0
            
            if day.isdigit():
                # If day is a number (1-7)
                day_index = int(day) - 1
            else:
                # If day is a day name (Monday, Tuesday, etc.)
                day_lower = day.lower()
                weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                
                for i, weekday in enumerate(weekdays):
                    if weekday in day_lower:
                        day_index = i
                        break
            
            # Ensure day_index is within bounds
            day_index = max(0, min(day_index, 6))
            
            # Get the workout for the requested day
            if 'workout_schedule' in workout_plan and len(workout_plan['workout_schedule']) > day_index:
                day_workout = workout_plan['workout_schedule'][day_index]
                
                # Format response
                formatted_exercises = []
                
                # Handle rest days
                if day_workout['focus'] == 'Rest Day' or day_workout['focus'] == 'Rest':
                    return jsonify({
                        'exercises': [],
                        'day': day,
                        'type': 'Rest',
                        'notes': 'Recovery day. Consider light cardio, stretching, or mobility work.'
                    })
                
                # Format exercises
                for exercise in day_workout['exercises']:
                    # Map priority level to color indicator
                    priority = exercise.get('priority', 'Average')
                    
                    status_indicator = '🟡'  # Default yellow (Average)
                    if priority == 'Needs Growth':
                        status_indicator = '🔴'  # Red
                    elif priority == 'Well Developed':
                        status_indicator = '🟢'  # Green
                    
                    formatted_exercise = {
                        'name': exercise['name'],
                        'focus': exercise['muscle'],
                        'sets': exercise['sets'],
                        'reps': exercise['reps'],
                        'rest': exercise['rest'],
                        'isPriority': priority == 'Needs Growth',  # High priority for muscles that need growth
                        'development_status': priority,
                        'status_indicator': status_indicator
                    }
                    formatted_exercises.append(formatted_exercise)
                
                return jsonify({
                    'exercises': formatted_exercises,
                    'day': day,
                    'type': day_workout['focus'],
                    'notes': day_workout.get('notes', '')
                })
            else:
                # Fallback for missing day
                return jsonify({
                    'exercises': [],
                    'day': day,
                    'type': 'Unknown',
                    'notes': 'No workout available for this day.'
                })
                
        except Exception as day_error:
            logger.error(f"Error processing day {day}: {str(day_error)}")
            return jsonify({
                'exercises': [],
                'day': day,
                'type': 'Error',
                'notes': 'Could not load workout for this day.'
            })
        
    except Exception as e:
        logger.error(f"Error generating workout for day {day}: {str(e)}")
        return jsonify({'error': 'Failed to generate workout'}), 500

@app.route('/schedule_analysis')
def schedule_analysis():
    """Schedule next analysis"""
    # In a real implementation, this would schedule an analysis
    flash('Feature coming soon: Schedule your next analysis.', 'info')
    return redirect(url_for('profile'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
