"""
This script analyzes a directory of compliant passport photos to learn the
optimal geometric properties (e.g., head size, position) for cropping.

To use:
1. Create a directory named 'training_data' inside the 'backend' directory.
2. Populate 'training_data' with a diverse set of high-quality, compliant
   passport photos (e.g., 20-50 images).
3. Run this script from the 'backend' directory:
   python learn_from_samples.py

This will generate a 'learned_profile.json' file containing the statistical
average and standard deviation of key facial features. The main application
will use this file to perform more intelligent, data-driven cropping.
"""
import cv2
import numpy as np
import os
import json

class PassportPhotoAnalyzer:
    """
    A simplified version of the processor for feature extraction from samples.
    """
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def analyze_image_features(self, image_path):
        """
        Analyzes a single image and extracts key geometric features of the face.
        """
        img = cv2.imread(image_path)
        if img is None:
            print(f"Warning: Could not read image {image_path}. Skipping.")
            return None
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
        
        if len(faces) != 1:
            print(f"Warning: Found {len(faces)} faces in {image_path}. Expected 1. Skipping.")
            return None
        
        x, y, w, h = faces[0]
        img_height, img_width = img.shape[:2]
        
        # Calculate the position of the top of the head, assuming it's roughly
        # 10-15% of the face height above the face bounding box 'y' coordinate.
        # This is an approximation to get a better "full head" height.
        head_top_y = max(0, y - (h * 0.15))
        full_head_height = (y + h) - head_top_y
        
        # Calculate key ratios
        head_height_ratio = full_head_height / img_height
        face_center_x_ratio = (x + w / 2) / img_width
        # We care more about the top of the head's position than the center of the box
        head_top_y_ratio = head_top_y / img_height
        
        return {
            "head_height_ratio": head_height_ratio,
            "face_center_x_ratio": face_center_x_ratio,
            "head_top_y_ratio": head_top_y_ratio
        }

def learn_from_directory(training_path="training_data", output_file="learned_profile.json"):
    """
    Processes all images in the training directory and saves the statistical profile.
    """
    if not os.path.isdir(training_path):
        print(f"Error: Training directory '{training_path}' not found.")
        print("Please create it and populate it with sample images.")
        return

    analyzer = PassportPhotoAnalyzer()
    feature_list = []
    
    print(f"Analyzing images in '{training_path}'...")
    for filename in os.listdir(training_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(training_path, filename)
            features = analyzer.analyze_image_features(image_path)
            if features:
                feature_list.append(features)
    
    if not feature_list:
        print("No valid faces were found in any images. Cannot generate a profile.")
        return
        
    print(f"Successfully analyzed {len(feature_list)} images.")

    # Calculate statistics
    profile = {
        "mean": {
            "head_height_ratio": np.mean([f["head_height_ratio"] for f in feature_list]),
            "face_center_x_ratio": np.mean([f["face_center_x_ratio"] for f in feature_list]),
            "head_top_y_ratio": np.mean([f["head_top_y_ratio"] for f in feature_list]),
        },
        "std_dev": {
            "head_height_ratio": np.std([f["head_height_ratio"] for f in feature_list]),
            "face_center_x_ratio": np.std([f["face_center_x_ratio"] for f in feature_list]),
            "head_top_y_ratio": np.std([f["head_top_y_ratio"] for f in feature_list]),
        },
        "sample_size": len(feature_list)
    }
    
    # Save the learned profile
    with open(output_file, 'w') as f:
        json.dump(profile, f, indent=2)
        
    print(f"Successfully created learning profile at '{output_file}'.")
    print("\nProfile details:")
    print(json.dumps(profile, indent=2))

if __name__ == "__main__":
    learn_from_directory()
