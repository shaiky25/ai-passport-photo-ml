"""
Tests for face detection validation functionality.
Tests Requirements 2.2, 2.3, 2.4 from the specification.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import cv2
import numpy as np


class TestFaceDetectionLogic:
    """Test face detection logic and validation without requiring MTCNN hardware."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Get the path to test fixtures directory."""
        return os.path.join(os.path.dirname(__file__), 'fixtures')
    
    @pytest.fixture
    def mock_processor(self):
        """Create a mocked PassportPhotoProcessor for testing."""
        with patch('application.MTCNN'):
            from application import PassportPhotoProcessor
            processor = PassportPhotoProcessor()
            return processor
    
    def test_no_face_detected_response_structure(self, mock_processor):
        """
        Test that zero faces returns correct error structure.
        Validates: Requirement 2.2 - WHEN the System detects zero faces 
        THEN the System SHALL report "No face detected"
        """
        # Mock MTCNN to return no faces
        mock_processor.detector.detect_faces = Mock(return_value=[])
        
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        no_face_image = os.path.join(fixtures_dir, 'no_face.jpg')
        
        if os.path.exists(no_face_image):
            result = mock_processor.detect_face_and_features(no_face_image)
            
            assert result is not None
            assert result['faces_detected'] == 0
            assert result['valid'] is False
            assert 'error' in result
            assert 'No face detected' in result['error']
    
    def test_multiple_faces_detected_response_structure(self, mock_processor):
        """
        Test that multiple faces returns correct error structure.
        Validates: Requirement 2.3 - WHEN the System detects multiple faces 
        THEN the System SHALL report "Multiple faces detected"
        """
        # Mock MTCNN to return multiple faces
        mock_processor.detector.detect_faces = Mock(return_value=[
            {'confidence': 0.99, 'box': [100, 100, 50, 50], 'keypoints': {}},
            {'confidence': 0.98, 'box': [200, 200, 50, 50], 'keypoints': {}}
        ])
        
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        multiple_faces_image = os.path.join(fixtures_dir, 'multiple_faces.jpg')
        
        if os.path.exists(multiple_faces_image):
            result = mock_processor.detect_face_and_features(multiple_faces_image)
            
            assert result is not None
            assert result['faces_detected'] > 1
            assert result['valid'] is False
            assert 'error' in result
            assert 'Multiple faces detected' in result['error']
    
    def test_single_face_bounding_box_structure(self, mock_processor):
        """
        Test that single face returns valid bounding box structure.
        Validates: Requirement 2.4 - WHEN the System detects exactly one face 
        THEN the System SHALL extract the face bounding box coordinates
        """
        # Mock MTCNN to return single face
        mock_processor.detector.detect_faces = Mock(return_value=[
            {'confidence': 0.99, 'box': [100, 150, 200, 250], 'keypoints': {'left_eye': (0, 0), 'right_eye': (0, 0)}}
        ])
        
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        single_face_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
        
        if os.path.exists(single_face_image):
            result = mock_processor.detect_face_and_features(single_face_image)
            
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
    
    def test_head_height_ratio_calculation(self, mock_processor):
        """
        Test that head height ratio is calculated correctly.
        Validates: Requirement 2.6 - WHEN the System detects a face 
        THEN the System SHALL calculate the head height ratio
        """
        # Mock MTCNN to return a face with known dimensions
        mock_processor.detector.detect_faces = Mock(return_value=[
            {'confidence': 0.99, 'box': [100, 100, 200, 300], 'keypoints': {'left_eye': (0, 0), 'right_eye': (0, 0)}}
        ])
        
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        test_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
        
        if os.path.exists(test_image):
            result = mock_processor.detect_face_and_features(test_image)
            
            if result and result.get('valid'):
                assert 'head_height_percent' in result
                assert isinstance(result['head_height_percent'], (int, float))
                assert 0 < result['head_height_percent'] <= 1
    
    def test_head_height_validation_flag(self, mock_processor):
        """
        Test that head height validation flag is set correctly.
        Validates: Requirement 2.7 - WHEN the head height ratio is between 0.50 and 0.69 
        THEN the System SHALL mark head height as valid
        """
        # Mock MTCNN to return a face
        mock_processor.detector.detect_faces = Mock(return_value=[
            {'confidence': 0.99, 'box': [100, 100, 200, 300], 'keypoints': {'left_eye': (0, 0), 'right_eye': (0, 0)}}
        ])
        
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        test_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
        
        if os.path.exists(test_image):
            result = mock_processor.detect_face_and_features(test_image)
            
            if result and result.get('valid'):
                assert 'head_height_valid' in result
                assert isinstance(result['head_height_valid'], bool)
                
                # Verify logic: if head height is in valid range, flag should be True
                if 0.50 <= result['head_height_percent'] <= 0.69:
                    assert result['head_height_valid'] is True
                else:
                    assert result['head_height_valid'] is False
    
    def test_horizontal_centering_flag(self, mock_processor):
        """
        Test that horizontal centering flag is present.
        Validates: Requirement 2.8 - WHEN the face center is within 30% of the horizontal image center 
        THEN the System SHALL mark the face as horizontally centered
        """
        # Mock MTCNN to return a face
        mock_processor.detector.detect_faces = Mock(return_value=[
            {'confidence': 0.99, 'box': [100, 100, 200, 300], 'keypoints': {'left_eye': (0, 0), 'right_eye': (0, 0)}}
        ])
        
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        test_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
        
        if os.path.exists(test_image):
            result = mock_processor.detect_face_and_features(test_image)
            
            if result and result.get('valid'):
                assert 'horizontally_centered' in result
                assert isinstance(result['horizontally_centered'], bool)
    
    def test_invalid_image_path_handling(self, mock_processor):
        """
        Test that invalid image paths are handled gracefully.
        """
        result = mock_processor.detect_face_and_features('nonexistent_image.jpg')
        assert result is None
    
    def test_image_dimensions_included(self, mock_processor):
        """
        Test that image dimensions are included in valid results.
        """
        # Mock MTCNN to return a face
        mock_processor.detector.detect_faces = Mock(return_value=[
            {'confidence': 0.99, 'box': [100, 100, 200, 300], 'keypoints': {'left_eye': (0, 0), 'right_eye': (0, 0)}}
        ])
        
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        test_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
        
        if os.path.exists(test_image):
            result = mock_processor.detect_face_and_features(test_image)
            
            if result and result.get('valid'):
                assert 'image_dimensions' in result
                assert 'width' in result['image_dimensions']
                assert 'height' in result['image_dimensions']
                assert result['image_dimensions']['width'] > 0
                assert result['image_dimensions']['height'] > 0
    
    def test_eyes_detected_count_included(self, mock_processor):
        """
        Test that eye detection count is included in results.
        """
        # Mock MTCNN to return a face with keypoints
        mock_processor.detector.detect_faces = Mock(return_value=[
            {'confidence': 0.99, 'box': [100, 100, 200, 300], 
             'keypoints': {'left_eye': (150, 150), 'right_eye': (250, 150), 'nose': (200, 200)}}
        ])
        
        fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        test_image = os.path.join(fixtures_dir, 'single_face_centered.jpg')
        
        if os.path.exists(test_image):
            result = mock_processor.detect_face_and_features(test_image)
            
            if result and result.get('valid'):
                assert 'eyes_detected' in result
                assert isinstance(result['eyes_detected'], int)
                assert result['eyes_detected'] >= 0


class TestFaceDetectionConstants:
    """Test that face detection constants are properly defined."""
    
    def test_head_height_constants_defined(self):
        """Test that HEAD_HEIGHT_MIN and HEAD_HEIGHT_MAX are defined correctly."""
        with patch('application.MTCNN'):
            from application import PassportPhotoProcessor
            
            assert hasattr(PassportPhotoProcessor, 'HEAD_HEIGHT_MIN')
            assert hasattr(PassportPhotoProcessor, 'HEAD_HEIGHT_MAX')
            assert PassportPhotoProcessor.HEAD_HEIGHT_MIN == 0.50
            assert PassportPhotoProcessor.HEAD_HEIGHT_MAX == 0.69
    
    def test_passport_size_constant_defined(self):
        """Test that PASSPORT_SIZE_PIXELS is defined correctly."""
        with patch('application.MTCNN'):
            from application import PassportPhotoProcessor
            
            assert hasattr(PassportPhotoProcessor, 'PASSPORT_SIZE_PIXELS')
            assert PassportPhotoProcessor.PASSPORT_SIZE_PIXELS == (600, 600)
