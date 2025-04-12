"""
Smart Adaptive Workout Generator based on Body Analysis Results.
This module dynamically creates personalized workout plans based on a user's
muscle development status, body type, and fitness goals.
"""

import json
import random
from datetime import datetime, timedelta

# Exercise mapping based on PPL (Push/Pull/Legs) split
EXERCISE_MAPPING = {
    # Push day exercises
    "Chest": [
        "Bench Press", "Incline DB Press", "Push-Up", "Cable Crossover",
        "Decline Push-Ups", "Pec Deck Fly", "Dips", "Chest Fly"
    ],
    "Shoulders": [
        "Overhead Press", "Lateral Raise", "Arnold Press", "Front Raise",
        "Upright Row", "Pike Push-Up", "DB Shoulder Press", "Machine Shoulder Press"
    ],
    "Triceps": [
        "Skullcrusher", "Dips", "Triceps Pushdown", "Overhead Extension",
        "Diamond Push-Ups", "Triceps Kickback", "Close-Grip Bench Press"
    ],
    
    # Pull day exercises
    "Back": [
        "Pull-Up", "Barbell Row", "Seated Cable Row", "Lat Pulldown",
        "Deadlift", "Chin-Ups", "T-Bar Row", "Single-Arm DB Row"
    ],
    "Biceps": [
        "Bicep Curl", "Incline Curl", "Hammer Curl", "Concentration Curl",
        "Cable Curl", "Preacher Curl", "Chin-Ups"
    ],
    "Rear Delts": [
        "Face Pull", "Reverse Pec Deck Fly", "Bent-Over Reverse Fly",
        "Cable Reverse Fly", "Rear Delt Row", "Seated Rear Delt Fly"
    ],
    
    # Legs day exercises
    "Quads": [
        "Squat", "Leg Press", "Lunges", "Leg Extension",
        "Bulgarian Split Squats", "Hack Squat", "Step-Ups"
    ],
    "Hamstrings": [
        "Romanian Deadlift", "Lying Curl", "Seated Leg Curl",
        "Good Morning", "Stiff-Legged Deadlift", "Nordic Curl"
    ],
    "Glutes": [
        "Hip Thrust", "Glute Kickbacks", "Cable Pull-Through",
        "Bulgarian Split Squats", "Glute Bridge", "Sumo Deadlift"
    ],
    "Calves": [
        "Seated Calf Raise", "Standing Calf Raise", "Calf Press",
        "Donkey Calf Raise", "Single-Leg Calf Raise"
    ],
    
    # For core workouts that can be added to any day
    "Core": [
        "Planks", "Leg Raises", "Russian Twists", "Cable Crunches",
        "Ab Rollout", "Hanging Leg Raise", "Mountain Climbers", "Side Planks"
    ],
    
    # For compatibility with older code that might use "Arms"
    "Arms": [
        "Bicep Curl", "Triceps Pushdown", "Hammer Curl", "Overhead Extension", 
        "Cable Curl", "Skullcrusher", "Concentration Curl", "Diamond Push-Ups"
    ]
}

# Weekly split templates based on training experience
SPLIT_TEMPLATES = {
    "beginner": {
        "3_day": ["Push", "Pull", "Legs", "Rest", "Rest", "Rest", "Legs"],
        "4_day": ["Push", "Pull", "Legs", "Rest", "Push", "Rest", "Legs"],
        "5_day": ["Push", "Pull", "Legs", "Rest", "Push", "Pull", "Legs"]
    },
    "intermediate": {
        "5_day": ["Push", "Pull", "Legs", "Rest", "Push", "Pull", "Legs"],
        "6_day": ["Push", "Pull", "Legs", "Push", "Pull", "Legs", "Legs"]
    },
    "advanced": {
        "6_day": ["Push", "Pull", "Legs", "Push", "Pull", "Legs", "Legs"]
    }
}

# Default set and rep schemes based on muscle development
DEFAULT_SET_REP_SCHEMES = {
    "Needs Growth": {"sets": 4, "reps": "12-15", "rest": "60-90s"},
    "Average": {"sets": 3, "reps": "10-12", "rest": "60-90s"},
    "Well Developed": {"sets": 2, "reps": "8-10", "rest": "45-60s"}
}

def analyze_muscle_development(bodybuilding_analysis):
    """
    Analyze muscle development from bodybuilding analysis data.
    Returns categorized muscle groups by development level.
    """
    muscle_development = {}
    muscle_categories = {
        "Needs Growth": [],
        "Average": [],
        "Well Developed": []
    }
    
    # Define mapping for legacy and standard muscle names to new structure
    muscle_mapping = {
        "arms": ["Biceps", "Triceps"],
        "Arms": ["Biceps", "Triceps"],
        "legs": ["Quads", "Hamstrings", "Calves", "Glutes"],
        "Legs": ["Quads", "Hamstrings", "Calves", "Glutes"],
        # Other muscles retain their names when capitalized
    }
    
    # Extract muscle development from analysis data
    if bodybuilding_analysis and 'muscle_development' in bodybuilding_analysis:
        muscle_development = bodybuilding_analysis['muscle_development']
    else:
        # Fallback extraction - try to find individual muscle metrics
        standard_muscles = ["arms", "chest", "shoulders", "back", "legs", "core", 
                            "biceps", "triceps", "quads", "hamstrings", "calves", "glutes"]
        
        for muscle in standard_muscles:
            # Check standard keys
            if f"{muscle}_development" in bodybuilding_analysis:
                status = bodybuilding_analysis[f"{muscle}_development"]
                muscle_development[muscle.capitalize()] = status
            
            # Check for alternate keys
            elif muscle.capitalize() in bodybuilding_analysis:
                status = bodybuilding_analysis[muscle.capitalize()]
                muscle_development[muscle.capitalize()] = status
    
    # Categorize muscles by development level
    for muscle, status in muscle_development.items():
        # Normalize status strings
        if isinstance(status, str):
            if status.lower() in ["needs growth", "needs_growth", "poor", "underdeveloped", "weak"]:
                normalized_status = "Needs Growth"
            elif status.lower() in ["average", "moderate", "normal", "medium"]:
                normalized_status = "Average"  
            elif status.lower() in ["well developed", "well_developed", "good", "excellent", "strong"]:
                normalized_status = "Well Developed"
            else:
                normalized_status = "Average"  # Default for unrecognized status
        else:
            normalized_status = "Average"  # Default for non-string values
        
        # Map muscle groups to new structure if needed
        if muscle in muscle_mapping:
            for mapped_muscle in muscle_mapping[muscle]:
                if mapped_muscle not in muscle_categories[normalized_status]:
                    muscle_categories[normalized_status].append(mapped_muscle)
        else:
            if muscle not in muscle_categories[normalized_status]:
                muscle_categories[normalized_status].append(muscle)
    
    # Fill in any missing essential muscle groups with average development
    essential_muscles = ["Chest", "Shoulders", "Back", "Triceps", "Biceps", 
                        "Quads", "Hamstrings", "Glutes", "Calves", "Core",
                        "Rear Delts"]
    
    all_categorized = []
    for muscles in muscle_categories.values():
        all_categorized.extend(muscles)
    
    for muscle in essential_muscles:
        if muscle not in all_categorized:
            muscle_categories["Average"].append(muscle)
    
    return muscle_categories

def determine_training_split(experience_level, categorized_muscles, goal="muscle_gain"):
    """
    Determine the optimal training split based on experience and goals.
    """
    # Count total muscle groups that need attention
    priority_count = len(categorized_muscles["Needs Growth"]) + len(categorized_muscles["Average"])
    
    # Determine days per week based on experience and priority count
    days_per_week = 3  # Default minimum
    
    if experience_level == "beginner":
        if priority_count <= 2:
            days_per_week = 3
        else:
            days_per_week = 4
    elif experience_level == "intermediate":
        if priority_count <= 2:
            days_per_week = 4
        else:
            days_per_week = 5
    elif experience_level == "advanced":
        days_per_week = 5 if priority_count <= 3 else 6
    
    # Adjust for specific goals
    if goal == "fat_loss":
        days_per_week = min(days_per_week + 1, 6)
    elif goal == "maintenance":
        days_per_week = max(days_per_week - 1, 3)
    
    # Get the appropriate split template
    split_key = f"{days_per_week}_day"
    available_templates = SPLIT_TEMPLATES.get(experience_level, {})
    
    # Fallback to lower experience level if needed
    if split_key not in available_templates and experience_level == "advanced":
        available_templates = SPLIT_TEMPLATES["intermediate"]
    if split_key not in available_templates and experience_level in ["advanced", "intermediate"]:
        available_templates = SPLIT_TEMPLATES["beginner"]
    
    # Get the closest available template if exact match not found
    if split_key not in available_templates:
        available_days = [int(k.split('_')[0]) for k in available_templates.keys()]
        closest_day = min(available_days, key=lambda x: abs(x - days_per_week))
        split_key = f"{closest_day}_day"
    
    # Get the template or use a default full body split
    split_template = available_templates.get(split_key, ["Full Body", "Rest", "Full Body", "Rest", "Full Body", "Rest", "Rest"])
    
    return split_template

def customize_muscle_group_order(split_template, categorized_muscles):
    """
    Customize the ordered muscle groups for each day based on priority.
    """
    # Create a priority order for muscle groups
    priority_order = (
        categorized_muscles["Needs Growth"] + 
        categorized_muscles["Average"] + 
        categorized_muscles["Well Developed"]
    )
    
    # Ensure all standard muscle groups are included
    all_muscles = ["Chest", "Shoulders", "Back", "Triceps", "Biceps", "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Rear Delts"]
    for muscle in all_muscles:
        if muscle not in priority_order:
            priority_order.append(muscle)
    
    # Generate customized training days
    customized_split = []
    
    for day_focus in split_template:
        if day_focus == "Rest":
            customized_split.append({"focus": "Rest", "muscle_groups": []})
            continue
        
        # Determine which muscle groups to train based on the day's focus
        if day_focus == "Full Body":
            # Pick 1 exercise from each muscle group, prioritizing needs growth
            muscles_for_day = all_muscles
        elif day_focus == "Upper Body":
            muscles_for_day = ["Chest", "Back", "Shoulders", "Arms"]
        elif day_focus == "Lower Body":
            muscles_for_day = ["Legs", "Core"]
        elif day_focus == "Push":
            muscles_for_day = ["Chest", "Shoulders", "Triceps"]
        elif day_focus == "Pull":
            muscles_for_day = ["Back", "Biceps", "Rear Delts"]
        elif day_focus == "Legs":
            muscles_for_day = ["Quads", "Glutes", "Hamstrings", "Calves", "Core"]
        elif "/" in day_focus:
            # Split day like "Chest/Triceps"
            muscles_for_day = day_focus.split("/")
        else:
            # Single muscle focus like "Chest"
            muscles_for_day = [day_focus]
        
        # Create the day's workout focus
        customized_split.append({
            "focus": day_focus,
            "muscle_groups": muscles_for_day
        })
    
    return customized_split

def generate_exercises_for_day(day_plan, categorized_muscles, day_number=None):
    """
    Generate specific exercises for each muscle group in a day's workout.
    Adjust volume (sets, reps) based on the muscle's development level.
    Enforce a hard limit of 8 exercises per day.
    """
    if day_plan["focus"] == "Rest":
        return {
            "focus": "Rest Day",
            "exercises": [],
            "notes": "Active recovery, stretching, and light cardio recommended."
        }
    
    # Sunday (day 7) is a special Leg Day with different exercises
    is_sunday_leg_day = day_number == 7 and day_plan["focus"] == "Legs"
    
    # First pass: Generate all potential exercises with priority info
    all_potential_exercises = []
    
    # Track muscle counts to ensure proper distribution
    muscle_counts = {}
    for muscle in day_plan["muscle_groups"]:
        muscle_counts[muscle] = 0
    
    # Get info from already used leg exercises to avoid repetition on Sunday
    used_leg_exercises = []
    if is_sunday_leg_day:
        day_plan["focus"] = "Legs (Strength Focus)"  # Mark Sunday as special leg day
    
    # Determine exercise count per muscle based on priority
    for muscle in day_plan["muscle_groups"]:
        # Standardize muscle name for lookup
        lookup_muscle = muscle
        
        # Determine development level for this muscle
        development_level = "Average"  # Default
        for level, muscles in categorized_muscles.items():
            if muscle in muscles:
                development_level = level
                break
            # For backward compatibility with old Arms data
            elif muscle in ["Triceps", "Biceps"] and "Arms" in muscles:
                development_level = level
                break
        
        # Determine number of exercises based on priority (initial allocation)
        if development_level == "Needs Growth":
            exercise_count = 3
        elif development_level == "Average":
            exercise_count = 2
        else:  # Well Developed
            exercise_count = 1
        
        # Adjust for special cases
        if day_plan["focus"] == "Full Body":
            exercise_count = 1  # Only 1 exercise per muscle on full body days
        
        # Get set/rep scheme based on development level
        scheme = DEFAULT_SET_REP_SCHEMES[development_level]
        
        # Select exercises for this muscle group
        muscle_exercises = []
        if lookup_muscle in EXERCISE_MAPPING:
            # Get all exercises for this muscle
            available_exercises = EXERCISE_MAPPING[lookup_muscle]
            
            # For Sunday leg day, use different exercise selection pattern
            if is_sunday_leg_day:
                # Specific emphasis for Sunday leg day based on muscle
                if lookup_muscle == "Quads":
                    # For Sunday, prioritize compound movements for quads
                    compound_exercises = ["Squat", "Leg Press", "Hack Squat"]
                    compound_available = [ex for ex in available_exercises if ex in compound_exercises]
                    if compound_available:
                        muscle_exercises = [random.choice(compound_available)]
                        # Add isolation if needed
                        if exercise_count > 1 and len(available_exercises) > len(compound_available):
                            isolation = [ex for ex in available_exercises if ex not in compound_available]
                            muscle_exercises.extend(random.sample(isolation, min(exercise_count-1, len(isolation))))
                elif lookup_muscle == "Hamstrings":
                    # For Sunday, prioritize Romanian Deadlift for hamstrings if available
                    if "Romanian Deadlift" in available_exercises:
                        muscle_exercises = ["Romanian Deadlift"]
                        remaining = [ex for ex in available_exercises if ex != "Romanian Deadlift"]
                        if exercise_count > 1 and remaining:
                            muscle_exercises.extend(random.sample(remaining, min(exercise_count-1, len(remaining))))
                    else:
                        muscle_exercises = random.sample(available_exercises, min(exercise_count, len(available_exercises)))
                else:
                    # For other leg muscles on Sunday, use standard random selection
                    muscle_exercises = random.sample(available_exercises, min(exercise_count, len(available_exercises)))
            else:
                # Standard exercise selection for non-Sunday workouts
                if len(available_exercises) >= exercise_count:
                    muscle_exercises = random.sample(available_exercises, exercise_count)
                else:
                    muscle_exercises = available_exercises
        
        # Add exercises to the potential list
        for exercise in muscle_exercises:
            # Assign priority scores for sorting later
            # Lower score = higher priority for inclusion
            priority_score = 0
            if development_level == "Needs Growth":
                priority_score = 0  # Highest priority
            elif development_level == "Average":
                priority_score = 10
            else:  # Well Developed
                priority_score = 20
            
            # Add order within muscle group to maintain distribution
            muscle_counts[muscle] += 1
            priority_score += muscle_counts[muscle]
            
            all_potential_exercises.append({
                "name": exercise,
                "muscle": muscle,
                "sets": scheme["sets"],
                "reps": scheme["reps"],
                "rest": scheme["rest"],
                "priority": development_level,
                "priority_score": priority_score
            })
    
    # Sort exercises by priority (lowest score = highest priority)
    all_potential_exercises.sort(key=lambda x: x["priority_score"])
    
    # Cap at maximum 8 exercises total
    MAX_EXERCISES = 8
    final_exercises = all_potential_exercises[:MAX_EXERCISES]
    
    # Ensure at least one exercise per muscle group if possible (only if we have space)
    if len(final_exercises) < MAX_EXERCISES:
        # Find which muscle groups don't have any exercise yet
        represented_muscles = {ex["muscle"] for ex in final_exercises}
        missing_muscles = [m for m in day_plan["muscle_groups"] if m not in represented_muscles]
        
        # Add one exercise for each missing muscle group if possible
        for muscle in missing_muscles:
            if len(final_exercises) >= MAX_EXERCISES:
                break  # Stop if we've reached the max
                
            # Find an exercise for this muscle
            for ex in all_potential_exercises:
                if ex["muscle"] == muscle and ex not in final_exercises:
                    final_exercises.append(ex)
                    break
    
    # Create the complete day workout
    if is_sunday_leg_day:
        notes = "Sunday Leg Day focuses on compound strength movements like Squats and Romanian Deadlifts. "
        weak_muscles = set([e["muscle"] for e in final_exercises if e["priority"] == "Needs Growth"])
        if weak_muscles:
            notes += f"Prioritize these weak areas: {', '.join(weak_muscles)}."
    else:
        notes = f"Focus on {'the weakest ' if final_exercises else ''}muscle groups: " + \
                ", ".join(set([e["muscle"] for e in final_exercises if e["priority"] == "Needs Growth"]))
    
    workout = {
        "focus": day_plan["focus"],
        "exercises": final_exercises,
        "notes": notes
    }
    
    return workout

def generate_complete_workout_plan(bodybuilding_analysis, experience="intermediate", goal="muscle_gain"):
    """
    Generate a complete 7-day workout plan based on bodybuilding analysis.
    
    Args:
        bodybuilding_analysis: Analysis data containing muscle development info
        experience: User's training experience level (beginner, intermediate, advanced)
        goal: Training goal (muscle_gain, fat_loss, maintenance)
        
    Returns:
        A dictionary with the complete workout plan.
    """
    # Analyze muscle development
    categorized_muscles = analyze_muscle_development(bodybuilding_analysis)
    
    # Determine appropriate training split
    split_template = determine_training_split(experience, categorized_muscles, goal)
    
    # Create customized muscle group order
    customized_split = customize_muscle_group_order(split_template, categorized_muscles)
    
    # Generate exercises for each day
    workout_days = []
    for day_index, day_plan in enumerate(customized_split):
        day_number = day_index + 1  # 1-based day number (7 = Sunday)
        day_workout = generate_exercises_for_day(day_plan, categorized_muscles, day_number)
        day_workout["day"] = day_number
        day_workout["weekday"] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_index]
        workout_days.append(day_workout)
    
    # Create date-based recommendations
    today = datetime.now()
    start_date = today
    # If today is past 8 PM, start tomorrow
    if today.hour >= 20:
        start_date = today + timedelta(days=1)
    
    # Build the complete plan
    workout_plan = {
        "generated_date": today.strftime("%Y-%m-%d"),
        "start_date": start_date.strftime("%Y-%m-%d"),
        "experience_level": experience,
        "goal": goal,
        "muscle_focus": {
            "primary": categorized_muscles["Needs Growth"],
            "secondary": categorized_muscles["Average"],
            "maintenance": categorized_muscles["Well Developed"]
        },
        "workout_schedule": workout_days
    }
    
    return workout_plan