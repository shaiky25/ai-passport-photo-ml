#!/usr/bin/env python3
"""
Detailed debugging of face detection
"""

import sys
import os
sys.path.append('backend')

import cv2
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    print("✓ MediaPipe is available")
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("✗ MediaPipe is NOT available")

def test_opencv_detection(image):
    """Test OpenCV face detection directly"""
    print("\n=== Testing OpenCV Face Detection ===")
    
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        detector = cv2.CascadeClassifier(cascade_path)
        
        if detector.empty():
            print("✗ Failed to load OpenCV cascade")
            return []
        
        print("✓ OpenCV cascade loaded successfully")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = image.shape[:2]
        
        print(f"Image dimensions: {width}x{height}")
        print(f"Grayscale conversion: OK")
        
        # Try different parameters
        for scale_factor in [1.1, 1.2, 1.3]:
            for min_neighbors in [3, 5, 7]:
                print(f"Trying scale_factor={scale_factor}, min_neighbors={min_neighbors}")
                
                faces = detector.detectMultiScale(
                    gray,
                    scaleFactor=scale_factor,
                    minNeighbors=min_neighbors,
                    minSize=(30, 30),  # Smaller minimum size
                    maxSize=(int(width*0.9), int(height*0.9)),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                print(f"  Found {len(faces)} faces")
                
                if len(faces) > 0:
                    print(f"  Face rectangles: {faces}")
                    return faces
        
        print("No faces found with any parameters")
        return []
        
    except Exception as e:
        print(f"✗ OpenCV detection failed: {e}")
        return []

def test_mediapipe_detection(image):
    """Test MediaPipe face detection directly"""
    print("\n=== Testing MediaPipe Face Detection ===")
    
    if not MEDIAPIPE_AVAILABLE:
        print("✗ MediaPipe not available")
        return []
    
    try:
        mp_face_detection = mp.solutions.face_detection
        
        # Try different confidence thresholds
        for confidence in [0.1, 0.3, 0.5]:
            print(f"Trying confidence threshold: {confidence}")
            
            detector = mp_face_detection.FaceDetection(
                model_selection=0,
                min_detection_confidence=confidence
            )
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            height, width = image.shape[:2]
            
            results = detector.process(rgb_image)
            
            if results.detections:
                print(f"  Found {len(results.detections)} faces")
                for i, detection in enumerate(results.detections):
                    bbox = detection.location_data.relative_bounding_box
                    x = int(bbox.xmin * width)
                    y = int(bbox.ymin * height)
                    w = int(bbox.width * width)
                    h = int(bbox.height * height)
                    conf = detection.score[0] if detection.score else 0.0
                    print(f"    Face {i}: bbox=({x}, {y}, {w}, {h}), confidence={conf:.3f}")
                
                return results.detections
            else:
                print(f"  No faces found with confidence {confidence}")
        
        print("No faces found with any confidence threshold")
        return []
        
    except Exception as e:
        print(f"✗ MediaPipe detection failed: {e}")
        return []

def main():
    test_images = [
        "backend/test_images/faiz.png",
        "backend/test_images/sample_image_1.jpg", 
        "backend/test_images/sample_image_2.jpg",
        "user_test_photo.jpg"
    ]
    
    for test_image_path in test_images:
        print(f"\n{'='*60}")
        print(f"Testing: {test_image_path}")
        print(f"{'='*60}")
        
        if not os.path.exists(test_image_path):
            print(f"✗ Image {test_image_path} not found")
            continue
        
        # Load image
        image = cv2.imread(test_image_path)
        if image is None:
            print(f"✗ Failed to load image {test_image_path}")
            continue
        
        print(f"✓ Loaded image: {test_image_path}")
        print(f"  Image shape: {image.shape}")
        print(f"  Image dtype: {image.dtype}")
        print(f"  Image min/max values: {image.min()}/{image.max()}")
        
        # Test both detection methods
        opencv_faces = test_opencv_detection(image)
        mediapipe_faces = test_mediapipe_detection(image)
        
        print(f"\n--- Summary for {test_image_path} ---")
        print(f"OpenCV faces found: {len(opencv_faces)}")
        print(f"MediaPipe faces found: {len(mediapipe_faces)}")
        
        # If we found faces, draw them
        if len(opencv_faces) > 0 or len(mediapipe_faces) > 0:
            debug_image = image.copy()
            
            # Draw OpenCV faces in green
            for (x, y, w, h) in opencv_faces:
                cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(debug_image, "OpenCV", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw MediaPipe faces in blue
            if mediapipe_faces:
                height, width = image.shape[:2]
                for detection in mediapipe_faces:
                    bbox = detection.location_data.relative_bounding_box
                    x = int(bbox.xmin * width)
                    y = int(bbox.ymin * height)
                    w = int(bbox.width * width)
                    h = int(bbox.height * height)
                    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(debug_image, "MediaPipe", (x, y-30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Save with unique name
            base_name = os.path.splitext(os.path.basename(test_image_path))[0]
            output_path = f'debug_detection_{base_name}.jpg'
            cv2.imwrite(output_path, debug_image)
            print(f"✓ Saved detection results to {output_path}")
        else:
            print("✗ No faces detected by either method")

if __name__ == "__main__":
    main()