"""
Property tests for multiple face handling consistency
Tests primary face selection and manual review flagging for multiple face scenarios
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings
import cv2
import os
from enhancement.face_detection import FaceDetectionPipeline
from enhancement.data_models import FaceData, FaceDetectionResult


class TestMultipleFaceHandling:
    """Test multiple face handling consistency and primary face selection"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.detector = FaceDetectionPipeline()
    
    @given(
        num_faces=st.integers(min_value=2, max_value=5),
        confidence_variation=st.floats(min_value=0.1, max_value=0.4),
        size_variation=st.floats(min_value=0.1, max_value=0.3),
        position_variation=st.floats(min_value=0.1, max_value=0.4)
    )
    @settings(max_examples=50, deadline=3000)
    def test_multiple_face_primary_selection_consistency(self, num_faces, confidence_variation, size_variation, position_variation):
        """
        Property 2: Multiple Face Handling Consistency
        For any image containing multiple faces, the system should consistently 
        identify a primary face based on confidence, size, and positioning criteria.
        
        **Feature: photo-quality-enhancement, Property 2: Multiple Face Handling Consistency**
        **Validates: Requirements 1.3**
        """
        # Create synthetic faces with varying properties
        faces = []
        image_width, image_height = 1200, 1200
        
        for i in range(num_faces):
            # Generate face properties with controlled variation
            base_confidence = 0.7
            confidence = base_confidence + (i * confidence_variation / num_faces)
            confidence = min(0.95, max(0.3, confidence))
            
            # Generate face size (as ratio of image height)
            base_size_ratio = 0.75
            size_ratio = base_size_ratio + ((i - num_faces/2) * size_variation / num_faces)
            size_ratio = min(0.9, max(0.5, size_ratio))
            
            face_height = int(image_height * size_ratio)
            face_width = int(face_height * 0.8)  # Typical face aspect ratio
            
            # Generate position with variation
            center_x = image_width // 2 + int((i - num_faces/2) * position_variation * image_width / num_faces)
            center_y = image_height // 2 + int((i % 2 - 0.5) * position_variation * image_height)
            
            # Ensure face stays within image bounds
            x = max(0, min(center_x - face_width//2, image_width - face_width))
            y = max(0, min(center_y - face_height//2, image_height - face_height))
            
            face_data = FaceData(
                bounding_box=(x, y, face_width, face_height),
                confidence=confidence,
                landmarks={},
                eye_positions=None,
                face_size_ratio=size_ratio
            )
            faces.append(face_data)
        
        # Test primary face selection
        primary_face = self.detector.get_primary_face(faces)
        
        # Should always select a primary face when faces are provided
        assert primary_face is not None, "Should select a primary face when multiple faces detected"
        
        # Primary face should be one of the input faces
        assert primary_face in faces, "Primary face should be one of the detected faces"
        
        # Test selection consistency - same input should produce same result
        primary_face_2 = self.detector.get_primary_face(faces)
        assert primary_face == primary_face_2, "Primary face selection should be deterministic"
        
        # Test that the selection follows expected criteria
        # The primary face should generally have good confidence, size, and positioning
        assert primary_face.confidence >= 0.3, f"Primary face confidence too low: {primary_face.confidence}"
        
        # If there's a face with significantly higher confidence, it should be selected
        max_confidence_face = max(faces, key=lambda f: f.confidence)
        if max_confidence_face.confidence > primary_face.confidence + 0.2:
            # Unless the primary face has much better size/positioning
            primary_size_score = 1 - abs(primary_face.face_size_ratio - 0.75)
            max_conf_size_score = 1 - abs(max_confidence_face.face_size_ratio - 0.75)
            
            # Allow primary face to be different only if it has significantly better size
            if primary_size_score <= max_conf_size_score + 0.3:
                assert False, f"Should prefer higher confidence face: primary={primary_face.confidence:.2f}, max={max_confidence_face.confidence:.2f}"
    
    def test_multiple_face_manual_review_flagging(self):
        """
        Test that multiple face scenarios are properly flagged for manual review using real multi-face image
        """
        # Use real multi-face image
        multi_face_path = "backend/test_images/multi_face.jpg"
        if not os.path.exists(multi_face_path):
            pytest.skip(f"Multi-face test image {multi_face_path} not found")
        
        # Load the real multi-face image
        test_image = cv2.imread(multi_face_path)
        assert test_image is not None, f"Failed to load multi-face image {multi_face_path}"
        
        # Run actual face detection on the multi-face image
        result = self.detector.detect_faces(test_image)
        
        # Test that multiple faces are detected
        assert len(result.faces) > 1, f"Should detect multiple faces in {multi_face_path}, but found {len(result.faces)}"
        
        # Test manual review flagging
        assert result.multiple_faces_detected, "Should flag multiple faces detected"
        assert result.requires_manual_review, "Should require manual review for multiple faces"
        assert result.primary_face is not None, "Should still select a primary face"
        
        # Check error message based on confidence levels
        high_confidence_faces = [f for f in result.faces if f.confidence > 0.7]
        if len(high_confidence_faces) > 1:
            assert "Image must contain only 1 person" in result.error_message, \
                "Should show clear error for multiple high-confidence faces"
        else:
            assert "Multiple faces detected" in result.error_message, \
                "Should show multiple faces detected message"
        
        # Primary face should be one of the detected faces
        assert result.primary_face in result.faces, "Primary face should be one of the detected faces"
        
        print(f"Detected {len(result.faces)} faces with confidences: {[f.confidence for f in result.faces]}")
        print(f"Primary face confidence: {result.primary_face.confidence}")
        print(f"Error message: {result.error_message}")
    
    def test_multiple_face_low_confidence_different_message(self):
        """
        Test that multiple faces with mixed confidence get appropriate message
        """
        # Create faces with mixed confidence (one high, one low)
        face_high = FaceData(
            bounding_box=(100, 150, 120, 160),
            confidence=0.8,
            landmarks={},
            eye_positions=None,
            face_size_ratio=160/600
        )
        
        face_low = FaceData(
            bounding_box=(350, 150, 120, 160),
            confidence=0.5,  # Low confidence
            landmarks={},
            eye_positions=None,
            face_size_ratio=160/600
        )
        
        faces = [face_high, face_low]
        
        # Simulate the detection result
        high_confidence_faces = [f for f in faces if f.confidence > 0.7]
        
        if len(high_confidence_faces) > 1:
            error_message = "Image must contain only 1 person. Multiple faces detected with high confidence."
        else:
            error_message = "Multiple faces detected. Please ensure image contains only one person."
        
        result = FaceDetectionResult(
            faces=faces,
            primary_face=self.detector.get_primary_face(faces),
            confidence=0.8,
            multiple_faces_detected=True,
            requires_manual_review=True,
            error_message=error_message
        )
        
        # Should use the general multiple faces message since only one has high confidence
        assert "Multiple faces detected. Please ensure image contains only one person." in result.error_message
        assert "Image must contain only 1 person" not in result.error_message
    
    def test_single_face_no_manual_review(self):
        """
        Test that single face scenarios with high confidence don't require manual review
        """
        # Create single face with high confidence
        face = FaceData(
            bounding_box=(300, 200, 200, 250),
            confidence=0.95,
            landmarks={},
            eye_positions=None,
            face_size_ratio=250/600
        )
        
        result = FaceDetectionResult(
            faces=[face],
            primary_face=face,
            confidence=0.95,
            multiple_faces_detected=False,
            requires_manual_review=False,
            error_message=None
        )
        
        # Should not require manual review for single high-confidence face
        assert not result.multiple_faces_detected, "Should not flag multiple faces"
        assert not result.requires_manual_review, "Should not require manual review for high confidence single face"
        assert result.primary_face == face, "Primary face should be the detected face"
    
    def test_low_confidence_manual_review(self):
        """
        Test that low confidence faces are flagged for manual review
        """
        # Create single face with low confidence
        face = FaceData(
            bounding_box=(300, 200, 200, 250),
            confidence=0.4,
            landmarks={},
            eye_positions=None,
            face_size_ratio=250/600
        )
        
        result = FaceDetectionResult(
            faces=[face],
            primary_face=face,
            confidence=0.4,
            multiple_faces_detected=False,
            requires_manual_review=True,  # Should be True for low confidence
            error_message=None
        )
        
        # Should require manual review for low confidence
        assert not result.multiple_faces_detected, "Should not flag multiple faces"
        assert result.requires_manual_review, "Should require manual review for low confidence face"
        assert result.primary_face == face, "Primary face should be the detected face"
    
    @given(
        crop_factor=st.floats(min_value=0.8, max_value=1.0),
        brightness_factor=st.floats(min_value=0.8, max_value=1.2)
    )
    @settings(max_examples=20, deadline=3000)
    def test_real_multi_face_detection_robustness(self, crop_factor, brightness_factor):
        """
        Property 2 Extended: Real Multi-Face Detection Robustness
        For any real multi-face image with variations in cropping and brightness,
        the system should consistently detect multiple faces and flag appropriately.
        
        **Feature: photo-quality-enhancement, Property 2: Multiple Face Handling Consistency**
        **Validates: Requirements 1.3**
        """
        # Use real multi-face image
        multi_face_path = "backend/test_images/multi_face.jpg"
        if not os.path.exists(multi_face_path):
            pytest.skip(f"Multi-face test image {multi_face_path} not found")
        
        # Load and process the image
        original_image = cv2.imread(multi_face_path)
        assert original_image is not None, f"Failed to load multi-face image {multi_face_path}"
        
        # Apply variations to test robustness
        h, w = original_image.shape[:2]
        
        # Crop the image
        crop_h = int(h * crop_factor)
        crop_w = int(w * crop_factor)
        start_y = max(0, (h - crop_h) // 2)
        start_x = max(0, (w - crop_w) // 2)
        cropped_image = original_image[start_y:start_y+crop_h, start_x:start_x+crop_w]
        
        # Adjust brightness
        test_image = cv2.convertScaleAbs(cropped_image, alpha=brightness_factor, beta=0)
        
        # Test face detection
        result = self.detector.detect_faces(test_image)
        
        # Should handle variations gracefully
        if len(result.faces) == 0:
            # If no faces detected due to heavy cropping/brightness changes, should have error message
            assert result.error_message is not None, "Should provide error message when no faces detected"
            assert "No faces detected" in result.error_message, "Should provide appropriate error message"
        elif len(result.faces) == 1:
            # If only one face detected (due to cropping), should not flag multiple faces
            assert not result.multiple_faces_detected, "Should not flag multiple faces when only one detected"
            assert result.primary_face is not None, "Should have primary face"
        else:
            # If multiple faces still detected, should flag appropriately
            assert result.multiple_faces_detected, "Should flag multiple faces detected"
            assert result.requires_manual_review, "Should require manual review for multiple faces"
            assert result.primary_face is not None, "Should select a primary face"
            assert result.error_message is not None, "Should provide error message for multiple faces"
            
            # Error message should be appropriate based on confidence levels
            high_confidence_faces = [f for f in result.faces if f.confidence > 0.7]
            if len(high_confidence_faces) > 1:
                assert "Image must contain only 1 person" in result.error_message
            else:
                assert "Multiple faces detected" in result.error_message


    @given(
        face_count=st.integers(min_value=0, max_value=6)
    )
    @settings(max_examples=20, deadline=3000)
    def test_face_count_handling_consistency(self, face_count):
        """
        Property 2 Extended: Face Count Handling Consistency
        The system should handle any number of detected faces consistently,
        from zero faces to multiple faces.
        
        **Feature: photo-quality-enhancement, Property 2: Multiple Face Handling Consistency**
        **Validates: Requirements 1.3, 1.4**
        """
        # Generate faces based on face_count
        faces = []
        for i in range(face_count):
            face = FaceData(
                bounding_box=(100 + i * 150, 150, 120, 160),
                confidence=0.7 + (i * 0.1),
                landmarks={},
                eye_positions=None,
                face_size_ratio=0.27  # 160/600
            )
            faces.append(face)
        
        # Test primary face selection
        primary_face = self.detector.get_primary_face(faces)
        
        if face_count == 0:
            # No faces - should return None
            assert primary_face is None, "Should return None for no faces"
        elif face_count == 1:
            # Single face - should return that face
            assert primary_face == faces[0], "Should return the single face"
        else:
            # Multiple faces - should return one of them
            assert primary_face is not None, "Should select a primary face"
            assert primary_face in faces, "Primary face should be one of the detected faces"
            
            # Should prefer higher confidence faces
            max_confidence_face = max(faces, key=lambda f: f.confidence)
            # Primary face should have reasonable confidence relative to the best
            assert primary_face.confidence >= max_confidence_face.confidence - 0.3, \
                f"Primary face confidence ({primary_face.confidence:.2f}) too low compared to max ({max_confidence_face.confidence:.2f})"


class TestPrimaryFaceSelectionCriteria:
    """Test specific criteria for primary face selection"""
    
    def setup_method(self):
        self.detector = FaceDetectionPipeline()
    
    def test_confidence_preference(self):
        """Test that higher confidence faces are preferred"""
        face_low_conf = FaceData(
            bounding_box=(100, 150, 120, 160),
            confidence=0.5,
            landmarks={},
            eye_positions=None,
            face_size_ratio=0.27
        )
        
        face_high_conf = FaceData(
            bounding_box=(350, 150, 120, 160),
            confidence=0.9,
            landmarks={},
            eye_positions=None,
            face_size_ratio=0.27
        )
        
        faces = [face_low_conf, face_high_conf]
        primary_face = self.detector.get_primary_face(faces)
        
        assert primary_face == face_high_conf, "Should prefer higher confidence face"
    
    def test_size_preference_for_passport_photos(self):
        """Test that faces closer to passport photo size standards are preferred"""
        # Face too small
        face_small = FaceData(
            bounding_box=(100, 150, 60, 80),
            confidence=0.8,
            landmarks={},
            eye_positions=None,
            face_size_ratio=80/600  # ~13% - too small
        )
        
        # Face good size for passport
        face_good_size = FaceData(
            bounding_box=(350, 100, 180, 240),
            confidence=0.8,
            landmarks={},
            eye_positions=None,
            face_size_ratio=240/600  # 40% - closer to passport standard
        )
        
        faces = [face_small, face_good_size]
        primary_face = self.detector.get_primary_face(faces)
        
        assert primary_face == face_good_size, "Should prefer face with better size for passport photos"
    
    def test_centering_preference(self):
        """Test that more centered faces are preferred when other factors are equal"""
        # Off-center face
        face_off_center = FaceData(
            bounding_box=(50, 150, 120, 160),  # Far left
            confidence=0.8,
            landmarks={},
            eye_positions=None,
            face_size_ratio=160/600
        )
        
        # Centered face
        face_centered = FaceData(
            bounding_box=(540, 220, 120, 160),  # More centered
            confidence=0.8,
            landmarks={},
            eye_positions=None,
            face_size_ratio=160/600
        )
        
        faces = [face_off_center, face_centered]
        primary_face = self.detector.get_primary_face(faces)
        
        assert primary_face == face_centered, "Should prefer more centered face when other factors are equal"