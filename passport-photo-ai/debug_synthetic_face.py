#!/usr/bin/env python3
"""
Debug script to understand synthetic face creation vs detection
"""

import sys
import os
sys.path.append('backend')

import cv2
import numpy as np
from enhancement.face_detection import FaceDetectionPipeline

def create_synthetic_face(image_size: int, face_size_ratio: float, 
                         center_offset_x: int, center_offset_y: int) -> np.ndarray:
    """Create a more realistic synthetic face image for testing"""
    # Create base image with slight texture
    image = np.random.randint(210, 230, (image_size, image_size, 3), dtype=np.uint8)
    
    # Calculate face dimensions
    face_height = int(image_size * face_size_ratio)
    face_width = int(face_height * 0.75)  # More realistic face proportions
    
    # Calculate center position with offset
    center_x = image_size // 2 + center_offset_x
    center_y = image_size // 2 + center_offset_y
    
    # Ensure face stays within image bounds
    center_x = max(face_width//2, min(center_x, image_size - face_width//2))
    center_y = max(face_height//2, min(center_y, image_size - face_height//2))
    
    print(f"Creating face:")
    print(f"  Image size: {image_size}x{image_size}")
    print(f"  Target face_size_ratio: {face_size_ratio}")
    print(f"  Calculated face_height: {face_height} (should be {face_size_ratio * image_size})")
    print(f"  Calculated face_width: {face_width}")
    print(f"  Center: ({center_x}, {center_y})")
    
    # Draw face shape (more realistic oval)
    face_color = (180, 150, 120)  # More realistic skin tone
    cv2.ellipse(image, (center_x, center_y), (face_width//2, face_height//2), 
               0, 0, 360, face_color, -1)
    
    # Add face shading for more realism
    cv2.ellipse(image, (center_x - face_width//6, center_y - face_height//8), 
               (face_width//3, face_height//3), 0, 0, 360, (160, 130, 100), -1)
    
    # Draw more realistic eyes
    eye_y = center_y - face_height//5
    eye_spacing = face_width//4
    eye_width = face_width//8
    eye_height = face_height//12
    
    # Left eye
    left_eye_x = center_x - eye_spacing
    cv2.ellipse(image, (left_eye_x, eye_y), (eye_width, eye_height), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(image, (left_eye_x, eye_y), eye_height//2, (100, 50, 30), -1)  # Iris
    cv2.circle(image, (left_eye_x, eye_y), eye_height//4, (0, 0, 0), -1)  # Pupil
    
    # Right eye
    right_eye_x = center_x + eye_spacing
    cv2.ellipse(image, (right_eye_x, eye_y), (eye_width, eye_height), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(image, (right_eye_x, eye_y), eye_height//2, (100, 50, 30), -1)  # Iris
    cv2.circle(image, (right_eye_x, eye_y), eye_height//4, (0, 0, 0), -1)  # Pupil
    
    # Draw eyebrows
    cv2.ellipse(image, (left_eye_x, eye_y - eye_height), (eye_width, eye_height//3), 
               0, 0, 180, (80, 60, 40), 3)
    cv2.ellipse(image, (right_eye_x, eye_y - eye_height), (eye_width, eye_height//3), 
               0, 0, 180, (80, 60, 40), 3)
    
    # Draw nose
    nose_y = center_y
    nose_width = face_width//12
    nose_height = face_height//8
    cv2.ellipse(image, (center_x, nose_y), (nose_width, nose_height), 0, 0, 360, (160, 130, 100), -1)
    
    # Draw nostrils
    cv2.circle(image, (center_x - nose_width//2, nose_y + nose_height//2), 2, (120, 90, 70), -1)
    cv2.circle(image, (center_x + nose_width//2, nose_y + nose_height//2), 2, (120, 90, 70), -1)
    
    # Draw mouth
    mouth_y = center_y + face_height//4
    mouth_width = face_width//4
    mouth_height = face_height//20
    cv2.ellipse(image, (center_x, mouth_y), (mouth_width, mouth_height), 0, 0, 180, (120, 80, 60), -1)
    
    # Add some facial structure
    # Cheekbones
    cv2.ellipse(image, (center_x - face_width//3, center_y + face_height//8), 
               (face_width//8, face_height//12), 0, 0, 360, (160, 130, 100), -1)
    cv2.ellipse(image, (center_x + face_width//3, center_y + face_height//8), 
               (face_width//8, face_height//12), 0, 0, 360, (160, 130, 100), -1)
    
    return image

def main():
    # Test parameters
    image_size = 600
    face_size_ratio = 0.75
    center_offset_x = 0
    center_offset_y = 0
    
    # Create synthetic face
    test_image = create_synthetic_face(image_size, face_size_ratio, center_offset_x, center_offset_y)
    
    # Save for inspection
    cv2.imwrite('debug_synthetic_face.jpg', test_image)
    print(f"Saved synthetic face to debug_synthetic_face.jpg")
    
    # Test detection
    detector = FaceDetectionPipeline()
    result = detector.detect_faces(test_image)
    
    print(f"\nDetection results:")
    print(f"  Faces detected: {len(result.faces)}")
    
    if result.primary_face:
        face = result.primary_face
        x, y, w, h = face.bounding_box
        detected_ratio = face.face_size_ratio
        
        print(f"  Primary face bounding box: ({x}, {y}, {w}, {h})")
        print(f"  Detected face_size_ratio: {detected_ratio}")
        print(f"  Expected face_size_ratio: {face_size_ratio}")
        print(f"  Ratio difference: {abs(detected_ratio - face_size_ratio)}")
        print(f"  Face height vs image height: {h}/{image_size} = {h/image_size}")
        
        # Test compliance
        compliance = detector.validate_face_compliance(face, test_image.shape[:2])
        print(f"  Face size valid: {compliance.face_size_valid}")
        print(f"  Issues: {compliance.issues}")
        
        # Draw detection on image
        debug_image = test_image.copy()
        cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(debug_image, f"Ratio: {detected_ratio:.3f}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imwrite('debug_detection_result.jpg', debug_image)
        print(f"Saved detection result to debug_detection_result.jpg")
    else:
        print(f"  No face detected!")
        print(f"  Error: {result.error_message}")

if __name__ == "__main__":
    main()