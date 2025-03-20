import logging

# Configure logging
logger = logging.getLogger(__name__)

def generate_recommendations(traits, experience_level='beginner'):
    """
    Generate fitness recommendations based on body traits
    
    Args:
        traits: Dictionary of body traits from analysis
        experience_level: User's fitness experience level
    
    Returns:
        Dictionary of recommendations
    """
    try:
        # Get body type and initialize recommendations
        body_type = traits.get('body_type', 'unknown')
        
        recommendations = {
            'strengths': [],
            'focus_areas': [],
            'exercise_recommendations': [],
            'training_split': {},
            'nutrition_tips': []
        }
        
        # Add strengths based on traits
        for trait, data in traits.items():
            if trait in ['body_type', 'description'] or not isinstance(data, dict):
                continue
                
            if data.get('rating') in ['excellent', 'good']:
                strength = get_strength_for_trait(trait, data.get('rating'))
                if strength:
                    recommendations['strengths'].append(strength)
        
        # Add focus areas based on traits
        for trait, data in traits.items():
            if trait in ['body_type', 'description'] or not isinstance(data, dict):
                continue
                
            if data.get('rating') in ['average', 'below_average']:
                focus = get_focus_for_trait(trait, data.get('rating'))
                if focus:
                    recommendations['focus_areas'].append(focus)
        
        # Generate exercise recommendations based on body type and traits
        recommendations['exercise_recommendations'] = get_exercises_by_body_type(
            body_type, 
            traits, 
            experience_level
        )
        
        # Generate training split recommendation
        recommendations['training_split'] = get_training_split(
            body_type, 
            experience_level
        )
        
        # Generate nutrition tips
        recommendations['nutrition_tips'] = get_nutrition_tips(body_type)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return {
            'strengths': ['Unable to determine strengths'],
            'focus_areas': ['Unable to determine focus areas'],
            'exercise_recommendations': ['Basic full-body training recommended'],
            'training_split': get_default_training_split(experience_level),
            'nutrition_tips': ['Maintain balanced nutrition with adequate protein']
        }

def get_strength_for_trait(trait, rating):
    """Get strength description for a highly-rated trait"""
    strengths = {
        'shoulder_width': {
            'excellent': "Broad shoulders give you excellent potential for upper body development",
            'good': "Good shoulder width provides a solid foundation for upper body training"
        },
        'shoulder_hip_ratio': {
            'excellent': "Excellent V-taper potential with your shoulder-to-hip ratio",
            'good': "Good proportions between shoulders and hips for aesthetic development"
        },
        'arm_length': {
            'excellent': "Longer arms give you leverage advantage in pulling exercises",
            'good': "Good arm length for balanced performance in pushing and pulling"
        },
        'leg_length': {
            'excellent': "Longer legs give you advantage in running and jumping activities",
            'good': "Good leg proportions for balanced lower body development"
        },
        'arm_torso_ratio': {
            'excellent': "Excellent arm-to-torso ratio for pulling exercises like rows and deadlifts",
            'good': "Good arm-to-torso proportions for balanced upper body development"
        },
        'torso_length': {
            'excellent': "Longer torso provides good core development potential",
            'good': "Good torso length for balanced physique development"
        }
    }
    
    return strengths.get(trait, {}).get(rating)

def get_focus_for_trait(trait, rating):
    """Get focus area description for a lower-rated trait"""
    focus_areas = {
        'shoulder_width': {
            'average': "Focus on shoulder development to enhance upper body width",
            'below_average': "Prioritize shoulder training to improve upper body proportions"
        },
        'shoulder_hip_ratio': {
            'average': "Work on broadening shoulders to enhance V-taper",
            'below_average': "Focus on upper body width development while maintaining lean waist"
        },
        'arm_length': {
            'average': "Standard arm training will work well for your proportions",
            'below_average': "Shorter arms may benefit from greater focus on arm isolation work"
        },
        'leg_length': {
            'average': "Standard leg training will be effective for your proportions",
            'below_average': "Focus on quad development to enhance leg appearance"
        },
        'arm_torso_ratio': {
            'average': "Balanced approach to arm and torso training recommended",
            'below_average': "Focus more on arm development to balance proportions"
        },
        'torso_length': {
            'average': "Standard torso training will be effective",
            'below_average': "Focus on creating illusion of length through lats and shoulders"
        }
    }
    
    return focus_areas.get(trait, {}).get(rating)

def get_exercises_by_body_type(body_type, traits, experience_level):
    """Get recommended exercises based on body type and traits"""
    exercises = []
    
    # Base recommendations on body type
    if body_type == "Mesomorph-Ectomorph":
        exercises.extend([
            "Focus on compound movements: squats, deadlifts, bench press, pull-ups",
            "Include both strength and hypertrophy training for balanced development",
            "Ensure adequate recovery due to your tendency to overtrain"
        ])
    elif body_type == "Mesomorph":
        exercises.extend([
            "Emphasize progressive overload in strength training",
            "Use a mix of compound and isolation exercises",
            "Moderate cardio (2-3 sessions per week) to maintain conditioning"
        ])
    elif body_type == "Endomorph":
        exercises.extend([
            "Higher rep ranges (10-15) to increase muscular endurance",
            "More frequent cardio sessions (3-4 per week) for metabolic boost",
            "Focus on full-body workouts for maximum calorie burn"
        ])
    elif body_type == "Ectomorph":
        exercises.extend([
            "Emphasize heavy compound lifts with lower rep ranges (4-8)",
            "Limit cardio to maintain caloric surplus",
            "Longer rest periods between sets (2-3 minutes)"
        ])
    else:  # Hybrid or unknown
        exercises.extend([
            "Balanced approach to strength and hypertrophy training",
            "Regular evaluation to determine which training styles work best",
            "Mix of compound and isolation exercises"
        ])
    
    # Add specific recommendations based on traits
    shoulder_width = traits.get('shoulder_width', {}).get('rating')
    if shoulder_width == 'below_average':
        exercises.append("Prioritize lateral raises, overhead presses, and upright rows for shoulder width")
    
    arm_length = traits.get('arm_length', {}).get('rating')
    if arm_length == 'excellent':
        exercises.append("Leverage your arm length with exercises like deadlifts and rows")
    elif arm_length == 'below_average':
        exercises.append("Focus on bench press and pushing movements where shorter arms are advantageous")
    
    # Add experience-specific advice
    if experience_level == 'beginner':
        exercises.append("Start with learning proper form on basic movements before adding weight")
        exercises.append("Begin with full-body workouts 3 times per week")
    elif experience_level == 'intermediate':
        exercises.append("Consider an upper/lower or push/pull/legs split for more focused training")
        exercises.append("Incorporate periodization to continue progression")
    elif experience_level == 'advanced':
        exercises.append("Implement specialized techniques like drop sets, supersets, and rest-pause training")
        exercises.append("Consider body part specialization phases to address lagging areas")
    
    return exercises

def get_training_split(body_type, experience_level):
    """Get recommended training split based on body type and experience"""
    if experience_level == 'beginner':
        return {
            'Monday': 'Full Body',
            'Tuesday': 'Rest/Light Cardio',
            'Wednesday': 'Full Body',
            'Thursday': 'Rest/Light Cardio',
            'Friday': 'Full Body',
            'Saturday': 'Active Recovery',
            'Sunday': 'Rest'
        }
    
    if experience_level == 'intermediate':
        if body_type in ["Mesomorph", "Mesomorph-Ectomorph"]:
            return {
                'Monday': 'Push (Chest, Shoulders, Triceps)',
                'Tuesday': 'Pull (Back, Biceps)',
                'Wednesday': 'Legs & Core',
                'Thursday': 'Rest/Light Cardio',
                'Friday': 'Push (Chest, Shoulders, Triceps)',
                'Saturday': 'Pull (Back, Biceps)',
                'Sunday': 'Rest'
            }
        elif body_type == "Endomorph":
            return {
                'Monday': 'Upper Body + HIIT',
                'Tuesday': 'Lower Body + Steady Cardio',
                'Wednesday': 'Rest/Light Activity',
                'Thursday': 'Full Body Circuit',
                'Friday': 'Upper Body + HIIT',
                'Saturday': 'Lower Body + Steady Cardio',
                'Sunday': 'Rest'
            }
        elif body_type == "Ectomorph":
            return {
                'Monday': 'Upper Body (Heavy)',
                'Tuesday': 'Lower Body (Heavy)',
                'Wednesday': 'Rest',
                'Thursday': 'Push (Moderate Volume)',
                'Friday': 'Pull (Moderate Volume)',
                'Saturday': 'Legs (Moderate Volume)',
                'Sunday': 'Rest'
            }
        else:
            return {
                'Monday': 'Upper Body',
                'Tuesday': 'Lower Body',
                'Wednesday': 'Rest/Light Activity',
                'Thursday': 'Upper Body',
                'Friday': 'Lower Body',
                'Saturday': 'Active Recovery',
                'Sunday': 'Rest'
            }
    
    if experience_level == 'advanced':
        if body_type in ["Mesomorph", "Mesomorph-Ectomorph"]:
            return {
                'Monday': 'Chest & Triceps',
                'Tuesday': 'Back & Biceps',
                'Wednesday': 'Legs',
                'Thursday': 'Shoulders & Abs',
                'Friday': 'Arms & Weakpoints',
                'Saturday': 'Active Recovery',
                'Sunday': 'Rest'
            }
        elif body_type == "Endomorph":
            return {
                'Monday AM': 'Push + Cardio',
                'Monday PM': 'Cardio',
                'Tuesday': 'Pull + HIIT',
                'Wednesday': 'Legs + Steady Cardio',
                'Thursday': 'Rest/Light Activity',
                'Friday': 'Full Body Circuit',
                'Saturday': 'Weakpoints + HIIT',
                'Sunday': 'Rest'
            }
        elif body_type == "Ectomorph":
            return {
                'Monday': 'Chest & Back (Heavy)',
                'Tuesday': 'Legs & Abs (Heavy)',
                'Wednesday': 'Shoulders & Arms (Moderate)',
                'Thursday': 'Rest',
                'Friday': 'Upper Body (Volume)',
                'Saturday': 'Lower Body (Volume)',
                'Sunday': 'Rest'
            }
        else:
            return {
                'Monday': 'Push',
                'Tuesday': 'Pull',
                'Wednesday': 'Legs',
                'Thursday': 'Rest',
                'Friday': 'Upper Body',
                'Saturday': 'Lower Body',
                'Sunday': 'Rest'
            }
    
    # Default fallback
    return get_default_training_split(experience_level)

def get_default_training_split(experience_level):
    """Get default training split based on experience level"""
    if experience_level == 'beginner':
        return {
            'Monday': 'Full Body',
            'Tuesday': 'Rest/Light Cardio',
            'Wednesday': 'Full Body',
            'Thursday': 'Rest/Light Cardio',
            'Friday': 'Full Body',
            'Saturday': 'Active Recovery',
            'Sunday': 'Rest'
        }
    elif experience_level == 'intermediate':
        return {
            'Monday': 'Upper Body',
            'Tuesday': 'Lower Body',
            'Wednesday': 'Rest/Light Activity',
            'Thursday': 'Upper Body',
            'Friday': 'Lower Body',
            'Saturday': 'Active Recovery',
            'Sunday': 'Rest'
        }
    else:  # advanced
        return {
            'Monday': 'Push (Chest, Shoulders, Triceps)',
            'Tuesday': 'Pull (Back, Biceps)',
            'Wednesday': 'Legs',
            'Thursday': 'Rest',
            'Friday': 'Push (Chest, Shoulders, Triceps)',
            'Saturday': 'Pull (Back, Biceps)',
            'Sunday': 'Legs'
        }

def get_nutrition_tips(body_type):
    """Get nutrition tips based on body type"""
    general_tips = [
        "Aim for 1.6-2.2g of protein per kg of bodyweight daily",
        "Stay hydrated with at least 3-4 liters of water daily",
        "Time protein intake within 2 hours after training"
    ]
    
    specific_tips = {
        "Mesomorph-Ectomorph": [
            "Consume 5-6 moderate-sized meals daily",
            "Slight caloric surplus (+200-300 calories) for muscle gain",
            "Moderate carbohydrate intake (40-50% of calories)"
        ],
        "Mesomorph": [
            "Balanced macronutrient profile (40% carbs, 30% protein, 30% fat)",
            "Adjust calories based on specific goals (maintenance, cutting, bulking)",
            "Carb timing around workouts for optimal performance"
        ],
        "Endomorph": [
            "Focus on protein and fiber-rich foods",
            "Limit simple carbohydrates and focus on complex carbs",
            "Consider carb cycling (higher on training days, lower on rest days)",
            "Slight caloric deficit (-300-500 calories) if fat loss is a goal"
        ],
        "Ectomorph": [
            "Consistent caloric surplus (+300-500 calories)",
            "Higher carbohydrate intake (50-60% of calories)",
            "Frequent meals (6-7 per day) to increase total caloric intake",
            "Liquid calories can help reach caloric goals"
        ],
        "Hybrid": [
            "Balanced macronutrient approach (40% carbs, 30% protein, 30% fat)",
            "Monitor body's response to different nutritional approaches",
            "Adjust meal frequency and timing based on energy levels and hunger"
        ]
    }
    
    tips = general_tips + specific_tips.get(body_type, specific_tips["Hybrid"])
    return tips
