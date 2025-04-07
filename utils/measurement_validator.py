import logging
import numpy as np
from typing import Dict, Tuple, List, Union, Optional

# Configure logging
logger = logging.getLogger(__name__)

class AnatomicalConstraints:
    """Defines anatomical constraints for body measurements"""
    
    # Male constraints for various body measurements as a percentage of height
    # Each tuple represents (min, max) percentage of height
    MALE_CONSTRAINTS = {
        'shoulder_width': (0.23, 0.28),     # Shoulder width typically 23-28% of height
        'chest_width': (0.20, 0.25),        # Chest width typically 20-25% of height
        'waist_width': (0.14, 0.18),        # Waist width typically 14-18% of height
        'hip_width': (0.17, 0.21),          # Hip width typically 17-21% of height
        'neck_circumference': (0.20, 0.24),  # Neck circumference typically 20-24% of height
        'arm_length': (0.43, 0.47),         # Arm length typically 43-47% of height
        'leg_length': (0.47, 0.52),         # Leg length typically 47-52% of height
        'torso_length': (0.28, 0.32),       # Torso length typically 28-32% of height
        'thigh_circumference': (0.18, 0.22), # Thigh circumference typically 18-22% of height
        'arm_circumference': (0.10, 0.13),   # Arm circumference typically 10-13% of height
    }
    
    # Female constraints for various body measurements as a percentage of height
    # Each tuple represents (min, max) percentage of height
    FEMALE_CONSTRAINTS = {
        'shoulder_width': (0.21, 0.26),     # Slightly narrower shoulders
        'chest_width': (0.19, 0.24),
        'waist_width': (0.13, 0.17),
        'hip_width': (0.18, 0.22),          # Slightly wider hips
        'neck_circumference': (0.18, 0.22),
        'arm_length': (0.43, 0.47),         # Similar arm proportions
        'leg_length': (0.47, 0.52),         # Similar leg proportions
        'torso_length': (0.28, 0.32),
        'thigh_circumference': (0.19, 0.23),
        'arm_circumference': (0.09, 0.12),
    }
    
    # Universal body ratios that apply to both genders
    # Each tuple represents (min, max) ratio
    UNIVERSAL_RATIOS = {
        'shoulder_to_waist': (1.4, 1.8),    # Shoulder-to-waist ratio
        'waist_to_hip': (0.6, 0.9),         # Waist-to-hip ratio
        'arm_to_torso': (1.4, 1.6),         # Arm length to torso length
        'leg_to_torso': (1.5, 1.8),         # Leg length to torso length
    }


class MeasurementValidator:
    """Validates and adjusts body measurements based on anatomical constraints"""
    
    def __init__(self):
        """Initialize the validator with anatomical constraints"""
        self.constraints = AnatomicalConstraints()
    
    def validate_measurements(self, 
                            measurements: Dict[str, float], 
                            height_cm: float,
                            gender: str = 'male') -> Tuple[Dict[str, float], Dict[str, str]]:
        """
        Validates measurements against anatomical constraints
        
        Args:
            measurements: Dictionary of body measurements in cm
            height_cm: Height in centimeters
            gender: 'male' or 'female'
            
        Returns:
            Tuple of (validated measurements, validation messages)
        """
        validated = measurements.copy()
        messages = {}
        
        # Select the appropriate constraints based on gender
        constraints = (self.constraints.MALE_CONSTRAINTS 
                      if gender.lower() == 'male' 
                      else self.constraints.FEMALE_CONSTRAINTS)
        
        # Validate each measurement against anatomical constraints
        for key, value in measurements.items():
            if key in constraints:
                min_pct, max_pct = constraints[key]
                min_value = min_pct * height_cm
                max_value = max_pct * height_cm
                
                # If measurement is outside constraints, adjust and log message
                if value < min_value:
                    messages[key] = f"Adjusted up (was {value:.1f}cm, min {min_value:.1f}cm)"
                    validated[key] = min_value
                elif value > max_value:
                    messages[key] = f"Adjusted down (was {value:.1f}cm, max {max_value:.1f}cm)"
                    validated[key] = max_value
                else:
                    # Measurement is within constraints
                    messages[key] = "Within normal range"
        
        # Validate ratios between measurements
        self._validate_ratios(validated, messages)
        
        return validated, messages
    
    def _validate_ratios(self, measurements: Dict[str, float], messages: Dict[str, str]):
        """Validates universal body ratios"""
        
        # Check shoulder-to-waist ratio
        if 'shoulder_width' in measurements and 'waist_width' in measurements:
            ratio = measurements['shoulder_width'] / measurements['waist_width']
            min_ratio, max_ratio = self.constraints.UNIVERSAL_RATIOS['shoulder_to_waist']
            
            if ratio < min_ratio:
                # Either shoulders are too narrow or waist too wide
                # Adjust waist width down (more favorable adjustment)
                measurements['waist_width'] = measurements['shoulder_width'] / min_ratio
                messages['waist_width'] = f"Adjusted for shoulder-to-waist ratio (now {measurements['waist_width']:.1f}cm)"
            elif ratio > max_ratio:
                # Either shoulders are too wide or waist too narrow
                # Adjust shoulders down (more favorable adjustment)
                measurements['shoulder_width'] = measurements['waist_width'] * max_ratio
                messages['shoulder_width'] = f"Adjusted for shoulder-to-waist ratio (now {measurements['shoulder_width']:.1f}cm)"
        
        # Check waist-to-hip ratio
        if 'waist_width' in measurements and 'hip_width' in measurements:
            ratio = measurements['waist_width'] / measurements['hip_width']
            min_ratio, max_ratio = self.constraints.UNIVERSAL_RATIOS['waist_to_hip']
            
            if ratio < min_ratio:
                # Waist is too narrow compared to hips
                measurements['waist_width'] = measurements['hip_width'] * min_ratio
                messages['waist_width'] = f"Adjusted for waist-to-hip ratio (now {measurements['waist_width']:.1f}cm)"
            elif ratio > max_ratio:
                # Waist is too wide compared to hips
                measurements['waist_width'] = measurements['hip_width'] * max_ratio
                messages['waist_width'] = f"Adjusted for waist-to-hip ratio (now {measurements['waist_width']:.1f}cm)"
    
    @staticmethod
    def estimate_circumference(width: float, depth_factor: float = 0.7) -> float:
        """
        Estimates circumference from width measurement
        Uses elliptical approximation: C ≈ π * sqrt((a² + b²)/2)
        where a is half the width and b is estimated depth
        """
        if width <= 0:
            return 0.0
            
        half_width = width / 2
        depth = half_width * depth_factor  # Estimate depth as a percentage of width
        
        # Approximate elliptical perimeter
        circumference = np.pi * np.sqrt((half_width**2 + depth**2) / 2)
        return circumference
    
    @staticmethod
    def normalize_coordinates(landmarks: Dict[int, Dict[str, float]], 
                            image_height: int,
                            image_width: int,
                            reference_height_cm: float) -> Dict[int, Dict[str, float]]:
        """
        Normalizes landmark coordinates to real-world measurements
        
        Args:
            landmarks: Dictionary of landmark coordinates
            image_height: Height of the image in pixels
            image_width: Width of the image in pixels
            reference_height_cm: Actual height of the person in cm
            
        Returns:
            Dictionary of normalized landmark coordinates in cm
        """
        if not landmarks or image_height <= 0 or image_width <= 0 or reference_height_cm <= 0:
            return landmarks
        
        # Calculate pixel-to-cm conversion factor based on height
        # Get y-coordinates of top (head) and bottom (feet) landmarks
        top_y = min(landmark['y'] for landmark in landmarks.values() if 'y' in landmark)
        bottom_y = max(landmark['y'] for landmark in landmarks.values() if 'y' in landmark)
        
        # Pixel height of the person in the image
        pixel_height = bottom_y - top_y
        
        # Calculate conversion factor (cm per pixel)
        cm_per_pixel = reference_height_cm / pixel_height if pixel_height > 0 else 0
        
        if cm_per_pixel <= 0:
            logger.warning("Could not calculate valid cm_per_pixel conversion factor")
            return landmarks
        
        # Create a new dictionary with normalized coordinates
        normalized = {}
        
        for idx, landmark in landmarks.items():
            normalized[idx] = landmark.copy()
            
            # Convert x and y from pixels to cm (using the person's actual height as reference)
            if 'x' in landmark:
                # Center x=0 at the middle of the body
                midline_x = image_width / 2
                x_from_center = (landmark['x'] - midline_x) * cm_per_pixel
                normalized[idx]['x'] = x_from_center
                
            if 'y' in landmark:
                # Make y=0 at the top of the head
                y_from_top = (landmark['y'] - top_y) * cm_per_pixel
                normalized[idx]['y'] = y_from_top
            
            # Scale z proportionally (z is already normalized in MediaPipe)
            if 'z' in landmark:
                normalized[idx]['z'] = landmark['z'] * reference_height_cm
        
        return normalized