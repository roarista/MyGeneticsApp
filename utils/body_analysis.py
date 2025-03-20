import logging
import numpy as np
import math
from mediapipe import solutions

# Configure logging
logger = logging.getLogger(__name__)

# MediaPipe pose landmark indices
mp_pose = solutions.pose

def calculate_distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((p2['x'] - p1['x'])**2 + (p2['y'] - p1['y'])**2)

def calculate_angle(p1, p2, p3):
    """Calculate angle between three points"""
    angle = math.degrees(math.atan2(p3['y'] - p2['y'], p3['x'] - p2['x']) - 
                         math.atan2(p1['y'] - p2['y'], p1['x'] - p2['x']))
    return angle + 360 if angle < 0 else angle

def analyze_body_traits(landmarks, height_cm=0.0, weight_kg=0.0):
    """
    Analyze body landmarks to identify genetic traits
    
    Args:
        landmarks: Dictionary of body landmarks from MediaPipe
        height_cm: User's height in cm (optional, float)
        weight_kg: User's weight in kg (optional, float)
        
    Returns:
        Dictionary of body traits and measurements
    """
    try:
        if not landmarks:
            logger.error("No landmarks provided for analysis")
            return {}
        
        # Initialize traits dictionary
        traits = {}
        
        # Track whether we have enough data for advanced calculations
        has_height_weight = height_cm > 0 and weight_kg > 0
        
        # Extract key landmark indices for readability
        # Shoulders
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        
        # Hips
        LEFT_HIP = 23
        RIGHT_HIP = 24
        
        # Arms
        LEFT_ELBOW = 13
        RIGHT_ELBOW = 14
        LEFT_WRIST = 15
        RIGHT_WRIST = 16
        
        # Legs
        LEFT_KNEE = 25
        RIGHT_KNEE = 26
        LEFT_ANKLE = 27
        RIGHT_ANKLE = 28
        
        # Feet (for wingspan calculation)
        LEFT_FOOT_INDEX = 31
        RIGHT_FOOT_INDEX = 32
        
        # 1. Calculate shoulder width
        shoulder_width = calculate_distance(landmarks[LEFT_SHOULDER], landmarks[RIGHT_SHOULDER])
        
        # 2. Calculate hip width
        hip_width = calculate_distance(landmarks[LEFT_HIP], landmarks[RIGHT_HIP])
        
        # 3. Calculate torso length (average of left and right sides)
        left_torso = calculate_distance(landmarks[LEFT_SHOULDER], landmarks[LEFT_HIP])
        right_torso = calculate_distance(landmarks[RIGHT_SHOULDER], landmarks[RIGHT_HIP])
        torso_length = (left_torso + right_torso) / 2
        
        # 4. Calculate arm length (average of left and right arms)
        left_upper_arm = calculate_distance(landmarks[LEFT_SHOULDER], landmarks[LEFT_ELBOW])
        left_forearm = calculate_distance(landmarks[LEFT_ELBOW], landmarks[LEFT_WRIST])
        left_arm = left_upper_arm + left_forearm
        
        right_upper_arm = calculate_distance(landmarks[RIGHT_SHOULDER], landmarks[RIGHT_ELBOW])
        right_forearm = calculate_distance(landmarks[RIGHT_ELBOW], landmarks[RIGHT_WRIST])
        right_arm = right_upper_arm + right_forearm
        
        arm_length = (left_arm + right_arm) / 2
        
        # 5. Calculate leg length (average of left and right legs)
        left_upper_leg = calculate_distance(landmarks[LEFT_HIP], landmarks[LEFT_KNEE])
        left_lower_leg = calculate_distance(landmarks[LEFT_KNEE], landmarks[LEFT_ANKLE])
        left_leg = left_upper_leg + left_lower_leg
        
        right_upper_leg = calculate_distance(landmarks[RIGHT_HIP], landmarks[RIGHT_KNEE])
        right_lower_leg = calculate_distance(landmarks[RIGHT_KNEE], landmarks[RIGHT_ANKLE])
        right_leg = right_upper_leg + right_lower_leg
        
        leg_length = (left_leg + right_leg) / 2
        
        # 6. Calculate shoulder-to-hip ratio
        shoulder_hip_ratio = shoulder_width / hip_width if hip_width > 0 else 0
        
        # 7. Calculate arm-to-height ratio (if height provided)
        arm_height_ratio = arm_length / height_cm if height_cm > 0 else 0
        
        # 8. Calculate leg-to-height ratio (if height provided)
        leg_height_ratio = leg_length / height_cm if height_cm > 0 else 0
        
        # 9. Calculate arm-to-torso ratio
        arm_torso_ratio = arm_length / torso_length if torso_length > 0 else 0
        
        # 10. Calculate leg-to-torso ratio
        leg_torso_ratio = leg_length / torso_length if torso_length > 0 else 0
        
        # Define points for additional measures
        NOSE = 0
        LEFT_EYE = 1
        RIGHT_EYE = 2
        LEFT_EAR = 3
        RIGHT_EAR = 4
        LEFT_MOUTH = 9
        RIGHT_MOUTH = 10
        
        # 11. Calculate waist (approximated)
        waist_points = [landmarks[LEFT_HIP], landmarks[RIGHT_HIP]]
        # Calculate points slightly above hips for waist approximation
        waist_y = (landmarks[LEFT_HIP]['y'] + landmarks[RIGHT_HIP]['y']) / 2 - 0.05  # Slightly above hips
        waist_left = {'x': landmarks[LEFT_HIP]['x'] - 0.02, 'y': waist_y, 'z': landmarks[LEFT_HIP]['z']}
        waist_right = {'x': landmarks[RIGHT_HIP]['x'] + 0.02, 'y': waist_y, 'z': landmarks[RIGHT_HIP]['z']}
        waist_width = calculate_distance(waist_left, waist_right)
        
        # 12. Calculate chest width (using shoulders)
        chest_width = shoulder_width * 0.9  # Approximate chest width
        
        # 13. Calculate neck (using ears and shoulders)
        neck_width = calculate_distance(landmarks[LEFT_EAR], landmarks[RIGHT_EAR]) * 0.7
        
        # 14. Calculate ankle width for frame size assessment
        ankle_width = (calculate_distance(landmarks[LEFT_ANKLE], {'x': landmarks[LEFT_ANKLE]['x'] + 0.02, 
                                        'y': landmarks[LEFT_ANKLE]['y'], 
                                        'z': landmarks[LEFT_ANKLE]['z']}) +
                      calculate_distance(landmarks[RIGHT_ANKLE], {'x': landmarks[RIGHT_ANKLE]['x'] - 0.02, 
                                         'y': landmarks[RIGHT_ANKLE]['y'], 
                                         'z': landmarks[RIGHT_ANKLE]['z']})) / 2
        
        # 15. Calculate wrist width for frame size assessment
        wrist_width = (calculate_distance(landmarks[LEFT_WRIST], {'x': landmarks[LEFT_WRIST]['x'] + 0.02, 
                                         'y': landmarks[LEFT_WRIST]['y'], 
                                         'z': landmarks[LEFT_WRIST]['z']}) +
                      calculate_distance(landmarks[RIGHT_WRIST], {'x': landmarks[RIGHT_WRIST]['x'] - 0.02, 
                                        'y': landmarks[RIGHT_WRIST]['y'], 
                                        'z': landmarks[RIGHT_WRIST]['z']})) / 2
        
        # New proportional measurements
        # 16. Estimate arm span (using shoulder width and arm length)
        arm_span = shoulder_width + (2 * arm_length)
        
        # 17. Calculate humerus length (upper arm)
        humerus_length = (left_upper_arm + right_upper_arm) / 2
        
        # 18. Calculate femur length (upper leg)
        femur_length = (left_upper_leg + right_upper_leg) / 2
        
        # 19. Calculate tibia length (lower leg)
        tibia_length = (left_lower_leg + right_lower_leg) / 2
        
        # 20. Calculate femur-to-tibia ratio
        femur_tibia_ratio = femur_length / tibia_length if tibia_length > 0 else 0
        
        # 21. Estimate clavicle width (as proportion of shoulder width)
        clavicle_width = shoulder_width * 0.85
        
        # Advanced calculations using height and weight if available
        if has_height_weight:
            # 22. Calculate BMI
            bmi = weight_kg / ((height_cm / 100) ** 2)
            
            # 23. Estimate body fat percentage using improved anthropometric measurements
            # Use more precise algorithms for body composition assessment
            
            # Calculate waist to hip ratio as a key indicator
            waist_to_hip = waist_width / hip_width
            
            # Calculate upper body ratios
            shoulder_to_waist = shoulder_width / waist_width
            chest_to_waist = chest_width / waist_width
            
            # Calculate body surface area estimation
            bsa = 0.007184 * (height_cm ** 0.725) * (weight_kg ** 0.425) if height_cm > 0 and weight_kg > 0 else 1.5
            
            # Method 1: Enhanced YMCA formula using skeletal ratios
            # Adjusts for muscle mass based on shoulder and chest proportions
            skeletal_adjustment = 0
            if shoulder_to_waist > 1.5:  # Indicates significant muscle development
                skeletal_adjustment = -4.0  # Reduce body fat estimate (more muscle)
            elif shoulder_to_waist < 1.2:  # Indicates less muscle development
                skeletal_adjustment = 2.0  # Increase body fat estimate (less muscle)
                
            ymca_bf = ((4.15 * waist_width * 100) - (0.082 * weight_kg) - 94.42) / weight_kg * 100
            ymca_adjusted = ymca_bf + skeletal_adjustment
            
            # Method 2: Modified BMI-based formula with anthropometric corrections
            # Account for muscle mass using shoulder-to-waist ratio
            bmi_correction = (shoulder_to_waist - 1.3) * 10  # Adjusts for muscularity
            bmi_bf = (1.2 * bmi) + (0.23 * 30) - bmi_correction - 16.2
            
            # Method 3: Advanced waist-to-height ratio with body shape adjustment
            waist_to_height = waist_width / (height_cm / 100)
            body_shape_factor = chest_to_waist / waist_to_hip  # Accounts for upper vs lower body composition
            wth_bf = (waist_to_height * 50) - (5 * body_shape_factor) - 15
            
            # Method 4: Sophisticated visual analysis using proportions
            # Use relative proportions across major body segments
            upper_body_width = (shoulder_width + chest_width) / 2
            lower_body_width = (hip_width + waist_width) / 2
            upper_lower_ratio = upper_body_width / lower_body_width
            
            # Adjust based on typical fat distribution patterns
            visual_bf_base = 18 + (waist_to_hip * 20) - (upper_lower_ratio * 10)
            visual_bf = max(8, min(visual_bf_base, 35))  # Reasonable constraints
            
            # Weighted average with greater emphasis on methods most reliable from image analysis
            # Visual and waist-to-height are more reliable from images than weight-based formulas
            body_fat_percentage = (
                (0.15 * ymca_adjusted) + 
                (0.15 * bmi_bf) + 
                (0.35 * wth_bf) + 
                (0.35 * visual_bf)
            )
            
            # Apply gender-specific adjustments if height and weight suggest a pattern
            # (This is a rough estimate since we don't have explicit gender input)
            height_weight_ratio = height_cm / weight_kg
            if height_weight_ratio > 2.8:  # Suggests female proportions
                body_fat_percentage += 3  # Females typically have 3-5% higher essential fat
            
            # Ensure result is in reasonable range and avoid extreme values
            body_fat_percentage = max(5, min(body_fat_percentage, 35))
            
            # 26. Estimate lean body mass
            lean_body_mass = weight_kg * (1 - (body_fat_percentage / 100))
            
            # 27. Calculate Fat-Free Mass Index (FFMI)
            # FFMI = LBM in kg / (height in meters)^2
            ffmi = lean_body_mass / ((height_cm / 100) ** 2)
            
            # 28. Normalize FFMI (commonly done to compare across heights)
            # Formula: Normalized FFMI = FFMI + (6.1 * (1.8 - height_m))
            height_m = height_cm / 100
            normalized_ffmi = ffmi + (6.1 * (1.8 - height_m))
            
            # 29. Estimate frame size based on wrist circumference and height
            wrist_height_ratio = wrist_width / height_cm
            
            # 30. Calculate ideal weight range based on frame size
            lower_ideal_weight = (height_cm - 100) - ((height_cm - 150) / 4)
            upper_ideal_weight = lower_ideal_weight + (lower_ideal_weight * 0.1)
            
            # 31. Calculate muscle potential (based on frame size, height, and genetic factors)
            muscle_potential = ((shoulder_width * wrist_width * ankle_width) / height_cm) * 50
            
            # 32. Calculate arm span to height ratio - important for athletic potential
            arm_span_height_ratio = arm_span / height_cm
            
            # Add the advanced metrics to traits
            traits['bmi'] = {
                'value': round(bmi, 1),
                'rating': classify_bmi(bmi)
            }
            
            traits['body_fat_percentage'] = {
                'value': round(body_fat_percentage, 1),
                'rating': classify_body_fat(body_fat_percentage)
            }
            
            traits['lean_body_mass'] = {
                'value': round(lean_body_mass, 1),
                'rating': 'informational'  # This is just informational, no classification
            }
            
            traits['ffmi'] = {
                'value': round(ffmi, 1),
                'rating': classify_ffmi(ffmi)
            }
            
            traits['normalized_ffmi'] = {
                'value': round(normalized_ffmi, 1),
                'rating': 'informational'
            }
            
            traits['frame_size'] = {
                'value': classify_frame_size(wrist_height_ratio),
                'rating': 'informational'  # Categorical value
            }
            
            traits['ideal_weight_range'] = {
                'value': f"{round(lower_ideal_weight, 1)} - {round(upper_ideal_weight, 1)} kg",
                'rating': 'informational'  # This is just informational
            }
            
            traits['muscle_potential'] = {
                'value': round(muscle_potential, 1),
                'rating': classify_muscle_potential(muscle_potential)
            }
            
            traits['arm_span_height_ratio'] = {
                'value': round(arm_span_height_ratio, 2),
                'rating': classify_arm_span_ratio(arm_span_height_ratio)
            }
        
        # Store the basic measured values
        traits['shoulder_width'] = {
            'value': shoulder_width,
            'rating': classify_shoulder_width(shoulder_width, height_cm)
        }
        
        traits['shoulder_hip_ratio'] = {
            'value': shoulder_hip_ratio,
            'rating': classify_shoulder_hip_ratio(shoulder_hip_ratio)
        }
        
        traits['arm_length'] = {
            'value': arm_length,
            'rating': classify_arm_length(arm_length, height_cm)
        }
        
        traits['leg_length'] = {
            'value': leg_length,
            'rating': classify_leg_length(leg_length, height_cm)
        }
        
        traits['arm_torso_ratio'] = {
            'value': arm_torso_ratio,
            'rating': classify_arm_torso_ratio(arm_torso_ratio)
        }
        
        traits['torso_length'] = {
            'value': torso_length,
            'rating': classify_torso_length(torso_length, height_cm)
        }
        
        # Add bone structure and joint metrics
        traits['femur_tibia_ratio'] = {
            'value': round(femur_tibia_ratio, 2),
            'rating': 'informational'
        }
        
        traits['humerus_length'] = {
            'value': round(humerus_length, 1),
            'rating': 'informational'
        }
        
        traits['clavicle_width'] = {
            'value': round(clavicle_width, 1),
            'rating': 'informational'
        }
        
        # Add waist-to-hip ratio, important for fitness assessment
        traits['waist_hip_ratio'] = {
            'value': round(waist_width / hip_width, 2) if hip_width > 0 else 0,
            'rating': classify_waist_hip_ratio(waist_width / hip_width if hip_width > 0 else 0)
        }
        
        # Determine body type based on proportions
        traits['body_type'] = determine_body_type(
            shoulder_hip_ratio,
            arm_torso_ratio,
            leg_torso_ratio
        )
        
        # Add description of what these measurements mean
        traits['description'] = get_trait_descriptions(traits['body_type'])
        
        return traits
        
    except Exception as e:
        logger.error(f"Error analyzing body traits: {str(e)}")
        return {
            'error': str(e),
            'body_type': 'unknown',
            'description': 'Unable to analyze body traits.'
        }

def classify_shoulder_width(width, height):
    """Classify shoulder width relative to height"""
    if height <= 0:
        # Use absolute values if height not provided
        if width > 200:
            return 'excellent'
        elif width > 170:
            return 'good'
        elif width > 140:
            return 'average'
        else:
            return 'below_average'
    else:
        # Use relative to height
        ratio = width / height
        if ratio > 0.25:
            return 'excellent'  # Very broad shoulders
        elif ratio > 0.22:
            return 'good'       # Broad shoulders
        elif ratio > 0.19:
            return 'average'    # Average shoulders
        else:
            return 'below_average'  # Narrow shoulders

def classify_shoulder_hip_ratio(ratio):
    """Classify shoulder-to-hip ratio"""
    if ratio > 1.5:
        return 'excellent'  # V-shaped torso
    elif ratio > 1.3:
        return 'good'       # Athletic torso
    elif ratio > 1.1:
        return 'average'    # Average torso
    else:
        return 'below_average'  # Rectangular or pear-shaped torso

def classify_arm_length(length, height):
    """Classify arm length relative to height"""
    if height <= 0:
        # Use absolute values if height not provided
        if length > 75:
            return 'excellent'
        elif length > 65:
            return 'good'
        elif length > 55:
            return 'average'
        else:
            return 'below_average'
    else:
        # Use relative to height
        ratio = length / height
        if ratio > 0.45:
            return 'excellent'  # Long arms (good for deadlifts, rows)
        elif ratio > 0.42:
            return 'good'
        elif ratio > 0.38:
            return 'average'
        else:
            return 'below_average'  # Short arms (good for bench press)

def classify_leg_length(length, height):
    """Classify leg length relative to height"""
    if height <= 0:
        # Use absolute values if height not provided
        if length > 90:
            return 'excellent'
        elif length > 80:
            return 'good'
        elif length > 70:
            return 'average'
        else:
            return 'below_average'
    else:
        # Use relative to height
        ratio = length / height
        if ratio > 0.55:
            return 'excellent'  # Long legs (good for running)
        elif ratio > 0.5:
            return 'good'
        elif ratio > 0.45:
            return 'average'
        else:
            return 'below_average'  # Short legs (good for squat)

def classify_arm_torso_ratio(ratio):
    """Classify arm-to-torso ratio"""
    if ratio > 1.1:
        return 'excellent'  # Long arms relative to torso
    elif ratio > 0.9:
        return 'good'
    elif ratio > 0.8:
        return 'average'
    else:
        return 'below_average'  # Short arms relative to torso

def classify_torso_length(length, height):
    """Classify torso length relative to height"""
    if height <= 0:
        # Use absolute values if height not provided
        if length > 70:
            return 'excellent'
        elif length > 60:
            return 'good'
        elif length > 50:
            return 'average'
        else:
            return 'below_average'
    else:
        # Use relative to height
        ratio = length / height
        if ratio > 0.35:
            return 'excellent'  # Long torso (good for swimming)
        elif ratio > 0.32:
            return 'good'
        elif ratio > 0.28:
            return 'average'
        else:
            return 'below_average'  # Short torso

def determine_body_type(shoulder_hip_ratio, arm_torso_ratio, leg_torso_ratio):
    """Determine body type based on proportions"""
    # Ectomorph: Thin, lean, typically with long limbs
    # Mesomorph: Athletic, muscular, with broad shoulders and narrow waist
    # Endomorph: Rounder, higher body fat percentage, broader waist
    
    if shoulder_hip_ratio > 1.4 and arm_torso_ratio > 0.9:
        if leg_torso_ratio > 2.0:
            return "Mesomorph-Ectomorph"  # Athletic with long limbs
        else:
            return "Mesomorph"  # Athletic, V-shaped body
    elif shoulder_hip_ratio < 1.2 and arm_torso_ratio < 0.85:
        return "Endomorph"  # Rounder shape
    elif arm_torso_ratio > 1.0 and leg_torso_ratio > 2.0:
        return "Ectomorph"  # Long, lean build
    else:
        return "Hybrid"  # Mix of body types

def classify_bmi(bmi):
    """Classify BMI according to standard categories"""
    if bmi < 18.5:
        return 'below_average'  # Underweight
    elif bmi < 25:
        return 'excellent'  # Normal weight
    elif bmi < 30:
        return 'average'  # Overweight
    else:
        return 'below_average'  # Obese

def classify_body_fat(percentage):
    """Classify body fat percentage"""
    # Using a general scale that works for most adults
    if percentage < 8:
        return 'below_average'  # Too low
    elif percentage < 15:
        return 'excellent'  # Athletic
    elif percentage < 20:
        return 'good'  # Fit
    elif percentage < 25:
        return 'average'  # Acceptable
    else:
        return 'below_average'  # High

def classify_frame_size(wrist_height_ratio):
    """Classify frame size based on wrist-to-height ratio"""
    if wrist_height_ratio < 0.1:
        return 'Small'
    elif wrist_height_ratio < 0.11:
        return 'Medium'
    else:
        return 'Large'

def classify_muscle_potential(potential):
    """Classify muscle building potential"""
    if potential > 80:
        return 'excellent'
    elif potential > 60:
        return 'good'
    elif potential > 40:
        return 'average'
    else:
        return 'below_average'

def classify_waist_hip_ratio(ratio):
    """Classify waist-to-hip ratio"""
    if ratio < 0.85:
        return 'excellent'  # Very good ratio
    elif ratio < 0.9:
        return 'good'
    elif ratio < 0.95:
        return 'average'
    else:
        return 'below_average'  # Higher health risk
        
def classify_ffmi(ffmi):
    """Classify Fat-Free Mass Index"""
    # FFMI is a measure of muscularity normalized for height
    if ffmi > 25:
        return 'excellent'  # Exceptional muscularity
    elif ffmi > 22:
        return 'good'       # Above average muscularity
    elif ffmi > 19:
        return 'average'    # Average muscularity
    else:
        return 'below_average'  # Below average muscularity
        
def classify_arm_span_ratio(ratio):
    """Classify arm span to height ratio"""
    # Typical arm span is roughly equal to height
    # Values over 1.0 indicate longer reach
    if ratio > 1.05:
        return 'excellent'  # Exceptional reach advantage
    elif ratio > 1.01:
        return 'good'       # Good reach
    elif ratio > 0.97:
        return 'average'    # Average proportions
    else:
        return 'below_average'  # Shorter reach

def get_trait_descriptions(body_type):
    """Get detailed descriptions of what body type means for fitness"""
    descriptions = {
        "Mesomorph-Ectomorph": (
            "You have an athletic frame with longer limbs. Your body responds well to both "
            "strength and endurance training. You likely excel at compound movements and "
            "can build muscle with proper nutrition and consistency."
        ),
        "Mesomorph": (
            "You have a naturally athletic build with broad shoulders and a narrower waist. "
            "Your body responds quickly to resistance training, and you can build muscle mass "
            "relatively easily compared to other body types."
        ),
        "Endomorph": (
            "You have a rounder build that may store fat more easily. Your strength is likely "
            "in your lower body, with potential for strong squats and leg movements. Focus on "
            "a mix of resistance training and cardio for best results."
        ),
        "Ectomorph": (
            "You have a naturally lean build with longer limbs. You may excel at endurance "
            "activities but might find it challenging to gain muscle mass. Focus on compound "
            "movements and ensure adequate caloric surplus during muscle-building phases."
        ),
        "Hybrid": (
            "You have characteristics of multiple body types, giving you versatility in different "
            "training modalities. This balanced structure allows you to perform well across "
            "various exercise types with proper training."
        ),
        "unknown": (
            "We couldn't determine your body type from the image provided. For better results, "
            "please upload a clear, full-body image in a neutral standing position."
        )
    }
    
    return descriptions.get(body_type, descriptions["unknown"])
