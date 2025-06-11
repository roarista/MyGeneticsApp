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
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin

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

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models and initialize db
import models
models.db = db

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

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

        # Get analysis ID from the results
        analysis_id = session['analysis_results'].get('id', 'unknown')
        
        # Redirect to detailed results page with the analysis ID
        if analysis_id and analysis_id != 'unknown':
            return redirect(url_for('view_analysis_results', analysis_id=analysis_id))
        else:
            # Fallback to original results page if ID not available
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

@app.route('/results/<analysis_id>')
def view_analysis_results(analysis_id):
    """Display detailed analysis results using the lovable_results.html template."""
    try:
        logger.info(f"📊 Accessing detailed results page for analysis ID: {analysis_id}")
        
        # Use session data instead of database query to avoid Flask app context issues
        if 'analysis_results' in session:
            results = session['analysis_results']
            logger.info(f"📊 Using analysis results from session: {results}")
            
            # Debug print to see what we're working with
            logger.info(f"DEBUG - Session analysis keys: {list(results.keys())}")
            
            # Create bodybuilding object to match template requirements
            bodybuilding = {
                'body_fat_percentage': results.get('body_fat', 0),
                'body_fat_confidence': 0.85,  # Default confidence value
                'body_type': results.get('body_type', 'Unknown'),
                'muscle_building_potential': results.get('muscle_potential', 5.0)
            }
            
            # Log the bodybuilding object for debugging
            logger.info(f"DEBUG - Bodybuilding object: {bodybuilding}")
            
            # Get measurements - construct from available data
            measurements = {
                'shoulder_width': 48.0,  # Default values
                'chest_circumference': 100.0,
                'waist_circumference': results.get('waist_circumference', 80.0),
                'arm_circumference': 35.0,
                'thigh_circumference': 55.0,
                'calf_circumference': 38.0
            }
            
            # Log measurements for debugging
            logger.info(f"DEBUG - Measurements: {measurements}")
            
            # Get traits from results
            traits = results.get('traits', {})
            
            # Add muscle fiber composition if missing
            if 'fast_twitch_percentage' not in traits:
                traits['fast_twitch_percentage'] = 50
                
            # Add frame size if missing
            if 'frame_size' not in traits:
                traits['frame_size'] = 'Medium'
                
            # Add insertions if missing
            if 'bicep_insertion' not in traits:
                traits['bicep_insertion'] = 'Medium'
                
            if 'calf_insertion' not in traits:
                traits['calf_insertion'] = 'Medium'
            
            # Log traits for debugging
            logger.info(f"DEBUG - Traits: {traits}")
            
            # Check if this is a dual photo analysis (default to standard)
            is_dual_photo = False
            
            # Check if this is a 3D scan (default to standard)
            is_3d_scan = False
            
            # Setup image data - using a placeholder or empty
            image_data = None
            front_image = None
            back_image = None
            
            # Define enhanced measurements with more metrics
            has_enhanced_measurements = True
            
            # Helper function to rate measurements
            def get_measurement_rating(value, thresholds):
                """Rate measurement based on thresholds [low, high]"""
                if value < thresholds[0]:
                    return {'rating': 'Underdeveloped', 'color': 'red'}
                elif value < thresholds[1]:
                    return {'rating': 'Average', 'color': 'yellow'}
                else:
                    return {'rating': 'Well Developed', 'color': 'green'}

            # Define thresholds for different measurements
            measurement_thresholds = {
                'shoulder_width': [42, 50],
                'chest_circumference': [90, 110],
                'arm_circumference': [30, 38],
                'waist_circumference': [70, 85],
                'thigh_circumference': [50, 60],
                'calf_circumference': [32, 40],
                'bmi': [18.5, 25],
                'weight': [55, 80],
                'height': [160, 180]
            }

            # Create categorized measurements with ratings
            categorized_measurements = {
                "Body Composition": {
                    'weight': {'value': results.get('user_info', {}).get('weight', 70), 'unit': 'kg', **get_measurement_rating(results.get('user_info', {}).get('weight', 70), measurement_thresholds['weight'])},
                    'height': {'value': results.get('user_info', {}).get('height', 170), 'unit': 'cm', **get_measurement_rating(results.get('user_info', {}).get('height', 170), measurement_thresholds['height'])},
                    'bmi': {'value': round(results.get('bmi', 22), 1), 'unit': '', **get_measurement_rating(results.get('bmi', 22), measurement_thresholds['bmi'])}
                },
                "Upper Body": {
                    'shoulder_width': {'value': 48.0, 'unit': 'cm', **get_measurement_rating(48.0, measurement_thresholds['shoulder_width'])},
                    'chest_circumference': {'value': 100.0, 'unit': 'cm', **get_measurement_rating(100.0, measurement_thresholds['chest_circumference'])},
                    'arm_circumference': {'value': 35.0, 'unit': 'cm', **get_measurement_rating(35.0, measurement_thresholds['arm_circumference'])},
                    'bicep_circumference': {'value': 36.0, 'unit': 'cm', **get_measurement_rating(36.0, measurement_thresholds['arm_circumference'])},
                    'forearm_circumference': {'value': 28.0, 'unit': 'cm', **get_measurement_rating(28.0, [25, 32])},
                    'wrist_circumference': {'value': 17.0, 'unit': 'cm', **get_measurement_rating(17.0, [15, 19])}
                },
                "Torso": {
                    'waist_circumference': {'value': results.get('waist_circumference', 80.0), 'unit': 'cm', **get_measurement_rating(results.get('waist_circumference', 80.0), measurement_thresholds['waist_circumference'])},
                    'hip_circumference': {'value': 96.0, 'unit': 'cm', **get_measurement_rating(96.0, [85, 105])},
                    'neck_circumference': {'value': 40.0, 'unit': 'cm', **get_measurement_rating(40.0, [35, 45])}
                },
                "Lower Body": {
                    'thigh_circumference': {'value': 55.0, 'unit': 'cm', **get_measurement_rating(55.0, measurement_thresholds['thigh_circumference'])},
                    'calf_circumference': {'value': 38.0, 'unit': 'cm', **get_measurement_rating(38.0, measurement_thresholds['calf_circumference'])},
                    'ankle_circumference': {'value': 22.0, 'unit': 'cm', **get_measurement_rating(22.0, [20, 25])}
                }
            }

            # Create genetic traits data
            genetic_traits = [
                {
                    'label': 'Frame Size',
                    'value': traits.get('frame_size', 'Medium'),
                    'impact': 'Determines overall bone structure and potential muscle mass'
                },
                {
                    'label': 'Bicep Insertion',
                    'value': traits.get('bicep_insertion', 'Medium'),
                    'impact': 'Higher insertion = better peak, lower = fuller appearance'
                },
                {
                    'label': 'Calf Insertion',
                    'value': traits.get('calf_insertion', 'Medium'),
                    'impact': 'Affects calf muscle shape and development potential'
                },
                {
                    'label': 'Shoulder Structure',
                    'value': f"{measurements.get('shoulder_width', 48)} cm",
                    'impact': 'Wider shoulders create better V-taper and aesthetic proportions'
                },
                {
                    'label': 'Metabolic Rate',
                    'value': f"{traits.get('metabolic_efficiency', 6)}/10",
                    'impact': 'Higher rate = easier fat loss, lower = easier muscle gain'
                },
                {
                    'label': 'Recovery Genetics',
                    'value': f"{traits.get('recovery_capacity', 7)}/10",
                    'impact': 'Better recovery allows more frequent and intense training'
                }
            ]
            
            # Debug categorized measurements
            logger.info(f"DEBUG - Categorized measurements keys: {list(categorized_measurements.keys())}")
            
            # Prepare chart data for existing JavaScript files
            user_info = results.get('user_info', {})
            chart_data = {
                'bodyType': results.get('body_type', 'balanced'),
                'bodyTypePosition': 50 if results.get('body_type') == 'Mesomorph' else (20 if results.get('body_type') == 'Ectomorph' else 80),
                'metabolicEfficiency': traits.get('metabolic_efficiency', 6.5),
                'muscleBuilding': traits.get('muscle_building_potential', 7.0),
                'recoveryCapacity': traits.get('recovery_capacity', 8.0),
                'shoulderToWaistRatio': measurements['shoulder_width'] / measurements['waist_circumference'],
                'bodyFatPercentage': results.get('body_fat', 15.0),
                'leanMassPercentage': results.get('lean_mass', 85.0),
                'userAge': user_info.get('age', 25),
                'gender': user_info.get('gender', 'male'),
                'heightCm': user_info.get('height', 170),
                'weightKg': user_info.get('weight', 70),
                'activityLevel': user_info.get('experience', 'moderate'),
                'maintenanceCalories': results.get('maintenance_calories', {
                    'sedentary': 1800,
                    'light': 2000,
                    'moderate': 2200,
                    'active': 2400,
                    'very_active': 2600
                })
            }
            
            # Generate recommendations based on body type and traits
            recommendations = {
                'strengths': [
                    f"Good {traits.get('body_type', 'balanced')} characteristics",
                    f"Recovery capacity of {traits.get('recovery_capacity', 8)}/10",
                    f"Metabolic efficiency rated {traits.get('metabolic_efficiency', 6.5)}/10"
                ],
                'focus_areas': [
                    "Maintain consistent training schedule",
                    "Focus on progressive overload",
                    "Monitor recovery between sessions"
                ],
                'exercise_recommendations': [
                    "Compound movements (squats, deadlifts)",
                    "Balanced push/pull exercises",
                    "Progressive resistance training"
                ],
                'nutrition_tips': [
                    f"Adequate protein intake ({user_info.get('weight', 70) * 1.8:.0f}g daily)",
                    "Balanced macronutrient distribution",
                    "Stay hydrated throughout training"
                ]
            }

            # Debug: Print all variables before rendering template
            template_vars = {
                'analysis_id': analysis_id,
                'bodybuilding': bodybuilding,
                'measurements': measurements,
                'traits': traits,
                'image_data': image_data,
                'front_image': front_image,
                'back_image': back_image,
                'is_dual_photo': is_dual_photo,
                'is_3d_scan': is_3d_scan,
                'categorized_measurements': categorized_measurements,
                'has_enhanced_measurements': has_enhanced_measurements,
                'chart_data': chart_data,
                'recommendations': recommendations,
                'user_info': user_info
            }
            
            logger.info("=== TEMPLATE VARIABLES DEBUG ===")
            for key, value in template_vars.items():
                if value is None:
                    logger.error(f"❌ {key} is None!")
                else:
                    logger.info(f"✓ {key}: {type(value)} - {str(value)[:100]}...")
            
            # Verify chart_data has all required fields
            required_chart_fields = ['bodyType', 'bodyTypePosition', 'metabolicEfficiency', 'muscleBuilding', 'recoveryCapacity']
            for field in required_chart_fields:
                if field not in chart_data:
                    logger.error(f"❌ Missing chart field: {field}")
                else:
                    logger.info(f"✓ Chart field {field}: {chart_data[field]}")

            return render_template(
                'lovable_results.html',
                analysis_id=analysis_id,
                bodybuilding=bodybuilding,
                measurements=measurements,
                traits=traits,
                image_data=image_data,
                front_image=front_image,
                back_image=back_image,
                is_dual_photo=is_dual_photo,
                is_3d_scan=is_3d_scan,
                categorized_measurements=categorized_measurements,
                has_enhanced_measurements=has_enhanced_measurements,
                chart_data=chart_data,
                recommendations=recommendations,
                user_info=user_info,
                genetic_traits=genetic_traits
            )
        else:
            logger.error(f"❌ No analysis results found in session")
            flash('No analysis results found. Please analyze your genetics first.', 'warning')
            return redirect(url_for('index'))
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ ERROR in /results/{analysis_id}: {str(e)}")
        logger.error(f"❌ TRACEBACK: {error_trace}")
        flash('An error occurred while displaying your results. Please try again.', 'danger')
        return redirect(url_for('index'))

def is_authenticated():
    return auth.is_authenticated

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        gender = request.form.get('gender')
        age = request.form.get('age')
        experience = request.form.get('experience')
        
        # Check if user with email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return render_template('signup.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            gender=gender
        )
        new_user.set_password(password)
        
        if age:
            new_user.age = int(age)
        
        if experience:
            new_user.experience_level = experience
        
        # Save user to database
        db.session.add(new_user)
        db.session.commit()
        
        # Log the user in
        login_user(new_user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/nutrition')
def nutrition():
    return render_template('nutrition.html')

@app.route('/nutrition/<analysis_id>')
def nutrition_with_analysis(analysis_id):
    """Display nutrition plan for a specific analysis"""
    # Get analysis data from session or database
    analysis_data = session.get('analysis_results', {})
    
    # Generate personalized nutrition data based on analysis
    if analysis_data:
        # Calculate personalized macros based on user data
        user_info = analysis_data.get('user_info', {})
        maintenance_calories = analysis_data.get('maintenance_calories', {})
        
        # Determine goal-based calories (example: slight deficit for fat loss)
        target_calories = maintenance_calories.get('moderate', 2200) - 300
        
        # Calculate macros (example: 1.8g protein per kg, 25% fat, rest carbs)
        weight_kg = user_info.get('weight', 70)
        protein_g = int(weight_kg * 1.8)
        fat_g = int((target_calories * 0.25) / 9)
        carb_g = int((target_calories - (protein_g * 4) - (fat_g * 9)) / 4)
        
        macros = {
            'protein': protein_g,
            'carbs': carb_g,
            'fats': fat_g
        }
        
        calories = {
            'maintenance': maintenance_calories.get('moderate', 2200),
            'target': target_calories
        }
    else:
        # Default values if no analysis data
        macros = None
        calories = None
    
    return render_template('nutrition.html', 
                         analysis_id=analysis_id,
                         macros=macros,
                         calories=calories)

@app.route('/workout')
def workout():
    return render_template('workout.html')

@app.route('/workout/<analysis_id>')
def workout_with_analysis(analysis_id):
    """Display workout plan for a specific analysis"""
    return render_template('workout.html', analysis_id=analysis_id)

@app.route('/api/workout/<analysis_id>/<day>')
def api_workout_day(analysis_id, day):
    """API endpoint to get workout data for a specific day"""
    try:
        # Define workout plans for each day
        workout_plans = {
            'Monday': {
                'type': 'Push',
                'exercises': [
                    {'name': 'Bench Press', 'focus': 'Chest, Triceps, Shoulders', 'sets': '3', 'reps': '8-10', 'rest': '90s'},
                    {'name': 'Overhead Press', 'focus': 'Shoulders, Triceps', 'sets': '3', 'reps': '8-10', 'rest': '90s'},
                    {'name': 'Incline Dumbbell Press', 'focus': 'Upper Chest, Shoulders', 'sets': '3', 'reps': '10-12', 'rest': '60s'},
                    {'name': 'Dips', 'focus': 'Triceps, Lower Chest', 'sets': '3', 'reps': '8-12', 'rest': '60s'},
                    {'name': 'Lateral Raises', 'focus': 'Side Delts', 'sets': '3', 'reps': '12-15', 'rest': '45s'},
                    {'name': 'Tricep Pushdowns', 'focus': 'Triceps', 'sets': '3', 'reps': '10-12', 'rest': '45s'}
                ]
            },
            'Tuesday': {
                'type': 'Pull',
                'exercises': [
                    {'name': 'Pull-ups', 'focus': 'Lats, Biceps, Rear Delts', 'sets': '3', 'reps': '6-10', 'rest': '90s'},
                    {'name': 'Barbell Rows', 'focus': 'Mid Traps, Rhomboids, Lats', 'sets': '3', 'reps': '8-10', 'rest': '90s'},
                    {'name': 'Lat Pulldowns', 'focus': 'Lats, Biceps', 'sets': '3', 'reps': '10-12', 'rest': '60s'},
                    {'name': 'Cable Rows', 'focus': 'Mid Traps, Rhomboids', 'sets': '3', 'reps': '10-12', 'rest': '60s'},
                    {'name': 'Face Pulls', 'focus': 'Rear Delts, Mid Traps', 'sets': '3', 'reps': '12-15', 'rest': '45s'},
                    {'name': 'Bicep Curls', 'focus': 'Biceps', 'sets': '3', 'reps': '10-12', 'rest': '45s'}
                ]
            },
            'Wednesday': {
                'type': 'Legs',
                'exercises': [
                    {'name': 'Squats', 'focus': 'Quads, Glutes, Core', 'sets': '3', 'reps': '8-10', 'rest': '2min'},
                    {'name': 'Romanian Deadlifts', 'focus': 'Hamstrings, Glutes', 'sets': '3', 'reps': '8-10', 'rest': '90s'},
                    {'name': 'Bulgarian Split Squats', 'focus': 'Quads, Glutes', 'sets': '3', 'reps': '10-12 each', 'rest': '60s'},
                    {'name': 'Leg Curls', 'focus': 'Hamstrings', 'sets': '3', 'reps': '10-12', 'rest': '60s'},
                    {'name': 'Calf Raises', 'focus': 'Calves', 'sets': '4', 'reps': '15-20', 'rest': '45s'},
                    {'name': 'Plank', 'focus': 'Core', 'sets': '3', 'reps': '30-60s', 'rest': '45s'}
                ]
            },
            'Thursday': {
                'type': 'Rest',
                'exercises': [
                    {'name': 'Light Walking', 'focus': 'Active Recovery', 'sets': '1', 'reps': '20-30 min', 'rest': 'N/A'},
                    {'name': 'Stretching', 'focus': 'Flexibility', 'sets': '1', 'reps': '15-20 min', 'rest': 'N/A'},
                    {'name': 'Foam Rolling', 'focus': 'Recovery', 'sets': '1', 'reps': '10-15 min', 'rest': 'N/A'}
                ]
            },
            'Friday': {
                'type': 'Push',
                'exercises': [
                    {'name': 'Incline Barbell Press', 'focus': 'Upper Chest, Shoulders', 'sets': '3', 'reps': '8-10', 'rest': '90s'},
                    {'name': 'Dumbbell Shoulder Press', 'focus': 'Shoulders, Triceps', 'sets': '3', 'reps': '8-10', 'rest': '90s'},
                    {'name': 'Decline Dumbbell Press', 'focus': 'Lower Chest', 'sets': '3', 'reps': '10-12', 'rest': '60s'},
                    {'name': 'Close-Grip Bench Press', 'focus': 'Triceps, Chest', 'sets': '3', 'reps': '8-10', 'rest': '90s'},
                    {'name': 'Arnold Press', 'focus': 'Shoulders', 'sets': '3', 'reps': '10-12', 'rest': '60s'},
                    {'name': 'Overhead Tricep Extension', 'focus': 'Triceps', 'sets': '3', 'reps': '10-12', 'rest': '45s'}
                ]
            },
            'Saturday': {
                'type': 'Pull',
                'exercises': [
                    {'name': 'Deadlifts', 'focus': 'Posterior Chain, Traps', 'sets': '3', 'reps': '5-8', 'rest': '2min'},
                    {'name': 'Wide-Grip Pulldowns', 'focus': 'Lats, Rear Delts', 'sets': '3', 'reps': '8-10', 'rest': '90s'},
                    {'name': 'T-Bar Rows', 'focus': 'Mid Traps, Lats', 'sets': '3', 'reps': '10-12', 'rest': '60s'},
                    {'name': 'Reverse Flyes', 'focus': 'Rear Delts', 'sets': '3', 'reps': '12-15', 'rest': '45s'},
                    {'name': 'Hammer Curls', 'focus': 'Biceps, Forearms', 'sets': '3', 'reps': '10-12', 'rest': '45s'},
                    {'name': 'Shrugs', 'focus': 'Upper Traps', 'sets': '3', 'reps': '12-15', 'rest': '45s'}
                ]
            },
            'Sunday': {
                'type': 'Legs',
                'exercises': [
                    {'name': 'Front Squats', 'focus': 'Quads, Core', 'sets': '3', 'reps': '8-10', 'rest': '90s'},
                    {'name': 'Stiff Leg Deadlifts', 'focus': 'Hamstrings, Glutes', 'sets': '3', 'reps': '10-12', 'rest': '90s'},
                    {'name': 'Walking Lunges', 'focus': 'Quads, Glutes', 'sets': '3', 'reps': '12-15 each', 'rest': '60s'},
                    {'name': 'Leg Extensions', 'focus': 'Quads', 'sets': '3', 'reps': '12-15', 'rest': '45s'},
                    {'name': 'Seated Calf Raises', 'focus': 'Calves', 'sets': '4', 'reps': '15-20', 'rest': '45s'},
                    {'name': 'Russian Twists', 'focus': 'Core', 'sets': '3', 'reps': '20-30', 'rest': '45s'}
                ]
            }
        }
        
        workout_data = workout_plans.get(day)
        if not workout_data:
            return jsonify({'error': f'No workout found for {day}'}), 404
            
        return jsonify(workout_data)
        
    except Exception as e:
        logger.error(f"Error fetching workout for {day}: {str(e)}")
        return jsonify({'error': 'Failed to load workout data'}), 500

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


@app.route('/test_results')
def test_results():
    """Test route to view the template with sample data"""
    bodybuilding = {
        'body_fat_percentage': 15.5,
        'body_fat_confidence': 0.85,
        'body_type': 'Mesomorph',
        'muscle_building_potential': 7.8
    }
    
    measurements = {
        'shoulder_width': 47.5,
        'waist_circumference': 81.0,
        'arm_circumference': 35.0,
        'thigh_circumference': 59.0,
        'chest_circumference': 98.0,
        'calf_circumference': 38.0
    }
    
    traits = {
        'fast_twitch_percentage': 65,
        'frame_size': 'Medium',
        'bicep_insertion': 'Low',
        'calf_insertion': 'High',
        'body_fat_percentage': 15.5,
        'lean_mass_percentage': 84.5,
        'muscle_building_potential': 7.8,
        'body_type': 'Mesomorph',
        'bmi': 23.9,
        'metabolic_efficiency': 7.2,
        'recovery_capacity': 8.5,
        'symmetry': {
            'upper_body': 85,
            'lower_body': 78,
            'left_right': 92
        },
        'muscle_fiber_composition': {
            'fast_twitch': 65,
            'slow_twitch': 35
        },
        'dominant_areas': {
            'chest': 82,
            'back': 75,
            'shoulders': 78,
            'arms': 80,
            'core': 76,
            'legs': 73
        }
    }
    
    recommendations = {
        'training': {
            'style': 'Hypertrophy-focused with strength elements',
            'frequency': '4-5 days per week',
            'volume': 'Moderate to high (12-16 sets per muscle group weekly)',
            'intensity': '70-85% of 1RM for main lifts'
        },
        'exercises': {
            'prioritize': ['Incline bench press', 'Weighted pull-ups', 'Hack squats'],
            'limit': ['Traditional deadlifts', 'Behind-neck presses']
        },
        'nutrition': {
            'protein': '2.0-2.2g per kg bodyweight',
            'carbs': 'Moderate to high (4-5g per kg on training days)',
            'timing': 'Focus on pre/post workout nutrition window'
        }
    }
    
    # Sample values for template testing
    return render_template(
        'lovable_results.html',
        analysis_id='test123',
        bodybuilding=bodybuilding,
        measurements=measurements,
        traits=traits,
        recommendations=recommendations,
        image_data=None,
        front_image=None,
        back_image=None,
        is_dual_photo=False,
        is_3d_scan=False,
        categorized_measurements={},
        has_enhanced_measurements=False
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)