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
        
        # Scale by image dimensions to get pixel distances, but with improved scaling
        # Use a more conservative approach to avoid exaggeration
        scaling_factor = min(image_height, image_width) * 0.8  # More conservative scaling
        
        for key in segments:
            if isinstance(segments[key], float) and "ratio" not in key:
                # Use a more appropriate scaling factor instead of max dimension
                segments[key] *= scaling_factor
        
        return segments
    
    def _calculate_distance(self, landmarks, idx1, idx2):
        """
        Calculate distance between two landmarks with improved validation to avoid extreme values.
        This prevents the detection of anatomically impossible limb lengths.
        """
        try:
            # Extract landmark coordinates
            x1, y1 = landmarks[idx1][0], landmarks[idx1][1]
            x2, y2 = landmarks[idx2][0], landmarks[idx2][1]
            
            # Validate coordinates are in expected range (normalized coordinates should be 0-1)
            if not (0 <= x1 <= 1 and 0 <= y1 <= 1 and 0 <= x2 <= 1 and 0 <= y2 <= 1):
                logger.warning(f"Landmark coordinates out of expected range: ({x1}, {y1}), ({x2}, {y2})")
                # Clamp values to valid range
                x1 = max(0, min(1, x1))
                y1 = max(0, min(1, y1))
                x2 = max(0, min(1, x2))
                y2 = max(0, min(1, y2))
            
            # Calculate Euclidean distance
            distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            
            # Check for unrealistic distances
            # In normalized coordinates, most body part distances should not exceed 0.8
            if distance > 0.8:
                logger.warning(f"Detected unusual distance {distance} between landmarks {idx1} and {idx2}")
                # Cap the distance to a reasonable maximum
                distance = 0.8
                
            return distance
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


class MeasurementValidator:
    """Validates body measurements against anatomical constraints"""
    
    # Stricter anatomically possible ranges as percentages of height
    # Based on anthropometric studies and standard human proportions
    ANATOMICAL_RATIOS = {
        'neck_cm': (0.17, 0.20),         # 17-20% of height
        'chest_cm': (0.45, 0.50),        # 45-50% of height
        'shoulders_cm': (0.23, 0.26),    # 23-26% of height (biacromial width)
        'waist_cm': (0.35, 0.43),        # 35-43% of height
        'hips_cm': (0.40, 0.46),         # 40-46% of height
        'arm_cm': (0.1, 0.13),           # 10-13% of height (arm circumference)
        'thigh_cm': (0.18, 0.21),        # 18-21% of height (thigh circumference)
        'calf_cm': (0.12, 0.14),         # 12-14% of height
        'wrist_cm': (0.08, 0.10),        # 8-10% of height
        'ankle_cm': (0.09, 0.11),        # 9-11% of height
    }
    
    # Additional constraints for length measurements
    # These will be used to validate length ratios
    LENGTH_RATIOS = {
        'arm_length': (0.33, 0.38),      # 33-38% of height
        'leg_length': (0.45, 0.52),      # 45-52% of height
        'torso_length': (0.30, 0.35),    # 30-35% of height
    }
    
    @staticmethod
    def validate_and_adjust(measurements: dict, height_cm: float) -> dict:
        """
        Validates measurements against anatomical constraints and adjusts if needed.
        Now includes validation for limb lengths and other key body proportions.
        """
        if not height_cm or height_cm <= 0:
            return measurements  # Can't validate without height
            
        validated = {}
        
        # Map measurement keys to validation keys
        validation_map = {
            'neck_cm': 'neck_cm',
            'chest_cm': 'chest_cm',
            'shoulders_cm': 'shoulders_cm',
            'waist_cm': 'waist_cm',
            'hips_cm': 'hips_cm',
            'left_arm_cm': 'arm_cm',
            'right_arm_cm': 'arm_cm',
            'left_thigh_cm': 'thigh_cm',
            'right_thigh_cm': 'thigh_cm',
            'left_calf_cm': 'calf_cm',
            'right_calf_cm': 'calf_cm',
            'wrist_cm': 'wrist_cm',
            'ankle_cm': 'ankle_cm',
        }
        
        # First pass: validate circumference measurements
        for measure, value in measurements.items():
            # Skip non-measurement fields like method or segments
            if measure in validation_map and isinstance(value, (int, float)):
                validation_key = validation_map[measure]
                
                if validation_key in MeasurementValidator.ANATOMICAL_RATIOS:
                    min_ratio, max_ratio = MeasurementValidator.ANATOMICAL_RATIOS[validation_key]
                    min_value = height_cm * min_ratio
                    max_value = height_cm * max_ratio
                    
                    if value < min_value:
                        # If too small, set to minimum
                        validated[measure] = round(min_value, 1)
                    elif value > max_value:
                        # If too large, set to maximum
                        validated[measure] = round(max_value, 1)
                    else:
                        # Within range, keep as is
                        validated[measure] = value
                else:
                    validated[measure] = value
            else:
                # Keep non-measurement values (like estimation_method)
                validated[measure] = value
        
        # Second pass: validate length measurements if present in segments
        if 'segments' in measurements:
            segments = measurements['segments']
            
            # Validate arm length
            if 'left_arm' in segments and 'right_arm' in segments:
                arm_length = (segments['left_arm'] + segments['right_arm']) / 2
                
                # Convert to cm based on height
                arm_length_cm = arm_length * height_cm
                
                if 'arm_length' in MeasurementValidator.LENGTH_RATIOS:
                    min_ratio, max_ratio = MeasurementValidator.LENGTH_RATIOS['arm_length']
                    min_value = height_cm * min_ratio
                    max_value = height_cm * max_ratio
                    
                    if arm_length_cm < min_value:
                        # Scale arm segments proportionally
                        scale_factor = min_value / arm_length_cm if arm_length_cm > 0 else 1.0
                        segments['left_arm'] *= scale_factor
                        segments['right_arm'] *= scale_factor
                    elif arm_length_cm > max_value:
                        # Scale arm segments proportionally
                        scale_factor = max_value / arm_length_cm
                        segments['left_arm'] *= scale_factor
                        segments['right_arm'] *= scale_factor
            
            # Validate leg length
            if 'left_leg' in segments and 'right_leg' in segments:
                leg_length = (segments['left_leg'] + segments['right_leg']) / 2
                
                # Convert to cm based on height
                leg_length_cm = leg_length * height_cm
                
                if 'leg_length' in MeasurementValidator.LENGTH_RATIOS:
                    min_ratio, max_ratio = MeasurementValidator.LENGTH_RATIOS['leg_length']
                    min_value = height_cm * min_ratio
                    max_value = height_cm * max_ratio
                    
                    if leg_length_cm < min_value:
                        # Scale leg segments proportionally
                        scale_factor = min_value / leg_length_cm if leg_length_cm > 0 else 1.0
                        segments['left_leg'] *= scale_factor
                        segments['right_leg'] *= scale_factor
                    elif leg_length_cm > max_value:
                        # Scale leg segments proportionally
                        scale_factor = max_value / leg_length_cm
                        segments['left_leg'] *= scale_factor
                        segments['right_leg'] *= scale_factor
            
            # Update segments in validated measurements
            validated['segments'] = segments
                
        # Add a flag indicating validation was performed
        validated["validation_performed"] = True
        validated["anatomical_validation"] = True
        
        return validated


class BodyMeasurementEstimator:
    def __init__(self):
        self.landmark_detector = BodyLandmarkDetector()
        self.validator = MeasurementValidator()
    
    def estimate_measurements(self, image_data, height_cm, weight_kg, gender, experience="beginner"):
        """Estimate body measurements from image and basic info with improved validation"""
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
            raw_measurements = self._convert_to_measurements(segments, height_cm, weight_kg, gender, experience)
            
            # Validate and adjust measurements
            validated_measurements = self.validator.validate_and_adjust(raw_measurements, height_cm)
            
            # Add reliable flag based on landmark quality
            if landmarks is not None and self._has_reliable_landmarks(landmarks):
                validated_measurements["reliable_estimation"] = True
            else:
                validated_measurements["reliable_estimation"] = False
            
            return validated_measurements
        
        except Exception as e:
            logger.error(f"Error estimating measurements: {str(e)}")
            # Get statistical estimates and validate them too
            raw_measurements = self._estimate_from_statistics(height_cm, weight_kg, gender)
            validated_measurements = self.validator.validate_and_adjust(raw_measurements, height_cm)
            validated_measurements["reliable_estimation"] = False
            return validated_measurements
    
    def _has_reliable_landmarks(self, landmarks):
        """Check if landmarks have good visibility and quality"""
        # Check if landmarks contain visibility information
        if landmarks.size > 0 and landmarks.shape[1] >= 4:
            # Get visibility values (4th column)
            visibilities = landmarks[:, 3]
            # Consider landmarks reliable if average visibility is above threshold
            return np.mean(visibilities) > 0.7
        return False
    
    def _convert_to_measurements(self, segments, height_cm, weight_kg, gender, experience):
        """Convert pixel-based measurements to cm using height as reference with conservative estimates"""
        # If we have no segments, use statistical estimation
        if not segments:
            return self._estimate_from_statistics(height_cm, weight_kg, gender)
        
        # Calculate BMI for additional adjustment
        bmi = weight_kg / ((height_cm / 100) ** 2) if height_cm > 0 and weight_kg > 0 else 22
        bmi_factor = self._calculate_bmi_adjustment(bmi, gender)
        
        # Reference values - more conservative than before
        if gender.lower() == 'male':
            reference = {
                'neck_ratio': 0.19,         # Neck circumference relative to height
                'chest_ratio': 0.46,        # Chest circumference relative to height
                'waist_ratio': 0.40,        # Waist circumference relative to height
                'hip_ratio': 0.43,          # Hip circumference relative to height
                'arm_ratio': 0.12,          # Arm circumference relative to height
                'thigh_ratio': 0.20,        # Thigh circumference relative to height
                'calf_ratio': 0.13,         # Calf circumference relative to height
                'wrist_ratio': 0.09,        # Wrist circumference relative to height
                'ankle_ratio': 0.10,        # Ankle circumference relative to height
            }
        else:
            reference = {
                'neck_ratio': 0.18,
                'chest_ratio': 0.45,
                'waist_ratio': 0.38, 
                'hip_ratio': 0.46,
                'arm_ratio': 0.11,
                'thigh_ratio': 0.21,
                'calf_ratio': 0.13,
                'wrist_ratio': 0.08,
                'ankle_ratio': 0.10,
            }
        
        # Use segments to adjust reference values
        measurements = {}
        
        # Shoulders and waist
        if 'shoulder_to_hip_ratio' in segments and segments['shoulder_to_hip_ratio'] > 0:
            # Apply milder adjustments
            shoulder_hip_deviation = segments['shoulder_to_hip_ratio'] - 1.4 if gender.lower() == 'male' else segments['shoulder_to_hip_ratio'] - 1.2
            
            # Limit the deviation effect
            shoulder_hip_deviation = max(-0.2, min(0.2, shoulder_hip_deviation))
            
            # Adjust shoulder and waist based on detected ratio
            reference['chest_ratio'] *= (1 + 0.05 * shoulder_hip_deviation)
            reference['waist_ratio'] *= (1 - 0.05 * shoulder_hip_deviation)
        
        # Apply BMI adjustments to circumference estimates (with more conservative multipliers)
        reference['waist_ratio'] *= bmi_factor
        reference['hip_ratio'] *= (bmi_factor * 0.7)
        reference['thigh_ratio'] *= (bmi_factor * 0.5)
        reference['arm_ratio'] *= (bmi_factor * 0.4)
        reference['chest_ratio'] *= (bmi_factor * 0.3)
        
        # Experience adjustments (more experienced = more muscle, but with conservative factors)
        muscle_factor = 1.0
        if experience == "intermediate":
            muscle_factor = 1.03
        elif experience == "advanced":
            muscle_factor = 1.05
        
        reference['arm_ratio'] *= muscle_factor
        reference['chest_ratio'] *= muscle_factor
        reference['thigh_ratio'] *= muscle_factor
        reference['calf_ratio'] *= muscle_factor
        
        # Calculate shoulder width with improved anatomical constraints
        # Standard anthropometric ratio: biacromial width is typically 23-26% of total height
        shoulders_cm = height_cm * 0.24  # Approximately 24% of height for average person
        
        if 'shoulder_width' in segments and segments['shoulder_width'] > 0:
            # Apply a more accurate scaling based on anthropometric research
            # The pixel value is normalized, so we scale it based on a percentage of height
            # Using a more conservative scaling factor to avoid unrealistic measurements
            
            # First check if the segment value is within reasonable limits
            if segments['shoulder_width'] <= 0.5:  # Normal range in normalized coordinates
                # Apply more accurate scaling with anatomical constraints
                # This uses a ratio based on standard anthropometric proportions
                shoulder_pixel_ratio = segments['shoulder_width']
                
                # Calculate an anatomically sound shoulder width range
                min_shoulder_cm = height_cm * 0.23  # Minimum anatomical ratio
                max_shoulder_cm = height_cm * 0.26  # Maximum anatomical ratio
                
                # Calculate shoulder width based on the detected pixel ratio, within anatomical constraints
                detected_shoulder_cm = min_shoulder_cm + shoulder_pixel_ratio * (max_shoulder_cm - min_shoulder_cm)
                
                # Blend statistical average with the detected measurement (weighted blend)
                # Give more weight to the statistical average for stability
                shoulders_cm = (shoulders_cm * 0.6) + (detected_shoulder_cm * 0.4)
            else:
                # If value is unreasonable, rely more on statistical values
                logger.warning(f"Detected unusual shoulder width: {segments['shoulder_width']}")
                # Still use the segment value but with much lower weight
                detected_shoulder_cm = segments['shoulder_width'] * (height_cm * 0.2)  # Scaling with limiting factor
                shoulders_cm = (shoulders_cm * 0.9) + (detected_shoulder_cm * 0.1)
        
        # Calculate final measurements
        measurements = {
            "neck_cm": round(height_cm * reference['neck_ratio'], 1),
            "chest_cm": round(height_cm * reference['chest_ratio'], 1),
            "shoulders_cm": round(shoulders_cm, 1),
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
            "reliable_measurements": ["shoulders_cm", "waist_cm"],  # Only list measurements we're confident about
            "segments": segments
        }
        
        return measurements
    
    def _estimate_from_statistics(self, height_cm, weight_kg, gender):
        """Fallback method to estimate using statistical averages with improved accuracy"""
        # Calculate BMI
        bmi = weight_kg / ((height_cm / 100) ** 2) if height_cm > 0 and weight_kg > 0 else 22
        bmi_factor = self._calculate_bmi_adjustment(bmi, gender)
        
        # Base ratios (height-based) - more conservative values
        if gender.lower() == 'male':
            neck_ratio = 0.19
            chest_ratio = 0.46
            shoulders_ratio = 0.25  # Conservative biacromial width
            waist_ratio = 0.40
            hip_ratio = 0.44
            arm_ratio = 0.12
            thigh_ratio = 0.20
            calf_ratio = 0.13
            wrist_ratio = 0.09
            ankle_ratio = 0.10
        else:
            neck_ratio = 0.18
            chest_ratio = 0.45
            shoulders_ratio = 0.24
            waist_ratio = 0.38
            hip_ratio = 0.46
            arm_ratio = 0.11
            thigh_ratio = 0.21
            calf_ratio = 0.13
            wrist_ratio = 0.08
            ankle_ratio = 0.10
        
        # Apply BMI adjustment with conservative multipliers
        waist_ratio *= bmi_factor
        hip_ratio *= (bmi_factor * 0.7)
        thigh_ratio *= (bmi_factor * 0.5)
        arm_ratio *= (bmi_factor * 0.4)
        chest_ratio *= (bmi_factor * 0.3)
        
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
            "estimation_method": "statistical",
            "reliable_estimation": False
        }
        
        return measurements
    
    def _calculate_bmi_adjustment(self, bmi, gender):
        """Calculate adjustment factor based on BMI with more conservative range"""
        # Normal BMI reference
        normal_bmi = 22 if gender.lower() == 'male' else 21
        
        # Calculate adjustment factor with narrower range
        if bmi <= normal_bmi:
            # Underweight: linear decrease down to 0.9 at BMI 16
            return max(0.95, 1.0 - 0.015 * (normal_bmi - bmi))
        else:
            # Overweight: linear increase up to 1.15 at BMI 35
            return min(1.15, 1.0 + 0.010 * (bmi - normal_bmi))


# Main function to use in the app
def estimate_measurements(image_data, height_cm, weight_kg, gender, experience="beginner"):
    """Top-level function to estimate body measurements from an image"""
    estimator = BodyMeasurementEstimator()
    return estimator.estimate_measurements(image_data, height_cm, weight_kg, gender, experience)