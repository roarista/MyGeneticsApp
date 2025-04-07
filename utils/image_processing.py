import cv2
import numpy as np
import mediapipe as mp
import logging
from .measurement_validator import MeasurementValidator

# Configure logging
logger = logging.getLogger(__name__)

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def process_image(image):
    """
    Pre-process the image for body analysis with enhanced feature extraction
    
    Args:
        image: OpenCV image (numpy array)
        
    Returns:
        Tuple of (processed image (numpy array), height, width)
    """
    # Make a copy to avoid modifying the original
    processed = image.copy()
    
    # Resize image to a standard size if needed
    max_dimension = 1024
    height, width = processed.shape[:2]
    
    # Initialize new dimensions with current dimensions
    new_height, new_width = height, width
    
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        processed = cv2.resize(processed, (new_width, new_height))
    
    # Apply slight Gaussian blur to reduce noise (helps with edge detection)
    processed = cv2.GaussianBlur(processed, (3, 3), 0)
    
    # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # This improves details in areas with different lighting conditions
    lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)
    merged = cv2.merge((cl, a_channel, b_channel))
    processed = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    
    # Sharpening to enhance edges (helps with muscle definition detection)
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    processed = cv2.filter2D(processed, -1, kernel)
    
    # Convert to RGB (MediaPipe uses RGB)
    image_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
    
    return image_rgb, new_height, new_width

def extract_body_landmarks(image, height_cm=0):
    """
    Extract body landmarks using MediaPipe with improved coordinate normalization
    
    Args:
        image: OpenCV image (numpy array)
        height_cm: User's height in cm (optional, for real-world scaling)
        
    Returns:
        Tuple of (annotated image, landmarks dictionary, confidence scores dictionary)
    """
    try:
        # Process the image
        image_rgb, height_px, width_px = process_image(image)
        
        # Initialize MediaPipe Pose with enhanced settings
        with mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,  # Use higher accuracy model
            enable_segmentation=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as pose:
            # Get pose landmarks
            results = pose.process(image_rgb)
            
            if not results.pose_landmarks:
                logger.warning("No pose landmarks detected")
                return image, None, None
            
            # Create a copy of the image for annotation
            annotated_image = image.copy()
            
            # Draw pose landmarks on the image
            mp_drawing.draw_landmarks(
                annotated_image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
            
            # Extract landmarks into a dictionary
            landmarks = {}
            confidence_scores = {}
            
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                # Store pixel coordinates scaled to image dimensions
                landmarks[idx] = {
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                }
                
                # Store confidence scores for each landmark (visibility is used as a proxy for confidence)
                confidence_level = "high" if landmark.visibility > 0.8 else "medium" if landmark.visibility > 0.5 else "low"
                confidence_scores[idx] = {
                    'score': float(landmark.visibility),
                    'level': confidence_level
                }
            
            # If height is provided, use the measurement validator to convert to real-world units
            if height_cm > 0:
                validator = MeasurementValidator()
                # Use validator to normalize coordinates to real-world measurements
                landmarks = validator.normalize_coordinates(landmarks, height_px, width_px, height_cm)
                
            return annotated_image, landmarks, confidence_scores
            
    except Exception as e:
        logger.error(f"Error extracting landmarks: {str(e)}")
        return image, None, None
