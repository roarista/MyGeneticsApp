import logging
from typing import Dict, List, Any, Optional
import math

# Configure logging
logger = logging.getLogger(__name__)

class WorkoutPlanner:
    """
    A class to handle workout plan generation based on user metrics and goals.
    """
    
    def __init__(self):
        self.base_exercises = {
            'chest': [
                {'name': 'Bench Press', 'target': 'overall chest development', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Incline Dumbbell Press', 'target': 'upper chest', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Cable Flyes', 'target': 'chest stretching and isolation', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Decline Press', 'target': 'lower chest development', 'sets': 3, 'reps': '10-12', 'difficulty': 'intermediate'},
                {'name': 'Push-Ups', 'target': 'chest, shoulders, and triceps', 'sets': 3, 'reps': '10-15', 'difficulty': 'beginner'},
                {'name': 'Dumbbell Press', 'target': 'chest development', 'sets': 3, 'reps': '8-12', 'difficulty': 'beginner'}
            ],
            'back': [
                {'name': 'Pull-ups/Lat Pulldowns', 'target': 'latissimus dorsi', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Bent-over Rows', 'target': 'middle back', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Seated Cable Rows', 'target': 'overall back development', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Face Pulls', 'target': 'rear deltoids and upper back', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Barbell Rows', 'target': 'upper and middle back', 'sets': 3, 'reps': '8-12', 'difficulty': 'intermediate'},
                {'name': 'Dumbbell Rows', 'target': 'back width and thickness', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'}
            ],
            'shoulders': [
                {'name': 'Overhead Press', 'target': 'overall shoulder development', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Lateral Raises', 'target': 'lateral deltoids', 'sets': 3, 'reps': '10-15', 'difficulty': 'beginner'},
                {'name': 'Front Raises', 'target': 'anterior deltoids', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Reverse Flyes', 'target': 'posterior deltoids', 'sets': 3, 'reps': '10-15', 'difficulty': 'beginner'},
                {'name': 'Arnold Press', 'target': 'all deltoid heads', 'sets': 3, 'reps': '8-12', 'difficulty': 'intermediate'},
                {'name': 'Upright Rows', 'target': 'upper traps and deltoids', 'sets': 3, 'reps': '10-12', 'difficulty': 'intermediate'}
            ],
            'arms': [
                {'name': 'Barbell Curls', 'target': 'biceps', 'sets': 3, 'reps': '8-12', 'difficulty': 'beginner'},
                {'name': 'Tricep Dips', 'target': 'triceps', 'sets': 3, 'reps': '8-12', 'difficulty': 'beginner'},
                {'name': 'Hammer Curls', 'target': 'brachialis and forearms', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Tricep Pushdowns', 'target': 'triceps', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Preacher Curls', 'target': 'biceps peak', 'sets': 3, 'reps': '10-12', 'difficulty': 'intermediate'},
                {'name': 'Skull Crushers', 'target': 'triceps long head', 'sets': 3, 'reps': '10-12', 'difficulty': 'intermediate'}
            ],
            'legs': [
                {'name': 'Squats', 'target': 'quadriceps and overall leg development', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Romanian Deadlifts', 'target': 'hamstrings and glutes', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Leg Press', 'target': 'quadriceps', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Bulgarian Split Squats', 'target': 'single-leg strength and balance', 'sets': 3, 'reps': '10-12 per leg', 'difficulty': 'intermediate'},
                {'name': 'Calf Raises', 'target': 'calf muscles', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Lunges', 'target': 'quads, glutes, and balance', 'sets': 3, 'reps': '10-12 per leg', 'difficulty': 'beginner'}
            ],
            'core': [
                {'name': 'Russian Twists', 'target': 'obliques', 'sets': 3, 'reps': '10-15 per side', 'difficulty': 'beginner'},
                {'name': 'Hanging Leg Raises', 'target': 'lower abs', 'sets': 3, 'reps': '10-15', 'difficulty': 'intermediate'},
                {'name': 'Ab Wheel Rollouts', 'target': 'entire core', 'sets': 3, 'reps': '8-12', 'difficulty': 'intermediate'},
                {'name': 'Cable Crunches', 'target': 'upper and middle abs', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Planks', 'target': 'core stability', 'sets': 3, 'reps': '30-60 seconds', 'difficulty': 'beginner'},
                {'name': 'Bicycle Crunches', 'target': 'obliques and abs', 'sets': 3, 'reps': '15-20', 'difficulty': 'beginner'}
            ],
            'cardio': [
                {'name': 'HIIT (High-Intensity Interval Training)', 'target': 'fat burning and cardiovascular health', 'sets': 1, 'reps': '20-30 min', 'difficulty': 'intermediate'},
                {'name': 'Steady-State Cardio', 'target': 'endurance and fat burning', 'sets': 1, 'reps': '30-45 min', 'difficulty': 'beginner'},
                {'name': 'Jump Rope', 'target': 'coordination and cardiovascular health', 'sets': 1, 'reps': '10-15 min', 'difficulty': 'beginner'},
                {'name': 'Treadmill Intervals', 'target': 'fat burning and cardiovascular health', 'sets': 1, 'reps': '20-30 min', 'difficulty': 'intermediate'},
                {'name': 'Cycling', 'target': 'lower body and cardiovascular health', 'sets': 1, 'reps': '30-45 min', 'difficulty': 'beginner'},
                {'name': 'Rowing', 'target': 'full body and cardiovascular health', 'sets': 1, 'reps': '20-30 min', 'difficulty': 'intermediate'}
            ]
        }
        
        self.specialized_exercises = {
            'shoulder_width': [
                {'name': 'Wide-Grip Upright Rows', 'target': 'lateral deltoids', 'sets': 3, 'reps': '10-12', 'difficulty': 'intermediate'},
                {'name': 'Lateral Raises with Hold', 'target': 'side delts', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Cable Lateral Raises', 'target': 'side delts', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Face Pulls with External Rotation', 'target': 'rear delts and upper back', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Dumbbell Front Raises', 'target': 'anterior deltoids', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'}
            ],
            'arm_development': [
                {'name': 'Close-Grip Bench Press', 'target': 'triceps', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Incline Dumbbell Curls', 'target': 'biceps', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Rope Pushdowns', 'target': 'triceps', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Concentration Curls', 'target': 'biceps peak', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Overhead Tricep Extensions', 'target': 'triceps long head', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'}
            ],
            'chest_development': [
                {'name': 'Cable Crossovers', 'target': 'inner chest', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Decline Push-Ups', 'target': 'lower chest', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Dumbbell Flyes', 'target': 'chest stretch', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Incline Bench Press', 'target': 'upper chest', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Pec Deck Machine', 'target': 'chest isolation', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'}
            ],
            'back_width': [
                {'name': 'Wide-Grip Pull-Ups', 'target': 'lats width', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Straight-Arm Pulldowns', 'target': 'lats', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Wide-Grip Seated Rows', 'target': 'back width', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Lat Pulldowns', 'target': 'lats', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'},
                {'name': 'Single-Arm Dumbbell Rows', 'target': 'back thickness', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'}
            ],
            'leg_development': [
                {'name': 'Front Squats', 'target': 'quads', 'sets': 3, 'reps': '8-10', 'difficulty': 'intermediate'},
                {'name': 'Bulgarian Split Squats', 'target': 'unilateral legs', 'sets': 3, 'reps': '10-12 per leg', 'difficulty': 'intermediate'},
                {'name': 'Hack Squats', 'target': 'quads', 'sets': 3, 'reps': '10-12', 'difficulty': 'intermediate'},
                {'name': 'Leg Extensions', 'target': 'quads isolation', 'sets': 3, 'reps': '12-15', 'difficulty': 'beginner'},
                {'name': 'Leg Curls', 'target': 'hamstrings', 'sets': 3, 'reps': '10-12', 'difficulty': 'beginner'}
            ],
            'fat_loss': [
                {'name': 'HIIT Circuit', 'target': 'fat burning and cardiovascular health', 'sets': 1, 'reps': '20-30 min', 'difficulty': 'intermediate'},
                {'name': 'Tabata Training', 'target': 'metabolic conditioning', 'sets': 1, 'reps': '20 min', 'difficulty': 'advanced'},
                {'name': 'Circuit Training', 'target': 'full body conditioning', 'sets': 1, 'reps': '30-45 min', 'difficulty': 'intermediate'},
                {'name': 'Sprint Intervals', 'target': 'fat burning and power', 'sets': 1, 'reps': '15-20 min', 'difficulty': 'intermediate'},
                {'name': 'Jump Rope Intervals', 'target': 'coordination and fat burning', 'sets': 1, 'reps': '15-20 min', 'difficulty': 'beginner'}
            ]
        }
        
        # Define baseline measurements for different body types and heights
        self.baseline_measurements = {
            'male': {
                'shoulder_width': lambda height: height * 0.25,  # 25% of height
                'chest_size': lambda height: height * 0.48,      # 48% of height
                'arm_size': lambda height: height * 0.15,        # 15% of height
                'waist_size': lambda height: height * 0.45,      # 45% of height
                'thigh_size': lambda height: height * 0.30,      # 30% of height
                'calf_size': lambda height: height * 0.20        # 20% of height
            },
            'female': {
                'shoulder_width': lambda height: height * 0.23,  # 23% of height
                'chest_size': lambda height: height * 0.46,      # 46% of height
                'arm_size': lambda height: height * 0.13,        # 13% of height
                'waist_size': lambda height: height * 0.43,      # 43% of height
                'thigh_size': lambda height: height * 0.31,      # 31% of height
                'calf_size': lambda height: height * 0.21        # 21% of height
            }
        }
        
    def analyze_physique(self, user_data):
        """
        Analyze user physique to identify weak points and potential areas for improvement.
        
        Args:
            user_data (dict): User metrics including height, weight, body measurements, 
                              body fat percentage, and training experience.
        
        Returns:
            dict: Analysis results with weak points and focus areas.
        """
        try:
            gender = user_data.get('gender', 'male').lower()
            height_cm = user_data.get('height_cm', 175)
            experience = user_data.get('experience', 'beginner')
            body_fat = user_data.get('body_fat_percentage', 20)
            
            # Get measurements or use estimations
            measurements = user_data.get('measurements', {})
            
            # Identify weak points based on ideal proportions
            weak_points = []
            focus_areas = []
            
            # Use baseline measurements for comparison
            baselines = self.baseline_measurements.get(gender, self.baseline_measurements['male'])
            
            # Check shoulder to waist ratio (V-taper)
            shoulder_width = measurements.get('shoulder_width_cm', 0)
            waist_size = measurements.get('waist_circumference_cm', 0)
            
            if shoulder_width and waist_size:
                shoulder_to_waist_ratio = shoulder_width / waist_size
                ideal_ratio = 1.6 if gender == 'male' else 1.4
                
                if shoulder_to_waist_ratio < ideal_ratio * 0.9:  # 10% below ideal
                    weak_points.append('shoulder_width')
                    focus_areas.append({
                        'name': 'Shoulder Width',
                        'rating': 'below_average',
                        'priority': 'high'
                    })
            
            # Check arm development
            arm_size = measurements.get('arm_circumference_cm', 0)
            ideal_arm_size = baselines.get('arm_size')(height_cm)
            
            if arm_size and arm_size < ideal_arm_size * 0.9:  # 10% below ideal
                weak_points.append('arm_development')
                focus_areas.append({
                    'name': 'Arm Development',
                    'rating': 'below_average',
                    'priority': 'medium'
                })
            
            # Check chest development
            chest_size = measurements.get('chest_circumference_cm', 0)
            ideal_chest_size = baselines.get('chest_size')(height_cm)
            
            if chest_size and chest_size < ideal_chest_size * 0.9:  # 10% below ideal
                weak_points.append('chest_development')
                focus_areas.append({
                    'name': 'Chest Development',
                    'rating': 'below_average',
                    'priority': 'medium'
                })
            
            # Check back width
            lat_spread = measurements.get('lat_spread_cm', 0)
            if lat_spread and lat_spread < shoulder_width * 0.9:  # Lats should be close to shoulder width
                weak_points.append('back_width')
                focus_areas.append({
                    'name': 'Back Width',
                    'rating': 'below_average',
                    'priority': 'medium'
                })
            
            # Check leg development
            thigh_size = measurements.get('thigh_circumference_cm', 0)
            ideal_thigh_size = baselines.get('thigh_size')(height_cm)
            
            if thigh_size and thigh_size < ideal_thigh_size * 0.9:  # 10% below ideal
                weak_points.append('leg_development')
                focus_areas.append({
                    'name': 'Leg Development',
                    'rating': 'below_average',
                    'priority': 'high'
                })
            
            # Check body fat levels
            high_body_fat = (gender == 'male' and body_fat > 18) or (gender == 'female' and body_fat > 25)
            if high_body_fat:
                weak_points.append('fat_loss')
                focus_areas.append({
                    'name': 'Fat Loss',
                    'rating': 'priority',
                    'priority': 'high'
                })
            
            # If no weak points identified, focus on overall development
            if not weak_points:
                focus_areas.append({
                    'name': 'Overall Development',
                    'rating': 'balanced',
                    'priority': 'medium'
                })
            
            return {
                'weak_points': weak_points,
                'focus_areas': focus_areas,
                'experience_level': experience,
                'high_body_fat': high_body_fat
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_physique: {str(e)}")
            # Return a default analysis if something goes wrong
            return {
                'weak_points': [],
                'focus_areas': [{
                    'name': 'Overall Development',
                    'rating': 'balanced',
                    'priority': 'medium'
                }],
                'experience_level': experience,
                'high_body_fat': False
            }
    
    def select_exercises_for_weak_points(self, weak_points, experience):
        """
        Select exercises that target the identified weak points.
        
        Args:
            weak_points (list): List of weak point identifiers.
            experience (str): User's training experience level.
        
        Returns:
            dict: Specialized exercises for each muscle group based on weak points.
        """
        specialized_exercises = {}
        
        for weak_point in weak_points:
            if weak_point in self.specialized_exercises:
                # Filter exercises based on experience
                exercises = [ex for ex in self.specialized_exercises[weak_point] 
                            if (experience == 'beginner' and ex['difficulty'] == 'beginner') or
                               (experience == 'intermediate' and ex['difficulty'] in ['beginner', 'intermediate']) or
                               (experience == 'advanced')]
                
                if exercises:
                    specialized_exercises[weak_point] = exercises
        
        return specialized_exercises
    
    def create_push_day(self, weak_points, experience, high_body_fat):
        """Create a push day workout focusing on chest, shoulders, and triceps."""
        exercises = []
        
        # Add main chest exercise
        chest_exercises = self.base_exercises['chest']
        if 'chest_development' in weak_points:
            # Add more chest exercises if it's a weak point
            chest_specific = self.specialized_exercises.get('chest_development', [])
            chest_exercises = chest_specific + chest_exercises
        
        # Filter by experience level
        chest_exercises = self._filter_by_experience(chest_exercises, experience)
        
        # Add 2-3 chest exercises
        exercises.extend(self._select_random_exercises(chest_exercises, 2))
        
        # Add shoulder exercises
        shoulder_exercises = self.base_exercises['shoulders']
        if 'shoulder_width' in weak_points:
            # Add more shoulder exercises if it's a weak point
            shoulder_specific = self.specialized_exercises.get('shoulder_width', [])
            shoulder_exercises = shoulder_specific + shoulder_exercises
        
        # Filter by experience level
        shoulder_exercises = self._filter_by_experience(shoulder_exercises, experience)
        
        # Add 1-2 shoulder exercises
        exercises.extend(self._select_random_exercises(shoulder_exercises, 2))
        
        # Add triceps exercises
        triceps_exercises = [ex for ex in self.base_exercises['arms'] if 'triceps' in ex['target'].lower()]
        if 'arm_development' in weak_points:
            # Add more triceps exercises if arms are a weak point
            arm_specific = [ex for ex in self.specialized_exercises.get('arm_development', []) 
                           if 'triceps' in ex['target'].lower()]
            triceps_exercises = arm_specific + triceps_exercises
        
        # Filter by experience level
        triceps_exercises = self._filter_by_experience(triceps_exercises, experience)
        
        # Add 1-2 triceps exercises
        exercises.extend(self._select_random_exercises(triceps_exercises, 2))
        
        # Add cardio if high body fat
        if high_body_fat:
            cardio_exercises = self.base_exercises['cardio']
            cardio_specific = self.specialized_exercises.get('fat_loss', [])
            cardio_exercises = cardio_specific + cardio_exercises
            
            # Filter by experience level
            cardio_exercises = self._filter_by_experience(cardio_exercises, experience)
            
            # Add 1 cardio exercise
            exercises.extend(self._select_random_exercises(cardio_exercises, 1))
        
        # Convert to the expected format
        formatted_exercises = []
        for ex in exercises:
            formatted_ex = {
                'name': ex['name'],
                'sets': str(ex['sets']),
                'reps': ex['reps'],
                'focus': ex['target'],
                'category': 'push'
            }
            formatted_exercises.append(formatted_ex)
        
        return formatted_exercises
    
    def create_pull_day(self, weak_points, experience, high_body_fat):
        """Create a pull day workout focusing on back, biceps, and rear shoulders."""
        exercises = []
        
        # Add main back exercises
        back_exercises = self.base_exercises['back']
        if 'back_width' in weak_points:
            # Add more back exercises if it's a weak point
            back_specific = self.specialized_exercises.get('back_width', [])
            back_exercises = back_specific + back_exercises
        
        # Filter by experience level
        back_exercises = self._filter_by_experience(back_exercises, experience)
        
        # Add 2-3 back exercises
        exercises.extend(self._select_random_exercises(back_exercises, 3))
        
        # Add biceps exercises
        biceps_exercises = [ex for ex in self.base_exercises['arms'] if 'biceps' in ex['target'].lower()]
        if 'arm_development' in weak_points:
            # Add more biceps exercises if arms are a weak point
            arm_specific = [ex for ex in self.specialized_exercises.get('arm_development', []) 
                           if 'biceps' in ex['target'].lower()]
            biceps_exercises = arm_specific + biceps_exercises
        
        # Filter by experience level
        biceps_exercises = self._filter_by_experience(biceps_exercises, experience)
        
        # Add 2 biceps exercises
        exercises.extend(self._select_random_exercises(biceps_exercises, 2))
        
        # Add rear shoulder exercise
        rear_delt_exercises = [ex for ex in self.base_exercises['shoulders'] 
                              if 'posterior' in ex['target'].lower() or 'rear' in ex['target'].lower()]
        
        # Filter by experience level
        rear_delt_exercises = self._filter_by_experience(rear_delt_exercises, experience)
        
        # Add 1 rear delt exercise if available
        if rear_delt_exercises:
            exercises.extend(self._select_random_exercises(rear_delt_exercises, 1))
        
        # Add cardio if high body fat
        if high_body_fat:
            cardio_exercises = self.base_exercises['cardio']
            cardio_specific = self.specialized_exercises.get('fat_loss', [])
            cardio_exercises = cardio_specific + cardio_exercises
            
            # Filter by experience level
            cardio_exercises = self._filter_by_experience(cardio_exercises, experience)
            
            # Add 1 cardio exercise
            exercises.extend(self._select_random_exercises(cardio_exercises, 1))
        
        # Convert to the expected format
        formatted_exercises = []
        for ex in exercises:
            formatted_ex = {
                'name': ex['name'],
                'sets': str(ex['sets']),
                'reps': ex['reps'],
                'focus': ex['target'],
                'category': 'pull'
            }
            formatted_exercises.append(formatted_ex)
        
        return formatted_exercises
    
    def create_leg_day(self, weak_points, experience, high_body_fat, posterior_chain_focus=False):
        """Create a leg day workout."""
        exercises = []
        
        # Add main leg exercises
        leg_exercises = self.base_exercises['legs']
        if 'leg_development' in weak_points:
            # Add more leg exercises if it's a weak point
            leg_specific = self.specialized_exercises.get('leg_development', [])
            leg_exercises = leg_specific + leg_exercises
        
        # Filter by experience level
        leg_exercises = self._filter_by_experience(leg_exercises, experience)
        
        if posterior_chain_focus:
            # Focus on hamstrings, glutes, and calves
            hamstring_exercises = [ex for ex in leg_exercises 
                                 if 'hamstring' in ex['target'].lower() or 'glute' in ex['target'].lower()]
            
            # Add 2-3 hamstring/glute exercises
            exercises.extend(self._select_random_exercises(hamstring_exercises, 2))
            
            # Add 1-2 quad exercises for balance
            quad_exercises = [ex for ex in leg_exercises if 'quad' in ex['target'].lower()]
            exercises.extend(self._select_random_exercises(quad_exercises, 1))
        else:
            # Standard leg day with emphasis on quads
            quad_exercises = [ex for ex in leg_exercises if 'quad' in ex['target'].lower()]
            
            # Add 2-3 quad exercises
            exercises.extend(self._select_random_exercises(quad_exercises, 2))
            
            # Add 1-2 hamstring/glute exercises
            hamstring_exercises = [ex for ex in leg_exercises 
                                 if 'hamstring' in ex['target'].lower() or 'glute' in ex['target'].lower()]
            exercises.extend(self._select_random_exercises(hamstring_exercises, 2))
        
        # Add calf exercises
        calf_exercises = [ex for ex in leg_exercises if 'calf' in ex['target'].lower()]
        if calf_exercises:
            exercises.extend(self._select_random_exercises(calf_exercises, 1))
        
        # Add core exercises
        core_exercises = self.base_exercises['core']
        core_exercises = self._filter_by_experience(core_exercises, experience)
        exercises.extend(self._select_random_exercises(core_exercises, 2))
        
        # Add cardio if high body fat
        if high_body_fat:
            cardio_exercises = self.base_exercises['cardio']
            cardio_specific = self.specialized_exercises.get('fat_loss', [])
            cardio_exercises = cardio_specific + cardio_exercises
            
            # Filter by experience level
            cardio_exercises = self._filter_by_experience(cardio_exercises, experience)
            
            # Add 1 cardio exercise
            exercises.extend(self._select_random_exercises(cardio_exercises, 1))
        
        # Convert to the expected format
        formatted_exercises = []
        for ex in exercises:
            formatted_ex = {
                'name': ex['name'],
                'sets': str(ex['sets']),
                'reps': ex['reps'],
                'focus': ex['target'],
                'category': 'legs'
            }
            formatted_exercises.append(formatted_ex)
        
        return formatted_exercises
    
    def create_rest_day_activities(self):
        """Create rest day activities for active recovery."""
        activities = [
            {
                'name': 'Light Walking',
                'sets': '1',
                'reps': '20-30 min',
                'focus': 'Active recovery, cardiovascular health',
                'category': 'rest'
            },
            {
                'name': 'Stretching Routine',
                'sets': '1',
                'reps': '15-20 min',
                'focus': 'Flexibility, recovery',
                'category': 'rest'
            },
            {
                'name': 'Foam Rolling',
                'sets': '1',
                'reps': '10-15 min',
                'focus': 'Myofascial release, recovery',
                'category': 'rest'
            }
        ]
        
        return activities
    
    def generate_workout_plan(self, user_data):
        """
        Generate a personalized weekly workout plan based on user data.
        
        Args:
            user_data (dict): User metrics including height, weight, body measurements, 
                              body fat percentage, and training experience.
        
        Returns:
            dict: Weekly workout plan with exercises for each day.
        """
        try:
            # Analyze physique to identify weak points
            analysis = self.analyze_physique(user_data)
            weak_points = analysis['weak_points']
            experience = analysis['experience_level']
            high_body_fat = analysis['high_body_fat']
            
            # Generate weekly workout plan based on Push/Pull/Legs split
            workout_plan = {
                'Monday': {
                    'category': 'push',
                    'focus': 'Chest, Shoulders, Triceps',
                    'exercises': self.create_push_day(weak_points, experience, high_body_fat)
                },
                'Tuesday': {
                    'category': 'pull',
                    'focus': 'Back, Biceps, Rear Delts',
                    'exercises': self.create_pull_day(weak_points, experience, high_body_fat)
                },
                'Wednesday': {
                    'category': 'legs',
                    'focus': 'Quadriceps, Hamstrings, Core',
                    'exercises': self.create_leg_day(weak_points, experience, high_body_fat)
                },
                'Thursday': {
                    'category': 'rest',
                    'focus': 'Active Recovery',
                    'exercises': self.create_rest_day_activities()
                },
                'Friday': {
                    'category': 'push',
                    'focus': 'Chest, Shoulders, Triceps',
                    'exercises': self.create_push_day(weak_points, experience, high_body_fat)
                },
                'Saturday': {
                    'category': 'pull',
                    'focus': 'Back, Biceps, Rear Delts',
                    'exercises': self.create_pull_day(weak_points, experience, high_body_fat)
                },
                'Sunday': {
                    'category': 'legs',
                    'focus': 'Posterior Chain Focus',
                    'exercises': self.create_leg_day(weak_points, experience, high_body_fat, posterior_chain_focus=True)
                }
            }
            
            return {
                'workout_plan': workout_plan,
                'analysis': analysis,
                'training_tips': self._generate_training_tips(experience, high_body_fat),
                'equipment': self._recommend_equipment(experience),
                'progression_methods': self._progression_methods(experience)
            }
            
        except Exception as e:
            logger.error(f"Error in generate_workout_plan: {str(e)}")
            # Return a default plan if something goes wrong
            return self._generate_default_workout_plan(user_data.get('experience', 'beginner'))
    
    def _filter_by_experience(self, exercises, experience):
        """Filter exercises based on user experience level."""
        if experience == 'beginner':
            return [ex for ex in exercises if ex['difficulty'] == 'beginner']
        elif experience == 'intermediate':
            return [ex for ex in exercises if ex['difficulty'] in ['beginner', 'intermediate']]
        else:  # advanced
            return exercises
    
    def _select_random_exercises(self, exercises, count):
        """Select a random subset of exercises, ensuring no duplicates."""
        import random
        
        if not exercises:
            return []
        
        count = min(count, len(exercises))
        return random.sample(exercises, count)
    
    def _generate_training_tips(self, experience, high_body_fat):
        """Generate training tips based on experience level and body composition."""
        tips = [
            "Focus on proper form before increasing weight",
            "Ensure adequate hydration before, during, and after workouts",
            "Allow 48 hours of recovery for muscle groups trained",
            "Track your workouts to ensure progressive overload"
        ]
        
        if experience == 'beginner':
            tips.extend([
                "Start with lighter weights to master technique",
                "Aim for 1-2 minutes of rest between sets",
                "Consistency is more important than intensity initially",
                "Learn to listen to your body - differentiating between muscle fatigue and pain"
            ])
        elif experience == 'intermediate':
            tips.extend([
                "Consider periodizing your training for better results",
                "Implement drop sets or supersets to increase intensity",
                "Vary repetition ranges to stimulate different muscle fibers",
                "Add compound movements before isolation exercises"
            ])
        else:  # advanced
            tips.extend([
                "Consider advanced techniques like rest-pause sets or mechanical drop sets",
                "Implement deload weeks every 6-8 weeks of intense training",
                "Focus on mind-muscle connection for lagging body parts",
                "Consider specialized training blocks for weak points"
            ])
        
        if high_body_fat:
            tips.extend([
                "Prioritize protein intake to preserve muscle during fat loss",
                "Consider adding 10-15 minutes of HIIT cardio post-workout",
                "Maintain a moderate calorie deficit for sustainable fat loss",
                "Stay active on rest days with light walking or mobility work"
            ])
        
        return tips
    
    def _recommend_equipment(self, experience):
        """Recommend equipment based on experience level."""
        basic_equipment = [
            "Dumbbells or adjustable dumbbells",
            "Resistance bands",
            "Comfortable athletic shoes",
            "Exercise mat"
        ]
        
        if experience == 'beginner':
            return basic_equipment
        
        intermediate_equipment = basic_equipment + [
            "Barbell and weight plates",
            "Pull-up bar",
            "Bench (flat or adjustable)",
            "Kettlebells"
        ]
        
        if experience == 'intermediate':
            return intermediate_equipment
        
        # Advanced equipment
        return intermediate_equipment + [
            "Cable machine or functional trainer",
            "Squat rack/power cage",
            "Specialized bars (e.g., EZ curl bar, trap bar)",
            "Recovery tools (foam roller, massage gun)"
        ]
    
    def _progression_methods(self, experience):
        """Recommend progression methods based on experience level."""
        methods = [
            "Gradually increase weight while maintaining proper form",
            "Add more repetitions before increasing weight",
            "Decrease rest time between sets for endurance improvements",
            "Increase training frequency as recovery capacity improves"
        ]
        
        if experience in ['intermediate', 'advanced']:
            methods.extend([
                "Use periodization to cycle between strength, hypertrophy, and endurance phases",
                "Implement progressive overload through increased time under tension",
                "Use advanced techniques like drop sets, super sets, or giant sets",
                "Track volume (sets × reps × weight) to ensure consistent progression"
            ])
        
        return methods
    
    def _generate_default_workout_plan(self, experience):
        """Generate a default workout plan if the main generation process fails."""
        # Create a basic push/pull/legs split
        push_exercises = [
            {'name': 'Bench Press', 'sets': '3', 'reps': '8-10', 'focus': 'Chest', 'category': 'push'},
            {'name': 'Overhead Press', 'sets': '3', 'reps': '8-10', 'focus': 'Shoulders', 'category': 'push'},
            {'name': 'Tricep Pushdowns', 'sets': '3', 'reps': '10-12', 'focus': 'Triceps', 'category': 'push'},
            {'name': 'Lateral Raises', 'sets': '3', 'reps': '12-15', 'focus': 'Side Delts', 'category': 'push'},
            {'name': 'Push-Ups', 'sets': '3', 'reps': '10-15', 'focus': 'Chest & Triceps', 'category': 'push'}
        ]
        
        pull_exercises = [
            {'name': 'Pull-Ups or Lat Pulldowns', 'sets': '3', 'reps': '8-10', 'focus': 'Back Width', 'category': 'pull'},
            {'name': 'Bent Over Rows', 'sets': '3', 'reps': '8-10', 'focus': 'Back Thickness', 'category': 'pull'},
            {'name': 'Bicep Curls', 'sets': '3', 'reps': '10-12', 'focus': 'Biceps', 'category': 'pull'},
            {'name': 'Face Pulls', 'sets': '3', 'reps': '12-15', 'focus': 'Rear Delts', 'category': 'pull'},
            {'name': 'Hammer Curls', 'sets': '3', 'reps': '10-12', 'focus': 'Brachialis', 'category': 'pull'}
        ]
        
        leg_exercises = [
            {'name': 'Squats', 'sets': '3', 'reps': '8-10', 'focus': 'Quads & Glutes', 'category': 'legs'},
            {'name': 'Romanian Deadlifts', 'sets': '3', 'reps': '8-10', 'focus': 'Hamstrings', 'category': 'legs'},
            {'name': 'Leg Press', 'sets': '3', 'reps': '10-12', 'focus': 'Quads', 'category': 'legs'},
            {'name': 'Calf Raises', 'sets': '3', 'reps': '15-20', 'focus': 'Calves', 'category': 'legs'},
            {'name': 'Lunges', 'sets': '3', 'reps': '10-12 per leg', 'focus': 'Quads & Balance', 'category': 'legs'}
        ]
        
        rest_day = [
            {'name': 'Light Walking', 'sets': '1', 'reps': '20-30 min', 'focus': 'Recovery', 'category': 'rest'},
            {'name': 'Stretching', 'sets': '1', 'reps': '15-20 min', 'focus': 'Flexibility', 'category': 'rest'},
            {'name': 'Foam Rolling', 'sets': '1', 'reps': '10 min', 'focus': 'Myofascial Release', 'category': 'rest'}
        ]
        
        workout_plan = {
            'Monday': {
                'category': 'push',
                'focus': 'Chest, Shoulders, Triceps',
                'exercises': push_exercises
            },
            'Tuesday': {
                'category': 'pull',
                'focus': 'Back, Biceps',
                'exercises': pull_exercises
            },
            'Wednesday': {
                'category': 'legs',
                'focus': 'Quadriceps, Hamstrings, Core',
                'exercises': leg_exercises
            },
            'Thursday': {
                'category': 'rest',
                'focus': 'Recovery',
                'exercises': rest_day
            },
            'Friday': {
                'category': 'push',
                'focus': 'Chest, Shoulders, Triceps',
                'exercises': push_exercises
            },
            'Saturday': {
                'category': 'pull',
                'focus': 'Back, Biceps',
                'exercises': pull_exercises
            },
            'Sunday': {
                'category': 'legs',
                'focus': 'Posterior Chain Focus',
                'exercises': leg_exercises
            }
        }
        
        return {
            'workout_plan': workout_plan,
            'analysis': {
                'weak_points': [],
                'focus_areas': [{
                    'name': 'Overall Development',
                    'rating': 'balanced',
                    'priority': 'medium'
                }],
                'experience_level': experience,
                'high_body_fat': False
            },
            'training_tips': self._generate_training_tips(experience, False),
            'equipment': self._recommend_equipment(experience),
            'progression_methods': self._progression_methods(experience)
        }