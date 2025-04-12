"""
Test routes for body composition calculations.
These routes are used for debugging and testing the calculation methods.
"""

from flask import jsonify, request, Blueprint, render_template, session
import logging
import traceback
import time

from utils.body_analysis import calculate_body_composition, analyze_body_traits
from utils.navy_body_fat import calculate_body_fat_navy_derived

logger = logging.getLogger(__name__)

test_routes = Blueprint('test_routes', __name__)

@test_routes.route('/test-calculation')
def test_calculation():
    """Test route to verify body composition calculation works correctly"""
    try:
        # Test with sample data
        height_cm = float(request.args.get('height', 175))
        weight_kg = float(request.args.get('weight', 70))
        age = int(request.args.get('age', 30))
        gender = request.args.get('gender', 'male')
        waist_cm = float(request.args.get('waist', 80))
        neck_cm = float(request.args.get('neck', 38))
        hip_cm = float(request.args.get('hip', 90)) if gender.lower() == 'female' else None
        
        height_m = height_cm / 100.0
        
        # Test Navy method
        try:
            if gender.lower() == 'female' and hip_cm is not None:
                navy_result, method = calculate_body_fat_navy_derived(
                    gender, height_cm, weight_kg, waist_cm, neck_cm, hip_cm
                )
            else:
                navy_result, method = calculate_body_fat_navy_derived(
                    gender, height_cm, weight_kg, waist_cm, neck_cm
                )
                
            navy_bf = navy_result
            navy_lean = 100 - navy_bf
        except Exception as e:
            logger.error(f"Navy method calculation error: {str(e)}")
            traceback.print_exc()
            navy_bf = "Error"
            navy_lean = "Error"
            method = "failed"
        
        # Test BMI method
        try:
            sex_value = 1 if gender.lower() == 'male' else 0
            bmi_bf, bmi_lean = calculate_body_composition(weight_kg, height_m, age, sex_value)
        except Exception as e:
            logger.error(f"BMI method calculation error: {str(e)}")
            traceback.print_exc()
            bmi_bf = "Error" 
            bmi_lean = "Error"
        
        # Test body traits analysis
        try:
            traits = analyze_body_traits(
                landmarks=None,
                original_image=None,
                height_cm=height_cm,
                weight_kg=weight_kg,
                gender=gender,
                age=age
            )
        except Exception as e:
            logger.error(f"Body traits analysis error: {str(e)}")
            traceback.print_exc()
            traits = {"error": str(e)}
            
        # Return all calculation results for comparison
        return jsonify({
            'navy_method': {
                'body_fat': navy_bf,
                'lean_mass': navy_lean,
                'calculation_method': method
            },
            'bmi_method': {
                'body_fat': bmi_bf,
                'lean_mass': bmi_lean
            },
            'body_traits': traits,
            'input_values': {
                'height_cm': height_cm,
                'height_m': height_m,
                'weight_kg': weight_kg,
                'age': age,
                'gender': gender,
                'waist_cm': waist_cm, 
                'neck_cm': neck_cm,
                'hip_cm': hip_cm
            }
        })
    except Exception as e:
        logger.error(f"Error in test calculation: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@test_routes.route('/debug-chart-data')
def debug_chart_data():
    """Test route to verify chart data format"""
    try:
        # Generate test chart data
        body_fat = 17.3
        lean_mass = 82.7
        
        # Store in session for template testing
        session['debug_chart_data'] = {
            'body_fat': body_fat,
            'lean_mass': lean_mass,
            'timestamp': time.time()
        }
        
        return jsonify({
            'body_fat': body_fat,
            'lean_mass': lean_mass,
            'session_data': session.get('debug_chart_data')
        })
    except Exception as e:
        logger.error(f"Error in debug chart data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@test_routes.route('/debug-chart-view')
def debug_chart_view():
    """Test route to render chart with test data"""
    # Get chart data from session or use defaults
    chart_data = session.get('debug_chart_data', {
        'body_fat': 17.3,
        'lean_mass': 82.7,
        'timestamp': time.time()
    })
    
    # Render a simple test template with the chart
    return render_template(
        'debug_chart.html',
        body_fat=chart_data['body_fat'],
        lean_mass=chart_data['lean_mass']
    )