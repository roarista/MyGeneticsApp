"""
Body Measurement Estimator

This module provides functionality to automatically estimate body measurements from uploaded photos
using AI-based computer vision techniques combined with user-provided basic information.
"""

import numpy as np
import logging
import cv2
import base64
import io
from PIL import Image
import mediapipe as mp

# Configure logging
logger = logging.getLogger(__name__)

class BodyLandmarkDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=True,
            min_detection_confidence=0.5
        )
    
    def detect_landmarks(self, image):
        """Detect body landmarks in an image"""
        try:
            # Convert to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = image
            else:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process image to find landmarks
            results = self.pose.process(image_rgb)
            
            if not results.pose_landmarks:
                logger.warning("No pose landmarks detected in image")
                return None
                
            # Extract landmarks as numpy array
            landmarks = []
            for landmark in results.pose_landmarks.landmark:
                landmarks.append([landmark.x, landmark.y, landmark.z, landmark.visibility])
            
            return np.array(landmarks)
        
        except Exception as e:
            logger.error(f"Error detecting landmarks: {str(e)}")
            return None
    
    def calculate_body_segments(self, landmarks, image_height, image_width):
        """Calculate body segment lengths and proportions"""
        if landmarks is None:
            return {}
        
        # Define key body segments
        segments = {
            # Torso
            "neck_to_hip": self._calculate_distance(landmarks, 
                self.mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                self.mp_pose.PoseLandmark.LEFT_HIP.value),
            
            # Arms
            "left_arm": self._calculate_distance(landmarks, 
                self.mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                self.mp_pose.PoseLandmark.LEFT_WRIST.value),
            "right_arm": self._calculate_distance(landmarks, 
                self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                self.mp_pose.PoseLandmark.RIGHT_WRIST.value),
            
            # Legs
            "left_leg": self._calculate_distance(landmarks, 
                self.mp_pose.PoseLandmark.LEFT_HIP.value,
                self.mp_pose.PoseLandmark.LEFT_ANKLE.value),
            "right_leg": self._calculate_distance(landmarks, 
                self.mp_pose.PoseLandmark.RIGHT_HIP.value,
                self.mp_pose.PoseLandmark.RIGHT_ANKLE.value),
            
            # Shoulders
            "shoulder_width": self._calculate_distance(landmarks, 
                self.mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value),
            
            # Hips
            "hip_width": self._calculate_distance(landmarks, 
                self.mp_pose.PoseLandmark.LEFT_HIP.value,
                self.mp_pose.PoseLandmark.RIGHT_HIP.value),
        }
        
        # Calculate additional body proportions
        segments["shoulder_to_hip_ratio"] = segments["shoulder_width"] / segments["hip_width"] if segments["hip_width"] > 0 else 0
        
        # Scale by image dimensions to get pixel distances
        for key in segments:
            if isinstance(segments[key], float) and "ratio" not in key:
                segments[key] *= max(image_height, image_width)
        
        return segments
    
    def _calculate_distance(self, landmarks, idx1, idx2):
        """Calculate distance between two landmarks"""
        try:
            x1, y1 = landmarks[idx1][0], landmarks[idx1][1]
            x2, y2 = landmarks[idx2][0], landmarks[idx2][1]
            return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        except Exception as e:
            logger.error(f"Error calculating distance: {str(e)}")
            return 0


def preprocess_image(image_data, target_size=(512, 512)):
    """Preprocess image for analysis"""
    try:
        # Handle different image data formats
        if isinstance(image_data, str):
            # Base64 encoded image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image_array = np.array(image)
        elif isinstance(image_data, np.ndarray):
            # Already a numpy array
            image_array = image_data
        else:
            raise ValueError("Unsupported image data format")
        
        # Ensure RGB format
        if len(image_array.shape) == 2:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
        elif image_array.shape[2] == 4:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
        
        # Resize for consistent processing
        original_image = image_array.copy()
        processed_image = cv2.resize(image_array, target_size)
        
        # Normalize pixel values
        processed_normalized = processed_image.astype(np.float32) / 255.0
        
        return original_image, processed_normalized
    
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None, None


class BodyMeasurementEstimator:
    def __init__(self):
        self.landmark_detector = BodyLandmarkDetector()
    
    def estimate_measurements(self, image_data, height_cm, weight_kg, gender, experience="beginner"):
        """Estimate body measurements from image and basic info"""
        try:
            # Process image
            original_image, processed_image = preprocess_image(image_data)
            if original_image is None or processed_image is None:
                logger.error("Failed to preprocess image")
                return self._estimate_from_statistics(height_cm, weight_kg, gender)
            
            h, w = original_image.shape[:2]
            
            # Detect landmarks
            landmarks = self.landmark_detector.detect_landmarks(processed_image)
            
            # Calculate pixel-based segments
            segments = self.landmark_detector.calculate_body_segments(landmarks, h, w) if landmarks is not None else {}
            
            # Convert to real-world measurements using height as reference
            measurements = self._convert_to_measurements(segments, height_cm, weight_kg, gender, experience)
            
            return measurements
        
        except Exception as e:
            logger.error(f"Error estimating measurements: {str(e)}")
            return self._estimate_from_statistics(height_cm, weight_kg, gender)
    
    def _convert_to_measurements(self, segments, height_cm, weight_kg, gender, experience):
        """Convert pixel-based measurements to cm using height as reference"""
        # If we have no segments, use statistical estimation
        if not segments:
            return self._estimate_from_statistics(height_cm, weight_kg, gender)
        
        # Calculate BMI for additional adjustment
        bmi = weight_kg / ((height_cm / 100) ** 2)
        bmi_factor = self._calculate_bmi_adjustment(bmi, gender)
        
        # Reference values
        if gender.lower() == 'male':
            reference = {
                'neck_ratio': 0.24,         # Neck circumference relative to height
                'chest_ratio': 0.52,        # Chest circumference relative to height
                'waist_ratio': 0.45,        # Waist circumference relative to height
                'hip_ratio': 0.48,          # Hip circumference relative to height
                'arm_ratio': 0.18,          # Arm circumference relative to height
                'thigh_ratio': 0.28,        # Thigh circumference relative to height
                'calf_ratio': 0.20,         # Calf circumference relative to height
                'wrist_ratio': 0.11,        # Wrist circumference relative to height
                'ankle_ratio': 0.13,        # Ankle circumference relative to height
            }
        else:
            reference = {
                'neck_ratio': 0.20,
                'chest_ratio': 0.49,
                'waist_ratio': 0.41, 
                'hip_ratio': 0.53,
                'arm_ratio': 0.16,
                'thigh_ratio': 0.30,
                'calf_ratio': 0.19,
                'wrist_ratio': 0.10,
                'ankle_ratio': 0.12,
            }
        
        # Use segments to adjust reference values
        measurements = {}
        
        # Shoulders and waist
        if 'shoulder_to_hip_ratio' in segments:
            shoulder_hip_deviation = segments['shoulder_to_hip_ratio'] - 1.4 if gender.lower() == 'male' else segments['shoulder_to_hip_ratio'] - 1.2
            
            # Adjust shoulder and waist based on detected ratio
            reference['chest_ratio'] *= (1 + 0.1 * shoulder_hip_deviation)
            reference['waist_ratio'] *= (1 - 0.1 * shoulder_hip_deviation)
        
        # Apply BMI adjustments to circumference estimates
        reference['waist_ratio'] *= bmi_factor
        reference['hip_ratio'] *= (bmi_factor * 0.8)
        reference['thigh_ratio'] *= (bmi_factor * 0.7)
        reference['arm_ratio'] *= (bmi_factor * 0.6)
        reference['chest_ratio'] *= (bmi_factor * 0.5)
        
        # Experience adjustments (more experienced = more muscle)
        muscle_factor = 1.0
        if experience == "intermediate":
            muscle_factor = 1.05
        elif experience == "advanced":
            muscle_factor = 1.1
        
        reference['arm_ratio'] *= muscle_factor
        reference['chest_ratio'] *= muscle_factor
        reference['thigh_ratio'] *= muscle_factor
        reference['calf_ratio'] *= muscle_factor
        
        # Calculate final measurements
        measurements = {
            "neck_cm": round(height_cm * reference['neck_ratio'], 1),
            "chest_cm": round(height_cm * reference['chest_ratio'], 1),
            "shoulders_cm": round(height_cm * reference['chest_ratio'] * 1.2, 1),
            "waist_cm": round(height_cm * reference['waist_ratio'], 1),
            "hips_cm": round(height_cm * reference['hip_ratio'], 1),
            "left_arm_cm": round(height_cm * reference['arm_ratio'], 1),
            "right_arm_cm": round(height_cm * reference['arm_ratio'], 1),
            "left_thigh_cm": round(height_cm * reference['thigh_ratio'], 1),
            "right_thigh_cm": round(height_cm * reference['thigh_ratio'], 1),
            "left_calf_cm": round(height_cm * reference['calf_ratio'], 1),
            "right_calf_cm": round(height_cm * reference['calf_ratio'], 1),
            "wrist_cm": round(height_cm * reference['wrist_ratio'], 1),
            "ankle_cm": round(height_cm * reference['ankle_ratio'], 1),
            "estimation_method": "ai_enhanced",
            "segments": segments
        }
        
        return measurements
    
    def _estimate_from_statistics(self, height_cm, weight_kg, gender):
        """Fallback method to estimate using statistical averages"""
        # Calculate BMI
        bmi = weight_kg / ((height_cm / 100) ** 2)
        bmi_factor = self._calculate_bmi_adjustment(bmi, gender)
        
        # Base ratios (height-based)
        if gender.lower() == 'male':
            neck_ratio = 0.24
            chest_ratio = 0.52
            shoulders_ratio = 0.62
            waist_ratio = 0.45
            hip_ratio = 0.48
            arm_ratio = 0.18
            thigh_ratio = 0.28
            calf_ratio = 0.20
            wrist_ratio = 0.11
            ankle_ratio = 0.13
        else:
            neck_ratio = 0.20
            chest_ratio = 0.49
            shoulders_ratio = 0.54
            waist_ratio = 0.41
            hip_ratio = 0.53
            arm_ratio = 0.16
            thigh_ratio = 0.30
            calf_ratio = 0.19
            wrist_ratio = 0.10
            ankle_ratio = 0.12
        
        # Apply BMI adjustment
        waist_ratio *= bmi_factor
        hip_ratio *= (bmi_factor * 0.8)
        thigh_ratio *= (bmi_factor * 0.7)
        arm_ratio *= (bmi_factor * 0.6)
        chest_ratio *= (bmi_factor * 0.5)
        
        # Calculate measurements
        measurements = {
            "neck_cm": round(height_cm * neck_ratio, 1),
            "chest_cm": round(height_cm * chest_ratio, 1),
            "shoulders_cm": round(height_cm * shoulders_ratio, 1),
            "waist_cm": round(height_cm * waist_ratio, 1),
            "hips_cm": round(height_cm * hip_ratio, 1),
            "left_arm_cm": round(height_cm * arm_ratio, 1),
            "right_arm_cm": round(height_cm * arm_ratio, 1),
            "left_thigh_cm": round(height_cm * thigh_ratio, 1),
            "right_thigh_cm": round(height_cm * thigh_ratio, 1),
            "left_calf_cm": round(height_cm * calf_ratio, 1),
            "right_calf_cm": round(height_cm * calf_ratio, 1),
            "wrist_cm": round(height_cm * wrist_ratio, 1),
            "ankle_cm": round(height_cm * ankle_ratio, 1),
            "estimation_method": "statistical"
        }
        
        return measurements
    
    def _calculate_bmi_adjustment(self, bmi, gender):
        """Calculate adjustment factor based on BMI"""
        # Normal BMI reference
        normal_bmi = 22 if gender.lower() == 'male' else 21
        
        # Calculate adjustment factor
        if bmi <= normal_bmi:
            # Underweight: linear decrease down to 0.9 at BMI 16
            return max(0.9, 1.0 - 0.025 * (normal_bmi - bmi))
        else:
            # Overweight: linear increase up to 1.3 at BMI 35
            return min(1.3, 1.0 + 0.023 * (bmi - normal_bmi))


# Main function to use in the app
def estimate_measurements(image_data, height_cm, weight_kg, gender, experience="beginner"):
    """Top-level function to estimate body measurements from an image"""
    estimator = BodyMeasurementEstimator()
    return estimator.estimate_measurements(image_data, height_cm, weight_kg, gender, experience)