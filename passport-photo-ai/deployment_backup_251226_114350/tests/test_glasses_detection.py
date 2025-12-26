"""
Tests for glasses and sunglasses detection in passport photos
Glasses and sunglasses are not allowed in passport photos according to ICAO standards
"""

import pytest
import numpy as np
import cv2
from PIL import Image, ImageDraw
import os
from enhancement.face_detection import FaceDetectionPipeline
from enhancement.data_models import FaceData


class TestGlassesDetection:
    """Tests for detecting glasses and sunglasses (not allowed in passport photos)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.face_detector = FaceDetectionPipeline()
        self.test_images_dir = "backend/test_images"
    
    def create_face_with_glasses(self, image_size=(800, 600), glasses_type='regular'):
        """Create test image with face wearing glasses"""
        image = Image.new('RGB', image_size, 'lightblue')
        draw = ImageDraw.Draw(image)
        
        width, height = image_size
        
        # Draw face
        face_height = int(height * 0.75)
        face_width = int(face_height * 0.8)
        face_x = (width - face_width) // 2
        face_y = (height - face_height) // 2
        
        draw.ellipse([face_x, face_y, face_x + face_width, face_y + face_height], 
                    fill=(255, 218, 185), outline=(200, 180, 160), width=2)
        
        # Draw eyes
        eye_y = face_y + face_height * 0.4
        left_eye_x = face_x + face_width * 0.3
        right_eye_x = face_x + face_width * 0.7
        eye_size = 8
        
        draw.ellipse([left_eye_x - eye_size, eye_y - eye_size//2, 
                     left_eye_x + eye_size, eye_y + eye_size//2], fill='black')
        draw.ellipse([right_eye_x - eye_size, eye_y - eye_size//2, 
                     right_eye_x + eye_size, eye_y + eye_size//2], fill='black')
        
        # Draw glasses based on type
        if glasses_type == 'regular':
            # Regular glasses - thin frames
            frame_color = 'black'
            lens_color = None  # Transparent
            frame_width = 2
        elif glasses_type == 'sunglasses':
            # Sunglasses - dark lenses
            frame_color = 'black'
            lens_color = (50, 50, 50)  # Dark gray lenses
            frame_width = 3
        elif glasses_type == 'thick_frames':
            # Thick frame glasses
            frame_color = 'black'
            lens_color = None
            frame_width = 5
        
        # Draw glasses frames and lenses
        glasses_width = int(face_width * 0.7)
        glasses_height = int(face_height * 0.2)
        glasses_x = face_x + (face_width - glasses_width) // 2
        glasses_y = eye_y - glasses_height // 2
        
        # Left lens
        left_lens_x = glasses_x
        left_lens_width = glasses_width // 2 - 10
        
        # Right lens  
        right_lens_x = glasses_x + glasses_width // 2 + 10
        right_lens_width = glasses_width // 2 - 10
        
        # Draw lenses (if sunglasses)
        if lens_color:
            draw.ellipse([left_lens_x, glasses_y, left_lens_x + left_lens_width, glasses_y + glasses_height], 
                        fill=lens_color)
            draw.ellipse([right_lens_x, glasses_y, right_lens_x + right_lens_width, glasses_y + glasses_height], 
                        fill=lens_color)
        
        # Draw frames
        draw.ellipse([left_lens_x, glasses_y, left_lens_x + left_lens_width, glasses_y + glasses_height], 
                    outline=frame_color, width=frame_width)
        draw.ellipse([right_lens_x, glasses_y, right_lens_x + right_lens_width, glasses_y + glasses_height], 
                    outline=frame_color, width=frame_width)
        
        # Draw bridge
        bridge_y = glasses_y + glasses_height // 2
        draw.line([(left_lens_x + left_lens_width, bridge_y), (right_lens_x, bridge_y)], 
                 fill=frame_color, width=frame_width)
        
        # Draw temples (arms)
        temple_length = face_width // 4
        draw.line([(left_lens_x, bridge_y), (left_lens_x - temple_length, bridge_y)], 
                 fill=frame_color, width=frame_width)
        draw.line([(right_lens_x + right_lens_width, bridge_y), (right_lens_x + right_lens_width + temple_length, bridge_y)], 
                 fill=frame_color, width=frame_width)
        
        # Create face data
        face_data = FaceData(
            bounding_box=(face_x, face_y, face_width, face_height),
            confidence=0.95,
            landmarks={
                'left_eye': (left_eye_x, eye_y),
                'right_eye': (right_eye_x, eye_y),
            },
            eye_positions=((left_eye_x, eye_y), (right_eye_x, eye_y)),
            face_size_ratio=face_height / height
        )
        
        return image, face_data
    
    def test_glasses_detection_synthetic(self):
        """Test glasses detection on synthetic images"""
        print("\n=== Testing Glasses Detection on Synthetic Images ===")
        
        test_cases = [
            {'glasses_type': 'regular', 'should_detect_glasses': True, 'should_detect_sunglasses': False},
            {'glasses_type': 'sunglasses', 'should_detect_glasses': False, 'should_detect_sunglasses': True},
            {'glasses_type': 'thick_frames', 'should_detect_glasses': True, 'should_detect_sunglasses': False},
        ]
        
        for case in test_cases:
            print(f"\nTesting: {case['glasses_type']}")
            
            # Create test image
            test_image, face_data = self.create_face_with_glasses(glasses_type=case['glasses_type'])
            img_array = np.array(test_image)
            
            # Test glasses detection
            glasses_info = self.face_detector.detect_glasses_or_sunglasses(img_array, face_data)
            
            print(f"  Glasses detected: {glasses_info['glasses_detected']}")
            print(f"  Sunglasses detected: {glasses_info['sunglasses_detected']}")
            print(f"  Confidence: {glasses_info['confidence']:.3f}")
            print(f"  Detection method: {glasses_info['detection_method']}")
            print(f"  Reasons: {glasses_info['reasons']}")
            
            if 'analysis_details' in glasses_info:
                details = glasses_info['analysis_details']
                print(f"  Line density: {details['line_density']:.4f}")
                print(f"  Brightness ratio: {details['brightness_ratio']:.3f}")
                print(f"  Eye contrast: {details['eye_contrast']:.1f}")
            
            # Test ICAO compliance with glasses
            compliance = self.face_detector.validate_eye_compliance_icao(
                face_data, test_image.size[::-1], img_array
            )
            
            print(f"  ICAO compliance: {compliance.icao_eye_compliance}")
            print(f"  Glasses in compliance: {compliance.glasses_detected}")
            print(f"  Sunglasses in compliance: {compliance.sunglasses_detected}")
            
            # Validate detection results
            if case['should_detect_glasses']:
                assert glasses_info['glasses_detected'] or compliance.glasses_detected, \
                    f"Should detect glasses for {case['glasses_type']}"
            
            if case['should_detect_sunglasses']:
                assert glasses_info['sunglasses_detected'] or compliance.sunglasses_detected, \
                    f"Should detect sunglasses for {case['glasses_type']}"
            
            # ICAO compliance should be False if any glasses detected
            if glasses_info['glasses_detected'] or glasses_info['sunglasses_detected']:
                assert not compliance.icao_eye_compliance, \
                    f"ICAO compliance should be False when glasses detected for {case['glasses_type']}"
            
            # Save test image
            output_name = f"test_glasses_{case['glasses_type']}.jpg"
            test_image.save(output_name, quality=95)
            print(f"  Saved: {output_name}")
    
    @pytest.mark.skipif(not os.path.exists("backend/test_images"), reason="Test images directory not found")
    def test_glasses_detection_real_images(self):
        """Test glasses detection on real images"""
        print("\n=== Testing Glasses Detection on Real Images ===")
        
        test_images = ["faiz.png", "sample_image_1.jpg", "sample_image_2.jpg"]
        
        for img_name in test_images:
            img_path = os.path.join(self.test_images_dir, img_name)
            if os.path.exists(img_path):
                print(f"\nTesting real image: {img_name}")
                
                # Load image
                img = Image.open(img_path).convert('RGB')
                img_array = np.array(img)
                
                # Detect faces
                face_result = self.face_detector.detect_faces(img_array)
                
                if face_result.primary_face:
                    face_data = face_result.primary_face
                    print(f"  Face detected - confidence: {face_data.confidence:.3f}")
                    
                    # Test glasses detection
                    glasses_info = self.face_detector.detect_glasses_or_sunglasses(img_array, face_data)
                    
                    print(f"  Glasses Detection Results:")
                    print(f"    Regular glasses: {glasses_info['glasses_detected']}")
                    print(f"    Sunglasses: {glasses_info['sunglasses_detected']}")
                    print(f"    Confidence: {glasses_info['confidence']:.3f}")
                    print(f"    Method: {glasses_info['detection_method']}")
                    
                    if glasses_info['reasons']:
                        print(f"    Reasons: {glasses_info['reasons']}")
                    
                    if 'analysis_details' in glasses_info:
                        details = glasses_info['analysis_details']
                        print(f"    Analysis:")
                        print(f"      Line density: {details['line_density']:.4f}")
                        print(f"      Brightness ratio: {details['brightness_ratio']:.3f}")
                        print(f"      Eye contrast: {details['eye_contrast']:.1f}")
                        print(f"      Eye brightness: {details['eye_brightness']:.1f}")
                        print(f"      Face brightness: {details['face_brightness']:.1f}")
                    
                    # Test comprehensive ICAO compliance
                    compliance = self.face_detector.validate_eye_compliance_icao(
                        face_data, img.size[::-1], img_array
                    )
                    
                    print(f"  ICAO Compliance Results:")
                    print(f"    Overall compliant: {compliance.is_compliant}")
                    print(f"    ICAO eye compliant: {compliance.icao_eye_compliance}")
                    print(f"    Eyes detected: {compliance.eyes_detected}")
                    print(f"    Glasses detected: {compliance.glasses_detected}")
                    print(f"    Sunglasses detected: {compliance.sunglasses_detected}")
                    
                    if compliance.issues:
                        print(f"    Issues:")
                        for issue in compliance.issues:
                            print(f"      - {issue}")
                    
                    # Check if glasses/sunglasses affect compliance
                    if compliance.glasses_detected or compliance.sunglasses_detected:
                        print(f"    ❌ Glasses/sunglasses detected - not suitable for passport photo")
                    else:
                        print(f"    ✅ No glasses detected - good for passport photo (eye-wise)")
                
                else:
                    print("  No face detected")
    
    def test_no_glasses_detection(self):
        """Test that faces without glasses are not flagged"""
        print("\n=== Testing No Glasses Detection ===")
        
        # Create face without glasses
        image = Image.new('RGB', (800, 600), 'lightblue')
        draw = ImageDraw.Draw(image)
        
        # Draw simple face without glasses
        face_x, face_y = 200, 100
        face_w, face_h = 400, 400
        
        draw.ellipse([face_x, face_y, face_x + face_w, face_y + face_h], 
                    fill=(255, 218, 185))
        
        # Draw eyes
        left_eye_x, right_eye_x = face_x + 120, face_x + 280
        eye_y = face_y + 150
        
        draw.ellipse([left_eye_x - 8, eye_y - 4, left_eye_x + 8, eye_y + 4], fill='black')
        draw.ellipse([right_eye_x - 8, eye_y - 4, right_eye_x + 8, eye_y + 4], fill='black')
        
        face_data = FaceData(
            bounding_box=(face_x, face_y, face_w, face_h),
            confidence=0.95,
            landmarks={'left_eye': (left_eye_x, eye_y), 'right_eye': (right_eye_x, eye_y)},
            eye_positions=((left_eye_x, eye_y), (right_eye_x, eye_y)),
            face_size_ratio=face_h / 600
        )
        
        img_array = np.array(image)
        
        # Test glasses detection
        glasses_info = self.face_detector.detect_glasses_or_sunglasses(img_array, face_data)
        
        print(f"Face without glasses:")
        print(f"  Glasses detected: {glasses_info['glasses_detected']}")
        print(f"  Sunglasses detected: {glasses_info['sunglasses_detected']}")
        print(f"  Confidence: {glasses_info['confidence']:.3f}")
        
        # Should not detect glasses
        assert not glasses_info['glasses_detected'], "Should not detect glasses on face without glasses"
        assert not glasses_info['sunglasses_detected'], "Should not detect sunglasses on face without glasses"
        
        # Test ICAO compliance
        compliance = self.face_detector.validate_eye_compliance_icao(
            face_data, image.size[::-1], img_array
        )
        
        print(f"  ICAO compliance (glasses aspect): {not (compliance.glasses_detected or compliance.sunglasses_detected)}")
        
        # Should not be flagged for glasses
        assert not compliance.glasses_detected, "Should not flag glasses on clean face"
        assert not compliance.sunglasses_detected, "Should not flag sunglasses on clean face"
        
        # Save test image
        image.save("test_no_glasses.jpg", quality=95)
        print(f"  Saved: test_no_glasses.jpg")


if __name__ == "__main__":
    # Run glasses detection tests
    test_class = TestGlassesDetection()
    test_class.setup_method()
    
    print("🧪 Running Glasses Detection Tests")
    print("=" * 50)
    
    # Run all tests
    test_class.test_glasses_detection_synthetic()
    test_class.test_no_glasses_detection()
    
    # Run real image tests if available
    if os.path.exists("backend/test_images"):
        test_class.test_glasses_detection_real_images()
    else:
        print("\n⚠️  Skipping real image tests - test_images directory not found")
    
    print("\n✅ All glasses detection tests completed!")
    print("📁 Check generated test images for visual verification")