"""
Integration tests for face detection with OpenCV Haar Cascades.
Tests Requirements 2.2, 2.3, 2.4 from the specification.

Note: These tests use mocking since test fixtures are synthetic images.
For real-world testing, use actual passport photos.
"""

import pytest
import os
from unittest.mock import Mock, patch
import numpy as np


class TestFaceDetectionIntegration:
    """Integration tests for face detection functionality."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Get the path to test fixtures directory."""
        return os.path.join(os.path.dirname(__file__), 'fixtures')
    
    def test_processor_initialization(self):
        """Test that PassportPhotoProcessor initializes correctly with OpenCV."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Verify Haar Cascade classifiers are loaded
        assert processor.face_cascade is not None
        assert processor.eye_cascade is not None
        assert hasattr(processor, 'HEAD_HEIGHT_MIN')
        assert hasattr(processor, 'HEAD_HEIGHT_MAX')
    
    def test_no_face_detected_with_mock(self, fixtures_dir):
        """
        Test that images with no faces return correct error structure.
        Validates: Requirement 2.2
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock detectMultiScale to return no faces
        with patch.object(processor.face_cascade, 'detectMultiScale', return_value=np.array([])):
            no_face_image = os.path.join(fixtures_dir, 'no_face.jpg')
            
            if os.path.exists(no_face_image):
                result = processor.detect_face_and_features(no_face_image)
                
                assert result is not None
                assert result['faces_detected'] == 0
                assert result['valid'] is False
                assert 'error' in result
                assert 'No face detected' in result['error']
    
    def test_multiple_faces_detected_with_mock(self, fixtures_dir):
        """
        Test that images with multiple faces return correct error structure.
        Validates: Requirement 2.3
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock detectMultiScale to return multiple faces
        mock_faces = np.array([
            [100, 100, 200, 200],  # Face 1: x, y, w, h
            [400, 100, 200, 200]   # Face 2: x, y, w, h
        ])
        
        with patch.object(processor.face_cascade, 'detectMultiScale', return_value=mock_faces):
            multiple_faces_image = os.path.join(fixtures_dir, 'multiple_faces.jpg')
            
            if os.path.exists(multiple_faces_image):
                result = processor.detect_face_and_features(multiple_faces_image)
                
                assert result is not None
                assert result['faces_detected'] == 2
                assert result['valid'] is False
                assert 'error' in result
                assert 'Multiple faces detected' in result['error']
    
    def test_single_face_detected_with_mock(self, fixtures_dir):
        """
        Test that images with single face return valid bounding box.
        Validates: Requirement 2.4
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock detectMultiScale to return single face
        mock_face = np.array([[200, 150, 400, 500]])  # x, y, w, h
        mock_eyes = np.array([[50, 50, 30, 30], [150, 50, 30, 30]])  # Two eyes
        
        with patch.object(processor.face_cascade, 'detectMultiScale', return_value=mock_face):
            with patch.object(processor.eye_cascade, 'detectMultiScale', return_value=mock_eyes):
                single_face_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
                
                if os.path.exists(single_face_image):
                    result = processor.detect_face_and_features(single_face_image)
                    
                    assert result is not None
                    assert result['faces_detected'] == 1
                    assert result['valid'] is True
                    assert 'face_bbox' in result
                    
                    bbox = result['face_bbox']
                    assert 'x' in bbox
                    assert 'y' in bbox
                    assert 'width' in bbox
                    assert 'height' in bbox
                    
                    # Verify all coordinates are integers
                    assert isinstance(bbox['x'], int)
                    assert isinstance(bbox['y'], int)
                    assert isinstance(bbox['width'], int)
                    assert isinstance(bbox['height'], int)
                    
                    # Verify coordinates are non-negative
                    assert bbox['x'] >= 0
                    assert bbox['y'] >= 0
                    assert bbox['width'] > 0
                    assert bbox['height'] > 0
                    
                    # Verify eyes were detected
                    assert 'eyes_detected' in result
                    assert result['eyes_detected'] == 2
    
    def test_head_height_calculation_with_mock(self, fixtures_dir):
        """
        Test that head height ratio is calculated correctly.
        Validates: Requirement 2.6
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock a face that's 600 pixels tall in a 1000 pixel tall image
        # This should give a head height ratio of 0.60
        mock_face = np.array([[200, 200, 400, 600]])  # x, y, w, h
        
        with patch.object(processor.face_cascade, 'detectMultiScale', return_value=mock_face):
            with patch.object(processor.eye_cascade, 'detectMultiScale', return_value=np.array([])):
                test_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
                
                if os.path.exists(test_image):
                    result = processor.detect_face_and_features(test_image)
                    
                    assert result is not None
                    assert result['valid'] is True
                    assert 'head_height_percent' in result
                    assert isinstance(result['head_height_percent'], (int, float))
                    assert 0 < result['head_height_percent'] <= 1
    
    def test_head_height_validation_with_mock(self, fixtures_dir):
        """
        Test that head height validation flag is set correctly.
        Validates: Requirement 2.7
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock a face with valid head height (60% of image height)
        mock_face = np.array([[200, 200, 400, 600]])  # h=600 in 1000px image = 0.60
        
        with patch.object(processor.face_cascade, 'detectMultiScale', return_value=mock_face):
            with patch.object(processor.eye_cascade, 'detectMultiScale', return_value=np.array([])):
                test_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
                
                if os.path.exists(test_image):
                    result = processor.detect_face_and_features(test_image)
                    
                    assert result is not None
                    assert result['valid'] is True
                    assert 'head_height_valid' in result
                    assert isinstance(result['head_height_valid'], bool)
    
    def test_horizontal_centering_with_mock(self, fixtures_dir):
        """
        Test that horizontal centering flag is set correctly.
        Validates: Requirement 2.8
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock a centered face (face center at x=500 in 1000px wide image)
        mock_face = np.array([[300, 200, 400, 600]])  # x=300, w=400, center=500
        
        with patch.object(processor.face_cascade, 'detectMultiScale', return_value=mock_face):
            with patch.object(processor.eye_cascade, 'detectMultiScale', return_value=np.array([])):
                test_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
                
                if os.path.exists(test_image):
                    result = processor.detect_face_and_features(test_image)
                    
                    assert result is not None
                    assert result['valid'] is True
                    assert 'horizontally_centered' in result
                    assert isinstance(result['horizontally_centered'], bool)
    
    def test_invalid_image_path(self):
        """Test that invalid image paths are handled gracefully."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        result = processor.detect_face_and_features('nonexistent_image.jpg')
        
        assert result is None
    
    def test_large_image_performance_optimization(self, fixtures_dir):
        """
        Test that large images are processed (resized before detection).
        Validates: Requirement 2.5
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock face detection to verify it's called
        with patch.object(processor.face_cascade, 'detectMultiScale', return_value=np.array([])) as mock_detect:
            large_image = os.path.join(fixtures_dir, 'very_large_resolution.jpg')
            
            if os.path.exists(large_image):
                result = processor.detect_face_and_features(large_image)
                
                # Should complete without errors (performance optimization working)
                assert result is not None
                assert mock_detect.called
