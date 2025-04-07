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
import math
from PIL import Image
import mediapipe as mp
from .measurement_validator import MeasurementValidator as ExternalMeasurementValidator

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
                
                if validation_key in ExternalMeasurementValidator.ANATOMICAL_RATIOS:
                    min_ratio, max_ratio = ExternalMeasurementValidator.ANATOMICAL_RATIOS[validation_key]
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
                
                if 'arm_length' in ExternalMeasurementValidator.LENGTH_RATIOS:
                    min_ratio, max_ratio = ExternalMeasurementValidator.LENGTH_RATIOS['arm_length']
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
                
                if 'leg_length' in ExternalMeasurementValidator.LENGTH_RATIOS:
                    min_ratio, max_ratio = ExternalMeasurementValidator.LENGTH_RATIOS['leg_length']
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
        # Use the improved MeasurementValidator from measurement_validator.py
        self.validator = ExternalMeasurementValidator()
    
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
        """
        Convert pixel-based measurements to cm using a multi-method approach for increased accuracy.
        This implementation combines:
        1. Anthropometric standards based on height/weight
        2. Visual analysis from the detected landmarks
        3. Statistical models based on population averages
        4. BMI-based adjustments
        
        Each measurement is assigned a confidence score which determines how much we rely on
        detected landmarks vs statistical averages.
        """
        # If we have no segments, use statistical estimation
        if not segments:
            return self._estimate_from_statistics(height_cm, weight_kg, gender)
        
        # Calculate BMI for additional adjustment
        bmi = weight_kg / ((height_cm / 100) ** 2) if height_cm > 0 and weight_kg > 0 else 22
        bmi_factor = self._calculate_bmi_adjustment(bmi, gender)
        
        # ANTHROPOMETRIC DATA
        # Reference values based on extensive anthropometric research studies
        # Sources: NASA anthropometric studies, ANSUR II database, CAESAR 3D anthropometric database
        if gender.lower() == 'male':
            # Male reference values with tighter ranges (more precise)
            reference = {
                # Format: 'measurement': (min_ratio, typical_ratio, max_ratio)
                # Each ratio represents percentage of height
                'neck_ratio': (0.185, 0.195, 0.205),
                'chest_ratio': (0.45, 0.475, 0.50),
                'shoulders_ratio': (0.225, 0.245, 0.265),
                'waist_ratio': (0.38, 0.42, 0.46),
                'hip_ratio': (0.41, 0.435, 0.46),
                'arm_ratio': (0.11, 0.12, 0.13),
                'thigh_ratio': (0.19, 0.205, 0.22),
                'calf_ratio': (0.12, 0.13, 0.14),
                'wrist_ratio': (0.085, 0.09, 0.095),
                'ankle_ratio': (0.095, 0.10, 0.105),
            }
            # Length proportions for males (as ratio of height)
            length_props = {
                'arm_length_ratio': (0.33, 0.35, 0.38),
                'leg_length_ratio': (0.45, 0.48, 0.52),
                'torso_length_ratio': (0.30, 0.33, 0.35),
            }
        else:
            # Female reference values
            reference = {
                'neck_ratio': (0.175, 0.185, 0.195),
                'chest_ratio': (0.44, 0.46, 0.48),
                'shoulders_ratio': (0.215, 0.235, 0.255),
                'waist_ratio': (0.36, 0.39, 0.42),
                'hip_ratio': (0.44, 0.465, 0.49),
                'arm_ratio': (0.105, 0.115, 0.125),
                'thigh_ratio': (0.20, 0.215, 0.23),
                'calf_ratio': (0.12, 0.13, 0.14),
                'wrist_ratio': (0.075, 0.08, 0.085),
                'ankle_ratio': (0.09, 0.095, 0.10),
            }
            # Length proportions for females
            length_props = {
                'arm_length_ratio': (0.32, 0.34, 0.37),
                'leg_length_ratio': (0.44, 0.47, 0.51),
                'torso_length_ratio': (0.30, 0.32, 0.34),
            }
            
        # MEASUREMENT CONFIDENCE TRACKING
        # Initialize confidence scores for each measurement (0-1 scale)
        confidence = {
            "neck_cm": 0.6,
            "chest_cm": 0.7,
            "shoulders_cm": 0.8,   # Shoulders are generally more reliable to detect
            "waist_cm": 0.75,
            "hips_cm": 0.7,
            "arm_cm": 0.6,
            "thigh_cm": 0.6,
            "calf_cm": 0.5,
            "wrist_cm": 0.5,
            "ankle_cm": 0.4,
        }
        
        # SEGMENT-BASED CALCULATIONS
        # Initialize measurements dictionary with default values
        measurements = {}
        reliable_measurements = []
        
        # 1. SHOULDER WIDTH CALCULATION - most reliable measurement from landmarks
        # Standard anthropometric ratio: biacromial width is typically 22.5-26.5% of total height
        
        # Start with statistical average
        shoulders_cm = height_cm * reference['shoulders_ratio'][1]
        
        # Adjust based on detected segments if available
        if 'shoulder_width' in segments and segments['shoulder_width'] > 0:
            # First validate the segment value is within reasonable limits
            if 0 < segments['shoulder_width'] <= 0.5:  # Normal range in normalized coordinates
                # Calculate detected shoulder width in cm
                # Using a more sophisticated mapping from normalized coordinates to anatomical proportions
                shoulder_pixel_ratio = segments['shoulder_width']
                
                # Map the normalized value to anatomical range
                min_shoulder_cm = height_cm * reference['shoulders_ratio'][0]
                max_shoulder_cm = height_cm * reference['shoulders_ratio'][2]
                typical_shoulder_cm = height_cm * reference['shoulders_ratio'][1]
                
                # Calculate shoulder width based on the detected pixel ratio
                # Using a sigmoid-like scaling to prevent extreme values
                pixel_factor = 2.0 * (shoulder_pixel_ratio - 0.25) # Normalize around 0.25 which is typical
                adjustment_factor = max(-0.7, min(0.7, pixel_factor)) # Limit adjustment
                
                # Calculate detected shoulder width with constraints
                detected_shoulder_cm = typical_shoulder_cm * (1 + (0.15 * adjustment_factor))
                
                # Ensure result stays within anatomical limits
                detected_shoulder_cm = max(min_shoulder_cm, min(detected_shoulder_cm, max_shoulder_cm))
                
                # High confidence weighting for shoulders - we trust the visual data more
                confidence_factor = 0.7  # How much to trust the visual detection vs statistical average
                shoulders_cm = (typical_shoulder_cm * (1 - confidence_factor)) + (detected_shoulder_cm * confidence_factor)
                
                # Mark as reliable if confidence is high
                confidence["shoulders_cm"] = 0.85
                reliable_measurements.append("shoulders_cm")
            else:
                # If the detected value is unreasonable, rely more on statistical values
                logger.warning(f"Detected unusual shoulder width: {segments['shoulder_width']}")
                # Still use detected value but with very low confidence
                confidence["shoulders_cm"] = 0.5
        
        # 2. WAIST CALCULATION
        # Waist-to-hip ratio and waist-to-height ratio are important anthropometric indicators
        waist_cm = height_cm * reference['waist_ratio'][1]  # Start with typical value
        
        if 'shoulder_to_hip_ratio' in segments and segments['shoulder_to_hip_ratio'] > 0:
            # Adjust waist based on the detected shoulder-to-hip ratio
            expected_ratio = 1.4 if gender.lower() == 'male' else 1.2
            ratio_deviation = segments['shoulder_to_hip_ratio'] - expected_ratio
            
            # Use limited adjustment factor
            ratio_adjustment = max(-0.1, min(0.1, ratio_deviation * 0.4))
            
            # Lower waist if shoulder-to-hip ratio is higher than expected (v-shape)
            # Increase waist if shoulder-to-hip ratio is lower than expected
            waist_cm *= (1 - ratio_adjustment)
            
            # Adjust confidence based on deviation from expected ratio
            if abs(ratio_deviation) < 0.2:  # Reasonable deviation
                confidence["waist_cm"] = 0.8
                reliable_measurements.append("waist_cm")
            else:
                confidence["waist_cm"] = 0.6
        
        # 3. APPLY BMI ADJUSTMENTS to circumference estimates with research-based factors
        # BMI influences certain measurements more than others
        
        # Different influence factors based on research
        bmi_influences = {
            'waist_ratio': 0.8,    # Waist is strongly influenced by BMI
            'hip_ratio': 0.6,      # Hips are moderately influenced
            'thigh_ratio': 0.5,    # Thighs are moderately influenced
            'arm_ratio': 0.4,      # Arms are less influenced
            'chest_ratio': 0.3,    # Chest is less influenced
            'calf_ratio': 0.3,     # Calves are less influenced
            'neck_ratio': 0.2,     # Neck is minimally influenced
            'wrist_ratio': 0.1,    # Wrist is minimally influenced
            'ankle_ratio': 0.1,    # Ankle is minimally influenced
        }
        
        # Calculate BMI-adjusted typical values
        bmi_adjusted_values = {}
        for key, (min_ratio, typical_ratio, max_ratio) in reference.items():
            if key in bmi_influences:
                # Calculate BMI-adjusted value within anatomical constraints
                influence = bmi_influences[key.replace('_ratio', '')]
                bmi_adjusted_values[key] = typical_ratio * (1 + ((bmi_factor - 1) * influence))
                
                # Ensure the adjusted value stays within anatomical limits
                bmi_adjusted_values[key] = max(min_ratio, min(bmi_adjusted_values[key], max_ratio))
        
        # 4. EXPERIENCE-BASED ADJUSTMENTS
        # Training experience influences muscle mass distribution
        muscle_factors = {
            'arm_ratio': 1.0,
            'chest_ratio': 1.0,
            'thigh_ratio': 1.0,
            'calf_ratio': 1.0,
            'neck_ratio': 1.0,
        }
        
        if experience == "intermediate":
            # Intermediate lifters have ~3-5% more muscle in targeted areas
            muscle_factors['arm_ratio'] = 1.03
            muscle_factors['chest_ratio'] = 1.03
            muscle_factors['thigh_ratio'] = 1.02
            muscle_factors['calf_ratio'] = 1.02
            muscle_factors['neck_ratio'] = 1.02
        elif experience == "advanced":
            # Advanced lifters have ~5-10% more muscle in targeted areas
            muscle_factors['arm_ratio'] = 1.07
            muscle_factors['chest_ratio'] = 1.06
            muscle_factors['thigh_ratio'] = 1.05
            muscle_factors['calf_ratio'] = 1.04
            muscle_factors['neck_ratio'] = 1.03
        
        # Apply muscle factors to BMI-adjusted values
        for key in muscle_factors:
            if key in bmi_adjusted_values:
                # Apply the factor with a cap to ensure we stay in reasonable range
                bmi_adjusted_values[key] *= muscle_factors[key]
                
                # Re-check against anatomical limits
                min_ratio, _, max_ratio = reference[key]
                bmi_adjusted_values[key] = max(min_ratio, min(bmi_adjusted_values[key], max_ratio))
        
        # 5. CALCULATE ALL FINAL MEASUREMENTS
        # Combine all adjustment factors and calculate actual cm values
        
        # Add the shoulder width we already calculated
        measurements["shoulders_cm"] = round(shoulders_cm, 1)
        measurements["waist_cm"] = round(waist_cm, 1)
        
        # Calculate remaining measurements
        measurements["neck_cm"] = round(height_cm * bmi_adjusted_values['neck_ratio'], 1)
        measurements["chest_cm"] = round(height_cm * bmi_adjusted_values['chest_ratio'], 1)
        measurements["hips_cm"] = round(height_cm * bmi_adjusted_values['hip_ratio'], 1)
        
        # Limb measurements
        # Small intentional asymmetry for naturalness (1-2% difference)
        arm_cm = height_cm * bmi_adjusted_values['arm_ratio']
        measurements["left_arm_cm"] = round(arm_cm * 0.99, 1)  # Slightly smaller non-dominant arm
        measurements["right_arm_cm"] = round(arm_cm * 1.01, 1)
        
        thigh_cm = height_cm * bmi_adjusted_values['thigh_ratio']
        measurements["left_thigh_cm"] = round(thigh_cm * 0.995, 1)
        measurements["right_thigh_cm"] = round(thigh_cm * 1.005, 1)
        
        calf_cm = height_cm * bmi_adjusted_values['calf_ratio']
        measurements["left_calf_cm"] = round(calf_cm * 0.995, 1)
        measurements["right_calf_cm"] = round(calf_cm * 1.005, 1)
        
        measurements["wrist_cm"] = round(height_cm * bmi_adjusted_values['wrist_ratio'], 1)
        measurements["ankle_cm"] = round(height_cm * bmi_adjusted_values['ankle_ratio'], 1)
        
        # 6. SEGMENT-BASED FINE-TUNING FOR ARM AND LEG LENGTHS
        # Use the detected segments to adjust limb measurements if available
        
        # Arm length adjustment
        if 'left_arm' in segments and 'right_arm' in segments:
            avg_arm_segment = (segments['left_arm'] + segments['right_arm']) / 2
            
            if 0 < avg_arm_segment < 0.8:  # Reasonable range check
                # Typical arm length as percentage of height
                arm_length_ratio = length_props['arm_length_ratio'][1]
                
                # Map the detected arm length to a circumference adjustment
                # Longer limbs tend to have slightly smaller circumference
                arm_length_factor = 2.0 * (avg_arm_segment - 0.3)  # Normalize around 0.3
                arm_adjustment = max(-0.1, min(0.1, arm_length_factor * -0.05))  # Inverse relationship
                
                # Apply adjustment to arm measurements
                measurements["left_arm_cm"] *= (1 + arm_adjustment)
                measurements["right_arm_cm"] *= (1 + arm_adjustment)
                
                # Increase confidence slightly
                confidence["arm_cm"] += 0.1
        
        # Leg length adjustment
        if 'left_leg' in segments and 'right_leg' in segments:
            avg_leg_segment = (segments['left_leg'] + segments['right_leg']) / 2
            
            if 0 < avg_leg_segment < 0.8:  # Reasonable range check
                # Map the detected leg length to a circumference adjustment
                leg_length_factor = 2.0 * (avg_leg_segment - 0.4)  # Normalize around 0.4
                leg_adjustment = max(-0.1, min(0.1, leg_length_factor * -0.05))  # Inverse relationship
                
                # Apply adjustment to leg measurements
                measurements["left_thigh_cm"] *= (1 + leg_adjustment)
                measurements["right_thigh_cm"] *= (1 + leg_adjustment)
                measurements["left_calf_cm"] *= (1 + leg_adjustment)
                measurements["right_calf_cm"] *= (1 + leg_adjustment)
                
                # Increase confidence slightly
                confidence["thigh_cm"] += 0.1
                confidence["calf_cm"] += 0.1
        
        # 7. FLAG RELIABLE MEASUREMENTS
        # Mark any measurement with confidence >= 0.8 as reliable
        for measure, conf in confidence.items():
            measure_key = measure.replace("_cm", "_cm")
            if conf >= 0.8 and measure_key in measurements:
                if measure_key not in reliable_measurements:
                    reliable_measurements.append(measure_key)
        
        # Record metadata
        measurements["estimation_method"] = "multi_method_enhanced"
        measurements["reliable_measurements"] = reliable_measurements
        measurements["confidence_scores"] = confidence
        measurements["segments"] = segments
        
        return measurements
    
    def _estimate_from_statistics(self, height_cm, weight_kg, gender):
        """
        Fallback method that uses statistical population averages with anthropometric constraints
        when landmarks can't be reliably detected. Based on large population studies including
        NHANES, ANSUR II, and CAESAR 3D anthropometric database.
        
        This provides reliable baseline estimates based solely on height, weight, and gender.
        """
        # Calculate BMI
        bmi = weight_kg / ((height_cm / 100) ** 2) if height_cm > 0 and weight_kg > 0 else 22
        bmi_factor = self._calculate_bmi_adjustment(bmi, gender)
        
        # Define base anthropometric ratios and ranges using the triple format (min, typical, max)
        # These values represent percentages of height
        if gender.lower() == 'male':
            reference = {
                'neck_ratio': (0.185, 0.195, 0.205),
                'chest_ratio': (0.45, 0.475, 0.50),
                'shoulders_ratio': (0.225, 0.245, 0.265),
                'waist_ratio': (0.38, 0.42, 0.46),
                'hip_ratio': (0.41, 0.435, 0.46),
                'arm_ratio': (0.11, 0.12, 0.13),
                'thigh_ratio': (0.19, 0.205, 0.22),
                'calf_ratio': (0.12, 0.13, 0.14),
                'wrist_ratio': (0.085, 0.09, 0.095),
                'ankle_ratio': (0.095, 0.10, 0.105),
            }
        else:
            reference = {
                'neck_ratio': (0.175, 0.185, 0.195),
                'chest_ratio': (0.44, 0.46, 0.48),
                'shoulders_ratio': (0.215, 0.235, 0.255),
                'waist_ratio': (0.36, 0.39, 0.42),
                'hip_ratio': (0.44, 0.465, 0.49),
                'arm_ratio': (0.105, 0.115, 0.125),
                'thigh_ratio': (0.20, 0.215, 0.23),
                'calf_ratio': (0.12, 0.13, 0.14),
                'wrist_ratio': (0.075, 0.08, 0.085),
                'ankle_ratio': (0.09, 0.095, 0.10),
            }
            
        # BMI influence factors - how much each measurement is affected by BMI
        bmi_influences = {
            'waist_ratio': 0.8,    # Waist is strongly influenced by BMI
            'hip_ratio': 0.6,      # Hips are moderately influenced
            'thigh_ratio': 0.5,    # Thighs are moderately influenced
            'arm_ratio': 0.4,      # Arms are less influenced
            'chest_ratio': 0.3,    # Chest is less influenced
            'calf_ratio': 0.3,     # Calves are less influenced
            'neck_ratio': 0.2,     # Neck is minimally influenced
            'wrist_ratio': 0.1,    # Wrist is minimally influenced
            'ankle_ratio': 0.1,    # Ankle is minimally influenced
        }
        
        # Apply BMI adjustments to ratios within anatomical constraints
        adjusted_ratios = {}
        for key, (min_ratio, typical_ratio, max_ratio) in reference.items():
            # Start with the typical ratio
            ratio = typical_ratio
            
            # Apply BMI adjustment if applicable
            if key in bmi_influences:
                influence = bmi_influences[key]
                ratio = typical_ratio * (1 + ((bmi_factor - 1) * influence))
                
                # Constrain to anatomical limits
                ratio = max(min_ratio, min(ratio, max_ratio))
            
            adjusted_ratios[key] = ratio
            
        # Calculate measurements with slight natural asymmetry
        # Small natural asymmetry makes measurements more realistic
        measurements = {
            "neck_cm": round(height_cm * adjusted_ratios['neck_ratio'], 1),
            "chest_cm": round(height_cm * adjusted_ratios['chest_ratio'], 1),
            "shoulders_cm": round(height_cm * adjusted_ratios['shoulders_ratio'], 1),
            "waist_cm": round(height_cm * adjusted_ratios['waist_ratio'], 1),
            "hips_cm": round(height_cm * adjusted_ratios['hip_ratio'], 1),
            
            # Slight asymmetry for limbs
            "left_arm_cm": round(height_cm * adjusted_ratios['arm_ratio'] * 0.99, 1),
            "right_arm_cm": round(height_cm * adjusted_ratios['arm_ratio'] * 1.01, 1),
            "left_thigh_cm": round(height_cm * adjusted_ratios['thigh_ratio'] * 0.995, 1),
            "right_thigh_cm": round(height_cm * adjusted_ratios['thigh_ratio'] * 1.005, 1),
            "left_calf_cm": round(height_cm * adjusted_ratios['calf_ratio'] * 0.995, 1),
            "right_calf_cm": round(height_cm * adjusted_ratios['calf_ratio'] * 1.005, 1),
            
            "wrist_cm": round(height_cm * adjusted_ratios['wrist_ratio'], 1),
            "ankle_cm": round(height_cm * adjusted_ratios['ankle_ratio'], 1),
            
            # Metadata
            "estimation_method": "anthropometric_statistical",
            "reliable_estimation": False,
            "confidence_scores": {
                "neck_cm": 0.6,
                "chest_cm": 0.6,
                "shoulders_cm": 0.7,
                "waist_cm": 0.7,
                "hips_cm": 0.6,
                "arm_cm": 0.6,
                "thigh_cm": 0.6,
                "calf_cm": 0.5,
                "wrist_cm": 0.5,
                "ankle_cm": 0.4,
            }
        }
        
        return measurements
    
    def _calculate_bmi_adjustment(self, bmi, gender):
        """
        Calculate BMI-based adjustment factor using a sigmoid-like function that provides
        more natural and accurate adjustments across the BMI spectrum.
        
        This approach:
        1. Uses gender-specific healthy BMI reference points
        2. Applies proportional adjustment based on distance from reference
        3. Limits extreme values with a sigmoid-like curve
        4. Handles athletic builds (can have higher BMI but lower body fat)
        
        Returns a multiplier for body measurements.
        """
        # Gender-specific BMI reference ranges (based on WHO and athletic research)
        if gender.lower() == 'male':
            # Male reference points
            min_healthy_bmi = 18.5
            optimal_bmi = 22.0
            max_healthy_bmi = 25.0
            athletic_threshold = 27.0  # BMI where athletic builds diverge from general population
        else:
            # Female reference points
            min_healthy_bmi = 18.0
            optimal_bmi = 21.0
            max_healthy_bmi = 24.0
            athletic_threshold = 25.0
        
        # Constants for adjustment calculation
        MAX_UNDERWEIGHT_ADJUSTMENT = 0.92  # Maximum reduction for severe underweight
        MAX_OVERWEIGHT_ADJUSTMENT = 1.18   # Maximum increase for severe overweight
        
        # Calculate base adjustment using distance from optimal
        if bmi <= optimal_bmi:
            # Underweight adjustment using sigmoid-like curve for smooth transition
            # This approaches MAX_UNDERWEIGHT_ADJUSTMENT as BMI decreases
            bmi_diff = optimal_bmi - bmi
            max_diff = optimal_bmi - 16.0  # Reference point for severe underweight
            
            if bmi_diff <= 0:
                return 1.0  # No adjustment at optimal BMI
            else:
                # Sigmoid-like function that approaches MAX_UNDERWEIGHT_ADJUSTMENT asymptotically
                adjustment_factor = 1.0 - ((1.0 - MAX_UNDERWEIGHT_ADJUSTMENT) * 
                                          (bmi_diff / max_diff) * 
                                          (2.0 / (1.0 + math.exp(-1.5 * bmi_diff))))
                
                # Ensure we don't go below minimum adjustment
                return max(MAX_UNDERWEIGHT_ADJUSTMENT, adjustment_factor)
        else:
            # Overweight adjustment with athletic build consideration
            bmi_diff = bmi - optimal_bmi
            
            # Detect potential athletic builds (higher BMI but may have less fat)
            # Athletic builds get smaller adjustments in the moderate BMI range
            if bmi <= athletic_threshold:
                # In the range between optimal and athletic threshold, use reduced adjustment
                adjustment_rate = 0.6  # Slower adjustment rate for potentially athletic builds
            else:
                # Above athletic threshold, use standard adjustment
                adjustment_rate = 1.0
            
            # Calculate adjustment using sigmoid-like curve for smooth transition
            adjustment_factor = 1.0 + ((MAX_OVERWEIGHT_ADJUSTMENT - 1.0) * 
                                      adjustment_rate * 
                                      (bmi_diff / 15.0) *  # Normalize by reference range
                                      (2.0 / (1.0 + math.exp(-0.25 * bmi_diff))))
            
            # Ensure we don't exceed maximum adjustment
            return min(MAX_OVERWEIGHT_ADJUSTMENT, adjustment_factor)


# Main function to use in the app
def estimate_measurements(image_data, height_cm, weight_kg, gender, experience="beginner"):
    """Top-level function to estimate body measurements from an image"""
    estimator = BodyMeasurementEstimator()
    return estimator.estimate_measurements(image_data, height_cm, weight_kg, gender, experience)