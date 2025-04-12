"""
Body Fat calculation using U.S. Navy method.

The U.S. Navy body fat formula is more accurate than BMI and uses 
measurements of circumference at specific body points.

For men: BF% = 86.010 × log10(abdomen - neck) - 70.041 × log10(height) + 36.76
For women: BF% = 163.205 × log10(waist + hip - neck) - 97.684 × log10(height) - 104.912

These formulas have been validated to be accurate to within 3-4% of underwater 
weighing, which is considered a gold standard for body fat testing.
"""

import math
import logging

logger = logging.getLogger(__name__)

def calculate_navy_body_fat(
    gender, 
    height_cm, 
    neck_cm, 
    waist_cm, 
    hip_cm=None
):
    """
    Calculate body fat percentage using the U.S. Navy method.
    
    Args:
        gender: 'male' or 'female'
        height_cm: Height in centimeters
        neck_cm: Neck circumference in centimeters
        waist_cm: Waist circumference in centimeters
        hip_cm: Hip circumference in centimeters (required for women)
        
    Returns:
        Body fat percentage as a float, or None if invalid parameters
    """
    try:
        # Validate inputs
        if height_cm <= 0 or neck_cm <= 0 or waist_cm <= 0:
            logger.warning("Invalid measurements for Navy body fat calculation")
            return None
            
        if gender.lower() == 'female' and (hip_cm is None or hip_cm <= 0):
            logger.warning("Hip measurement required for female body fat calculation")
            return None
            
        # Apply the Navy formula based on gender
        if gender.lower() == 'male':
            # Male formula
            body_fat = 86.010 * math.log10(waist_cm - neck_cm) - 70.041 * math.log10(height_cm) + 36.76
        else:
            # Female formula
            body_fat = 163.205 * math.log10(waist_cm + hip_cm - neck_cm) - 97.684 * math.log10(height_cm) - 104.912
        
        # Limit to physiologically realistic range
        body_fat = max(3.0, min(body_fat, 45.0))
        
        return body_fat
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error in Navy body fat calculation: {str(e)}")
        return None

def calculate_waist_to_height_ratio(waist_cm, height_cm):
    """
    Calculate waist-to-height ratio, a powerful predictor of health risks
    
    Args:
        waist_cm: Waist circumference in centimeters
        height_cm: Height in centimeters
        
    Returns:
        Waist-to-height ratio as a float, or None if invalid parameters
    """
    try:
        if waist_cm <= 0 or height_cm <= 0:
            return None
            
        ratio = waist_cm / height_cm
        return ratio
    except (ValueError, TypeError):
        return None

def calculate_body_fat_navy_derived(
    gender, 
    height_cm, 
    weight_kg, 
    waist_cm, 
    neck_cm=None, 
    hip_cm=None
):
    """
    Derive body fat percentage using a variation of the Navy method.
    
    This function uses the full Navy method if all measurements are available,
    or falls back to a derived formula using the waist-to-height ratio if some
    measurements are missing.
    
    Args:
        gender: 'male' or 'female'
        height_cm: Height in centimeters
        weight_kg: Weight in kilograms
        waist_cm: Waist circumference in centimeters
        neck_cm: Neck circumference in centimeters (optional)
        hip_cm: Hip circumference in centimeters (optional, needed for women)
        
    Returns:
        Body fat percentage as a float
    """
    # Try the full Navy formula if all measurements are available
    if neck_cm is not None and waist_cm is not None:
        if gender.lower() == 'female' and hip_cm is not None:
            navy_bf = calculate_navy_body_fat(gender, height_cm, neck_cm, waist_cm, hip_cm)
            if navy_bf is not None:
                return navy_bf, 'full_navy'
        elif gender.lower() == 'male':
            navy_bf = calculate_navy_body_fat(gender, height_cm, neck_cm, waist_cm)
            if navy_bf is not None:
                return navy_bf, 'full_navy'
    
    # Calculate BMI
    bmi = weight_kg / ((height_cm / 100) ** 2) if height_cm > 0 else 0
    
    # Calculate waist-to-height ratio
    waist_height_ratio = calculate_waist_to_height_ratio(waist_cm, height_cm)
    
    # Use waist-to-height ratio and BMI to estimate body fat
    # This is a derived formula based on research correlating these measures
    if waist_height_ratio is not None:
        if gender.lower() == 'male':
            # Male derived formula
            bf_estimate = (waist_height_ratio * 100 - 34) + (bmi * 0.15)
        else:
            # Female derived formula (women naturally have higher essential fat)
            bf_estimate = (waist_height_ratio * 100 - 34) + (bmi * 0.15) + 10
            
        # Apply corrections based on expected ranges
        if bf_estimate < 3:  # Below essential fat levels
            bf_estimate = 3 + (bf_estimate * 0.5)
        elif bf_estimate > 45:  # Above realistic maximum
            bf_estimate = 45
            
        return bf_estimate, 'derived'
    
    # Last resort: use BMI-based estimation
    if gender.lower() == 'male':
        bf_estimate = 1.20 * bmi + 0.23 * 30 - 16.2  # assume age 30
    else:
        bf_estimate = 1.20 * bmi + 0.23 * 30 - 5.4
        
    # Ensure reasonable bounds
    bf_min = 5 if gender.lower() == 'male' else 10  # Essential fat levels
    bf_estimate = max(bf_min, min(bf_estimate, 45))
    
    return bf_estimate, 'bmi_based'