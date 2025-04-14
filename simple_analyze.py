from flask import Flask, render_template, request, redirect, url_for, session
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "super-secret-key"

# Make session permanent by default to improve persistence
@app.before_request
def make_session_permanent():
    session.permanent = True
    # Set session timeout to 7 days
    session.modified = True

# Simple body composition calculation
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        weight = float(request.form.get('weight', 0))
        height = float(request.form.get('height', 0)) / 100  # convert to meters
        age = int(request.form.get('age', 0))
        sex = 1 if request.form.get('sex', '').lower() == 'male' else 0

        print("📥 Received:", weight, height, age, sex)
        logger.debug(f"📥 Received: weight={weight}, height={height}, age={age}, sex={sex}")

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

        return redirect(url_for('results'))

    except Exception as e:
        print("❌ Error in /analyze:", str(e))
        logger.error(f"❌ Error in /analyze: {str(e)}")
        return redirect(url_for('home'))

@app.route('/results')
def results():
    try:
        logger.debug(f"🔍 Results route - Session keys: {list(session.keys())}")
        
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
            return render_template('error.html', message="No analysis data found. Please try again.")
            
        logger.debug(f"📊 Displaying results: body_fat={body_fat}, lean_mass={lean_mass}")
        return render_template('results.html', body_fat=body_fat, lean_mass=lean_mass)
        
    except Exception as e:
        logger.error(f"❌ Error in /results: {str(e)}")
        return render_template('error.html', message=f"Error displaying results: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)