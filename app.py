import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from replit import web
from replit.web import auth
import uuid
import datetime
import numpy as np
import cv2
from werkzeug.utils import secure_filename
from utils.image_processing import process_image, extract_body_landmarks
from utils.body_analysis import analyze_body_traits
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
try:
    from google_auth import google_auth
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Google authentication module not available")


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        # Convert height to meters
        height_m = height / 100

        # Calculate body composition
        sex_value = 1 if gender.lower() == 'male' else 0
        body_fat, lean_mass = calculate_body_composition(weight, height_m, age, sex_value)

        # Store in session
        session['analysis_results'] = {
            'body_fat': body_fat,
            'lean_mass': lean_mass
        }
        session.modified = True

        return redirect(url_for('results'))

    except Exception as e:
        logger.error(f"Error in analyze route: {str(e)}")
        flash("Error analyzing data. Please try again.", "danger")
        return redirect(url_for('index'))

@app.route('/results')
def results():
    try:
        if 'analysis_results' not in session:
            flash('No analysis results found. Please try again.', 'warning')
            return redirect(url_for('index'))

        results = session['analysis_results']
        return render_template('results.html',
                             body_fat=results['body_fat'],
                             lean_mass=results['lean_mass'])

    except Exception as e:
        logger.error(f"Error displaying results: {str(e)}")
        flash("Error displaying results. Please try again.", "danger")
        return redirect(url_for('index'))

def is_authenticated():
    return auth.is_authenticated

# Import admin_bp and register it after db is initialized
from admin import admin_bp
app.register_blueprint(admin_bp)

# Import and register google_auth if available
try:
    app.register_blueprint(google_auth)
except NameError:
    pass #Ignore if google_auth is not defined


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)