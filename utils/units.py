"""
Unit handling utilities for consistent measurement display throughout the application.
"""

# Define standard units for each type of measurement
UNITS = {
    # Length measurements
    "height": "cm",
    "weight": "kg",
    "shoulder_width": "cm",
    "arm_length": "cm", 
    "leg_length": "cm",
    "torso_length": "cm",
    "wrist_circumference": "cm",
    "waist_circumference": "cm",
    "hip_circumference": "cm",
    "chest_circumference": "cm",
    "thigh_circumference": "cm",
    "calf_circumference": "cm",
    "bicep_circumference": "cm",
    "forearm_circumference": "cm",
    "neck_circumference": "cm",
    "ankle_circumference": "cm",
    "humerus_length": "cm",
    "femur_length": "cm",
    "tibia_length": "cm",
    "clavicle_width": "cm",
    
    # Ratios (unitless)
    "shoulder_hip_ratio": "",
    "arm_torso_ratio": "",
    "leg_torso_ratio": "",
    "waist_hip_ratio": "",
    "arm_span_height_ratio": "",
    "femur_tibia_ratio": "",
    "bmi": "kg/m²",
    "ffmi": "kg/m²",
    
    # Percentages
    "body_fat": "%",
    "muscle_mass": "%",
    "body_water": "%",
    
    # Other
    "muscle_potential": "kg/year",
    "ideal_weight_range": "kg",
    "maintenance_calories": "kcal"
}

def format_trait_value(trait_name, value):
    """
    Format a trait value with the appropriate unit.
    
    Args:
        trait_name: The key name of the trait
        value: The numeric or string value of the trait
        
    Returns:
        String with the value and its unit (if applicable)
    """
    # Convert trait name to snake_case for dictionary lookup
    lookup_key = trait_name.lower().replace(" ", "_")
    
    # Get the unit or default to an empty string
    unit = UNITS.get(lookup_key, "")
    
    # Don't add units to non-numeric or already formatted values
    if not isinstance(value, (int, float)) or isinstance(value, str):
        return str(value)
    
    # Format the value based on its type
    if isinstance(value, int):
        formatted_value = f"{value}"
    else:  # float
        formatted_value = f"{value:.1f}" if value % 1 != 0 else f"{int(value)}"
    
    # Add unit if applicable
    return f"{formatted_value} {unit}".strip()

def get_unit(trait_name):
    """
    Get the unit for a specific trait.
    
    Args:
        trait_name: The key name of the trait
        
    Returns:
        String with the unit symbol
    """
    # Convert trait name to snake_case for dictionary lookup
    lookup_key = trait_name.lower().replace(" ", "_")
    return UNITS.get(lookup_key, "")