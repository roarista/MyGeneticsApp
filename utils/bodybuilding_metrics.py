"""
Bodybuilding Metrics Module

This module provides specialized analysis functions for bodybuilders and fitness enthusiasts,
focusing on physique proportions, symmetry, and body composition metrics.
"""

import math
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Function to complete bodybuilding analysis
def complete_bodybuilding_analysis(user_data):
    """
    Complete bodybuilding analysis using provided user data and measurements
    
    Args:
        user_data: Dictionary containing user information and measurements:
            - height_cm: Height in centimeters
            - weight_kg: Weight in kilograms
            - gender: 'male' or 'female'
            - neck_cm: Neck circumference in cm
            - chest_cm: Chest circumference in cm
            - shoulders_cm: Shoulder circumference in cm
            - waist_cm: Waist circumference in cm
            - hips_cm: Hip circumference in cm
            - left_arm_cm: Left arm circumference in cm
            - right_arm_cm: Right arm circumference in cm
            - left_thigh_cm: Left thigh circumference in cm
            - right_thigh_cm: Right thigh circumference in cm
            - left_calf_cm: Left calf circumference in cm
            - right_calf_cm: Right calf circumference in cm
            - wrist_cm: Wrist circumference in cm
            - ankle_cm: Ankle circumference in cm
            - experience: Training experience level
            
    Returns:
        Dictionary with bodybuilding analysis results
    """
    try:
        # Extract user data
        height_cm = float(user_data.get('height_cm', 0))
        weight_kg = float(user_data.get('weight_kg', 0))
        gender = user_data.get('gender', 'male')
        experience = user_data.get('experience', 'beginner')
        
        # Extract body measurements
        neck_cm = float(user_data.get('neck_cm', 0))
        shoulders_cm = float(user_data.get('shoulders_cm', 0))
        chest_cm = float(user_data.get('chest_cm', 0))
        waist_cm = float(user_data.get('waist_cm', 0))
        hips_cm = float(user_data.get('hips_cm', 0))
        left_arm_cm = float(user_data.get('left_arm_cm', 0))
        right_arm_cm = float(user_data.get('right_arm_cm', 0))
        left_thigh_cm = float(user_data.get('left_thigh_cm', 0))
        right_thigh_cm = float(user_data.get('right_thigh_cm', 0))
        left_calf_cm = float(user_data.get('left_calf_cm', 0))
        right_calf_cm = float(user_data.get('right_calf_cm', 0))
        wrist_cm = float(user_data.get('wrist_cm', 0))
        ankle_cm = float(user_data.get('ankle_cm', 0))
        
        # Create a measurements dictionary for analysis functions
        measurements = {
            'neck': neck_cm,
            'shoulders': shoulders_cm,
            'chest': chest_cm,
            'waist': waist_cm,
            'hips': hips_cm,
            'left_arm': left_arm_cm,
            'right_arm': right_arm_cm,
            'left_thigh': left_thigh_cm,
            'right_thigh': right_thigh_cm,
            'left_calf': left_calf_cm,
            'right_calf': right_calf_cm,
            'wrist': wrist_cm,
            'ankle': ankle_cm
        }
        
        # Calculate body fat percentage
        if neck_cm > 0 and waist_cm > 0:
            if gender.lower() == 'male':
                body_fat_percentage = estimate_bodyfat_from_measurements(
                    gender, waist_cm, neck_cm, height_cm)
            else:
                body_fat_percentage = estimate_bodyfat_from_measurements(
                    gender, waist_cm, neck_cm, height_cm, hips_cm)
        else:
            # Default to estimate based on BMI
            bmi = weight_kg / ((height_cm / 100) ** 2) if height_cm > 0 else 0
            if gender.lower() == 'male':
                body_fat_percentage = 1.20 * bmi + 0.23 * 30 - 16.2  # Assume age 30 by default
            else:
                body_fat_percentage = 1.20 * bmi + 0.23 * 30 - 5.4
                
            # Ensure reasonable bounds
            body_fat_percentage = max(5 if gender.lower() == 'male' else 10, 
                                       min(body_fat_percentage, 40))
        
        # Categorize body fat percentage
        bf_category = "Not Available"
        if body_fat_percentage is not None:
            if gender.lower() == 'male':
                if body_fat_percentage < 8:
                    bf_category = "Very Lean (Competition)"
                elif body_fat_percentage < 12:
                    bf_category = "Lean (Athletic)"
                elif body_fat_percentage < 18:
                    bf_category = "Fit"
                elif body_fat_percentage < 25:
                    bf_category = "Average"
                else:
                    bf_category = "Above Average"
            else:
                if body_fat_percentage < 15:
                    bf_category = "Very Lean (Competition)"
                elif body_fat_percentage < 20:
                    bf_category = "Lean (Athletic)"
                elif body_fat_percentage < 25:
                    bf_category = "Fit"
                elif body_fat_percentage < 32:
                    bf_category = "Average"
                else:
                    bf_category = "Above Average"
        
        # Calculate lean body mass
        lbm = calculate_lean_body_mass(weight_kg, body_fat_percentage)
        
        # Calculate FFMI (Fat-Free Mass Index)
        ffmi = calculate_fat_free_mass_index(lbm, height_cm) if lbm is not None else None
        
        # Calculate normalized FFMI
        norm_ffmi = calculate_normalized_ffmi(ffmi, height_cm) if ffmi is not None else None
        
        # Categorize FFMI
        ffmi_category = "Not Available"
        if norm_ffmi is not None:
            if gender.lower() == 'male':
                if norm_ffmi < 18:
                    ffmi_category = "Below Average"
                elif norm_ffmi < 20:
                    ffmi_category = "Average"
                elif norm_ffmi < 22:
                    ffmi_category = "Above Average"
                elif norm_ffmi < 24:
                    ffmi_category = "Excellent"
                elif norm_ffmi < 26:
                    ffmi_category = "Superior"
                else:
                    ffmi_category = "Exceptional"
            else:
                if norm_ffmi < 16:
                    ffmi_category = "Below Average"
                elif norm_ffmi < 18:
                    ffmi_category = "Average"
                elif norm_ffmi < 20:
                    ffmi_category = "Above Average"
                elif norm_ffmi < 22:
                    ffmi_category = "Excellent"
                elif norm_ffmi < 24:
                    ffmi_category = "Superior"
                else:
                    ffmi_category = "Exceptional"
        
        # Analyze muscle balance
        muscle_balance = analyze_muscle_balance(measurements)
        
        # Analyze arm and leg symmetry
        arm_symmetry = None
        if left_arm_cm is not None and right_arm_cm is not None and left_arm_cm > 0 and right_arm_cm > 0:
            arm_symmetry = analyze_arm_symmetry(left_arm_cm, right_arm_cm)
            
        leg_symmetry = None
        if left_thigh_cm is not None and right_thigh_cm is not None and left_thigh_cm > 0 and right_thigh_cm > 0:
            leg_symmetry = analyze_arm_symmetry(left_thigh_cm, right_thigh_cm)
        
        # Analyze shoulder-to-waist ratio
        shoulder_to_waist = None
        if shoulders_cm is not None and waist_cm is not None and shoulders_cm > 0 and waist_cm > 0:
            shoulder_to_waist = analyze_shoulder_to_waist_ratio(shoulders_cm, waist_cm)
        
        # Analyze genetic potential if we have wrist and ankle measurements
        genetic_potential = None
        if wrist_cm is not None and ankle_cm is not None and wrist_cm > 0 and ankle_cm > 0:
            genetic_potential = analyze_bodybuilding_potential(height_cm, wrist_cm, ankle_cm, gender)
        
        # Create user data dictionary for recommendations
        user_data = {
            'gender': gender,
            'height': height_cm,
            'weight': weight_kg,
            'body_fat': body_fat_percentage,
            'experience': experience,
            'goal': user_data.get('goal', 'build_muscle')
        }
        
        # Generate recommendations
        recommendation_data = {
            'body_fat_percentage': body_fat_percentage,
            'muscle_balance': muscle_balance if muscle_balance else {},
            'genetic_potential': {'rating': 'average'}  # Default value
        }
        
        # Add genetic potential data if available
        if genetic_potential is not None and 'genetic_potential' in genetic_potential:
            recommendation_data['genetic_potential'] = genetic_potential['genetic_potential']
            
        recommendations = formulate_bodybuilding_recommendations(recommendation_data, user_data)
        
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
            'proportions': {
                'shoulder_to_waist': shoulder_to_waist if shoulder_to_waist else {},
            },
            'genetic_potential': genetic_potential.get('genetic_potential', {}) if genetic_potential else {},
            'max_measurements': genetic_potential.get('max_measurements', {}) if genetic_potential else {},
            'recommendations': recommendations,
            'measurements': measurements
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error in complete bodybuilding analysis: {str(e)}")
        return {
            'error': f"Failed to complete bodybuilding analysis: {str(e)}",
            'body_composition': {
                'body_fat_percentage': 0,
                'body_fat_category': 'Unknown',
                'lean_body_mass': 0,
                'ffmi': 0,
                'ffmi_category': 'Unknown'
            }
        }

# Constants for ideal bodybuilding proportions
# Based on classical bodybuilding aesthetics like the Golden Ratio
IDEAL_SHOULDER_WAIST_RATIO = 1.618  # Golden ratio
IDEAL_CHEST_WAIST_RATIO = 1.4
IDEAL_ARM_NECK_RATIO = 1.0
IDEAL_CALF_NECK_RATIO = 0.96
IDEAL_THIGH_WAIST_RATIO = 0.75
IDEAL_ARM_FOREARM_RATIO = 1.47

# Formulas for body composition calculations
def calculate_body_fat_percentage(weight_kg, height_cm, age, gender, neck_cm, waist_cm, hip_cm=None):
    """
    Calculate body fat percentage using Navy method formula.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age: Age in years
        gender: 'male' or 'female'
        neck_cm: Neck circumference in cm
        waist_cm: Waist circumference in cm
        hip_cm: Hip circumference in cm (required for females)
        
    Returns:
        Body fat percentage as float
    """
    height_m = height_cm / 100
    
    try:
        if gender.lower() == 'male':
            # Male Navy formula
            body_fat = 495 / (1.0324 - 0.19077 * math.log10(waist_cm - neck_cm) + 0.15456 * math.log10(height_cm)) - 450
        else:
            # Female Navy formula (requires hip measurement)
            if hip_cm is None:
                raise ValueError("Hip circumference is required for female body fat calculation")
            body_fat = 495 / (1.29579 - 0.35004 * math.log10(waist_cm + hip_cm - neck_cm) + 0.22100 * math.log10(height_cm)) - 450
        
        # Ensure result is within reasonable bounds
        body_fat = max(3.0, min(body_fat, 45.0))
        return round(body_fat, 1)
        
    except (ValueError, ZeroDivisionError) as e:
        logger.error(f"Error calculating body fat percentage: {e}")
        return None

def calculate_lean_body_mass(weight_kg, body_fat_percentage):
    """
    Calculate lean body mass (everything except fat).
    
    Args:
        weight_kg: Total body weight in kg
        body_fat_percentage: Body fat as percentage
        
    Returns:
        Lean body mass in kg
    """
    try:
        lbm = weight_kg * (1 - (body_fat_percentage / 100))
        return round(lbm, 1)
    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating lean body mass: {e}")
        return None

def calculate_fat_free_mass_index(lean_body_mass_kg, height_cm):
    """
    Calculate Fat-Free Mass Index (FFMI), a measure of muscularity normalized for height.
    
    Args:
        lean_body_mass_kg: Lean body mass in kg
        height_cm: Height in centimeters
        
    Returns:
        FFMI value (standard range is approximately 18-25 for men, 15-21 for women)
    """
    try:
        height_m = height_cm / 100
        ffmi = lean_body_mass_kg / (height_m * height_m)
        return round(ffmi, 1)
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.error(f"Error calculating FFMI: {e}")
        return None

def calculate_normalized_ffmi(ffmi, height_cm):
    """
    Calculate normalized FFMI, adjusted to a height of 1.83m (6ft).
    Values above 25 may indicate exceptional muscle development.
    
    Args:
        ffmi: FFMI value
        height_cm: Height in centimeters
        
    Returns:
        Normalized FFMI value
    """
    try:
        height_m = height_cm / 100
        normalized_ffmi = ffmi + (6.1 * (1.83 - height_m))
        return round(normalized_ffmi, 1)
    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating normalized FFMI: {e}")
        return None

# Physique proportion analysis
def analyze_shoulder_to_waist_ratio(shoulder_cm, waist_cm):
    """
    Calculate and evaluate shoulder-to-waist ratio (V-taper).
    
    Args:
        shoulder_cm: Shoulder circumference or shoulder width in cm
        waist_cm: Waist circumference at narrowest point in cm
        
    Returns:
        Dictionary with ratio value and assessment
    """
    try:
        ratio = shoulder_cm / waist_cm
        
        if ratio < 1.3:
            assessment = "below_average"
            description = "Below average V-taper. Focus on developing lats and deltoids."
        elif 1.3 <= ratio < 1.5:
            assessment = "average"
            description = "Average V-taper. Continue developing shoulder width."
        elif 1.5 <= ratio < 1.618:
            assessment = "above_average"
            description = "Good V-taper. Close to the ideal golden ratio."
        else:  # ratio >= 1.618
            assessment = "excellent"
            description = "Excellent V-taper, matching or exceeding the golden ratio."
            
        return {
            "value": round(ratio, 2),
            "rating": assessment,
            "description": description,
            "ideal": IDEAL_SHOULDER_WAIST_RATIO
        }
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.error(f"Error analyzing shoulder-to-waist ratio: {e}")
        return None

def analyze_arm_symmetry(left_arm_cm, right_arm_cm):
    """
    Analyze the symmetry between left and right arm measurements.
    
    Args:
        left_arm_cm: Left arm circumference in cm
        right_arm_cm: Right arm circumference in cm
        
    Returns:
        Dictionary with symmetry ratio and assessment
    """
    try:
        # Always divide larger by smaller for consistent ratio > 1
        if left_arm_cm >= right_arm_cm:
            ratio = left_arm_cm / right_arm_cm
            dominant = "left"
        else:
            ratio = right_arm_cm / left_arm_cm
            dominant = "right"
        
        # Interpret the ratio
        if ratio < 1.03:
            assessment = "excellent"
            description = "Excellent arm symmetry. Difference is less than 3%."
        elif 1.03 <= ratio < 1.05:
            assessment = "good"
            description = "Good arm symmetry. Minor difference (3-5%)."
        elif 1.05 <= ratio < 1.1:
            assessment = "average"
            description = f"Average symmetry. {dominant.title()} arm is noticeably larger (5-10%)."
        else:  # ratio >= 1.1
            assessment = "below_average"
            description = f"Below average symmetry. {dominant.title()} arm is significantly larger (>10%)."
        
        difference_percent = (ratio - 1) * 100
        
        return {
            "ratio": round(ratio, 2),
            "difference_percent": round(difference_percent, 1),
            "dominant_arm": dominant,
            "rating": assessment,
            "description": description
        }
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.error(f"Error analyzing arm symmetry: {e}")
        return None

def analyze_muscle_balance(measurements):
    """
    Analyze overall muscle balance across major body parts.
    
    Args:
        measurements: Dictionary with the following keys (all in cm):
            - chest
            - shoulders
            - waist
            - hips
            - left_arm
            - right_arm
            - left_thigh
            - right_thigh
            - left_calf
            - right_calf
            - neck
            
    Returns:
        Dictionary with balance assessments and recommendations
    """
    try:
        balance = {}
        
        # Calculate averages for paired measurements
        arms_avg = (measurements.get('left_arm', 0) + measurements.get('right_arm', 0)) / 2
        thighs_avg = (measurements.get('left_thigh', 0) + measurements.get('right_thigh', 0)) / 2
        calves_avg = (measurements.get('left_calf', 0) + measurements.get('right_calf', 0)) / 2
        
        # Get other measurements
        chest = measurements.get('chest', 0)
        waist = measurements.get('waist', 0)
        neck = measurements.get('neck', 0)
        shoulders = measurements.get('shoulders', 0)
        
        # Calculate key ratios
        if waist > 0:
            chest_waist_ratio = chest / waist
            balance['chest_waist_ratio'] = {
                "value": round(chest_waist_ratio, 2),
                "ideal": IDEAL_CHEST_WAIST_RATIO,
                "description": "Ratio of chest to waist circumference"
            }
            
            thigh_waist_ratio = thighs_avg / waist
            balance['thigh_waist_ratio'] = {
                "value": round(thigh_waist_ratio, 2),
                "ideal": IDEAL_THIGH_WAIST_RATIO,
                "description": "Ratio of thigh to waist circumference"
            }
        
        if neck > 0:
            arm_neck_ratio = arms_avg / neck
            balance['arm_neck_ratio'] = {
                "value": round(arm_neck_ratio, 2),
                "ideal": IDEAL_ARM_NECK_RATIO,
                "description": "Ratio of arm to neck circumference"
            }
            
            calf_neck_ratio = calves_avg / neck
            balance['calf_neck_ratio'] = {
                "value": round(calf_neck_ratio, 2),
                "ideal": IDEAL_CALF_NECK_RATIO,
                "description": "Ratio of calf to neck circumference"
            }
        
        # Calculate upper/lower body balance
        if thighs_avg > 0 and arms_avg > 0:
            upper_lower_ratio = arms_avg / thighs_avg
            
            if upper_lower_ratio < 0.5:
                upper_lower_assessment = "Lower body dominant"
                upper_lower_recommendation = "Focus on upper body development"
            elif 0.5 <= upper_lower_ratio < 0.6:
                upper_lower_assessment = "Moderately lower body dominant"
                upper_lower_recommendation = "Slightly increase upper body training"
            elif 0.6 <= upper_lower_ratio < 0.7:
                upper_lower_assessment = "Balanced with slight lower body emphasis"
                upper_lower_recommendation = "Maintain current balance"
            elif 0.7 <= upper_lower_ratio < 0.8:
                upper_lower_assessment = "Well balanced physique"
                upper_lower_recommendation = "Maintain current balance"
            elif 0.8 <= upper_lower_ratio < 0.9:
                upper_lower_assessment = "Balanced with slight upper body emphasis"
                upper_lower_recommendation = "Maintain current balance"
            elif 0.9 <= upper_lower_ratio < 1.1:
                upper_lower_assessment = "Moderately upper body dominant"
                upper_lower_recommendation = "Slightly increase lower body training"
            else:  # ratio >= 1.1
                upper_lower_assessment = "Upper body dominant"
                upper_lower_recommendation = "Focus on lower body development"
            
            balance['upper_lower_balance'] = {
                "ratio": round(upper_lower_ratio, 2),
                "assessment": upper_lower_assessment,
                "recommendation": upper_lower_recommendation
            }
        
        # Generate overall assessment
        imbalances = []
        
        if 'chest_waist_ratio' in balance and balance['chest_waist_ratio']['value'] < IDEAL_CHEST_WAIST_RATIO * 0.9:
            imbalances.append("chest development")
        
        if 'arm_neck_ratio' in balance and balance['arm_neck_ratio']['value'] < IDEAL_ARM_NECK_RATIO * 0.9:
            imbalances.append("arm development")
        
        if 'calf_neck_ratio' in balance and balance['calf_neck_ratio']['value'] < IDEAL_CALF_NECK_RATIO * 0.9:
            imbalances.append("calf development")
        
        if 'thigh_waist_ratio' in balance and balance['thigh_waist_ratio']['value'] < IDEAL_THIGH_WAIST_RATIO * 0.9:
            imbalances.append("quad development")
        
        if imbalances:
            balance['weak_points'] = imbalances
        
        return balance
        
    except (TypeError, ValueError, ZeroDivisionError) as e:
        logger.error(f"Error analyzing muscle balance: {e}")
        return None

def estimate_bodyfat_from_measurements(gender, waist_cm, neck_cm, height_cm, hip_cm=None):
    """
    Estimate body fat percentage from circumference measurements.
    
    Args:
        gender: 'male' or 'female'
        waist_cm: Waist circumference at navel in cm
        neck_cm: Neck circumference in cm
        height_cm: Height in cm
        hip_cm: Hip circumference in cm (required for females)
        
    Returns:
        Estimated body fat percentage
    """
    try:
        if gender.lower() == 'male':
            body_fat = 86.010 * math.log10(waist_cm - neck_cm) - 70.041 * math.log10(height_cm) + 36.76
        else:
            if hip_cm is None:
                raise ValueError("Hip measurement required for female body fat estimation")
            body_fat = 163.205 * math.log10(waist_cm + hip_cm - neck_cm) - 97.684 * math.log10(height_cm) - 78.387
            
        # Clamp to realistic values
        body_fat = max(3.0, min(body_fat, 40.0))
        return round(body_fat, 1)
    except (ValueError, ZeroDivisionError) as e:
        logger.error(f"Error estimating body fat from measurements: {e}")
        return None

def estimate_ideal_weight(height_cm, gender, body_fat_target=None, frame_size='medium'):
    """
    Estimate ideal weight based on height, gender, and target body composition.
    
    Args:
        height_cm: Height in centimeters
        gender: 'male' or 'female'
        body_fat_target: Target body fat percentage (default: 12% for men, 22% for women)
        frame_size: 'small', 'medium', or 'large' (affects ideal weight calculation)
        
    Returns:
        Dictionary with ideal weight in different units and formulas
    """
    try:
        # Set default body fat targets if not specified
        if body_fat_target is None:
            body_fat_target = 12.0 if gender.lower() == 'male' else 22.0
            
        # Frame size adjustments (in kg)
        frame_adjustments = {
            'small': -2.7,
            'medium': 0,
            'large': 2.7
        }
        
        # Height in different units
        height_m = height_cm / 100
        height_inches = height_cm / 2.54
        
        # Calculate ideal weights using different formulas
        # Hamwi Formula
        if gender.lower() == 'male':
            hamwi_kg = 48.0 + 1.1 * (height_inches - 60)
        else:
            hamwi_kg = 45.5 + 0.9 * (height_inches - 60)
            
        # Robinson Formula
        if gender.lower() == 'male':
            robinson_kg = 52.0 + 1.9 * (height_inches - 60)
        else:
            robinson_kg = 49.0 + 1.7 * (height_inches - 60)
            
        # Miller Formula
        if gender.lower() == 'male':
            miller_kg = 56.2 + 1.41 * (height_inches - 60)
        else:
            miller_kg = 53.1 + 1.36 * (height_inches - 60)
            
        # Devine Formula
        if gender.lower() == 'male':
            devine_kg = 50.0 + 2.3 * (height_inches - 60)
        else:
            devine_kg = 45.5 + 2.3 * (height_inches - 60)
            
        # Average of the four formulas
        ideal_weight_avg = (hamwi_kg + robinson_kg + miller_kg + devine_kg) / 4
        
        # Adjust for frame size
        ideal_weight_avg += frame_adjustments.get(frame_size.lower(), 0)
        
        # Calculate fat-free mass and total weight at target body fat percentage
        ffm = ideal_weight_avg * (1 - (body_fat_target / 100))
        ideal_weight_at_target_bf = ffm / (1 - (body_fat_target / 100))
        
        # BMI-based calculation
        if gender.lower() == 'male':
            ideal_bmi = 24.5  # Midpoint of normal BMI range for men
        else:
            ideal_bmi = 22.5  # Midpoint of normal BMI range for women
            
        bmi_weight = ideal_bmi * (height_m * height_m)
        
        # Create result dictionary
        result = {
            "hamwi_formula_kg": round(hamwi_kg, 1),
            "robinson_formula_kg": round(robinson_kg, 1),
            "miller_formula_kg": round(miller_kg, 1),
            "devine_formula_kg": round(devine_kg, 1),
            "bmi_formula_kg": round(bmi_weight, 1),
            "average_kg": round(ideal_weight_avg, 1),
            "average_lbs": round(ideal_weight_avg * 2.20462, 1),
            "at_target_body_fat": {
                "target_percentage": body_fat_target,
                "weight_kg": round(ideal_weight_at_target_bf, 1),
                "weight_lbs": round(ideal_weight_at_target_bf * 2.20462, 1),
                "fat_free_mass_kg": round(ffm, 1)
            }
        }
        
        return result
    except Exception as e:
        logger.error(f"Error estimating ideal weight: {e}")
        return None

def analyze_bodybuilding_potential(height_cm, wrist_cm, ankle_cm, gender):
    """
    Analyze genetic muscular potential based on frame size indicators.
    
    Args:
        height_cm: Height in centimeters
        wrist_cm: Wrist circumference in cm
        ankle_cm: Ankle circumference in cm
        gender: 'male' or 'female'
        
    Returns:
        Dictionary with genetic potential assessment and estimated maximum muscular measurements
    """
    try:
        # Validate inputs
        if not height_cm or not wrist_cm or not ankle_cm or not gender:
            logger.error("Missing required measurements for genetic potential analysis")
            return None
            
        if height_cm <= 0 or wrist_cm <= 0 or ankle_cm <= 0:
            logger.error("Invalid measurements (must be positive values)")
            return None
        
        # Calculate frame size indicators
        height_m = height_cm / 100
        wrist_height_ratio = wrist_cm / height_cm
        ankle_height_ratio = ankle_cm / height_cm
        
        # Determine genetic potential score
        # Higher score indicates better natural potential for muscle building
        base_score = (wrist_height_ratio + ankle_height_ratio) * 100
        
        # Adjust score based on gender
        if gender.lower() == 'male':
            genetic_score = base_score * 1.0  # No adjustment for males
        else:
            genetic_score = base_score * 0.9  # Slight adjustment for females
            
        # Interpret genetic score
        if genetic_score < 10:
            potential = "below_average"
            description = "Below average genetic potential for muscle building. Your frame suggests an ectomorphic body type."
            
        elif 10 <= genetic_score < 11:
            potential = "average"
            description = "Average genetic potential for muscle building. Your frame suggests a balanced body type."
            
        elif 11 <= genetic_score < 12:
            potential = "above_average"
            description = "Above average genetic potential for muscle building. Your frame suggests a mesomorphic tendency."
            
        else:  # genetic_score >= 12
            potential = "excellent"
            description = "Excellent genetic potential for muscle building. Your frame suggests strong mesomorphic characteristics."
            
        # Estimate maximum muscular measurements (Martin Berkhan formula and adjustments)
        # These are theoretical maximums at ~5-6% body fat for males, ~12-14% for females
        max_arm_cm = wrist_cm * 2.5
        max_calf_cm = ankle_cm * 1.9
        max_forearm_cm = wrist_cm * 1.8
        max_neck_cm = neck_circumference = height_cm * 0.24
        max_chest_cm = height_cm * 0.6
        max_thigh_cm = height_cm * 0.36
        
        # Modest adjustment for females - less dimorphism in some measurements
        if gender.lower() == 'female':
            max_arm_cm *= 0.85
            max_forearm_cm *= 0.9
            max_neck_cm *= 0.9
            max_chest_cm *= 0.85  # Less difference in chest
            max_thigh_cm *= 0.95  # Less difference in thighs
        
        # Calculate estimate of fat-free mass maximum (Casey Butt formula)
        height_inches = height_cm / 2.54
        wrist_inches = wrist_cm / 2.54
        ankle_inches = ankle_cm / 2.54
        bodyfat_percentage = 5 if gender.lower() == 'male' else 14
        
        if gender.lower() == 'male':
            # Casey Butt formula for males
            max_ffm_lbs = (height_inches * 0.5 + wrist_inches + ankle_inches) * 7.8
            lean_factor = (height_inches - 69) * 0.5
        else:
            # Adjusted formula for females
            max_ffm_lbs = (height_inches * 0.4 + wrist_inches * 0.8 + ankle_inches * 0.8) * 7
            lean_factor = (height_inches - 64) * 0.4
            
        max_ffm_lbs += lean_factor
        max_ffm_kg = max_ffm_lbs / 2.20462
        
        # Calculate maximum realistic weight at given body fat percentage
        max_weight_kg = max_ffm_kg / (1 - (bodyfat_percentage / 100))
        max_ffmi = max_ffm_kg / (height_m * height_m)
        
        return {
            "genetic_potential": {
                "score": round(genetic_score, 1),
                "rating": potential,
                "description": description
            },
            "max_measurements": {
                "arm_cm": round(max_arm_cm, 1),
                "calf_cm": round(max_calf_cm, 1),
                "forearm_cm": round(max_forearm_cm, 1),
                "neck_cm": round(max_neck_cm, 1),
                "chest_cm": round(max_chest_cm, 1),
                "thigh_cm": round(max_thigh_cm, 1)
            },
            "maximum_muscular_potential": {
                "max_ffm_kg": round(max_ffm_kg, 1),
                "max_ffm_lbs": round(max_ffm_lbs, 1),
                "max_weight_at_bf_kg": round(max_weight_kg, 1),
                "max_weight_at_bf_lbs": round(max_weight_kg * 2.20462, 1),
                "body_fat_percentage": bodyfat_percentage,
                "max_ffmi": round(max_ffmi, 1)
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing bodybuilding potential: {e}")
        return None

def formulate_bodybuilding_recommendations(analysis_results, user_data):
    """
    Generate customized bodybuilding recommendations based on analysis results.
    
    Args:
        analysis_results: Dictionary containing all analysis results
        user_data: Dictionary with user information like experience level, goals, etc.
        
    Returns:
        Dictionary with structured recommendations
    """
    recommendations = {}
    
    try:
        # Validate inputs
        if not analysis_results or not isinstance(analysis_results, dict):
            logger.warning("Invalid analysis results provided to recommendations engine")
            analysis_results = {}
            
        if not user_data or not isinstance(user_data, dict):
            logger.warning("Invalid user data provided to recommendations engine")
            user_data = {}
    
        # Extract relevant data with safe fallbacks for all values
        body_fat = analysis_results.get('body_fat_percentage', 18)
        
        # Convert body_fat to float if it's not None, otherwise use default
        if body_fat is not None:
            try:
                body_fat = float(body_fat)
            except (ValueError, TypeError):
                body_fat = 18.0
        else:
            body_fat = 18.0
            
        genetic_potential = analysis_results.get('genetic_potential', {})
        if not isinstance(genetic_potential, dict):
            genetic_potential = {}
        genetic_rating = genetic_potential.get('rating', 'average')
        
        muscle_balance = analysis_results.get('muscle_balance', {})
        if not isinstance(muscle_balance, dict):
            muscle_balance = {}
            
        weak_points = muscle_balance.get('weak_points', [])
        if not isinstance(weak_points, list):
            weak_points = []
            
        experience = user_data.get('experience', 'beginner')
        gender = user_data.get('gender', 'male')
        goal = user_data.get('goal', 'build_muscle')
        
        # Determine optimal training frequency
        if experience == 'beginner':
            training_frequency = "3-4"
            volume_per_muscle = "10-12 weekly sets per muscle group"
        elif experience == 'intermediate':
            training_frequency = "4-5"
            volume_per_muscle = "13-16 weekly sets per muscle group"
        else:  # advanced
            training_frequency = "5-6"
            volume_per_muscle = "16-20 weekly sets per muscle group"
            
        # Determine optimal training split
        if training_frequency in ["3-4"]:
            training_split = "Full Body or Upper/Lower"
            training_schedule = {
                "Monday": "Full Body" if training_frequency == "3-4" else "Upper Body",
                "Tuesday": "Rest" if training_frequency == "3-4" else "Lower Body",
                "Wednesday": "Full Body" if training_frequency == "3-4" else "Rest",
                "Thursday": "Rest" if training_frequency == "3-4" else "Upper Body",
                "Friday": "Full Body" if training_frequency == "3-4" else "Lower Body",
                "Saturday": "Rest",
                "Sunday": "Rest"
            }
        elif training_frequency in ["4-5"]:
            training_split = "Upper/Lower or Push/Pull/Legs"
            if weak_points and any(point in ['arm development', 'chest development'] for point in weak_points):
                training_schedule = {
                    "Monday": "Push (Chest, Shoulders, Triceps)",
                    "Tuesday": "Pull (Back, Biceps)",
                    "Wednesday": "Legs",
                    "Thursday": "Rest",
                    "Friday": "Push (Chest, Shoulders, Triceps)",
                    "Saturday": "Pull (Back, Biceps)",
                    "Sunday": "Rest"
                }
            else:
                training_schedule = {
                    "Monday": "Upper Body",
                    "Tuesday": "Lower Body",
                    "Wednesday": "Rest",
                    "Thursday": "Upper Body",
                    "Friday": "Lower Body",
                    "Saturday": "Rest",
                    "Sunday": "Rest"
                }
        else:  # 5-6 days
            training_split = "Push/Pull/Legs or Body Part Split"
            training_schedule = {
                "Monday": "Push (Chest, Shoulders, Triceps)",
                "Tuesday": "Pull (Back, Biceps)",
                "Wednesday": "Legs",
                "Thursday": "Rest",
                "Friday": "Push (Chest, Shoulders, Triceps)",
                "Saturday": "Pull (Back, Biceps)",
                "Sunday": "Legs"
            }
            
        # Determine rep ranges based on goals
        if goal == "build_muscle":
            rep_ranges = "8-12 reps for most exercises, focusing on progressive overload"
            rest_periods = "60-90 seconds for isolation exercises, 2-3 minutes for compound lifts"
        elif goal == "strength":
            rep_ranges = "4-6 reps for main lifts, 6-8 reps for accessory work"
            rest_periods = "3-5 minutes for main lifts, 2-3 minutes for accessory work"
        elif goal == "fat_loss":
            rep_ranges = "10-15 reps with shorter rest periods, consider supersets and circuits"
            rest_periods = "30-60 seconds, use supersets to increase work density"
        else:  # general fitness
            rep_ranges = "8-15 reps with moderate weights, focus on form and mind-muscle connection"
            rest_periods = "60-90 seconds between sets"
            
        # Initialize nutrition variables to avoid unbound variables
        caloric_surplus = "250-350 calories above maintenance"
        caloric_deficit = "300-500 calories below maintenance"
        caloric_recommendation = "Maintenance calories (TDEE)"
        protein_recommendation = "1.6-2g per kg of bodyweight"
        carb_recommendation = "3-5g per kg of bodyweight"
        fat_recommendation = "0.8-1g per kg of bodyweight"
            
        # Determine nutrition recommendations
        if goal == "build_muscle":
            if genetic_rating in ["below_average", "average"]:
                caloric_surplus = "250-350 calories above maintenance"
            else:
                caloric_surplus = "350-500 calories above maintenance"
                
            protein_recommendation = "1.8-2.2g per kg of bodyweight"
            carb_recommendation = "4-7g per kg of bodyweight"
            fat_recommendation = "0.8-1.2g per kg of bodyweight"
            
        elif goal == "fat_loss":
            if body_fat > 25:
                caloric_deficit = "500-750 calories below maintenance"
            else:
                caloric_deficit = "300-500 calories below maintenance"
                
            protein_recommendation = "2.2-2.6g per kg of bodyweight"
            carb_recommendation = "2-4g per kg of bodyweight"
            fat_recommendation = "0.8-1g per kg of bodyweight"
            
        else:  # maintenance or general fitness
            caloric_recommendation = "Maintenance calories (TDEE)"
            protein_recommendation = "1.6-2g per kg of bodyweight"
            carb_recommendation = "3-5g per kg of bodyweight"
            fat_recommendation = "0.8-1g per kg of bodyweight"
            
        # Create recommendations dictionary
        recommendations = {
            "training": {
                "frequency": f"{training_frequency} days per week",
                "split": training_split,
                "weekly_schedule": training_schedule,
                "volume": volume_per_muscle,
                "rep_ranges": rep_ranges,
                "rest_periods": rest_periods
            },
            "nutrition": {
                "protein": protein_recommendation,
                "carbs": carb_recommendation,
                "fats": fat_recommendation,
                "meal_frequency": "4-6 meals per day" if goal == "build_muscle" else "3-5 meals per day",
                "caloric_adjustment": caloric_surplus if goal == "build_muscle" else 
                                     caloric_deficit if goal == "fat_loss" else 
                                     caloric_recommendation
            }
        }
        
        # Add weak point focus if necessary
        if weak_points:
            focus_exercises = []
            for weak_point in weak_points:
                if "chest" in weak_point:
                    focus_exercises.append({
                        "area": "Chest", 
                        "exercises": ["Incline Bench Press", "Dumbbell Flyes", "Cable Crossovers"],
                        "frequency": "2-3 times per week",
                        "volume": "4-6 sets per session"
                    })
                    
                elif "arm" in weak_point:
                    focus_exercises.append({
                        "area": "Arms",
                        "exercises": ["Close-Grip Bench Press", "Skull Crushers", "Incline Dumbbell Curls", "Hammer Curls"],
                        "frequency": "2-3 times per week",
                        "volume": "3-4 sets per exercise"
                    })
                    
                elif "calf" in weak_point:
                    focus_exercises.append({
                        "area": "Calves",
                        "exercises": ["Standing Calf Raises", "Seated Calf Raises", "Donkey Calf Raises"],
                        "frequency": "3-4 times per week",
                        "volume": "4-6 sets per session"
                    })
                    
                elif "quad" in weak_point or "thigh" in weak_point:
                    focus_exercises.append({
                        "area": "Legs",
                        "exercises": ["Front Squats", "Leg Extensions", "Hack Squats"],
                        "frequency": "2 times per week",
                        "volume": "4-5 sets per exercise"
                    })
            
            recommendations["weak_points"] = {
                "areas": weak_points,
                "focus_exercises": focus_exercises,
                "approach": "Prioritize these areas by training them first in your workouts when fresh."
            }
        
        return recommendations
    
    except Exception as e:
        logger.error(f"Error formulating bodybuilding recommendations: {e}")
        return {
            "training": {
                "frequency": "3-5 days per week",
                "split": "Full Body or Upper/Lower",
                "note": "An error occurred while creating detailed recommendations."
            }
        }