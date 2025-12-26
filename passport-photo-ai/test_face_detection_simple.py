#!/usr/bin/env python3
"""
Simple test of face detection on user_test_photo.jpg
"""

import sys
import os
sys.path.append('backend')

import cv2
import numpy as np
from enhancement.face_detection import FaceDetectionPipeline

def main():
    # Test with the original user test photo
    test_image_path = "user_test_photo.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"Test image {test_image_path} not found")
        return
    
    # Load image
    image = cv2.imread(test_image_path)
    if image is None:
        print(f"Failed to load image {test_image_path}")
        return
    
    print(f"Loaded image: {test_image_path}")
    print(f"Image shape: {image.shape}")
    
    # Test face detection
    detector = FaceDetectionPipeline()
    result = detector.detect_faces(image)
    
    print(f"\nFace detection results:")
    print(f"  Faces detected: {len(result.faces)}")
    print(f"  Primary face: {result.primary_face is not None}")
    print(f"  Overall confidence: {result.confidence:.3f}")
    print(f"  Multiple faces detected: {result.multiple_faces_detected}")
    print(f"  Requires manual review: {result.requires_manual_review}")
    print(f"  Error message: {result.error_message}")
    
    if result.primary_face:
        face = result.primary_face
        x, y, w, h = face.bounding_box
        print(f"\nPrimary face details:")
        print(f"  Bounding box: ({x}, {y}, {w}, {h})")
        print(f"  Face size ratio: {face.face_size_ratio:.3f}")
        print(f"  Confidence: {face.confidence:.3f}")
        print(f"  Eye positions: {face.eye_positions}")
        
        # Test compliance
        compliance = detector.validate_face_compliance(face, image.shape[:2])
        print(f"\nCompliance check:")
        print(f"  Overall compliant: {compliance.is_compliant}")
        print(f"  Face size valid: {compliance.face_size_valid}")
        print(f"  Eye positioning valid: {compliance.eye_positioning_valid}")
        print(f"  Centering valid: {compliance.centering_valid}")
        print(f"  Issues: {compliance.issues}")
        
        # Draw detection on image and save
        debug_image = image.copy()
        cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(debug_image, f"Conf: {face.confidence:.3f}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(debug_image, f"Ratio: {face.face_size_ratio:.3f}", (x, y-30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if face.eye_positions:
            left_eye, right_eye = face.eye_positions
            cv2.circle(debug_image, left_eye, 5, (255, 0, 0), -1)
            cv2.circle(debug_image, right_eye, 5, (255, 0, 0), -1)
        
        cv2.imwrite('debug_face_detection_result.jpg', debug_image)
        print(f"\nSaved detection result to debug_face_detection_result.jpg")

if __name__ == "__main__":
    main()