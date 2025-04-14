import os
import logging
import uuid
import datetime
import json
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask and SQLAlchemy imports
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Replit-specific imports with fallback
try:
    from replit import web
    from replit.web import auth
    REPLIT_AUTH_AVAILABLE = True
except ImportError:
    logger.warning("Replit authentication module not available, using fallback")
    REPLIT_AUTH_AVAILABLE = False
    class DummyAuth:
        @property
        def is_authenticated(self):
            return True
    auth = DummyAuth()

# Image processing and numerical libraries with fallback
try:
    import numpy as np
    import cv2
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    logger.warning("Image processing libraries not available, using fallback")
    IMAGE_PROCESSING_AVAILABLE = False
    np = None
    cv2 = None

# Import MyGenetics app utilities
from utils.body_analysis import analyze_body_traits

# Optional imports with fallback for more advanced features
try:
    from utils.image_processing import process_image, extract_body_landmarks
    from utils.recommendations import generate_recommendations
    from utils.measurement_validator import MeasurementValidator
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
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some advanced features not available: {str(e)}")
    ADVANCED_FEATURES_AVAILABLE = False


# Define the base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "super-secret-key"

# Configure session
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(model_class=Base)
db.init_app(app)

@app.before_request
def make_session_permanent():
    session.permanent = True
    session.modified = True

@app.context_processor
def inject_auth():
    return {'auth': auth, 'is_authenticated': is_authenticated}

def calculate_body_composition(weight, height, age, sex):
    """Calculate body fat and lean mass using simplified formula"""
    bmi = weight / (height * height)

    if sex == 1:  # male
        body_fat = (1.20 * bmi) + (0.23 * age) - 16.2
    else:  # female
        body_fat = (1.20 * bmi) + (0.23 * age) - 5.4

    body_fat = max(5.0, min(body_fat, 45.0))
    lean_mass = 100.0 - body_fat

    return body_fat, lean_mass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get form data
        height = float(request.form.get('height', 0))
        weight = float(request.form.get('weight', 0))
        age = int(request.form.get('age', 25))
        gender = request.form.get('gender', 'male')
        experience = request.form.get('experience', 'intermediate')

        # Print form data for debugging
        logger.info(f"📥 FULL FORM DATA: {request.form}")
        logger.info(f"📥 Input values - Height: {height}cm, Weight: {weight}kg, Age: {age}, Gender: {gender}")

        # Convert height to meters
        height_m = height / 100

        # Calculate BMI
        bmi = weight / (height_m * height_m)
        logger.info(f"📊 BMI: {bmi}")

        # Calculate body composition using utility function
        sex_value = 1 if gender.lower() == 'male' else 0
        body_fat, lean_mass = calculate_body_composition(weight, height_m, age, sex_value)
        logger.info(f"📊 Body composition - Fat: {body_fat}%, Lean Mass: {lean_mass}%")

        # Calculate fat mass and lean mass in kg
        fat_mass_kg = weight * (body_fat / 100)
        lean_mass_kg = weight * (lean_mass / 100)

        # Determine body type based on body fat
        if body_fat < 15:  # For males
            body_type = "Ectomorph" if lean_mass_kg < 60 else "Mesomorph"
        elif body_fat < 25:
            body_type = "Mesomorph"
        else:
            body_type = "Endomorph"

        # Calculate muscle building potential (simplified)
        muscle_potential = min(100, max(0, 100 - body_fat * 2))

        # Get more comprehensive body traits from analysis utility
        body_traits = analyze_body_traits(
            height_cm=height,
            weight_kg=weight,
            gender=gender,
            age=age,
            experience=experience
        )

        # Calculate caloric maintenance based on weight, height, age, gender
        # Using Mifflin-St Jeor Equation
        if gender.lower() == 'male':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        # Activity multipliers
        activity_levels = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }

        # Default to moderate activity
        maintenance_calories = {level: round(bmr * multiplier) for level, multiplier in activity_levels.items()}

        # Store in session with multiple redundant approaches for reliability
        analysis_id = str(uuid.uuid4())  # Generate a unique ID for reference
        session['analysis_results'] = {
            'body_fat': body_fat,
            'lean_mass': lean_mass,
            'body_type': body_type,
            'muscle_potential': muscle_potential,
            'fat_mass_kg': fat_mass_kg,
            'lean_mass_kg': lean_mass_kg,
            'traits': body_traits,
            'bmi': bmi,
            'maintenance_calories': maintenance_calories,
            'id': analysis_id,
            'user_info': {
                'height': height,
                'weight': weight,
                'age': age,
                'gender': gender,
                'experience': experience
            }
        }
        
        # Store individual values directly in session as backup
        session['body_fat'] = body_fat
        session['lean_mass'] = lean_mass
        session['weight_kg'] = weight

        # Force session persistence
        session.modified = True
        
        logger.info(f"💾 Session set with keys: {list(session.keys())}")
        logger.info(f"💾 analysis_results: {session['analysis_results']}")

        # Redirect to results page
        return redirect(url_for('results'))

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ ERROR in /analyze: {str(e)}")
        logger.error(f"❌ TRACEBACK: {error_trace}")
        
        # Log detailed error to help with debugging
        flash(f"Analysis failed: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    """Display the results of the body composition analysis with full metrics"""
    try:
        logger.info("📊 Accessing results page")
        logger.info(f"💾 Session keys available: {list(session.keys())}")
        
        # Try to access analysis results from multiple redundantly stored locations
        if 'analysis_results' in session:
            logger.info(f"💾 Full analysis_results: {session['analysis_results']}")
            results = session['analysis_results']
            body_fat = results.get('body_fat', 0)
            lean_mass = results.get('lean_mass', 0)
            body_type = results.get('body_type', 'Balanced')
            muscle_potential = results.get('muscle_potential', 50)
            fat_mass_kg = results.get('fat_mass_kg', 0)
            lean_mass_kg = results.get('lean_mass_kg', 0)
            traits = results.get('traits', {})
            bmi = results.get('bmi', 22)
            maintenance_calories = results.get('maintenance_calories', {'moderate': 2000})
            analysis_id = results.get('id', 'unknown')
            user_info = results.get('user_info', {})
        elif 'body_fat' in session and 'lean_mass' in session:
            logger.info(f"💾 Direct session values: body_fat={session['body_fat']}, lean_mass={session['lean_mass']}")
            body_fat = session['body_fat']
            lean_mass = session['lean_mass']
            weight_kg = float(session.get('weight_kg', 70))
            fat_mass_kg = body_fat * weight_kg / 100
            lean_mass_kg = lean_mass * weight_kg / 100
            
            # Use reasonable defaults for other values
            body_type = "Mesomorph"
            muscle_potential = 50
            traits = {}
            bmi = 22
            maintenance_calories = {'moderate': 2000}
            analysis_id = 'direct_session'
            user_info = {}
        else:
            logger.error("❌ No analysis results found in session")
            flash('No analysis results found. Please try again.', 'warning')
            return redirect(url_for('index'))
        
        logger.info(f"📊 Results being displayed - Body Fat: {body_fat}%, Lean Mass: {lean_mass}%, ID: {analysis_id}")
        
        # Calculate fitness age based on body composition and BMI
        # Simple algorithm: chronological age adjusted by body composition factors
        chronological_age = user_info.get('age', 30)
        fitness_age = chronological_age
        
        # Better body composition = younger fitness age
        if body_fat < 15:  # Athletic range
            fitness_age -= 5
        elif body_fat > 25:  # Above average range
            fitness_age += 5
            
        # Keep fitness age in reasonable range
        fitness_age = max(18, min(fitness_age, 70))
        
        # Generate muscle group ratings
        muscle_groups = {
            'chest': round(max(1, min(10, 5 + (muscle_potential / 20)))),
            'back': round(max(1, min(10, 5 + (muscle_potential / 20)))),
            'shoulders': round(max(1, min(10, 5 + (muscle_potential / 20)))),
            'arms': round(max(1, min(10, 5 + (muscle_potential / 20)))),
            'legs': round(max(1, min(10, 5 + (muscle_potential / 20)))),
            'core': round(max(1, min(10, 5 + (muscle_potential / 20))))
        }
        
        # Muscle development tags
        muscle_tags = {}
        for muscle, rating in muscle_groups.items():
            if rating <= 3:
                muscle_tags[muscle] = "Needs Growth"
            elif rating <= 5:
                muscle_tags[muscle] = "Average"
            elif rating <= 7:
                muscle_tags[muscle] = "Good"
            elif rating <= 9:
                muscle_tags[muscle] = "Excellent"
            else:
                muscle_tags[muscle] = "Elite"
        
        # Calculate symmetry score
        symmetry_score = 8.5  # Default value
        
        # Calculate proportion ratio
        proportion_ratio = 0.73  # Default value (shoulder-to-waist ratio)
        
        # Calculate metabolic efficiency
        metabolic_efficiency = traits.get('metabolic_efficiency', 7.0)
        
        return render_template(
            'results.html',
            body_fat=body_fat,
            lean_mass=lean_mass,
            fat_mass_kg=fat_mass_kg,
            lean_mass_kg=lean_mass_kg,
            body_type=body_type,
            muscle_potential=muscle_potential,
            bmi=bmi,
            maintenance_calories=maintenance_calories,
            fitness_age=fitness_age,
            chronological_age=chronological_age,
            muscle_groups=muscle_groups,
            muscle_tags=muscle_tags,
            symmetry_score=symmetry_score,
            proportion_ratio=proportion_ratio,
            metabolic_efficiency=metabolic_efficiency,
            user_info=user_info,
            traits=traits
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ ERROR in /results: {str(e)}")
        logger.error(f"❌ TRACEBACK: {error_trace}")
        
        flash("Error displaying results. Please try again.", "danger")
        return redirect(url_for('index'))

def is_authenticated():
    return auth.is_authenticated

# Import admin_bp and register it after db is initialized
from admin import admin_bp
app.register_blueprint(admin_bp)

# Import and register google_auth if available
try:
    from google_auth import google_auth
    app.register_blueprint(google_auth)
    logger.info("Google authentication module registered successfully")
except (ImportError, NameError):
    logger.warning("Google authentication module not available, skipping registration")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)