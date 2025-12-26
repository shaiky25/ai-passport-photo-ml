"""
Comprehensive tests for ICAO-compliant eye validation and positioning
Tests eye detection, positioning, symmetry, and compliance with passport photo standards
"""

import pytest
import numpy as np
import cv2
from PIL import Image, ImageDraw
import os
import tempfile
from hypothesis import given, strategies as st, settings
from enhancement.face_detection import FaceDetectionPipeline
from enhancement.data_models import FaceData, ComplianceResult


class TestEyeValidationICAO:
    """Comprehensive tests for ICAO eye validation system"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.face_detector = FaceDetectionPipeline()
        self.test_images_dir = "backend/test_images"
    
    def create_test_face_with_eyes(self, image_size=(800, 600), eye_level_ratio=0.7, 
                                  eye_distance_ratio=0.35, eye_y_offset=0):
        """Create test image with precisely positioned eyes for validation testing"""
        image = Image.new('RGB', image_size, 'lightblue')
        draw = ImageDraw.Draw(image)
        
        width, height = image_size
        
        # Calculate face dimensions (75% of image height)
        face_height = int(height * 0.75)
        face_width = int(face_height * 0.8)
        
        # Center the face
        face_x = (width - face_width) // 2
        face_y = (height - face_height) // 2
        
        # Draw face outline
        draw.ellipse([face_x, face_y, face_x + face_width, face_y + face_height], 
                    fill=(255, 218, 185), outline=(200, 180, 160), width=2)
        
        # Calculate eye positions based on parameters
        eye_y = int(height * eye_level_ratio) + eye_y_offset
        eye_distance = int(face_width * eye_distance_ratio)
        
        face_center_x = face_x + face_width // 2
        left_eye_x = face_center_x - eye_distance // 2
        right_eye_x = face_center_x + eye_distance // 2
        
        # Draw eyes
        eye_size = 8
        draw.ellipse([left_eye_x - eye_size, eye_y - eye_size//2, 
                     left_eye_x + eye_size, eye_y + eye_size//2], fill='black')
        draw.ellipse([right_eye_x - eye_size, eye_y - eye_size//2, 
                     right_eye_x + eye_size, eye_y + eye_size//2], fill='black')
        
        # Draw nose and mouth for completeness
        nose_x = face_center_x
        nose_y = face_y + face_height * 0.6
        draw.ellipse([nose_x - 3, nose_y - 5, nose_x + 3, nose_y + 5], fill=(200, 150, 120))
        
        mouth_y = face_y + face_height * 0.8
        draw.arc([nose_x - 15, mouth_y - 5, nose_x + 15, mouth_y + 5], 0, 180, fill='black', width=2)
        
        # Create corresponding face data
        face_data = FaceData(
            bounding_box=(face_x, face_y, face_width, face_height),
            confidence=0.95,
            landmarks={
                'left_eye': (left_eye_x, eye_y),
                'right_eye': (right_eye_x, eye_y),
                'nose_tip': (nose_x, nose_y),
                'mouth_center': (nose_x, mouth_y)
            },
            eye_positions=((left_eye_x, eye_y), (right_eye_x, eye_y)),
            face_size_ratio=face_height / height
        )
        
        return image, face_data
    
    def test_icao_eye_level_validation(self):
        """Test ICAO eye level positioning requirements"""
        print("\n=== Testing ICAO Eye Level Validation ===")
        
        # Test cases with different eye level ratios
        test_cases = [
            {'eye_level_ratio': 0.5, 'expected_valid': False, 'description': 'Eyes too high (50%)'},
            {'eye_level_ratio': 0.65, 'expected_valid': True, 'description': 'Eyes at lower bound (65%)'},
            {'eye_level_ratio': 0.7, 'expected_valid': True, 'description': 'Eyes optimal (70%)'},
            {'eye_level_ratio': 0.75, 'expected_valid': True, 'description': 'Eyes at upper bound (75%)'},
            {'eye_level_ratio': 0.85, 'expected_valid': False, 'description': 'Eyes too low (85%)'},
        ]
        
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            
            # Create test image
            test_image, face_data = self.create_test_face_with_eyes(
                eye_level_ratio=case['eye_level_ratio']
            )
            
            # Validate eye compliance
            compliance = self.face_detector.validate_eye_compliance_icao(
                face_data, test_image.size[::-1]  # (height, width)
            )
            
            print(f"  Eye level ratio: {case['eye_level_ratio']:.2f}")
            print(f"  Expected valid: {case['expected_valid']}")
            print(f"  Actual valid: {compliance.eye_level_valid}")
            print(f"  Eyes detected: {compliance.eyes_detected}")
            print(f"  ICAO compliance: {compliance.icao_eye_compliance}")
            
            # Validate results
            assert compliance.eyes_detected, "Eyes should be detected"
            assert compliance.eye_level_valid == case['expected_valid'], \
                f"Eye level validation failed for {case['description']}"
            
            if compliance.eye_validation_details:
                actual_ratio = compliance.eye_validation_details['eye_level_ratio']
                print(f"  Measured eye level ratio: {actual_ratio:.3f}")
                
                # Allow small tolerance for drawing precision
                assert abs(actual_ratio - case['eye_level_ratio']) < 0.05, \
                    f"Measured ratio {actual_ratio:.3f} should be close to expected {case['eye_level_ratio']:.3f}"
            
            # Save test image for visual inspection
            output_name = f"test_eye_level_{case['eye_level_ratio']:.2f}.jpg"
            test_image.save(output_name, quality=95)
            print(f"  Saved: {output_name}")
    
    def test_icao_eye_distance_validation(self):
        """Test ICAO eye distance requirements"""
        print("\n=== Testing ICAO Eye Distance Validation ===")
        
        # Test cases with different eye distance ratios
        test_cases = [
            {'eye_distance_ratio': 0.2, 'expected_valid': False, 'description': 'Eyes too close (20%)'},
            {'eye_distance_ratio': 0.3, 'expected_valid': True, 'description': 'Eyes at lower bound (30%)'},
            {'eye_distance_ratio': 0.35, 'expected_valid': True, 'description': 'Eyes optimal (35%)'},
            {'eye_distance_ratio': 0.4, 'expected_valid': True, 'description': 'Eyes at upper bound (40%)'},
            {'eye_distance_ratio': 0.5, 'expected_valid': False, 'description': 'Eyes too far (50%)'},
        ]
        
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            
            # Create test image
            test_image, face_data = self.create_test_face_with_eyes(
                eye_distance_ratio=case['eye_distance_ratio']
            )
            
            # Validate eye compliance
            compliance = self.face_detector.validate_eye_compliance_icao(
                face_data, test_image.size[::-1]
            )
            
            print(f"  Eye distance ratio: {case['eye_distance_ratio']:.2f}")
            print(f"  Expected valid: {case['expected_valid']}")
            print(f"  Actual valid: {compliance.eye_distance_valid}")
            print(f"  ICAO compliance: {compliance.icao_eye_compliance}")
            
            # Validate results
            assert compliance.eyes_detected, "Eyes should be detected"
            assert compliance.eye_distance_valid == case['expected_valid'], \
                f"Eye distance validation failed for {case['description']}"
            
            if compliance.eye_validation_details:
                actual_ratio = compliance.eye_validation_details['eye_distance_ratio']
                print(f"  Measured eye distance ratio: {actual_ratio:.3f}")
                
                # Allow small tolerance for drawing precision
                assert abs(actual_ratio - case['eye_distance_ratio']) < 0.05, \
                    f"Measured ratio {actual_ratio:.3f} should be close to expected {case['eye_distance_ratio']:.3f}"
            
            # Save test image
            output_name = f"test_eye_distance_{case['eye_distance_ratio']:.2f}.jpg"
            test_image.save(output_name, quality=95)
            print(f"  Saved: {output_name}")
    
    def test_icao_eye_symmetry_validation(self):
        """Test ICAO eye symmetry (horizontal alignment) requirements"""
        print("\n=== Testing ICAO Eye Symmetry Validation ===")
        
        # Test cases with different eye Y offsets
        test_cases = [
            {'eye_y_offset': 0, 'expected_valid': True, 'description': 'Perfect alignment'},
            {'eye_y_offset': 10, 'expected_valid': True, 'description': 'Small offset (10px)'},
            {'eye_y_offset': 25, 'expected_valid': False, 'description': 'Large offset (25px)'},
            {'eye_y_offset': 50, 'expected_valid': False, 'description': 'Very large offset (50px)'},
        ]
        
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            
            # Create test image with asymmetric eyes
            test_image, face_data = self.create_test_face_with_eyes(
                eye_y_offset=case['eye_y_offset']
            )
            
            # Manually adjust one eye position to create asymmetry
            if case['eye_y_offset'] > 0:
                left_eye, right_eye = face_data.eye_positions
                # Move right eye down by offset
                adjusted_right_eye = (right_eye[0], right_eye[1] + case['eye_y_offset'])
                face_data.eye_positions = (left_eye, adjusted_right_eye)
                
                # Update landmarks too
                face_data.landmarks['right_eye'] = adjusted_right_eye
            
            # Validate eye compliance
            compliance = self.face_detector.validate_eye_compliance_icao(
                face_data, test_image.size[::-1]
            )
            
            print(f"  Eye Y offset: {case['eye_y_offset']}px")
            print(f"  Expected valid: {case['expected_valid']}")
            print(f"  Actual valid: {compliance.eye_symmetry_valid}")
            print(f"  ICAO compliance: {compliance.icao_eye_compliance}")
            
            # Validate results
            assert compliance.eyes_detected, "Eyes should be detected"
            assert compliance.eye_symmetry_valid == case['expected_valid'], \
                f"Eye symmetry validation failed for {case['description']}"
            
            if compliance.eye_validation_details:
                y_diff = compliance.eye_validation_details['eye_y_difference']
                tolerance = compliance.eye_validation_details['eye_y_tolerance']
                print(f"  Measured Y difference: {y_diff:.1f}px")
                print(f"  Tolerance: {tolerance:.1f}px")
            
            # Save test image
            output_name = f"test_eye_symmetry_{case['eye_y_offset']}px.jpg"
            test_image.save(output_name, quality=95)
            print(f"  Saved: {output_name}")
    
    def test_comprehensive_icao_compliance(self):
        """Test comprehensive ICAO compliance with all eye requirements"""
        print("\n=== Testing Comprehensive ICAO Compliance ===")
        
        # Test cases combining multiple factors
        test_cases = [
            {
                'eye_level_ratio': 0.7, 'eye_distance_ratio': 0.35, 'eye_y_offset': 0,
                'expected_compliant': True, 'description': 'Perfect ICAO compliance'
            },
            {
                'eye_level_ratio': 0.5, 'eye_distance_ratio': 0.35, 'eye_y_offset': 0,
                'expected_compliant': False, 'description': 'Bad eye level'
            },
            {
                'eye_level_ratio': 0.7, 'eye_distance_ratio': 0.2, 'eye_y_offset': 0,
                'expected_compliant': False, 'description': 'Bad eye distance'
            },
            {
                'eye_level_ratio': 0.7, 'eye_distance_ratio': 0.35, 'eye_y_offset': 30,
                'expected_compliant': False, 'description': 'Bad eye symmetry'
            },
        ]
        
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            
            # Create test image
            test_image, face_data = self.create_test_face_with_eyes(
                eye_level_ratio=case['eye_level_ratio'],
                eye_distance_ratio=case['eye_distance_ratio'],
                eye_y_offset=case['eye_y_offset']
            )
            
            # Adjust eye asymmetry if needed
            if case['eye_y_offset'] > 0:
                left_eye, right_eye = face_data.eye_positions
                adjusted_right_eye = (right_eye[0], right_eye[1] + case['eye_y_offset'])
                face_data.eye_positions = (left_eye, adjusted_right_eye)
                face_data.landmarks['right_eye'] = adjusted_right_eye
            
            # Validate comprehensive compliance
            compliance = self.face_detector.validate_eye_compliance_icao(
                face_data, test_image.size[::-1]
            )
            
            print(f"  Expected compliant: {case['expected_compliant']}")
            print(f"  Actual compliant: {compliance.icao_eye_compliance}")
            print(f"  Overall compliant: {compliance.is_compliant}")
            print(f"  Eyes detected: {compliance.eyes_detected}")
            print(f"  Eye level valid: {compliance.eye_level_valid}")
            print(f"  Eye distance valid: {compliance.eye_distance_valid}")
            print(f"  Eye symmetry valid: {compliance.eye_symmetry_valid}")
            print(f"  Issues: {compliance.issues}")
            
            # Validate results
            assert compliance.icao_eye_compliance == case['expected_compliant'], \
                f"ICAO eye compliance failed for {case['description']}"
            
            # Save test image
            safe_desc = case['description'].replace(' ', '_').lower()
            output_name = f"test_icao_compliance_{safe_desc}.jpg"
            test_image.save(output_name, quality=95)
            print(f"  Saved: {output_name}")
    
    @pytest.mark.skipif(not os.path.exists("backend/test_images"), reason="Test images directory not found")
    def test_real_images_eye_validation(self):
        """Test eye validation on real images"""
        print("\n=== Testing Real Images Eye Validation ===")
        
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
                    print(f"  Eye positions available: {face_data.eye_positions is not None}")
                    
                    # Test basic compliance
                    basic_compliance = self.face_detector.validate_face_compliance(
                        face_data, img.size[::-1]
                    )
                    
                    # Test ICAO eye compliance
                    icao_compliance = self.face_detector.validate_eye_compliance_icao(
                        face_data, img.size[::-1]
                    )
                    
                    print(f"  Basic compliance: {basic_compliance.is_compliant}")
                    print(f"  ICAO eye compliance: {icao_compliance.icao_eye_compliance}")
                    print(f"  Eyes detected: {icao_compliance.eyes_detected}")
                    
                    if icao_compliance.eyes_detected:
                        print(f"  Eye level valid: {icao_compliance.eye_level_valid}")
                        print(f"  Eye distance valid: {icao_compliance.eye_distance_valid}")
                        print(f"  Eye symmetry valid: {icao_compliance.eye_symmetry_valid}")
                        print(f"  Eye visibility valid: {icao_compliance.eye_visibility_valid}")
                        
                        if icao_compliance.eye_validation_details:
                            details = icao_compliance.eye_validation_details
                            print(f"  Eye level ratio: {details.get('eye_level_ratio', 'N/A'):.3f}")
                            print(f"  Eye distance ratio: {details.get('eye_distance_ratio', 'N/A'):.3f}")
                            print(f"  Eye Y difference: {details.get('eye_y_difference', 'N/A'):.1f}px")
                    
                    if icao_compliance.issues:
                        print(f"  Issues: {icao_compliance.issues}")
                    
                    # Test enhanced eye detection
                    enhanced_face_data = self.face_detector.enhance_eye_detection_with_landmarks(
                        img_array, face_data
                    )
                    
                    if enhanced_face_data.landmarks and 'left_eye_points' in enhanced_face_data.landmarks:
                        print(f"  Enhanced landmarks available: {len(enhanced_face_data.landmarks)} types")
                        print(f"  Enhanced confidence: {enhanced_face_data.confidence:.3f}")
                    
                else:
                    print("  No face detected")
    
    @given(
        eye_level_ratio=st.floats(min_value=0.5, max_value=0.9),
        eye_distance_ratio=st.floats(min_value=0.2, max_value=0.5),
        eye_y_offset=st.integers(min_value=0, max_value=40)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_eye_validation_consistency(self, eye_level_ratio, eye_distance_ratio, eye_y_offset):
        """Property test: Eye validation should be consistent and predictable"""
        
        # Create test image with given parameters
        test_image, face_data = self.create_test_face_with_eyes(
            eye_level_ratio=eye_level_ratio,
            eye_distance_ratio=eye_distance_ratio,
            eye_y_offset=eye_y_offset
        )
        
        # Adjust eye asymmetry if needed
        if eye_y_offset > 0:
            left_eye, right_eye = face_data.eye_positions
            adjusted_right_eye = (right_eye[0], right_eye[1] + eye_y_offset)
            face_data.eye_positions = (left_eye, adjusted_right_eye)
            face_data.landmarks['right_eye'] = adjusted_right_eye
        
        # Validate compliance
        compliance = self.face_detector.validate_eye_compliance_icao(
            face_data, test_image.size[::-1]
        )
        
        # Property 1: Eyes should always be detected for our synthetic images
        assert compliance.eyes_detected, "Eyes should always be detected in synthetic images"
        
        # Property 2: Eye level validation should match expected ranges
        expected_eye_level_valid = 0.60 <= eye_level_ratio <= 0.80
        assert compliance.eye_level_valid == expected_eye_level_valid, \
            f"Eye level validation inconsistent: ratio={eye_level_ratio:.3f}, expected={expected_eye_level_valid}, actual={compliance.eye_level_valid}"
        
        # Property 3: Eye distance validation should match expected ranges
        expected_eye_distance_valid = 0.25 <= eye_distance_ratio <= 0.45
        assert compliance.eye_distance_valid == expected_eye_distance_valid, \
            f"Eye distance validation inconsistent: ratio={eye_distance_ratio:.3f}, expected={expected_eye_distance_valid}, actual={compliance.eye_distance_valid}"
        
        # Property 4: Eye symmetry should be invalid for large offsets
        face_height = face_data.bounding_box[3]
        eye_y_tolerance = face_height * 0.05
        expected_eye_symmetry_valid = eye_y_offset <= eye_y_tolerance
        assert compliance.eye_symmetry_valid == expected_eye_symmetry_valid, \
            f"Eye symmetry validation inconsistent: offset={eye_y_offset}, tolerance={eye_y_tolerance:.1f}, expected={expected_eye_symmetry_valid}, actual={compliance.eye_symmetry_valid}"
        
        # Property 5: ICAO compliance should require all individual validations to pass
        expected_icao_compliance = (compliance.eye_level_valid and 
                                   compliance.eye_distance_valid and 
                                   compliance.eye_visibility_valid and 
                                   compliance.eye_symmetry_valid)
        assert compliance.icao_eye_compliance == expected_icao_compliance, \
            f"ICAO compliance inconsistent: expected={expected_icao_compliance}, actual={compliance.icao_eye_compliance}"
        
        # Property 6: Validation details should always be present when eyes are detected
        assert compliance.eye_validation_details is not None, "Eye validation details should be present"
        assert 'eye_level_ratio' in compliance.eye_validation_details, "Eye level ratio should be in details"
        assert 'eye_distance_ratio' in compliance.eye_validation_details, "Eye distance ratio should be in details"


if __name__ == "__main__":
    # Run comprehensive tests
    test_class = TestEyeValidationICAO()
    test_class.setup_method()
    
    print("🧪 Running Comprehensive ICAO Eye Validation Tests")
    print("=" * 60)
    
    # Run all tests
    test_class.test_icao_eye_level_validation()
    test_class.test_icao_eye_distance_validation()
    test_class.test_icao_eye_symmetry_validation()
    test_class.test_comprehensive_icao_compliance()
    
    # Run real image tests if available
    if os.path.exists("backend/test_images"):
        test_class.test_real_images_eye_validation()
    else:
        print("\n⚠️  Skipping real image tests - test_images directory not found")
    
    print("\n✅ All comprehensive ICAO eye validation tests completed!")
    print("📁 Check generated test images for visual verification")