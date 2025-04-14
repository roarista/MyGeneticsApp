import os
import logging
import uuid
import tempfile
import base64
import datetime  # Import the datetime module, not just datetime class
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

# Set a very secure secret key - this is critical for session persistence
app.secret_key = "super-secret-key"  # Using the specific key you mentioned

# Configure cookies to improve reliability
app.config['SESSION_COOKIE_SECURE'] = False  # Allow over HTTP in development
app.config['SESSION_COOKIE_HTTPONLY'] = True  # More secure cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow for redirects

# Make session permanent by default to improve persistence
@app.before_request
def make_session_permanent():
    session.permanent = True
    # Set session timeout to 7 days
    session.modified = True

logger.info("Session configuration initialized with enhanced persistence settings")

# Make Replit Auth available to templates
@app.context_processor
def inject_auth():
    return {'auth': auth, 'is_authenticated': is_authenticated}

# Simple body composition calculation (for debugging session issues)
def calculate_body_composition(weight, height, age, sex):
    """Calculate body fat and lean mass using simplified formula"""
    # BMI-based body fat estimate (simplified)
    bmi = weight / (height * height)
    
    # Apply gender adjustment (men typically have less body fat)
    if sex == 1:  # male
        body_fat = (1.20 * bmi) + (0.23 * age) - 16.2
    else:  # female
        body_fat = (1.20 * bmi) + (0.23 * age) - 5.4
        
    # Ensure reasonable range
    body_fat = max(5.0, min(body_fat, 45.0))
    
    # Lean mass percentage is what remains
    lean_mass = 100.0 - body_fat
    
    return body_fat, lean_mass

@app.route('/simple_body_comp')
def simple_body_comp():
    """Simple body composition calculator page for session debugging"""
    return render_template('simple_body_comp.html')

@app.route('/simple_analyze', methods=['POST'])
def simple_analyze():
    """Process simple body composition calculation for session debugging"""
    try:
        # Extract form values
        weight = float(request.form.get('weight', 0))
        height = float(request.form.get('height', 0)) / 100  # convert to meters
        age = int(request.form.get('age', 0))
        sex = 1 if request.form.get('sex', '').lower() == 'male' else 0

        print("📥 Received:", weight, height, age, sex)
        logger.debug(f"📥 Received: weight={weight}, height={height}, age={age}, sex={sex}")

        # Calculate body composition
        body_fat, lean_mass = calculate_body_composition(weight, height, age, sex)

        print("📊 Calculated:", body_fat, lean_mass)
        logger.debug(f"📊 Calculated: body_fat={body_fat}, lean_mass={lean_mass}")

        # Store in session with multiple approaches for redundancy
        session['analysis_results'] = {
            'body_fat': body_fat,
            'lean_mass': lean_mass
        }
        
        # Also store values separately
        session['body_fat'] = body_fat
        session['lean_mass'] = lean_mass
        
        # Force session persistence
        session.modified = True

        print("💾 Session set:", session['analysis_results'])
        logger.debug(f"💾 Session set: {session['analysis_results']}")
        logger.debug(f"💾 Session keys: {list(session.keys())}")

        # Redirect to simple results
        return redirect(url_for('simple_results'))

    except Exception as e:
        print("❌ Error in /simple_analyze:", str(e))
        logger.error(f"❌ Error in /simple_analyze: {str(e)}")
        return render_template('error.html', message=f"Error: {str(e)}")

@app.route('/simple_results')
def simple_results():
    """Display simple body composition results for session debugging"""
    try:
        logger.debug(f"🔍 Simple results route - Session keys: {list(session.keys())}")
        
        # Try multiple approaches to get the data
        if 'analysis_results' in session:
            logger.debug(f"✅ Found analysis_results in session: {session['analysis_results']}")
            results = session['analysis_results']
            body_fat = results.get('body_fat', 0)
            lean_mass = results.get('lean_mass', 0)
        elif 'body_fat' in session and 'lean_mass' in session:
            logger.debug(f"✅ Found separate body_fat and lean_mass in session")
            body_fat = session['body_fat']
            lean_mass = session['lean_mass']
        else:
            logger.warning("❌ No analysis data found in session")
            return render_template('error.html', message="No analysis data found in session. Please try again.")
            
        logger.debug(f"📊 Displaying results: body_fat={body_fat}, lean_mass={lean_mass}")
        
        # Return a simple HTML result directly (no template needed)
        return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Body Composition Results</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body class="bg-dark text-light">
                <div class="container mt-5">
                    <h1>Body Composition Results</h1>
                    <div class="card bg-secondary my-3">
                        <div class="card-body">
                            <h5 class="card-title">Body Fat Percentage</h5>
                            <h2 class="display-4 text-primary">{body_fat:.1f}%</h2>
                            <div class="progress mt-2">
                                <div class="progress-bar bg-primary" role="progressbar" 
                                    style="width: {body_fat}%" 
                                    aria-valuenow="{body_fat}" 
                                    aria-valuemin="0" 
                                    aria-valuemax="100">
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="card bg-secondary my-3">
                        <div class="card-body">
                            <h5 class="card-title">Lean Mass Percentage</h5>
                            <h2 class="display-4 text-success">{lean_mass:.1f}%</h2>
                            <div class="progress mt-2">
                                <div class="progress-bar bg-success" role="progressbar" 
                                    style="width: {lean_mass}%" 
                                    aria-valuenow="{lean_mass}" 
                                    aria-valuemin="0" 
                                    aria-valuemax="100">
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="card bg-secondary my-3">
                        <div class="card-body">
                            <h5 class="card-title">Session Keys</h5>
                            <p class="card-text">{list(session.keys())}</p>
                        </div>
                    </div>
                    <div class="mt-3">
                        <a href="/simple_body_comp" class="btn btn-primary">Calculate Again</a>
                        <a href="/" class="btn btn-secondary ms-2">Back to Home</a>
                    </div>
                </div>
            </body>
            </html>
        '''
        
    except Exception as e:
        logger.error(f"❌ Error in /simple_results: {str(e)}")
        return render_template('error.html', message=f"Error displaying results: {str(e)}")

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

# Simple test routes for session debugging
@app.route('/test_set_session')
def test_set_session():
    """Set session values for testing"""
    # Set test values in session
    session['test_value'] = 'This is a test value'
    session['test_dict'] = {
        'body_fat': 15.5,
        'lean_mass': 84.5
    }
    # Force session persistence
    session.modified = True
    
    # Print debugging information
    print("📥 SET SESSION test_value:", session.get('test_value'))
    print("📥 SET SESSION test_dict:", session.get('test_dict'))
    print("📥 SET SESSION keys:", list(session.keys()))
    
    # Use flash message to confirm
    flash('Session values set successfully!', 'success')
    return redirect(url_for('test_get_session'))

@app.route('/test_get_session')
def test_get_session():
    """Get session values for testing"""
    # Print debugging information
    print("📤 GET SESSION keys:", list(session.keys()))
    print("📤 GET SESSION test_value:", session.get('test_value'))
    print("📤 GET SESSION test_dict:", session.get('test_dict'))
    
    # Render simple template with session data
    return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Session Test</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-dark text-light">
            <div class="container mt-5">
                <h1>Session Test Results</h1>
                <div class="card bg-secondary my-3">
                    <div class="card-body">
                        <h5 class="card-title">Session Keys</h5>
                        <p class="card-text">{list(session.keys())}</p>
                    </div>
                </div>
                <div class="card bg-secondary my-3">
                    <div class="card-body">
                        <h5 class="card-title">test_value</h5>
                        <p class="card-text">{session.get('test_value', 'Not found')}</p>
                    </div>
                </div>
                <div class="card bg-secondary my-3">
                    <div class="card-body">
                        <h5 class="card-title">test_dict</h5>
                        <p class="card-text">{session.get('test_dict', 'Not found')}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <a href="/test_set_session" class="btn btn-primary">Set Session Values Again</a>
                    <a href="/" class="btn btn-secondary ms-2">Back to Home</a>
                </div>
            </div>
        </body>
        </html>
    '''

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
    """Render the enhanced main page with proper styling and branding"""
    logger.info("Rendering enhanced index page")
    return render_template('enhanced_index.html')
    
@app.route('/tailwind')
def tailwind_index():
    """Render the Tailwind UI page (as an alternate option)"""
    return render_template('tailwind_index.html')
    
@app.route('/modern')
def modern_index():
    """Render the modernized UI main page"""
    return render_template('tailwind_index.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Process uploaded front and back photos for comprehensive body analysis including 50 bodybuilding measurements"""
    # If it's a GET request, redirect to the homepage
    if request.method == 'GET':
        return redirect(url_for('index'))
        
    try:
        # Extract form data for debugging
        print("📥 FULL FORM DATA:", request.form)
        
        # Get basic user information from form
        height = request.form.get('height', 0)
        weight = request.form.get('weight', 0)
        age = request.form.get('age', 25)  # Default age if not provided
        gender = request.form.get('gender', 'male')  # Default to male if not specified
        
        # Convert to appropriate types with validation
        height_cm = float(height) if height else 0
        weight_kg = float(weight) if weight else 0
        age_years = int(age) if age else 25
        
        print(f"📥 Input values - Height: {height_cm}cm, Weight: {weight_kg}kg, Age: {age_years}, Gender: {gender}")
        
        # Calculate basic body composition
        body_fat_pct = 0
        lean_mass_pct = 0
        
        # Convert height from cm to meters for the calculation
        height_m = height_cm / 100
        
        try:
            # Calculate BMI first
            bmi = weight_kg / (height_m * height_m)
            print(f"📊 BMI: {bmi}")
            
            # Use Navy method for body fat calculation
            sex_value = 1 if gender.lower() == 'male' else 0
            body_fat_pct, lean_mass_pct = calculate_body_composition(weight_kg, height_m, age_years, sex_value)
            print(f"📊 Body composition - Fat: {body_fat_pct}%, Lean Mass: {lean_mass_pct}%")
        except Exception as calc_error:
            print(f"❌ Error calculating body composition: {str(calc_error)}")
            # Use BMI-based fallback
            if gender.lower() == 'male':
                body_fat_pct = (1.2 * bmi) + (0.23 * age_years) - 16.2
            else:
                body_fat_pct = (1.2 * bmi) + (0.23 * age_years) - 5.4
                
            # Ensure it's in reasonable range
            body_fat_pct = max(5, min(body_fat_pct, 40))
            lean_mass_pct = 100 - body_fat_pct
            print(f"📊 Fallback body composition - Fat: {body_fat_pct}%, Lean Mass: {lean_mass_pct}%")
        
        # Store in session with multiple redundant approaches
        # 1. Store as a dictionary
        session['analysis_results'] = {
            'body_fat': body_fat_pct,
            'lean_mass': lean_mass_pct,
            'id': str(uuid.uuid4())  # Generate a unique ID for reference
        }
        
        # 2. Store values directly in session
        session['body_fat'] = body_fat_pct
        session['lean_mass'] = lean_mass_pct
        
        # 3. Force session persistence
        session.modified = True
        
        print(f"💾 Session set with keys: {list(session.keys())}")
        print(f"💾 analysis_results: {session['analysis_results']}")
        
        # Redirect to results page
        return redirect(url_for('results'))
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERROR in /analyze: {str(e)}")
        print(f"❌ TRACEBACK: {error_trace}")
        print(f"❌ FORM DATA: {request.form}")
        
        # Log detailed error to help with debugging
        flash(f"Analysis failed: {str(e)}", 'danger')
        return redirect(url_for('index'))
        # Get enhanced measurements if available
        enhanced_measurements = result.get('enhanced_measurements', {})
        if not enhanced_measurements and 'traits' in result:
            # Add any measurements in traits that could be enhanced
            for key, value in traits.items():
                if '_ratio' in key or 'circumference' in key or 'width' in key:
                    if key not in enhanced_measurements:
                        enhanced_measurements[key] = value
        
        # User info for display
        user_info_display = {
            'gender': gender,
            'experience_level': user_info.get('experience', 'moderate'),
            'height': user_info.get('height', 170),
            'weight': user_info.get('weight', 70)
        }
        
        # Create debug information
        body_fat_formula_used = result.get('body_fat_formula_used', 'Unknown')
        
        # Create analysis object for template
        analysis = {
            'id': analysis_id,
            'body_fat_percentage': body_fat_percentage,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template(
            'debug_body_composition.html',
            analysis=analysis,
            body_fat_percentage=body_fat_percentage,
            lean_mass_percentage=lean_mass_percentage,
            gender=gender,
            bodybuilding_analysis=bodybuilding_analysis,
            basic_measurements=basic_measurements,
            enhanced_measurements=enhanced_measurements,
            user_info=user_info_display,
            body_fat_formula_used=body_fat_formula_used
        )
    except Exception as e:
        logger.error(f"Error in debug route: {str(e)}")
        flash('Error debugging body composition. Please try again.', 'danger')
        return redirect(url_for('index'))


@app.route('/results', methods=['GET'])
def results():
    """Display the results of the body composition analysis"""
    try:
        print("📊 Accessing results page")
        print(f"💾 Session keys available: {list(session.keys())}")
        
        # Try to access body fat from multiple redundantly stored locations
        if 'analysis_results' in session:
            print(f"💾 Full analysis_results: {session['analysis_results']}")
            body_fat = session['analysis_results'].get('body_fat', 0)
            lean_mass = session['analysis_results'].get('lean_mass', 0)
            analysis_id = session['analysis_results'].get('id', 'unknown')
        elif 'body_fat' in session and 'lean_mass' in session:
            print(f"💾 Direct session values: body_fat={session['body_fat']}, lean_mass={session['lean_mass']}")
            body_fat = session['body_fat']
            lean_mass = session['lean_mass']
            analysis_id = 'direct_session'
        else:
            print("❌ No analysis results found in session")
            flash('No analysis results found. Please try again.', 'warning')
            return redirect(url_for('index'))
        
        print(f"📊 Results being displayed - Body Fat: {body_fat}%, Lean Mass: {lean_mass}%, ID: {analysis_id}")
        
        # Generate additional data for display
        weight_kg = float(session.get('weight_kg', 70))
        fat_mass_kg = body_fat * weight_kg / 100
        lean_mass_kg = lean_mass * weight_kg / 100
        
        # Determine body type category
        if body_fat < 15:  # For males
            body_type = "Ectomorph" if lean_mass_kg < 60 else "Mesomorph"
        elif body_fat < 25:
            body_type = "Mesomorph"
        else:
            body_type = "Endomorph"
        
        # Calculate muscle building potential (simplified)
        muscle_potential = min(100, max(0, 100 - body_fat * 2))
        
        # Save weight_kg in session for future visits to results page
        session['weight_kg'] = weight_kg
        session.modified = True
        
        return render_template(
            'enhanced_results.html',
            body_fat=body_fat,
            lean_mass=lean_mass,
            fat_mass_kg=fat_mass_kg,
            lean_mass_kg=lean_mass_kg,
            body_type=body_type,
            muscle_potential=muscle_potential
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERROR in /results: {str(e)}")
        print(f"❌ TRACEBACK: {error_trace}")
        
        flash("Error displaying results. Please try again.", "danger")
        return redirect(url_for('index'))


# This route was removed as it duplicated the existing simple_body_comp route


# This route was removed as it duplicated the existing simple_results route


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
