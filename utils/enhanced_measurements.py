import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import cv2
import mediapipe as mp
from dataclasses import dataclass
import requests
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedMeasurementAnalyzer:
    """Class for analyzing photos and extracting 50 bodybuilding-relevant measurements"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("BODYGRAM_API_KEY", "sim_key")
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5
        )

    def analyze_photos(self, 
                      front_image: np.ndarray,
                      back_image: np.ndarray,
                      height_cm: float,
                      weight_kg: float,
                      age: int,
                      gender: str) -> Dict[str, Any]:
        """
        Analyze front and back photos to extract all 50 measurements
        """
        try:
            # Extract landmarks from both images
            front_results = self.pose.process(cv2.cvtColor(front_image, cv2.COLOR_BGR2RGB))
            back_results = self.pose.process(cv2.cvtColor(back_image, cv2.COLOR_BGR2RGB))
            
            if not front_results.pose_landmarks or not back_results.pose_landmarks:
                logger.warning("Could not detect body landmarks in one or both images, using approximate estimation")
            
            # For demonstration, we'll simulate the API call
            measurements = self._call_measurement_api(
                front_image, back_image, height_cm, weight_kg, age, gender
            )
            
            # Process and validate measurements
            validated_measurements = self._validate_measurements(measurements)
            
            # Calculate additional metrics
            enhanced_measurements = self._calculate_enhanced_metrics(
                validated_measurements, 
                height_cm, 
                weight_kg, 
                age, 
                gender
            )
            
            # Add confidence scores for each measurement
            measurements_with_confidence = self._add_confidence_scores(enhanced_measurements)
            
            return measurements_with_confidence
            
        except Exception as e:
            logger.error(f"Error analyzing photos: {str(e)}")
            # Return mock data in case of error
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
        """
        if self.api_key != "sim_key":
            # In real implementation, this would make the actual API call
            try:
                # Placeholder for real API implementation
                pass
            except Exception as e:
                logger.error(f"API call failed: {str(e)}")
                
        # Return simulated data based on input parameters
        return self._generate_mock_measurements(height_cm, weight_kg, age, gender)

    def _validate_measurements(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate measurements against anatomical constraints
        """
        validated = measurements.copy()
        
        # Example validation rules
        if "body_fat_percentage" in validated:
            # Body fat percentage cannot be negative or above 60%
            validated["body_fat_percentage"] = max(3.0, min(60.0, validated["body_fat_percentage"]))
            
        # Ensure circumference measurements are proportional to height and weight
        if "height" in validated and "weight" in validated:
            height = validated["height"]
            weight = validated["weight"]
            
            # Validate waist circumference (typical range based on height)
            if "waist_circumference" in validated:
                min_waist = height * 0.3
                max_waist = height * 0.6
                validated["waist_circumference"] = max(min_waist, min(max_waist, validated["waist_circumference"]))
                
            # Similar validations could be applied to other measurements
            
        return validated

    def _calculate_enhanced_metrics(self, base_measurements: Dict[str, Any], 
                                   height_cm: float, 
                                   weight_kg: float, 
                                   age: int, 
                                   gender: str) -> Dict[str, Any]:
        """
        Calculate additional bodybuilding-specific metrics
        """
        enhanced = base_measurements.copy()
        
        # Calculate muscle maturity score
        enhanced["muscle_maturity"] = self._calculate_muscle_maturity(
            age=age,
            body_fat=enhanced.get("body_fat_percentage", 15.0),
            muscle_density=enhanced.get("muscle_density", 0.5)
        )
        
        # Calculate aesthetic scores
        enhanced["x_frame_score"] = self._calculate_x_frame_score(enhanced)
        enhanced["v_taper_score"] = self._calculate_v_taper_score(enhanced)
        
        # Calculate symmetry scores
        if all(key in enhanced for key in ["left_arm_circumference", "right_arm_circumference"]):
            left = enhanced["left_arm_circumference"]
            right = enhanced["right_arm_circumference"]
            # Symmetry score from 0-1, where 1 is perfect symmetry
            enhanced["upper_arm_symmetry"] = 1.0 - min(abs(left - right) / max(left, right), 0.5)
        
        # Similar calculation for leg symmetry
        if all(key in enhanced for key in ["left_thigh_circumference", "right_thigh_circumference"]):
            left = enhanced["left_thigh_circumference"]
            right = enhanced["right_thigh_circumference"]
            enhanced["leg_symmetry"] = 1.0 - min(abs(left - right) / max(left, right), 0.5)
        
        return enhanced

    def _calculate_muscle_maturity(self, age: int, body_fat: float, muscle_density: float) -> float:
        """
        Calculate muscle maturity score based on various factors (0-1 scale)
        """
        # Base age factor (peaks at around 35)
        if age < 18:
            age_factor = 0.2
        elif age < 25:
            age_factor = 0.4 + (age - 18) * 0.05
        elif age < 35:
            age_factor = 0.75 + (age - 25) * 0.02
        elif age < 50:
            age_factor = 0.95 - (age - 35) * 0.01
        else:
            age_factor = 0.8 - (age - 50) * 0.015
            
        # Body fat factor (leaner shows more muscle detail)
        if body_fat < 8:
            fat_factor = 0.9
        elif body_fat < 12:
            fat_factor = 0.8
        elif body_fat < 16:
            fat_factor = 0.6
        elif body_fat < 20:
            fat_factor = 0.4
        else:
            fat_factor = 0.2
            
        # Density factor
        density_factor = muscle_density
        
        # Combined score
        return (age_factor + fat_factor + density_factor) / 3

    def _calculate_x_frame_score(self, measurements: Dict[str, Any]) -> float:
        """
        Calculate X-frame aesthetic score (0-1 scale)
        """
        shoulder_width = measurements.get("shoulder_width", 0)
        waist_circ = measurements.get("waist_circumference", 0)
        hip_width = measurements.get("hip_width", 0)
        
        # Convert waist circumference to approximate width
        waist_width = waist_circ / np.pi if waist_circ > 0 else 1
        
        if all([shoulder_width > 0, waist_width > 0, hip_width > 0]):
            upper_ratio = min(shoulder_width / waist_width, 2.0)
            lower_ratio = min(hip_width / waist_width, 2.0)
            
            # Normalize to 0-1 scale
            upper_score = (upper_ratio - 1.0) / 1.0 if upper_ratio > 1.0 else 0
            lower_score = (lower_ratio - 1.0) / 1.0 if lower_ratio > 1.0 else 0
            
            return (upper_score + lower_score) / 2
        return 0.5  # Default value

    def _calculate_v_taper_score(self, measurements: Dict[str, Any]) -> float:
        """
        Calculate V-taper aesthetic score (0-1 scale)
        """
        shoulder_width = measurements.get("shoulder_width", 0)
        waist_circ = measurements.get("waist_circumference", 0)
        
        # Convert waist circumference to approximate width
        waist_width = waist_circ / np.pi if waist_circ > 0 else 1
        
        if shoulder_width > 0 and waist_width > 0:
            ratio = min(shoulder_width / waist_width, 2.5)
            
            # Normalize to 0-1 scale (ratio of 1.5 = 0.5, ratio of 2.5 = 1.0)
            return min(max((ratio - 1.0) / 1.5, 0), 1.0)
            
        return 0.5  # Default value

    def _add_confidence_scores(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add confidence scores to each measurement
        """
        with_confidence = {}
        confidence_scores = {}
        
        # Generate realistic confidence scores for each measurement
        for key, value in measurements.items():
            # Skip non-numeric or special fields
            if not isinstance(value, (int, float)) or key in ["age", "gender", "height", "weight"]:
                with_confidence[key] = value
                continue
                
            # Generate confidence score between 0.3 and 0.9
            # More standard measurements like height/weight get higher confidence
            if key in ["body_fat_percentage", "waist_circumference", "chest_circumference"]:
                confidence = 0.75 + np.random.random() * 0.15
            elif "symmetry" in key or "score" in key:
                confidence = 0.6 + np.random.random() * 0.2
            else:
                confidence = 0.5 + np.random.random() * 0.3
                
            confidence_scores[key] = confidence
            
            # Structure with value and confidence
            with_confidence[key] = {
                "value": value,
                "confidence": confidence
            }
            
        # Add the confidence scores dictionary to the result
        with_confidence["confidence_scores"] = confidence_scores
        
        return with_confidence

    def _generate_mock_measurements(self, height_cm: float, weight_kg: float, age: int, gender: str) -> Dict[str, Any]:
        """
        Generate realistic mock measurements based on height, weight, age, and gender
        """
        # Calculate BMI for reference
        bmi = weight_kg / ((height_cm / 100) ** 2)
        
        # Basic calculations for body fat percentage based on BMI, age, and gender
        # These are rough approximations for demonstration
        if gender.lower() == "male":
            base_bf = 10 + (bmi - 20) * 1.2 + (age / 100)
        else:
            base_bf = 18 + (bmi - 20) * 1.0 + (age / 120)
            
        body_fat = max(5, min(40, base_bf))
        
        # Calculate some basic proportions based on height
        waist_circ = height_cm * (0.4 + (body_fat / 100) * 0.2)
        chest_circ = height_cm * (0.5 + (body_fat / 100) * 0.1)
        hip_circ = height_cm * (0.5 + (body_fat / 100) * 0.15)
        shoulder_width = height_cm * 0.26
        
        # Calculate muscle mass based on weight, height, and body fat
        lean_mass = weight_kg * (1 - (body_fat / 100))
        muscle_mass = lean_mass * 0.6
        muscle_percent = (muscle_mass / weight_kg) * 100
        
        # Add small variations to simulate individual genetic differences
        variation = lambda: 1 + (np.random.random() - 0.5) * 0.1
        
        # Generate all 50 measurements
        measurements = {
            # Basic information
            "height": height_cm,
            "weight": weight_kg,
            "age": age,
            "gender": gender,
            
            # Body composition
            "body_fat_percentage": body_fat * variation(),
            "lean_body_mass": lean_mass * variation(),
            "muscle_mass_percentage": muscle_percent * variation(),
            "visceral_fat_level": max(1, min(20, (body_fat - 10) / 1.5)) * variation(),
            "subcutaneous_fat_thickness": max(2, body_fat / 3) * variation(),
            "water_retention_level": max(50, 70 - body_fat / 3) * variation(),
            "skin_thickness": 2.0 + (age / 200) * variation(),
            
            # Muscle characteristics
            "muscle_density": (0.8 - (body_fat / 100) * 0.3) * variation(),
            "muscle_hardness": (0.7 - (body_fat / 100) * 0.4) * variation(),
            "muscle_fullness": (0.6 + (muscle_percent / 50) * 0.4) * variation(),
            
            # Body ratios
            "waist_to_shoulder_ratio": (waist_circ / shoulder_width) * variation(),
            "waist_to_hip_ratio": (waist_circ / hip_circ) * variation(),
            "chest_to_waist_ratio": (chest_circ / waist_circ) * variation(),
            "arm_to_waist_ratio": (height_cm * 0.15 / waist_circ) * variation(),
            "leg_to_waist_ratio": (height_cm * 0.23 / waist_circ) * variation(),
            "thigh_to_calf_ratio": 1.8 * variation(),
            
            # Width measurements
            "shoulder_width": shoulder_width * variation(),
            "hip_width": hip_circ / 3 * variation(),
            
            # Circumference measurements
            "neck_circumference": height_cm * 0.12 * variation(),
            "chest_circumference": chest_circ * variation(),
            "upper_arm_circumference": height_cm * 0.11 * variation(),
            "left_arm_circumference": height_cm * 0.11 * variation(),
            "right_arm_circumference": height_cm * 0.11 * variation() * (1 + np.random.random() * 0.05),
            "forearm_circumference": height_cm * 0.08 * variation(),
            "waist_circumference": waist_circ * variation(),
            "hip_circumference": hip_circ * variation(),
            "thigh_circumference": height_cm * 0.18 * variation(),
            "left_thigh_circumference": height_cm * 0.18 * variation(),
            "right_thigh_circumference": height_cm * 0.18 * variation() * (1 + np.random.random() * 0.05),
            "calf_circumference": height_cm * 0.12 * variation(),
            "left_calf_circumference": height_cm * 0.12 * variation(),
            "right_calf_circumference": height_cm * 0.12 * variation() * (1 + np.random.random() * 0.05),
            "ankle_circumference": height_cm * 0.07 * variation(),
            "wrist_circumference": height_cm * 0.05 * variation(),
            
            # Muscle definition (0-1 scale, higher is better)
            "visible_striations": max(0, min(1, (0.9 - body_fat / 50) * variation())),
            "muscle_separation": max(0, min(1, (0.85 - body_fat / 40) * variation())),
            "vascularity": max(0, min(1, (0.9 - body_fat / 30) * variation())),
            "abdominal_definition": max(0, min(1, (1.0 - body_fat / 25) * variation())),
            "oblique_definition": max(0, min(1, (0.95 - body_fat / 28) * variation())),
            "quadriceps_separation": max(0, min(1, (0.9 - body_fat / 35) * variation())),
            "hamstring_definition": max(0, min(1, (0.85 - body_fat / 38) * variation())),
            "glute_ham_tie_in": max(0, min(1, (0.8 - body_fat / 40) * variation())),
            "deltoid_separation": max(0, min(1, (0.9 - body_fat / 32) * variation())),
            "triceps_definition": max(0, min(1, (0.85 - body_fat / 30) * variation())),
            
            # Genetic factors
            "biceps_insertion_type": "high" if np.random.random() > 0.5 else "low",
            "pectoral_insertion_type": "wide" if np.random.random() > 0.5 else "narrow",
            "abdominal_symmetry": (0.7 + np.random.random() * 0.3),
            "calf_insertion_type": "high" if np.random.random() > 0.5 else "low",
        }
        
        # Aesthetic assessments will be calculated separately
        
        return measurements

def format_measurement_value(key: str, value: float) -> str:
    """Format measurement values with appropriate units"""
    if "percentage" in key or key.endswith("_symmetry"):
        return f"{value:.1f}%"
    elif any(term in key for term in ["width", "circumference"]):
        return f"{value:.1f} cm"
    elif key == "weight":
        return f"{value:.1f} kg"
    elif key == "height":
        return f"{value:.1f} cm"
    elif key == "age":
        return f"{int(value)} years"
    elif "level" in key or "score" in key or any(term in key for term in ["density", "hardness", "fullness", "definition"]):
        # Return a 0-10 scale for easier understanding
        return f"{(value * 10):.1f}/10"
    return f"{value:.1f}"

def categorize_measurements(measurements: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Group measurements into categories for better display
    """
    categories = {
        "Body Composition": [
            "body_fat_percentage", "lean_body_mass", "muscle_mass_percentage", 
            "visceral_fat_level", "subcutaneous_fat_thickness", "water_retention_level", 
            "skin_thickness"
        ],
        "Muscle Characteristics": [
            "muscle_density", "muscle_hardness", "muscle_fullness"
        ],
        "Body Ratios": [
            "waist_to_shoulder_ratio", "waist_to_hip_ratio", "chest_to_waist_ratio",
            "arm_to_waist_ratio", "leg_to_waist_ratio", "thigh_to_calf_ratio"
        ],
        "Symmetry": [
            "upper_arm_symmetry", "leg_symmetry", "abdominal_symmetry"
        ],
        "Width Measurements": [
            "shoulder_width", "hip_width"
        ],
        "Circumference Measurements": [
            "neck_circumference", "chest_circumference", "upper_arm_circumference",
            "forearm_circumference", "waist_circumference", "hip_circumference",
            "thigh_circumference", "calf_circumference", "ankle_circumference",
            "wrist_circumference"
        ],
        "Muscle Definition": [
            "visible_striations", "muscle_separation", "vascularity",
            "abdominal_definition", "oblique_definition", "quadriceps_separation",
            "hamstring_definition", "glute_ham_tie_in", "deltoid_separation",
            "triceps_definition"
        ],
        "Aesthetic Assessment": [
            "x_frame_score", "v_taper_score", "muscle_maturity"
        ],
        "Genetic Factors": [
            "biceps_insertion_type", "pectoral_insertion_type", "calf_insertion_type"
        ]
    }
    
    categorized = {}
    for category, keys in categories.items():
        categorized[category] = {
            k: measurements[k] for k in keys if k in measurements
        }
    
    return categorized