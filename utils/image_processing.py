import cv2
import numpy as np
import mediapipe as mp
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def process_image(image):
    """
    Pre-process the image for body analysis
    
    Args:
        image: OpenCV image (numpy array)
        
    Returns:
        Processed image (numpy array)
    """
    # Resize image to a standard size if needed
    max_dimension = 1024
    height, width = image.shape[:2]
    
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height))
    
    # Convert to RGB (MediaPipe uses RGB)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    return image_rgb

def extract_body_landmarks(image):
    """
    Extract body landmarks using MediaPipe
    
    Args:
        image: OpenCV image (numpy array)
        
    Returns:
        Tuple of (annotated image, landmarks dictionary)
    """
    try:
        # Process the image
        image_rgb = process_image(image)
        height, width = image_rgb.shape[:2]
        
        # Initialize MediaPipe Pose
        with mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,  # Use higher accuracy model
            enable_segmentation=True,
            min_detection_confidence=0.5
        ) as pose:
            # Get pose landmarks
            results = pose.process(image_rgb)
            
            if not results.pose_landmarks:
                logger.warning("No pose landmarks detected")
                return image, None
            
            # Create a copy of the image for annotation
            annotated_image = image.copy()
            
            # Draw pose landmarks on the image
            mp_drawing.draw_landmarks(
                annotated_image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
            
            # Extract landmarks into a dictionary with normalized coordinates
            landmarks = {}
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                landmarks[idx] = {
                    'x': landmark.x * width,
                    'y': landmark.y * height,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                }
            
            return annotated_image, landmarks
            
    except Exception as e:
        logger.error(f"Error extracting landmarks: {str(e)}")
        return image, None
