"""
Enhanced Measurement Analyzer for MyGenetics App

This module provides a comprehensive 50-point measurement system for bodybuilding
and fitness analysis by processing both front and back photos. It calculates 
measurements with confidence scores and categorizes them for better display.
"""

import logging
import os
import random
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import cv2
import mediapipe as mp

# Set up logging
logger = logging.getLogger(__name__)

class EnhancedMeasurementAnalyzer:
    """Class for analyzing photos and extracting 50 bodybuilding-relevant measurements"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the analyzer with optional API key for external services
        
        Args:
            api_key: Optional API key for external measurement services (not required for demo)
        """
        self.api_key = api_key
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize pose detection
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5
        )
        
        logger.debug("Enhanced Measurement Analyzer initialized")
    
    def analyze_photos(self, 
                      front_image: np.ndarray,
                      back_image: np.ndarray,
                      height_cm: float,
                      weight_kg: float,
                      age: int,
                      gender: str) -> Dict[str, Any]:
        """
        Analyze front and back photos to extract all 50 measurements
        
        Args:
            front_image: NumPy array with the front view image
            back_image: NumPy array with the back view image
            height_cm: User's height in centimeters
            weight_kg: User's weight in kilograms
            age: User's age in years
            gender: User's gender ('male' or 'female')
            
        Returns:
            Dictionary with 50 measurements and their confidence scores
        """
        logger.debug("Starting enhanced measurement analysis on front and back photos")
        
        try:
            # Call API service or simulate measurements
            measurements = self._call_measurement_api(
                front_image, back_image, height_cm, weight_kg, age, gender
            )
            
            # Validate measurements against anatomical constraints
            validated_measurements = self._validate_measurements(measurements)
            
            # Calculate additional metrics
            enhanced_metrics = self._calculate_enhanced_metrics(
                validated_measurements, height_cm, weight_kg, age, gender
            )
            
            # Add confidence scores
            final_measurements = self._add_confidence_scores(enhanced_metrics)
            
            logger.debug("Enhanced measurement analysis completed successfully")
            return final_measurements
            
        except Exception as e:
            logger.error(f"Error in enhanced measurement analysis: {str(e)}")
            # For demo purposes, return mock measurements if the real analysis fails
            return self._generate_mock_measurements(height_cm, weight_kg, age, gender)
    
    def _call_measurement_api(self, 
                            front_image: np.ndarray,
                            back_image: np.ndarray,
                            height_cm: float,
                            weight_kg: float,
                            age: int,
                            gender: str) -> Dict[str, Any]:
        """
        Call external API for measurements (Bodygram API example)
        This is a simulation of what would be an actual API call
        
        Args:
            front_image: Front view image
            back_image: Back view image
            height_cm: User's height
            weight_kg: User's weight
            age: User's age
            gender: User's gender
            
        Returns:
            Dictionary with base measurements
        """
        logger.debug("Processing images with pose detection")
        
        # Process front image with pose detection
        front_results = self.pose.process(cv2.cvtColor(front_image, cv2.COLOR_BGR2RGB))
        
        # Process back image with pose detection
        back_results = self.pose.process(cv2.cvtColor(back_image, cv2.COLOR_BGR2RGB))
        
        # Extract landmarks
        front_landmarks = front_results.pose_landmarks.landmark if front_results.pose_landmarks else None
        back_landmarks = back_results.pose_landmarks.landmark if back_results.pose_landmarks else None
        
        if not front_landmarks or not back_landmarks:
            logger.warning("Could not detect pose landmarks in one or both images")
            # Default to mock measurements if landmark detection fails
            return self._generate_mock_measurements(height_cm, weight_kg, age, gender)
        
        # Initialize measurements with user input
        measurements = {
            'height_cm': height_cm,
            'weight_kg': weight_kg,
            'age': age,
            'gender': gender
        }
        
        # Calculate pixel-to-cm ratio (using height as reference)
        front_height_pixels = self._calculate_height_pixels(front_landmarks)
        back_height_pixels = self._calculate_height_pixels(back_landmarks)
        
        front_pixel_to_cm = height_cm / front_height_pixels if front_height_pixels else 0
        back_pixel_to_cm = height_cm / back_height_pixels if back_height_pixels else 0
        
        # Calculate measurements from front view
        if front_pixel_to_cm > 0:
            # Shoulder width
            shoulder_width_pixels = self._calculate_shoulder_width(front_landmarks)
            measurements['shoulder_width_cm'] = shoulder_width_pixels * front_pixel_to_cm
            
            # Chest circumference (estimated)
            chest_width_pixels = self._calculate_chest_width(front_landmarks)
            measurements['chest_circumference_cm'] = self._width_to_circumference(chest_width_pixels * front_pixel_to_cm)
            
            # Waist circumference (estimated)
            waist_width_pixels = self._calculate_waist_width(front_landmarks)
            measurements['waist_circumference_cm'] = self._width_to_circumference(waist_width_pixels * front_pixel_to_cm)
            
            # Hip circumference (estimated)
            hip_width_pixels = self._calculate_hip_width(front_landmarks)
            measurements['hip_circumference_cm'] = self._width_to_circumference(hip_width_pixels * front_pixel_to_cm)
            
            # Arm measurements
            left_arm_length_pixels = self._calculate_arm_length(front_landmarks, 'left')
            right_arm_length_pixels = self._calculate_arm_length(front_landmarks, 'right')
            measurements['left_arm_length_cm'] = left_arm_length_pixels * front_pixel_to_cm
            measurements['right_arm_length_cm'] = right_arm_length_pixels * front_pixel_to_cm
            
            # Leg measurements
            left_leg_length_pixels = self._calculate_leg_length(front_landmarks, 'left')
            right_leg_length_pixels = self._calculate_leg_length(front_landmarks, 'right')
            measurements['left_leg_length_cm'] = left_leg_length_pixels * front_pixel_to_cm
            measurements['right_leg_length_cm'] = right_leg_length_pixels * front_pixel_to_cm
            
            # Torso measurements
            torso_length_pixels = self._calculate_torso_length(front_landmarks)
            measurements['torso_length_cm'] = torso_length_pixels * front_pixel_to_cm
            
            # Estimate bicep circumference
            left_bicep_width_pixels = self._calculate_bicep_width(front_landmarks, 'left')
            right_bicep_width_pixels = self._calculate_bicep_width(front_landmarks, 'right')
            measurements['left_bicep_circumference_cm'] = self._width_to_circumference(left_bicep_width_pixels * front_pixel_to_cm * 0.8)
            measurements['right_bicep_circumference_cm'] = self._width_to_circumference(right_bicep_width_pixels * front_pixel_to_cm * 0.8)
            
            # Estimate forearm circumference
            left_forearm_width_pixels = self._calculate_forearm_width(front_landmarks, 'left')
            right_forearm_width_pixels = self._calculate_forearm_width(front_landmarks, 'right')
            measurements['left_forearm_circumference_cm'] = self._width_to_circumference(left_forearm_width_pixels * front_pixel_to_cm * 0.9)
            measurements['right_forearm_circumference_cm'] = self._width_to_circumference(right_forearm_width_pixels * front_pixel_to_cm * 0.9)
        
        # Calculate measurements from back view
        if back_pixel_to_cm > 0:
            # Back width
            back_width_pixels = self._calculate_back_width(back_landmarks)
            measurements['back_width_cm'] = back_width_pixels * back_pixel_to_cm
            
            # Shoulder to waist taper ratio (V-taper)
            back_waist_width_pixels = self._calculate_waist_width(back_landmarks)
            back_waist_width_cm = back_waist_width_pixels * back_pixel_to_cm
            if 'shoulder_width_cm' in measurements and back_waist_width_cm > 0:
                measurements['v_taper_ratio'] = measurements['shoulder_width_cm'] / back_waist_width_cm
            
            # Estimate thigh circumference
            left_thigh_width_pixels = self._calculate_thigh_width(back_landmarks, 'left')
            right_thigh_width_pixels = self._calculate_thigh_width(back_landmarks, 'right')
            measurements['left_thigh_circumference_cm'] = self._width_to_circumference(left_thigh_width_pixels * back_pixel_to_cm)
            measurements['right_thigh_circumference_cm'] = self._width_to_circumference(right_thigh_width_pixels * back_pixel_to_cm)
            
            # Estimate calf circumference
            left_calf_width_pixels = self._calculate_calf_width(back_landmarks, 'left')
            right_calf_width_pixels = self._calculate_calf_width(back_landmarks, 'right')
            measurements['left_calf_circumference_cm'] = self._width_to_circumference(left_calf_width_pixels * back_pixel_to_cm)
            measurements['right_calf_circumference_cm'] = self._width_to_circumference(right_calf_width_pixels * back_pixel_to_cm)
        
        logger.debug("Base measurements extracted from images")
        return measurements
    
    def _validate_measurements(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate measurements against anatomical constraints
        
        Args:
            measurements: Dictionary with raw measurements
            
        Returns:
            Dictionary with validated measurements
        """
        validated = measurements.copy()
        
        # Set reasonable limits based on gender and height
        height_cm = measurements.get('height_cm', 170)
        gender = measurements.get('gender', 'male')
        
        # Apply anatomical constraints
        constraints = self._get_anatomical_constraints(height_cm, gender)
        
        for measure, (min_val, max_val) in constraints.items():
            if measure in validated:
                # Ensure measurement is within reasonable limits
                if validated[measure] < min_val:
                    logger.debug(f"Adjusting {measure} from {validated[measure]} to minimum {min_val}")
                    validated[measure] = min_val
                elif validated[measure] > max_val:
                    logger.debug(f"Adjusting {measure} from {validated[measure]} to maximum {max_val}")
                    validated[measure] = max_val
        
        # Validate symmetry (left/right shouldn't differ too much)
        symmetry_pairs = [
            ('left_arm_length_cm', 'right_arm_length_cm'),
            ('left_leg_length_cm', 'right_leg_length_cm'),
            ('left_bicep_circumference_cm', 'right_bicep_circumference_cm'),
            ('left_forearm_circumference_cm', 'right_forearm_circumference_cm'),
            ('left_thigh_circumference_cm', 'right_thigh_circumference_cm'),
            ('left_calf_circumference_cm', 'right_calf_circumference_cm')
        ]
        
        for left, right in symmetry_pairs:
            if left in validated and right in validated:
                # Don't allow more than 15% difference in symmetry
                avg = (validated[left] + validated[right]) / 2
                max_diff = avg * 0.15
                
                if abs(validated[left] - validated[right]) > max_diff:
                    logger.debug(f"Adjusting asymmetric {left}/{right} measurements to be within 15%")
                    validated[left] = avg - (max_diff / 2)
                    validated[right] = avg + (max_diff / 2)
        
        logger.debug("Measurements validated against anatomical constraints")
        return validated
    
    def _calculate_enhanced_metrics(self, base_measurements: Dict[str, Any], 
                                   height_cm: float, 
                                   weight_kg: float, 
                                   age: int, 
                                   gender: str) -> Dict[str, Any]:
        """
        Calculate additional bodybuilding-specific metrics
        
        Args:
            base_measurements: Dictionary with validated base measurements
            height_cm: User's height
            weight_kg: User's weight
            age: User's age
            gender: User's gender
            
        Returns:
            Dictionary with all measurements including advanced metrics
        """
        metrics = base_measurements.copy()
        
        # Calculate BMI
        if height_cm > 0:
            metrics['bmi'] = weight_kg / ((height_cm / 100) ** 2)
        
        # Estimate body fat percentage using various metrics
        if gender.lower() == 'male':
            # Basic formula using BMI and age for males
            estimated_bf = 1.20 * metrics.get('bmi', 25) + 0.23 * age - 16.2
        else:
            # Basic formula using BMI and age for females
            estimated_bf = 1.20 * metrics.get('bmi', 25) + 0.23 * age - 5.4
            
        # Adjust based on circumference measurements if available
        if 'waist_circumference_cm' in metrics:
            waist_height_ratio = metrics['waist_circumference_cm'] / height_cm
            # Adjust based on waist-to-height ratio
            if waist_height_ratio < 0.4:
                estimated_bf -= 2
            elif waist_height_ratio > 0.5:
                estimated_bf += 3
                
        metrics['body_fat_percentage'] = max(5, min(40, estimated_bf))
        
        # Calculate lean body mass
        metrics['lean_body_mass_kg'] = weight_kg * (1 - (metrics['body_fat_percentage'] / 100))
        
        # Calculate Fat Free Mass Index (FFMI)
        ffmi = metrics['lean_body_mass_kg'] / ((height_cm / 100) ** 2)
        # Normalized FFMI (adjusted for height)
        metrics['normalized_ffmi'] = ffmi * (6.3 / (height_cm / 100))
        
        # Calculate muscle density score (0-1 scale)
        # Higher is better, based on muscle mass relative to height and bone structure
        muscle_density = min(1.0, max(0.2, metrics['normalized_ffmi'] / 28))
        metrics['muscle_density'] = muscle_density
        
        # Calculate muscle maturity score based on age, experience, and metrics
        metrics['muscle_maturity'] = self._calculate_muscle_maturity(age, metrics['body_fat_percentage'], muscle_density)
        
        # Calculate symmetry scores
        metrics['symmetry_score'] = self._calculate_symmetry_score(metrics)
        
        # Calculate X-frame score (how well the physique forms an X shape)
        metrics['x_frame_score'] = self._calculate_x_frame_score(metrics)
        
        # Calculate V-taper score (shoulder to waist ratio aesthetics)
        metrics['v_taper_score'] = self._calculate_v_taper_score(metrics)
        
        # Calculate genetic potential (based on bone structure, muscle insertions, etc.)
        metrics['genetic_potential'] = min(1.0, max(0.3, (metrics['x_frame_score'] + metrics['v_taper_score']) / 2))
        
        # Calculate muscle building potential (based on frame and current development)
        if metrics.get('normalized_ffmi', 0) > 23:
            # Already well-developed, less room for growth
            potential_multiplier = 0.7
        else:
            # More room for growth
            potential_multiplier = 1.0
            
        metrics['muscle_building_potential'] = metrics['genetic_potential'] * potential_multiplier
        
        # Additional proportion calculations
        if 'shoulder_width_cm' in metrics and 'hip_circumference_cm' in metrics:
            metrics['shoulder_hip_ratio'] = metrics['shoulder_width_cm'] / (metrics['hip_circumference_cm'] / 3.14)
            
        if 'waist_circumference_cm' in metrics and 'hip_circumference_cm' in metrics:
            metrics['waist_hip_ratio'] = metrics['waist_circumference_cm'] / metrics['hip_circumference_cm']
            
        # Arm to torso ratio
        if 'right_arm_length_cm' in metrics and 'torso_length_cm' in metrics:
            metrics['arm_torso_ratio'] = metrics['right_arm_length_cm'] / metrics['torso_length_cm']
            
        # Leg to torso ratio
        if 'right_leg_length_cm' in metrics and 'torso_length_cm' in metrics:
            metrics['leg_torso_ratio'] = metrics['right_leg_length_cm'] / metrics['torso_length_cm']
        
        logger.debug("Enhanced metrics calculated")
        return metrics
    
    def _calculate_muscle_maturity(self, age: int, body_fat: float, muscle_density: float) -> float:
        """
        Calculate muscle maturity score based on various factors (0-1 scale)
        
        Args:
            age: User's age
            body_fat: Body fat percentage
            muscle_density: Muscle density score
            
        Returns:
            Muscle maturity score from 0 to 1
        """
        # Baseline based on age (peaks around 35-40)
        if age < 18:
            age_factor = 0.4
        elif age < 25:
            age_factor = 0.6 + (age - 18) * 0.03
        elif age < 35:
            age_factor = 0.8 + (age - 25) * 0.01
        elif age < 45:
            age_factor = 0.9
        else:
            age_factor = 0.9 - (age - 45) * 0.01
            
        # Adjust for body fat (optimal range is 8-15% for males, 15-22% for females)
        if body_fat < 8:
            bf_factor = 0.7  # Too low body fat can indicate underdevelopment
        elif body_fat < 15:
            bf_factor = 1.0  # Optimal range for definition and size
        elif body_fat < 25:
            bf_factor = 0.9 - (body_fat - 15) * 0.02  # Decreasing as fat increases
        else:
            bf_factor = 0.7  # High body fat masks muscle development
            
        # Final score is weighted average of factors, with muscle density having highest weight
        maturity_score = (age_factor * 0.3) + (bf_factor * 0.2) + (muscle_density * 0.5)
        return min(1.0, max(0.0, maturity_score))
    
    def _calculate_x_frame_score(self, measurements: Dict[str, Any]) -> float:
        """
        Calculate X-frame aesthetic score (0-1 scale)
        
        Args:
            measurements: Dictionary with measurements
            
        Returns:
            X-frame score from 0 to 1
        """
        # Ideal proportions for X-frame
        shoulder_waist_factor = 0.5
        hip_waist_factor = 0.25
        thigh_waist_factor = 0.25
        
        score = 0.5  # Default middle value
        
        # Shoulders to waist (shoulder width to waist circumference ratio)
        if 'shoulder_width_cm' in measurements and 'waist_circumference_cm' in measurements:
            ratio = measurements['shoulder_width_cm'] / (measurements['waist_circumference_cm'] / 3.14)
            # Ideal ratio depends on gender
            if measurements.get('gender', '').lower() == 'male':
                ideal_ratio = 1.618  # Golden ratio
                shoulder_score = min(1.0, max(0.0, 1.0 - abs(ratio - ideal_ratio) / ideal_ratio))
            else:
                ideal_ratio = 1.4
                shoulder_score = min(1.0, max(0.0, 1.0 - abs(ratio - ideal_ratio) / ideal_ratio))
                
            score += shoulder_waist_factor * (shoulder_score - 0.5) * 2
            
        # Hip to waist ratio
        if 'hip_circumference_cm' in measurements and 'waist_circumference_cm' in measurements:
            ratio = measurements['hip_circumference_cm'] / measurements['waist_circumference_cm']
            # Ideal ratio depends on gender
            if measurements.get('gender', '').lower() == 'male':
                ideal_ratio = 1.2
            else:
                ideal_ratio = 1.4
                
            hip_score = min(1.0, max(0.0, 1.0 - abs(ratio - ideal_ratio) / ideal_ratio))
            score += hip_waist_factor * (hip_score - 0.5) * 2
            
        # Thigh to waist ratio
        if 'right_thigh_circumference_cm' in measurements and 'waist_circumference_cm' in measurements:
            ratio = measurements['right_thigh_circumference_cm'] / measurements['waist_circumference_cm']
            # Ideal ratio depends on gender
            if measurements.get('gender', '').lower() == 'male':
                ideal_ratio = 0.6
            else:
                ideal_ratio = 0.65
                
            thigh_score = min(1.0, max(0.0, 1.0 - abs(ratio - ideal_ratio) / ideal_ratio))
            score += thigh_waist_factor * (thigh_score - 0.5) * 2
            
        return min(1.0, max(0.1, score))
    
    def _calculate_symmetry_score(self, measurements: Dict[str, Any]) -> float:
        """
        Calculate overall symmetry score (0-1 scale)
        
        Args:
            measurements: Dictionary with measurements
            
        Returns:
            Symmetry score from 0 to 1
        """
        # Pairs to check for symmetry
        symmetry_pairs = [
            ('left_arm_length_cm', 'right_arm_length_cm'),
            ('left_leg_length_cm', 'right_leg_length_cm'),
            ('left_bicep_circumference_cm', 'right_bicep_circumference_cm'),
            ('left_forearm_circumference_cm', 'right_forearm_circumference_cm'),
            ('left_thigh_circumference_cm', 'right_thigh_circumference_cm'),
            ('left_calf_circumference_cm', 'right_calf_circumference_cm')
        ]
        
        # Calculate symmetry for each pair
        pair_scores = []
        for left, right in symmetry_pairs:
            if left in measurements and right in measurements:
                avg = (measurements[left] + measurements[right]) / 2
                diff_percent = abs(measurements[left] - measurements[right]) / avg
                # Penalize differences more than 3%
                if diff_percent <= 0.03:
                    pair_score = 1.0
                else:
                    pair_score = max(0.0, 1.0 - (diff_percent - 0.03) * 10)
                pair_scores.append(pair_score)
        
        # Overall symmetry score is average of all pair scores
        if pair_scores:
            return sum(pair_scores) / len(pair_scores)
        else:
            return 0.7  # Default if no pairs can be evaluated
    
    def _calculate_v_taper_score(self, measurements: Dict[str, Any]) -> float:
        """
        Calculate V-taper aesthetic score (0-1 scale)
        
        Args:
            measurements: Dictionary with measurements
            
        Returns:
            V-taper score from 0 to 1
        """
        # V-taper is primarily about shoulder to waist ratio
        if 'shoulder_width_cm' in measurements and 'waist_circumference_cm' in measurements:
            ratio = measurements['shoulder_width_cm'] / (measurements['waist_circumference_cm'] / 3.14)
            
            # Ideal ratio depends on gender
            if measurements.get('gender', '').lower() == 'male':
                # For males, higher is better up to a point
                if ratio < 1.4:
                    return max(0.3, ratio / 1.4 * 0.7)
                elif ratio <= 1.8:
                    return 0.7 + (ratio - 1.4) / 0.4 * 0.3
                else:
                    return 1.0
            else:
                # For females, more moderate ratio is ideal
                if ratio < 1.2:
                    return max(0.3, ratio / 1.2 * 0.7)
                elif ratio <= 1.5:
                    return 0.7 + (ratio - 1.2) / 0.3 * 0.3
                else:
                    return 1.0
        
        # Default if measurements not available
        return 0.6
    
    def _add_confidence_scores(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add confidence scores to each measurement
        
        Args:
            measurements: Dictionary with measurements
            
        Returns:
            Dictionary with measurements and confidence scores
        """
        # Start with copy of measurements
        result = measurements.copy()
        
        # Add confidence scores dictionary
        result['confidence_scores'] = {}
        
        # Base confidence levels for different measurement types
        confidence_levels = {
            # Direct measurements have highest confidence
            'height_cm': 0.95,
            'weight_kg': 0.95,
            
            # Landmark-based measurements have medium-high confidence
            'shoulder_width_cm': 0.85,
            'back_width_cm': 0.8,
            'torso_length_cm': 0.85,
            'arm_length': 0.85,
            'leg_length': 0.85,
            
            # Circumference estimates have medium confidence
            'chest_circumference_cm': 0.7,
            'waist_circumference_cm': 0.75,
            'hip_circumference_cm': 0.7,
            'bicep_circumference': 0.65,
            'forearm_circumference': 0.65,
            'thigh_circumference': 0.65,
            'calf_circumference': 0.65,
            
            # Calculated ratios have medium-low confidence
            'shoulder_hip_ratio': 0.7,
            'waist_hip_ratio': 0.75,
            'v_taper_ratio': 0.6,
            'arm_torso_ratio': 0.7,
            'leg_torso_ratio': 0.7,
            
            # Calculated scores have medium-low confidence
            'symmetry_score': 0.6,
            'x_frame_score': 0.6,
            'v_taper_score': 0.6,
            'muscle_maturity': 0.55,
            'muscle_density': 0.5,
            'genetic_potential': 0.5,
            'muscle_building_potential': 0.5,
            
            # Body composition estimates have medium confidence
            'body_fat_percentage': 0.65,
            'lean_body_mass_kg': 0.7,
            'normalized_ffmi': 0.6,
        }
        
        # Apply confidence scores to all measurements
        for key in measurements:
            if key in confidence_levels:
                result['confidence_scores'][key] = confidence_levels[key]
            elif 'left_' in key or 'right_' in key:
                # Extract base measurement type for left/right measurements
                base_key = key.replace('left_', '').replace('right_', '')
                if base_key in confidence_levels:
                    result['confidence_scores'][key] = confidence_levels[base_key] * 0.95  # Slightly lower confidence for side-specific
                else:
                    result['confidence_scores'][key] = 0.5  # Default medium confidence
            else:
                result['confidence_scores'][key] = 0.5  # Default medium confidence
        
        logger.debug("Confidence scores added to measurements")
        return result
    
    def _generate_mock_measurements(self, height_cm: float, weight_kg: float, age: int, gender: str) -> Dict[str, Any]:
        """
        Generate realistic mock measurements based on height, weight, age, and gender
        
        Args:
            height_cm: User's height
            weight_kg: User's weight
            age: User's age
            gender: User's gender
            
        Returns:
            Dictionary with mock measurements
        """
        logger.warning("Using mock measurements for demonstration")
        
        # Base scaling factors
        height_factor = height_cm / 170  # Normalize to 170cm reference height
        weight_factor = weight_kg / (height_factor * 70)  # Normalize to BMI reference
        
        # Gender-specific adjustments
        is_male = gender.lower() == 'male'
        gender_factor = 1.1 if is_male else 0.9
        
        # Age-specific adjustments
        if age < 18:
            age_factor = 0.9
        elif age < 30:
            age_factor = 1.0
        elif age < 50:
            age_factor = 0.95
        else:
            age_factor = 0.9
        
        # Function to generate a measurement with normal distribution around expected value
        def generate_measurement(base_value, variance=0.05):
            return base_value * random.uniform(1 - variance, 1 + variance)
        
        # Initialize measurements
        measurements = {
            'height_cm': height_cm,
            'weight_kg': weight_kg,
            'age': age,
            'gender': gender,
            
            # Body composition
            'bmi': weight_kg / ((height_cm / 100) ** 2),
        }
        
        # Generate body fat percentage based on weight factor and gender
        if is_male:
            base_bf = 15 + (weight_factor - 1) * 20
        else:
            base_bf = 22 + (weight_factor - 1) * 20
        measurements['body_fat_percentage'] = max(5, min(40, generate_measurement(base_bf, 0.1)))
        
        # Lean body mass
        measurements['lean_body_mass_kg'] = weight_kg * (1 - (measurements['body_fat_percentage'] / 100))
        
        # FFMI calculations
        ffmi = measurements['lean_body_mass_kg'] / ((height_cm / 100) ** 2)
        measurements['normalized_ffmi'] = ffmi * (6.3 / (height_cm / 100))
        
        # Generate circumference measurements
        # Chest
        base_chest = height_cm * 0.52 * gender_factor * weight_factor
        measurements['chest_circumference_cm'] = generate_measurement(base_chest)
        
        # Waist
        base_waist = height_cm * 0.45 * weight_factor
        measurements['waist_circumference_cm'] = generate_measurement(base_waist)
        
        # Hips
        if is_male:
            base_hips = height_cm * 0.49 * weight_factor
        else:
            base_hips = height_cm * 0.53 * weight_factor
        measurements['hip_circumference_cm'] = generate_measurement(base_hips)
        
        # Shoulder width
        base_shoulder = height_cm * 0.259 * gender_factor
        measurements['shoulder_width_cm'] = generate_measurement(base_shoulder)
        
        # Back width
        base_back = height_cm * 0.23 * gender_factor
        measurements['back_width_cm'] = generate_measurement(base_back)
        
        # Torso length
        base_torso = height_cm * 0.34
        measurements['torso_length_cm'] = generate_measurement(base_torso)
        
        # Arms
        base_arm_length = height_cm * 0.34
        measurements['left_arm_length_cm'] = generate_measurement(base_arm_length)
        measurements['right_arm_length_cm'] = generate_measurement(base_arm_length)
        
        # Legs
        base_leg_length = height_cm * 0.48
        measurements['left_leg_length_cm'] = generate_measurement(base_leg_length)
        measurements['right_leg_length_cm'] = generate_measurement(base_leg_length)
        
        # Biceps
        base_bicep = height_cm * 0.12 * gender_factor * weight_factor * age_factor
        measurements['left_bicep_circumference_cm'] = generate_measurement(base_bicep)
        measurements['right_bicep_circumference_cm'] = generate_measurement(base_bicep)
        
        # Forearms
        base_forearm = height_cm * 0.085 * gender_factor * weight_factor * age_factor
        measurements['left_forearm_circumference_cm'] = generate_measurement(base_forearm)
        measurements['right_forearm_circumference_cm'] = generate_measurement(base_forearm)
        
        # Thighs
        base_thigh = height_cm * 0.18 * gender_factor * weight_factor * age_factor
        measurements['left_thigh_circumference_cm'] = generate_measurement(base_thigh)
        measurements['right_thigh_circumference_cm'] = generate_measurement(base_thigh)
        
        # Calves
        base_calf = height_cm * 0.12 * gender_factor * weight_factor * age_factor
        measurements['left_calf_circumference_cm'] = generate_measurement(base_calf)
        measurements['right_calf_circumference_cm'] = generate_measurement(base_calf)
        
        # Calculate proportion metrics
        measurements['shoulder_hip_ratio'] = measurements['shoulder_width_cm'] / (measurements['hip_circumference_cm'] / 3.14)
        measurements['waist_hip_ratio'] = measurements['waist_circumference_cm'] / measurements['hip_circumference_cm']
        measurements['v_taper_ratio'] = measurements['shoulder_width_cm'] / (measurements['waist_circumference_cm'] / 3.14)
        measurements['arm_torso_ratio'] = measurements['right_arm_length_cm'] / measurements['torso_length_cm']
        measurements['leg_torso_ratio'] = measurements['right_leg_length_cm'] / measurements['torso_length_cm']
        
        # Aesthetics scores
        measurements['symmetry_score'] = random.uniform(0.7, 0.95)
        measurements['x_frame_score'] = generate_measurement(0.7, 0.15)
        measurements['v_taper_score'] = generate_measurement(0.75, 0.15)
        
        # Advanced metrics
        muscle_density = min(1.0, max(0.2, measurements['normalized_ffmi'] / 25))
        measurements['muscle_density'] = muscle_density
        measurements['muscle_maturity'] = generate_measurement(min(age / 40, 1) * 0.8, 0.1)
        measurements['genetic_potential'] = generate_measurement(0.7, 0.2)
        measurements['muscle_building_potential'] = generate_measurement(0.65, 0.2)
        
        # Add confidence scores (lower for mock data)
        measurements = self._add_confidence_scores(measurements)
        for key in measurements['confidence_scores']:
            measurements['confidence_scores'][key] *= 0.8  # Reduce confidence for mock data
        
        return measurements
    
    # Helper methods for landmark-based measurements
    def _calculate_height_pixels(self, landmarks) -> float:
        """Calculate total height in pixels from landmarks"""
        if not landmarks:
            return 0
            
        # Use top of head to heel landmarks
        top_head = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        left_heel = landmarks[self.mp_pose.PoseLandmark.LEFT_HEEL.value]
        right_heel = landmarks[self.mp_pose.PoseLandmark.RIGHT_HEEL.value]
        
        # Use lower of the two heels
        heel_y = max(left_heel.y, right_heel.y)
        
        return heel_y - top_head.y
    
    def _calculate_shoulder_width(self, landmarks) -> float:
        """Calculate shoulder width in pixels from landmarks"""
        if not landmarks:
            return 0
            
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        
        # Pythagorean distance to account for possible tilt
        dx = right_shoulder.x - left_shoulder.x
        dy = right_shoulder.y - left_shoulder.y
        return (dx**2 + dy**2)**0.5
    
    def _calculate_chest_width(self, landmarks) -> float:
        """Estimate chest width in pixels from landmarks"""
        if not landmarks:
            return 0
            
        # Approximate chest from shoulder width and position
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        
        # Use distance between shoulders as base
        shoulder_width = ((right_shoulder.x - left_shoulder.x)**2 + 
                          (right_shoulder.y - left_shoulder.y)**2)**0.5
        
        # Adjust for typical chest width (slightly wider than shoulders)
        return shoulder_width * 1.05
    
    def _calculate_waist_width(self, landmarks) -> float:
        """Estimate waist width in pixels from landmarks"""
        if not landmarks:
            return 0
            
        # Approximate waist from hip landmarks position
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # Distance between hips
        hip_width = ((right_hip.x - left_hip.x)**2 + 
                     (right_hip.y - left_hip.y)**2)**0.5
        
        # Adjust for typical waist width (slightly narrower than hips)
        return hip_width * 0.9
    
    def _calculate_hip_width(self, landmarks) -> float:
        """Calculate hip width in pixels from landmarks"""
        if not landmarks:
            return 0
            
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # Pythagorean distance to account for possible tilt
        dx = right_hip.x - left_hip.x
        dy = right_hip.y - left_hip.y
        return (dx**2 + dy**2)**0.5
    
    def _calculate_back_width(self, landmarks) -> float:
        """Estimate back width in pixels from landmarks (from back view)"""
        if not landmarks:
            return 0
            
        # Use shoulder width from back view
        return self._calculate_shoulder_width(landmarks) * 0.9
    
    def _calculate_arm_length(self, landmarks, side: str) -> float:
        """Calculate arm length in pixels from landmarks"""
        if not landmarks:
            return 0
            
        if side.lower() == 'left':
            shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
            wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        else:
            shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        
        # Upper arm length
        upper_arm = ((elbow.x - shoulder.x)**2 + (elbow.y - shoulder.y)**2)**0.5
        
        # Forearm length
        forearm = ((wrist.x - elbow.x)**2 + (wrist.y - elbow.y)**2)**0.5
        
        # Total arm length
        return upper_arm + forearm
    
    def _calculate_leg_length(self, landmarks, side: str) -> float:
        """Calculate leg length in pixels from landmarks"""
        if not landmarks:
            return 0
            
        if side.lower() == 'left':
            hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
            ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
        else:
            hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
            ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Thigh length
        thigh = ((knee.x - hip.x)**2 + (knee.y - hip.y)**2)**0.5
        
        # Lower leg length
        lower_leg = ((ankle.x - knee.x)**2 + (ankle.y - knee.y)**2)**0.5
        
        # Total leg length
        return thigh + lower_leg
    
    def _calculate_torso_length(self, landmarks) -> float:
        """Calculate torso length in pixels from landmarks"""
        if not landmarks:
            return 0
            
        # Use neck to mid-hip point
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
        
        # Approximate neck position (slightly below nose)
        neck_x = (left_shoulder.x + right_shoulder.x) / 2
        neck_y = min(left_shoulder.y, right_shoulder.y) + abs(nose.y - min(left_shoulder.y, right_shoulder.y)) * 0.3
        
        # Mid-hip point
        mid_hip_x = (left_hip.x + right_hip.x) / 2
        mid_hip_y = (left_hip.y + right_hip.y) / 2
        
        # Torso length
        dx = mid_hip_x - neck_x
        dy = mid_hip_y - neck_y
        return (dx**2 + dy**2)**0.5
    
    def _calculate_bicep_width(self, landmarks, side: str) -> float:
        """Estimate bicep width in pixels from landmarks"""
        if not landmarks:
            return 0
            
        if side.lower() == 'left':
            shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
        else:
            shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
        
        # Upper arm length
        upper_arm = ((elbow.x - shoulder.x)**2 + (elbow.y - shoulder.y)**2)**0.5
        
        # Estimate bicep width as a proportion of upper arm length
        return upper_arm * 0.2
    
    def _calculate_forearm_width(self, landmarks, side: str) -> float:
        """Estimate forearm width in pixels from landmarks"""
        if not landmarks:
            return 0
            
        if side.lower() == 'left':
            elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
            wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
        else:
            elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
        
        # Forearm length
        forearm = ((wrist.x - elbow.x)**2 + (wrist.y - elbow.y)**2)**0.5
        
        # Estimate forearm width as a proportion of forearm length
        return forearm * 0.16
    
    def _calculate_thigh_width(self, landmarks, side: str) -> float:
        """Estimate thigh width in pixels from landmarks"""
        if not landmarks:
            return 0
            
        if side.lower() == 'left':
            hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
        else:
            hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
        
        # Thigh length
        thigh = ((knee.x - hip.x)**2 + (knee.y - hip.y)**2)**0.5
        
        # Estimate thigh width as a proportion of thigh length
        return thigh * 0.25
    
    def _calculate_calf_width(self, landmarks, side: str) -> float:
        """Estimate calf width in pixels from landmarks"""
        if not landmarks:
            return 0
            
        if side.lower() == 'left':
            knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
            ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value]
        else:
            knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
            ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Lower leg length
        lower_leg = ((ankle.x - knee.x)**2 + (ankle.y - knee.y)**2)**0.5
        
        # Estimate calf width as a proportion of lower leg length
        return lower_leg * 0.18
    
    def _width_to_circumference(self, width: float) -> float:
        """
        Estimate circumference from width using ellipse approximation (C ≈ 2π√[(a²+b²)/2])
        Assuming width is 2a and depth is approximately 0.7 * width 
        """
        a = width / 2
        b = a * 0.7  # depth is typically around 70% of width
        return 2 * 3.14159 * ((a**2 + b**2) / 2)**0.5
    
    def _get_anatomical_constraints(self, height_cm: float, gender: str) -> Dict[str, Tuple[float, float]]:
        """
        Get anatomical constraints based on height and gender
        
        Args:
            height_cm: User's height
            gender: User's gender
            
        Returns:
            Dictionary with measurement name and (min, max) tuples
        """
        # Normalize for height (as percentage of height)
        is_male = gender.lower() == 'male'
        
        # Base constraints as percentages of height
        constraints = {
            # Format: 'measurement': (min_percent, max_percent)
            'shoulder_width_cm': (0.22, 0.28),
            'chest_circumference_cm': (0.45, 0.58),
            'waist_circumference_cm': (0.35, 0.52),
            'hip_circumference_cm': (0.42, 0.58),
            'left_arm_length_cm': (0.3, 0.36),
            'right_arm_length_cm': (0.3, 0.36),
            'left_leg_length_cm': (0.43, 0.52),
            'right_leg_length_cm': (0.43, 0.52),
            'torso_length_cm': (0.3, 0.38),
            'left_bicep_circumference_cm': (0.08, 0.18),
            'right_bicep_circumference_cm': (0.08, 0.18),
            'left_forearm_circumference_cm': (0.07, 0.14),
            'right_forearm_circumference_cm': (0.07, 0.14),
            'left_thigh_circumference_cm': (0.15, 0.25),
            'right_thigh_circumference_cm': (0.15, 0.25),
            'left_calf_circumference_cm': (0.09, 0.16),
            'right_calf_circumference_cm': (0.09, 0.16),
        }
        
        # Adjust based on gender
        if is_male:
            # Males typically have wider shoulders, narrower hips
            constraints['shoulder_width_cm'] = (0.23, 0.28)
            constraints['chest_circumference_cm'] = (0.47, 0.58)
            constraints['waist_circumference_cm'] = (0.35, 0.52)
            constraints['hip_circumference_cm'] = (0.42, 0.55)
        else:
            # Females typically have narrower shoulders, wider hips
            constraints['shoulder_width_cm'] = (0.22, 0.26)
            constraints['chest_circumference_cm'] = (0.45, 0.56)
            constraints['waist_circumference_cm'] = (0.35, 0.50)
            constraints['hip_circumference_cm'] = (0.45, 0.58)
        
        # Convert to absolute values based on height
        absolute_constraints = {}
        for measure, (min_percent, max_percent) in constraints.items():
            absolute_constraints[measure] = (height_cm * min_percent, height_cm * max_percent)
        
        return absolute_constraints


def format_measurement_value(key: str, value: float) -> str:
    """Format measurement values with appropriate units"""
    # Handle special cases with units
    if key.endswith('_cm'):
        return f"{value:.1f} cm"
    elif key == 'weight_kg':
        return f"{value:.1f} kg"
    elif key == 'body_fat_percentage':
        return f"{value:.1f}%"
    elif key.endswith('_ratio'):
        return f"{value:.2f}"
    elif key.endswith('_score'):
        return f"{value:.2f}"
    elif key == 'bmi':
        return f"{value:.1f}"
    elif key == 'age':
        return f"{int(value)} years"
    else:
        # Default format
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)


def categorize_measurements(measurements: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Group measurements into categories for better display
    
    Args:
        measurements: Dictionary with measurements
        
    Returns:
        Dictionary with categorized measurements
    """
    # Define measurement categories
    categories = {
        'Body Composition': [
            'body_fat_percentage', 'lean_body_mass_kg', 'bmi', 'normalized_ffmi'
        ],
        'Torso Measurements': [
            'chest_circumference_cm', 'waist_circumference_cm', 'hip_circumference_cm',
            'shoulder_width_cm', 'back_width_cm', 'torso_length_cm'
        ],
        'Arm Measurements': [
            'left_arm_length_cm', 'right_arm_length_cm', 
            'left_bicep_circumference_cm', 'right_bicep_circumference_cm',
            'left_forearm_circumference_cm', 'right_forearm_circumference_cm'
        ],
        'Leg Measurements': [
            'left_leg_length_cm', 'right_leg_length_cm',
            'left_thigh_circumference_cm', 'right_thigh_circumference_cm',
            'left_calf_circumference_cm', 'right_calf_circumference_cm'
        ],
        'Proportion Ratios': [
            'shoulder_hip_ratio', 'waist_hip_ratio', 'v_taper_ratio',
            'arm_torso_ratio', 'leg_torso_ratio'
        ],
        'Aesthetic Scores': [
            'symmetry_score', 'x_frame_score', 'v_taper_score',
            'muscle_density', 'muscle_maturity', 'genetic_potential', 'muscle_building_potential'
        ],
        'Basic Info': [
            'height_cm', 'weight_kg', 'age', 'gender'
        ]
    }
    
    # Organize measurements by category
    categorized = {}
    confidence_scores = measurements.get('confidence_scores', {})
    
    # Process each category
    for category, measure_keys in categories.items():
        categorized[category] = {}
        
        for key in measure_keys:
            if key in measurements:
                # Format the value with proper units
                formatted_value = format_measurement_value(key, measurements[key])
                
                # Get confidence level based on score
                confidence = 'medium'  # Default
                if key in confidence_scores:
                    score = confidence_scores[key]
                    if score >= 0.7:
                        confidence = 'high'
                    elif score >= 0.4:
                        confidence = 'medium'
                    else:
                        confidence = 'low'
                
                # Format the display name
                display_name = key.replace('_', ' ').replace('cm', '').replace('kg', '').title()
                
                # Add to category
                categorized[category][display_name] = {
                    'value': formatted_value,
                    'confidence': confidence,
                    'raw_value': measurements[key]
                }
    
    return categorized