"""
Body composition analysis utilities.
Provides functions for calculating body fat percentage and lean mass.
"""

import logging
import math
import numpy as np

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def calculate_body_composition(weight_kg, height_m, age, sex):
    """
    Calculate body fat percentage using BMI-based estimation
    
    Args:
        weight_kg (float): Weight in kilograms
        height_m (float): Height in meters
        age (int): Age in years
        sex (int): 1 for male, 0 for female
        
    Returns:
        tuple: (body_fat_percentage, lean_mass_percentage)
    """
    logger.debug(f"BMI calculation input - weight: {weight_kg}kg, height: {height_m}m, age: {age}, sex: {sex}")
    
    try:
        if not all(isinstance(x, (int, float)) for x in [weight_kg, height_m, age]):
            raise ValueError("Invalid input types")
        if not 30 <= weight_kg <= 300:
            logger.warning(f"Weight {weight_kg} outside recommended range")
            weight_kg = max(30, min(300, weight_kg))
        if not 1.0 <= height_m <= 2.5:
            logger.warning(f"Height {height_m} outside recommended range")
            height_m = max(1.0, min(2.5, height_m))
        if not 18 <= age <= 100:
            logger.warning(f"Age {age} outside recommended range")
            age = max(18, min(100, age))
        if sex not in [0, 1]:
            logger.warning(f"Invalid sex value: {sex}, defaulting to 0")
            sex = 0

        bmi = weight_kg / (height_m ** 2)
        logger.debug(f"Calculated BMI: {bmi:.1f}")
        
        body_fat = (1.20 * bmi) + (0.23 * age) - (10.8 * sex) - 5.4
        logger.debug(f"Initial body fat calculation: {body_fat:.1f}%")
        
        # Apply physiological constraints
        body_fat = max(5, min(50, body_fat))
        lean_mass = 100 - body_fat
        
        logger.debug(f"Final BMI-based results - Body Fat: {body_fat:.1f}%, Lean Mass: {lean_mass:.1f}%")
        return round(body_fat, 1), round(lean_mass, 1)
        
    except Exception as e:
        logger.error(f"Error in BMI-based body composition calculation: {str(e)}")
        # Return reasonable defaults if calculation fails
        return 20.0, 80.0

def analyze_body_traits(landmarks=None, original_image=None, height_cm=None, weight_kg=None, gender='male', age=30, experience=None, is_back_view=False, **kwargs):
    """
    Analyze body traits from image landmarks or measurements.
    This function integrates with the existing code base and calls
    other utility functions for calculation.
    
    Args:
        landmarks: Body landmarks from pose detection
        original_image: Original uploaded image
        height_cm: Height in centimeters
        weight_kg: Weight in kilograms
        gender: 'male' or 'female'
        age: Age in years
        experience: User's fitness experience level (e.g., 'beginner', 'intermediate', 'advanced')
        is_back_view: Boolean indicating if the image is a back view
        **kwargs: Additional keyword arguments for flexibility
        
    Returns:
        dict: Dictionary of body traits and metrics
    """
    logger.debug(f"Analyzing body traits - height: {height_cm}cm, weight: {weight_kg}kg, gender: {gender}, age: {age}")
    
    try:
        # Initialize height_m to avoid unbound variable errors
        height_m = 1.75  # Default height (175 cm)
        
        # Calculate BMI
        if height_cm and weight_kg:
            height_m = height_cm / 100.0
            bmi = weight_kg / (height_m ** 2)
            bmi = round(bmi, 1)
        else:
            bmi = 22.0  # Default healthy BMI
            
        # Calculate body fat percentage using Navy Method or BMI formula
            
        try:
            from utils.navy_body_fat import calculate_body_fat_navy_derived
            from utils.bodybuilding_metrics import calculate_body_fat_percentage
            
            # Get measurements from landmarks if available
            waist_cm = None
            neck_cm = None
            hip_cm = None
            
            # If we have measurements from landmarks, use them
            if landmarks is not None:
                # This would extract measurements from landmarks
                # For now, we'll use default calculations
                pass
                
            # Try to get body fat using Navy method first
            if all(x is not None for x in [height_cm, weight_kg, waist_cm, neck_cm]):
                if gender.lower() == 'female' and hip_cm is not None:
                    body_fat, method = calculate_body_fat_navy_derived(
                        gender, height_cm, weight_kg, waist_cm, neck_cm, hip_cm
                    )
                else:
                    body_fat, method = calculate_body_fat_navy_derived(
                        gender, height_cm, weight_kg, waist_cm, neck_cm
                    )
                logger.debug(f"Body fat calculated using {method}: {body_fat:.1f}%")
            else:
                # Fall back to BMI-based estimation
                sex_value = 1 if gender.lower() == 'male' else 0
                body_fat, lean_mass = calculate_body_composition(weight_kg, height_m, age, sex_value)
                logger.debug(f"Body fat calculated using BMI method: {body_fat:.1f}%")
                
        except Exception as e:
            logger.error(f"Error calculating body fat: {str(e)}")
            # Use BMI-based method as fallback
            sex_value = 1 if gender.lower() == 'male' else 0
            body_fat, lean_mass = calculate_body_composition(weight_kg, height_m, age, sex_value)
            
        # Ensure body fat is within physiological ranges
        body_fat = max(3.0, min(45.0, body_fat))
        lean_mass = 100 - body_fat
            
        # Define muscle building potential formula based on body composition
        # and other factors
        muscle_building = 5.0 + (10 - body_fat / 5.0) * 0.5  # Higher potential with lower body fat
        if gender.lower() == 'male':
            muscle_building += 1.0  # Males typically have higher potential due to hormones
            
        # Cap between 1-10
        muscle_building = max(1.0, min(10.0, muscle_building))
        
        # Identify body type based on metrics
        # Rough estimation based on common traits
        if body_fat < 10 and bmi < 23:
            body_type = 'ectomorph'
        elif body_fat < 15 and bmi >= 23 and bmi <= 28:
            body_type = 'mesomorph'
        elif body_fat > 20 and bmi > 25:
            body_type = 'endomorph'
        elif body_fat < 15 and bmi < 25:
            body_type = 'ecto-mesomorph'
        elif body_fat > 18 and bmi >= 23 and bmi <= 30:
            body_type = 'endo-mesomorph'
        else:
            body_type = 'balanced'
            
        # Log the determined body type
        logger.debug(f"Determined body type: {body_type}")
            
        # Compile results
        traits = {
            'body_fat_percentage': round(body_fat, 1),
            'lean_mass_percentage': round(lean_mass, 1),
            'muscle_building_potential': round(muscle_building, 1),
            'body_type': body_type,
            'bmi': bmi,
            'metabolic_efficiency': round(7.0 - (body_fat - 15) / 5, 1) if body_fat > 15 else round(7.0 + (15 - body_fat) / 10, 1),
            'recovery_capacity': round(min(9.0, 5.0 + (muscle_building / 2.0)), 1),
        }
        
        # Debug log the calculated traits
        logger.debug(f"Body traits calculated: {traits}")
        return traits
        
    except Exception as e:
        logger.error(f"Error in body traits analysis: {str(e)}")
        # Return default values if analysis fails
        return {
            'body_fat_percentage': 20.0,
            'lean_mass_percentage': 80.0,
            'muscle_building_potential': 5.0,
            'body_type': 'balanced',
            'bmi': 22.0,
            'metabolic_efficiency': 7.0,
            'recovery_capacity': 6.0,
        }