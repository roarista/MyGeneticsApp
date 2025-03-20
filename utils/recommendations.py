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
            'nutrition_tips': [],
            'calorie_recommendations': {},
            'workout_plan': {}
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
        
        # Determine appropriate goal based on body composition
        goal = 'maintain'  # Default goal
        activity_level = 'moderate'  # Default activity level
        
        # Extract height, weight and body fat if available
        height_cm = 0
        weight_kg = 0
        body_fat = 0
        
        if 'height_cm' in traits:
            height_cm = traits['height_cm']
        
        if 'weight_kg' in traits:
            weight_kg = traits['weight_kg']
        
        if 'body_fat_percentage' in traits and isinstance(traits['body_fat_percentage'], dict):
            body_fat = traits['body_fat_percentage']['value']
            body_fat_rating = traits['body_fat_percentage']['rating']
            
            # Add body fat specific recommendations
            if body_fat_rating == 'excellent':
                recommendations['strengths'].append(f"Body fat percentage of {body_fat}% is ideal for muscle definition and performance")
            elif body_fat_rating == 'good':
                recommendations['strengths'].append(f"Body fat percentage of {body_fat}% is good for overall health and aesthetics")
            elif body_fat_rating == 'average':
                recommendations['focus_areas'].append(f"Consider a slight caloric deficit to reduce body fat percentage from {body_fat}%")
                goal = 'lose_fat'  # Set goal based on body fat
            elif body_fat_rating == 'below_average':
                if body_fat < 10:  # Too low
                    recommendations['focus_areas'].append(f"Body fat at {body_fat}% may be too low; consider increasing calories for health")
                    goal = 'gain_muscle'
                else:  # Too high
                    recommendations['focus_areas'].append(f"Focus on reducing body fat from {body_fat}% through diet and cardio")
                    goal = 'lose_fat'
        
        # Add BMI recommendations if available
        if 'bmi' in traits and isinstance(traits['bmi'], dict):
            bmi = traits['bmi']['value']
            bmi_rating = traits['bmi']['rating']
            
            if bmi_rating == 'excellent':
                recommendations['strengths'].append(f"BMI of {bmi} is in the optimal range for health and performance")
            elif bmi_rating == 'below_average' and bmi < 18.5:
                recommendations['focus_areas'].append(f"BMI of {bmi} is underweight; focus on increasing caloric intake and muscle building")
                goal = 'gain_muscle'
            elif bmi_rating == 'below_average' and bmi > 30:
                recommendations['focus_areas'].append(f"BMI of {bmi} indicates higher body fat; prioritize fat loss for health improvement")
                goal = 'lose_fat'
        
        # Add muscle potential recommendations if available
        if 'muscle_potential' in traits and isinstance(traits['muscle_potential'], dict):
            potential = traits['muscle_potential']['value']
            potential_rating = traits['muscle_potential']['rating']
            
            if potential_rating in ['excellent', 'good']:
                recommendations['strengths'].append(f"High genetic potential for muscle gain; focus on progressive overload")
            elif potential_rating in ['average', 'below_average']:
                recommendations['focus_areas'].append(f"Focus on technique optimization to maximize your genetic muscle building potential")
        
        # Generate specific workout plans based on body traits and identified weaknesses
        recommendations['workout_plan'] = generate_detailed_workout_plan(
            body_type,
            experience_level,
            traits,
            goal
        )
        
        # Calculate calorie recommendations if we have the required metrics
        if height_cm > 0 and weight_kg > 0 and body_fat > 0:
            # Based on training frequency, estimate activity level
            if experience_level == 'beginner':
                activity_level = 'light'
            elif experience_level == 'intermediate':
                activity_level = 'moderate'
            else:
                activity_level = 'very_active'
                
            # Calculate calorie recommendations
            recommendations['calorie_recommendations'] = calculate_calorie_recommendations(
                weight_kg,
                height_cm,
                body_fat,
                activity_level,
                goal
            )
            
            # Add specific nutrition advice based on calorie calculations
            if goal == 'lose_fat':
                calories = recommendations['calorie_recommendations']['target']
                protein = recommendations['calorie_recommendations']['protein_g']
                recommendations['nutrition_tips'].append(f"Aim for {calories} calories per day with at least {protein}g of protein to preserve muscle")
                recommendations['nutrition_tips'].append("Focus on high-volume, low-calorie foods like vegetables and lean proteins to stay full")
            elif goal == 'gain_muscle':
                calories = recommendations['calorie_recommendations']['target']
                protein = recommendations['calorie_recommendations']['protein_g']
                carbs = recommendations['calorie_recommendations']['carbs_g']
                recommendations['nutrition_tips'].append(f"Consume {calories} calories daily with {protein}g protein and {carbs}g carbs to support growth")
                recommendations['nutrition_tips'].append("Prioritize post-workout nutrition with protein and fast-digesting carbs")
            elif goal == 'recomp':
                train_cals = recommendations['calorie_recommendations']['training_day']
                rest_cals = recommendations['calorie_recommendations']['rest_day']
                protein = recommendations['calorie_recommendations']['protein_g']
                recommendations['nutrition_tips'].append(f"Training days: {train_cals} calories; Rest days: {rest_cals} calories; Protein: {protein}g daily")
                recommendations['nutrition_tips'].append("Time your carbohydrate intake around training for optimal performance and recovery")
        
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
    """Get recommended training split based on body type and experience - Always Push/Pull/Legs"""
    # Always use a Push/Pull/Legs split, but customize based on body type and experience
    
    # Base template for all users is Push/Pull/Legs
    if body_type == "Endomorph":
        # Higher frequency and more metabolic work for endomorphs
        return {
            'Monday': 'Push (Chest, Shoulders, Triceps) + HIIT',
            'Tuesday': 'Pull (Back, Biceps) + HIIT',
            'Wednesday': 'Legs (Quads, Hamstrings, Calves) + HIIT',
            'Thursday': 'Rest/Light Cardio',
            'Friday': 'Push (Chest, Shoulders, Triceps) + HIIT',
            'Saturday': 'Pull (Back, Biceps) + HIIT',
            'Sunday': 'Legs (Quads, Hamstrings, Calves) + HIIT'
        }
    elif body_type == "Ectomorph":
        # Lower training frequency with more recovery for ectomorphs
        if experience_level == 'beginner':
            return {
                'Monday': 'Push (Chest, Shoulders, Triceps)',
                'Tuesday': 'Pull (Back, Biceps)',
                'Wednesday': 'Legs (Quads, Hamstrings, Calves)',
                'Thursday': 'Rest',
                'Friday': 'Push (Chest, Shoulders, Triceps)',
                'Saturday': 'Pull (Back, Biceps)',
                'Sunday': 'Rest'
            }
        else:
            return {
                'Monday': 'Push (Chest, Shoulders, Triceps) - Heavy',
                'Tuesday': 'Pull (Back, Biceps) - Heavy',
                'Wednesday': 'Legs (Quads, Hamstrings, Calves) - Heavy',
                'Thursday': 'Rest',
                'Friday': 'Push (Chest, Shoulders, Triceps) - Volume',
                'Saturday': 'Pull (Back, Biceps) - Volume',
                'Sunday': 'Legs (Quads, Hamstrings, Calves) - Volume'
            }
    elif body_type in ["Mesomorph", "Mesomorph-Ectomorph"]:
        # Balanced approach with intensity techniques for mesomorphs
        if experience_level == 'beginner':
            return {
                'Monday': 'Push (Chest, Shoulders, Triceps)',
                'Tuesday': 'Pull (Back, Biceps)',
                'Wednesday': 'Legs (Quads, Hamstrings, Calves)',
                'Thursday': 'Rest/Light Cardio',
                'Friday': 'Push (Chest, Shoulders, Triceps)',
                'Saturday': 'Pull (Back, Biceps)',
                'Sunday': 'Rest'
            }
        else:
            return {
                'Monday': 'Push (Chest, Shoulders, Triceps) - Strength',
                'Tuesday': 'Pull (Back, Biceps) - Strength',
                'Wednesday': 'Legs (Quads, Hamstrings, Calves) - Strength',
                'Thursday': 'Rest/Light Cardio',
                'Friday': 'Push (Chest, Shoulders, Triceps) - Hypertrophy',
                'Saturday': 'Pull (Back, Biceps) - Hypertrophy',
                'Sunday': 'Legs (Quads, Hamstrings, Calves) - Hypertrophy'
            }
    else:  # Hybrid or unknown
        # Standard Push/Pull/Legs for hybrid body types
        return {
            'Monday': 'Push (Chest, Shoulders, Triceps)',
            'Tuesday': 'Pull (Back, Biceps)',
            'Wednesday': 'Legs (Quads, Hamstrings, Calves)',
            'Thursday': 'Rest',
            'Friday': 'Push (Chest, Shoulders, Triceps)',
            'Saturday': 'Pull (Back, Biceps)',
            'Sunday': 'Legs (Quads, Hamstrings, Calves)'
        }

def get_default_training_split(experience_level):
    """Get default training split based on experience level - Always Push/Pull/Legs"""
    if experience_level == 'beginner':
        # For beginners, use a simplified Push/Pull/Legs with fewer days
        return {
            'Monday': 'Push (Chest, Shoulders, Triceps)',
            'Tuesday': 'Pull (Back, Biceps)',
            'Wednesday': 'Legs (Quads, Hamstrings, Calves)',
            'Thursday': 'Rest/Light Cardio',
            'Friday': 'Push (Chest, Shoulders, Triceps)',
            'Saturday': 'Pull (Back, Biceps)',
            'Sunday': 'Rest'
        }
    elif experience_level == 'intermediate':
        # Standard Push/Pull/Legs for intermediate lifters
        return {
            'Monday': 'Push (Chest, Shoulders, Triceps)',
            'Tuesday': 'Pull (Back, Biceps)',
            'Wednesday': 'Legs (Quads, Hamstrings, Calves)',
            'Thursday': 'Rest/Light Cardio',
            'Friday': 'Push (Chest, Shoulders, Triceps)',
            'Saturday': 'Pull (Back, Biceps)',
            'Sunday': 'Legs (Quads, Hamstrings, Calves)'
        }
    else:  # advanced
        # More intense Push/Pull/Legs with specialization for advanced lifters
        return {
            'Monday': 'Push (Chest, Shoulders, Triceps) - Strength',
            'Tuesday': 'Pull (Back, Biceps) - Strength',
            'Wednesday': 'Legs (Quads, Hamstrings, Calves) - Strength',
            'Thursday': 'Rest',
            'Friday': 'Push (Chest, Shoulders, Triceps) - Hypertrophy',
            'Saturday': 'Pull (Back, Biceps) - Hypertrophy',
            'Sunday': 'Legs (Quads, Hamstrings, Calves) - Hypertrophy'
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
    
def generate_detailed_workout_plan(body_type, experience_level, traits, goal):
    """
    Generate detailed workout plans with specific exercises based on 
    body type, experience, traits, and goals
    
    Args:
        body_type: Body type classification
        experience_level: User's fitness experience level
        traits: Dictionary of body traits from analysis
        goal: Training goal (lose_fat, gain_muscle, maintain, recomp)
        
    Returns:
        Dictionary with detailed workout plan
    """
    workout_plan = {}
    
    # Base exercises for each body part
    base_exercises = {
        'chest': [
            {'name': 'Bench Press', 'target': 'overall chest development', 'sets': 3, 'reps': '8-10'},
            {'name': 'Incline Dumbbell Press', 'target': 'upper chest', 'sets': 3, 'reps': '8-10'},
            {'name': 'Chest Flyes', 'target': 'chest stretching and isolation', 'sets': 3, 'reps': '10-12'},
            {'name': 'Push-ups', 'target': 'overall chest and core stability', 'sets': 3, 'reps': '10-15'}
        ],
        'back': [
            {'name': 'Pull-ups/Lat Pulldowns', 'target': 'latissimus dorsi', 'sets': 3, 'reps': '8-10'},
            {'name': 'Bent-over Rows', 'target': 'middle back', 'sets': 3, 'reps': '8-10'},
            {'name': 'Seated Cable Rows', 'target': 'overall back development', 'sets': 3, 'reps': '10-12'},
            {'name': 'Face Pulls', 'target': 'rear deltoids and upper back', 'sets': 3, 'reps': '12-15'}
        ],
        'shoulders': [
            {'name': 'Overhead Press', 'target': 'overall shoulder development', 'sets': 3, 'reps': '8-10'},
            {'name': 'Lateral Raises', 'target': 'lateral deltoids', 'sets': 3, 'reps': '10-15'},
            {'name': 'Front Raises', 'target': 'anterior deltoids', 'sets': 3, 'reps': '10-12'},
            {'name': 'Reverse Flyes', 'target': 'posterior deltoids', 'sets': 3, 'reps': '10-15'}
        ],
        'arms': [
            {'name': 'Barbell Curls', 'target': 'biceps', 'sets': 3, 'reps': '8-12'},
            {'name': 'Tricep Dips', 'target': 'triceps', 'sets': 3, 'reps': '8-12'},
            {'name': 'Hammer Curls', 'target': 'brachialis and forearms', 'sets': 3, 'reps': '10-12'},
            {'name': 'Tricep Pushdowns', 'target': 'triceps', 'sets': 3, 'reps': '10-12'}
        ],
        'legs': [
            {'name': 'Squats', 'target': 'quadriceps and overall leg development', 'sets': 3, 'reps': '8-10'},
            {'name': 'Romanian Deadlifts', 'target': 'hamstrings and glutes', 'sets': 3, 'reps': '8-10'},
            {'name': 'Leg Press', 'target': 'quadriceps', 'sets': 3, 'reps': '10-12'},
            {'name': 'Calf Raises', 'target': 'calf muscles', 'sets': 3, 'reps': '12-15'}
        ],
        'core': [
            {'name': 'Planks', 'target': 'core stability', 'sets': 3, 'reps': '30-60 seconds'},
            {'name': 'Russian Twists', 'target': 'obliques', 'sets': 3, 'reps': '10-15 per side'},
            {'name': 'Hanging Leg Raises', 'target': 'lower abs', 'sets': 3, 'reps': '10-15'},
            {'name': 'Ab Wheel Rollouts', 'target': 'entire core', 'sets': 3, 'reps': '8-12'}
        ]
    }
    
    # Adjust training parameters based on goal
    if goal == 'lose_fat':
        rep_range = '12-15'
        rest_time = '30-45 seconds'
        workout_structure = 'circuit-style with supersets'
    elif goal == 'gain_muscle':
        rep_range = '6-10'
        rest_time = '90-120 seconds'
        workout_structure = 'traditional sets with progressive overload'
    else:  # maintain or recomp
        rep_range = '8-12'
        rest_time = '60-90 seconds'
        workout_structure = 'balanced approach with varied intensity'
    
    # Identify weak areas from traits and create a more detailed weakness dictionary
    weak_areas = []
    weakness_details = {}
    
    for trait, data in traits.items():
        if not isinstance(data, dict):
            continue
            
        rating = data.get('rating')
        if rating == 'below_average' or rating == 'poor':
            if 'shoulder' in trait:
                weak_areas.append('shoulders')
                weakness_details['shoulders'] = {
                    'severity': 2 if rating == 'poor' else 1,
                    'trait': trait,
                    'description': data.get('description', 'Underdeveloped shoulder area')
                }
            elif 'arm' in trait:
                weak_areas.append('arms')
                weakness_details['arms'] = {
                    'severity': 2 if rating == 'poor' else 1,
                    'trait': trait,
                    'description': data.get('description', 'Underdeveloped arm area')
                }
            elif 'leg' in trait:
                weak_areas.append('legs')
                weakness_details['legs'] = {
                    'severity': 2 if rating == 'poor' else 1,
                    'trait': trait,
                    'description': data.get('description', 'Underdeveloped leg area')
                }
            elif 'torso' in trait or 'chest' in trait:
                weak_areas.append('chest')
                weakness_details['chest'] = {
                    'severity': 2 if rating == 'poor' else 1,
                    'trait': trait,
                    'description': data.get('description', 'Underdeveloped chest/torso area')
                }
            elif 'back' in trait:
                weak_areas.append('back')
                weakness_details['back'] = {
                    'severity': 2 if rating == 'poor' else 1,
                    'trait': trait,
                    'description': data.get('description', 'Underdeveloped back area')
                }
            elif 'core' in trait or 'waist' in trait:
                weak_areas.append('core')
                weakness_details['core'] = {
                    'severity': 2 if rating == 'poor' else 1,
                    'trait': trait,
                    'description': data.get('description', 'Underdeveloped core area')
                }
                
    # Create specific training focus based on body type
    if body_type == "Ectomorph":
        # Focus on muscle building with compound movements
        workout_plan['training_focus'] = "Muscle building with compound lifts and higher calories"
        workout_plan['rep_ranges'] = "Lower rep ranges (6-8) with heavier weights"
        workout_plan['rest_periods'] = "Longer rest periods (2-3 minutes)"
        workout_plan['frequency'] = "3-4 workouts per week"
        workout_plan['cardio'] = "Minimal cardio (1-2 sessions of 20-30 min LISS)"
        
    elif body_type == "Endomorph":
        # Focus on fat loss with higher volume
        workout_plan['training_focus'] = "Fat loss with higher volume and metabolic conditioning"
        workout_plan['rep_ranges'] = "Higher rep ranges (12-15) with moderate weights"
        workout_plan['rest_periods'] = "Shorter rest periods (30-60 seconds)"
        workout_plan['frequency'] = "4-5 workouts per week"
        workout_plan['cardio'] = "Regular cardio (3-4 sessions with mix of HIIT and LISS)"
        
    elif body_type in ["Mesomorph", "Mesomorph-Ectomorph"]:
        # Balanced approach
        workout_plan['training_focus'] = "Balanced muscle development with strength training"
        workout_plan['rep_ranges'] = "Mixed rep ranges (6-12)"
        workout_plan['rest_periods'] = "Moderate rest periods (60-90 seconds)"
        workout_plan['frequency'] = "4-5 workouts per week"
        workout_plan['cardio'] = "Moderate cardio (2-3 sessions, mix of HIIT and LISS)"
    
    else:  # Hybrid or unknown
        workout_plan['training_focus'] = "Balanced development with focus on consistency"
        workout_plan['rep_ranges'] = "Standard rep ranges (8-12)"
        workout_plan['rest_periods'] = "60-90 seconds between sets"
        workout_plan['frequency'] = "3-4 workouts per week"
        workout_plan['cardio'] = "2-3 sessions of cardio (mix of intensities)"
    
    # Create the split based on experience level
    if experience_level == "beginner":
        # Create Push/Pull/Legs for beginners but with simplified exercises and form focus
        workout_plan['split_type'] = "Push/Pull/Legs for Beginners"
        
        # Push day for beginners
        workout_plan['push_day'] = {
            'name': 'Push (Chest, Shoulders, Triceps)',
            'focus': 'Upper body pushing muscles with emphasis on form',
            'exercises': [
                {'name': 'Push-ups', 'target': 'chest and triceps', 'sets': 3, 'reps': '8-12'},
                {'name': 'Dumbbell Bench Press', 'target': 'chest and stability', 'sets': 3, 'reps': '8-10'},
                {'name': 'Seated Dumbbell Shoulder Press', 'target': 'shoulders', 'sets': 3, 'reps': '8-10'},
                {'name': 'Lateral Raises', 'target': 'side deltoids', 'sets': 2, 'reps': '10-12'},
                {'name': 'Tricep Dumbbell Extensions', 'target': 'triceps', 'sets': 2, 'reps': '10-12'}
            ],
            'beginner_tips': [
                'Focus on proper form rather than weight',
                'Ensure full range of motion on all exercises',
                'Rest 90-120 seconds between sets'
            ]
        }
        
        # Pull day for beginners
        workout_plan['pull_day'] = {
            'name': 'Pull (Back, Biceps)',
            'focus': 'Upper body pulling muscles with emphasis on mind-muscle connection',
            'exercises': [
                {'name': 'Assisted Pull-ups or Lat Pulldowns', 'target': 'back width', 'sets': 3, 'reps': '8-10'},
                {'name': 'Seated Cable Rows', 'target': 'back thickness', 'sets': 3, 'reps': '10-12'},
                {'name': 'Single-Arm Dumbbell Rows', 'target': 'lats and mid-back', 'sets': 3, 'reps': '10-12 per arm'},
                {'name': 'Face Pulls', 'target': 'rear deltoids and posture', 'sets': 2, 'reps': '12-15'},
                {'name': 'Dumbbell Bicep Curls', 'target': 'biceps', 'sets': 2, 'reps': '10-12'}
            ],
            'beginner_tips': [
                'Focus on squeezing your back muscles, not just pulling with arms',
                'Keep your shoulders down and back',
                'Avoid momentum and swinging'
            ]
        }
        
        # Legs day for beginners
        workout_plan['legs_day'] = {
            'name': 'Legs (Quads, Hamstrings, Calves)',
            'focus': 'Lower body development with focus on balance and stability',
            'exercises': [
                {'name': 'Goblet Squats', 'target': 'quads and core stability', 'sets': 3, 'reps': '10-12'},
                {'name': 'Dumbbell Romanian Deadlifts', 'target': 'hamstrings and glutes', 'sets': 3, 'reps': '10-12'},
                {'name': 'Walking Lunges', 'target': 'quads, glutes, and balance', 'sets': 2, 'reps': '10 steps each leg'},
                {'name': 'Leg Press (Light Weight)', 'target': 'overall leg development', 'sets': 3, 'reps': '12-15'},
                {'name': 'Standing Calf Raises', 'target': 'calves', 'sets': 3, 'reps': '15-20'},
                {'name': 'Planks', 'target': 'core stability', 'sets': 3, 'reps': '30-45 seconds'}
            ],
            'beginner_tips': [
                'Start with bodyweight or light weight to master form',
                'Focus on control during both concentric and eccentric phases',
                'Keep your knees in line with your toes during squats and lunges'
            ]
        }
        
    elif experience_level == "intermediate":
        # Create upper/lower or push/pull/legs split
        workout_plan['split_type'] = "Push/Pull/Legs"
        
        # Push day
        workout_plan['push_day'] = {
            'name': 'Push (Chest, Shoulders, Triceps)',
            'focus': 'Upper body pushing muscles',
            'exercises': [
                base_exercises['chest'][0],  # Bench Press
                base_exercises['chest'][1],  # Incline Dumbbell Press
                base_exercises['shoulders'][0],  # Overhead Press
                base_exercises['shoulders'][1],  # Lateral Raises
                base_exercises['arms'][3]    # Tricep Pushdowns
            ]
        }
        
        # Pull day
        workout_plan['pull_day'] = {
            'name': 'Pull (Back, Biceps)',
            'focus': 'Upper body pulling muscles',
            'exercises': [
                base_exercises['back'][0],   # Pull-ups/Lat Pulldowns
                base_exercises['back'][1],   # Bent-over Rows
                base_exercises['back'][3],   # Face Pulls
                base_exercises['arms'][0],   # Barbell Curls
                base_exercises['arms'][2]    # Hammer Curls
            ]
        }
        
        # Legs day
        workout_plan['legs_day'] = {
            'name': 'Legs & Core',
            'focus': 'Lower body development',
            'exercises': [
                base_exercises['legs'][0],   # Squats
                base_exercises['legs'][1],   # Romanian Deadlifts
                base_exercises['legs'][2],   # Leg Press
                base_exercises['legs'][3],   # Calf Raises
                base_exercises['core'][0],   # Planks
                base_exercises['core'][1]    # Russian Twists
            ]
        }
        
    else:  # advanced
        # Create more specialized split
        workout_plan['split_type'] = "Advanced Push/Pull/Legs with specialization"
        
        # Add more advanced exercises and techniques
        # Push day
        workout_plan['push_day'] = {
            'name': 'Push (Chest, Shoulders, Triceps)',
            'focus': 'Upper body pushing muscles with intensity techniques',
            'exercises': [
                base_exercises['chest'][0],  # Bench Press
                {'name': 'Incline Bench Press', 'target': 'upper chest', 'sets': '4', 'reps': '6-8'},
                {'name': 'Dumbbell Flyes', 'target': 'chest stretching', 'sets': '3', 'reps': '10-12'},
                {'name': 'Arnold Press', 'target': 'shoulders with rotation', 'sets': '3', 'reps': '8-10'},
                base_exercises['shoulders'][1],  # Lateral Raises
                {'name': 'Skull Crushers', 'target': 'triceps long head', 'sets': '3', 'reps': '8-10'},
                base_exercises['arms'][3]    # Tricep Pushdowns
            ],
            'advanced_techniques': [
                'Drop sets on final set of lateral raises',
                'Rest-pause on bench press',
                'Superset tricep exercises'
            ]
        }
        
        # Pull day
        workout_plan['pull_day'] = {
            'name': 'Pull (Back, Biceps)',
            'focus': 'Upper body pulling muscles with mind-muscle connection',
            'exercises': [
                {'name': 'Deadlifts', 'target': 'overall back and posterior chain', 'sets': '4', 'reps': '5-6'},
                base_exercises['back'][0],   # Pull-ups/Lat Pulldowns
                {'name': 'Meadows Rows', 'target': 'lats and mid-back', 'sets': '3', 'reps': '8-10'},
                base_exercises['back'][3],   # Face Pulls
                {'name': 'Incline Dumbbell Curls', 'target': 'biceps peak', 'sets': '3', 'reps': '8-10'},
                base_exercises['arms'][2],   # Hammer Curls
                {'name': 'Cable Curls', 'target': 'continuous tension on biceps', 'sets': '3', 'reps': '12-15'}
            ],
            'advanced_techniques': [
                'Eccentric emphasis on pull-ups',
                'Heavy/light supersets for biceps',
                'Mechanical drop sets on rows'
            ]
        }
        
        # Legs day
        workout_plan['legs_day'] = {
            'name': 'Legs & Core',
            'focus': 'Complete lower body development with progressive overload',
            'exercises': [
                {'name': 'Back Squats', 'target': 'quadriceps and overall development', 'sets': '4', 'reps': '6-8'},
                {'name': 'Bulgarian Split Squats', 'target': 'unilateral leg development', 'sets': '3', 'reps': '8-10 per leg'},
                base_exercises['legs'][1],   # Romanian Deadlifts
                {'name': 'Leg Extensions', 'target': 'quadriceps isolation', 'sets': '3', 'reps': '12-15'},
                {'name': 'Seated Leg Curl', 'target': 'hamstrings isolation', 'sets': '3', 'reps': '12-15'},
                {'name': 'Standing Calf Raises', 'target': 'gastrocnemius', 'sets': '4', 'reps': '12-15'},
                {'name': 'Seated Calf Raises', 'target': 'soleus', 'sets': '3', 'reps': '15-20'},
                {'name': 'Cable Crunches', 'target': 'rectus abdominis', 'sets': '3', 'reps': '12-15'}
            ],
            'advanced_techniques': [
                'Tempo squats (3-1-1 cadence)',
                'Supersets for opposing muscle groups',
                'Giant sets for calves'
            ]
        }
    
    # Add weak area specialization
    workout_plan['weak_area_focus'] = {}
    for area in weak_areas:
        if area == 'shoulders':
            workout_plan['weak_area_focus']['shoulders'] = {
                'priority': 'High',
                'volume': 'Increase sets by 50% for shoulder exercises',
                'frequency': 'Train shoulders 2-3 times per week',
                'key_exercises': [
                    {'name': 'Lateral Raises', 'target': 'side deltoid width', 'sets': '4', 'reps': '12-15'},
                    {'name': 'Face Pulls', 'target': 'rear deltoids and posture', 'sets': '3', 'reps': '15-20'},
                    {'name': 'Upright Rows', 'target': 'trap and deltoid development', 'sets': '3', 'reps': '10-12'}
                ]
            }
        elif area == 'arms':
            workout_plan['weak_area_focus']['arms'] = {
                'priority': 'High',
                'volume': 'Add dedicated arm day or increase arm volume by 30-50%',
                'frequency': 'Train arms 2-3 times per week',
                'key_exercises': [
                    {'name': 'EZ Bar Curls', 'target': 'overall biceps development', 'sets': '4', 'reps': '8-12'},
                    {'name': 'Incline Dumbbell Curls', 'target': 'biceps stretch', 'sets': '3', 'reps': '10-12'},
                    {'name': 'Close-Grip Bench Press', 'target': 'triceps with compound movement', 'sets': '4', 'reps': '8-10'},
                    {'name': 'Overhead Tricep Extension', 'target': 'long head of triceps', 'sets': '3', 'reps': '10-12'}
                ]
            }
        elif area == 'legs':
            workout_plan['weak_area_focus']['legs'] = {
                'priority': 'High',
                'volume': 'Increase leg volume by 30-50%, split between quad and hamstring focus',
                'frequency': 'Train legs 2 times per week with different focus each day',
                'key_exercises': [
                    {'name': 'Front Squats', 'target': 'quadriceps and core', 'sets': '4', 'reps': '8-10'},
                    {'name': 'Walking Lunges', 'target': 'overall leg development', 'sets': '3', 'reps': '10-12 per leg'},
                    {'name': 'Leg Press (Feet High)', 'target': 'hamstring and glute emphasis', 'sets': '4', 'reps': '10-12'},
                    {'name': 'Glute-Ham Raises', 'target': 'hamstring and glute tie-in', 'sets': '3', 'reps': '8-12'}
                ]
            }
    
    # Add calorie and nutrition info based on goal
    if goal == 'lose_fat':
        workout_plan['nutrition_emphasis'] = 'Caloric deficit with high protein'
    elif goal == 'gain_muscle':
        workout_plan['nutrition_emphasis'] = 'Caloric surplus with emphasis on protein and carbs around workouts'
    else:
        workout_plan['nutrition_emphasis'] = 'Maintenance calories with balanced macros'
    
    return workout_plan

def calculate_calorie_recommendations(weight_kg, height_cm, body_fat, activity_level, goal):
    """
    Calculate calorie recommendations based on body metrics and goals
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        body_fat: Body fat percentage
        activity_level: String describing activity level (sedentary, light, moderate, very_active, extra_active)
        goal: String describing goal (maintain, lose_fat, gain_muscle, recomp)
        
    Returns:
        Dictionary with calorie and macronutrient recommendations
    """
    # Calculate Basal Metabolic Rate (BMR) using Katch-McArdle Formula (uses lean body mass)
    lean_mass = weight_kg * (1 - (body_fat / 100))
    bmr = 370 + (21.6 * lean_mass)
    
    # Apply activity multiplier
    activity_multipliers = {
        'sedentary': 1.2,      # Desk job, little or no exercise
        'light': 1.375,        # Light exercise 1-3 days/week
        'moderate': 1.55,      # Moderate exercise 3-5 days/week
        'very_active': 1.725,  # Heavy exercise 6-7 days/week
        'extra_active': 1.9    # Very heavy exercise, physical job or twice daily training
    }
    
    multiplier = activity_multipliers.get(activity_level, 1.55)  # Default to moderate
    maintenance_calories = bmr * multiplier
    
    # Adjust based on goal
    if goal == 'lose_fat':
        target_calories = maintenance_calories * 0.8  # 20% deficit
        protein_ratio = 0.35  # Higher protein during cutting
        carb_ratio = 0.3
        fat_ratio = 0.35
    elif goal == 'gain_muscle':
        target_calories = maintenance_calories * 1.1  # 10% surplus
        protein_ratio = 0.25
        carb_ratio = 0.5  # Higher carbs for muscle gain
        fat_ratio = 0.25
    elif goal == 'recomp':
        # Body recomposition - training days in slight surplus, rest days in slight deficit
        training_day_calories = maintenance_calories * 1.05
        rest_day_calories = maintenance_calories * 0.9
        target_calories = maintenance_calories  # Average
        protein_ratio = 0.3
        carb_ratio = 0.4
        fat_ratio = 0.3
        return {
            'maintenance': round(maintenance_calories),
            'training_day': round(training_day_calories),
            'rest_day': round(rest_day_calories),
            'protein_g': round(target_calories * protein_ratio / 4),  # 4 calories per gram
            'carbs_g': round(target_calories * carb_ratio / 4),       # 4 calories per gram
            'fat_g': round(target_calories * fat_ratio / 9)           # 9 calories per gram
        }
    else:  # maintain
        target_calories = maintenance_calories
        protein_ratio = 0.3
        carb_ratio = 0.4
        fat_ratio = 0.3
    
    return {
        'maintenance': round(maintenance_calories),
        'target': round(target_calories),
        'protein_g': round(target_calories * protein_ratio / 4),  # 4 calories per gram
        'carbs_g': round(target_calories * carb_ratio / 4),       # 4 calories per gram
        'fat_g': round(target_calories * fat_ratio / 9)           # 9 calories per gram
    }
