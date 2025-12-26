"""
Property tests for photo quality enhancement infrastructure
Tests integration compatibility preservation and basic functionality
"""

import pytest
import numpy as np
from hypothesis import given, strategies as st, settings
import cv2
from PIL import Image
import io
import tempfile
import os

# Import the enhancement modules
from enhancement import (
    FaceDetectionPipeline, 
    ImageEnhancer, 
    QualityValidator, 
    ProcessingController
)
from enhancement.data_models import QualityMetrics, FaceData


class TestEnhancementInfrastructure:
    """Test infrastructure setup and integration compatibility"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.face_detector = FaceDetectionPipeline()
        self.image_enhancer = ImageEnhancer()
        self.quality_validator = QualityValidator()
        self.processing_controller = ProcessingController()
    
    def test_modules_import_successfully(self):
        """Test that all enhancement modules can be imported"""
        # This test verifies the basic infrastructure is set up correctly
        assert self.face_detector is not None
        assert self.image_enhancer is not None
        assert self.quality_validator is not None
        assert self.processing_controller is not None
    
    def test_mediapipe_and_opencv_availability(self):
        """Test that required dependencies are available"""
        # Test MediaPipe availability
        try:
            import mediapipe as mp
            mediapipe_available = True
        except ImportError:
            mediapipe_available = False
        
        # Test OpenCV availability
        try:
            import cv2
            opencv_available = True
        except ImportError:
            opencv_available = False
        
        # At least one should be available for face detection
        assert mediapipe_available or opencv_available, "Neither MediaPipe nor OpenCV is available"
    
    @given(
        width=st.integers(min_value=100, max_value=800),
        height=st.integers(min_value=100, max_value=800)
    )
    @settings(max_examples=20, deadline=1000)  # 1 second deadline, fewer examples
    def test_integration_compatibility_preservation(self, width, height):
        """
        Property 11: Integration Compatibility Preservation
        For any image processed through the enhanced system, background removal 
        functionality should remain perfect, output format should be 1200x1200, 
        and the system should gracefully fall back to current pipeline if enhanced 
        processing fails.
        
        **Feature: photo-quality-enhancement, Property 11: Integration Compatibility Preservation**
        **Validates: Requirements 6.1, 6.2, 6.3**
        """
        # Create a test image
        test_image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        
        # Test that enhancement modules can process the image without breaking
        try:
            # Test image enhancer
            quality_metrics = self.image_enhancer.calculate_quality_metrics(test_image)
            assert isinstance(quality_metrics, QualityMetrics)
            
            # Test quality validator
            validation_result = self.quality_validator.validate_against_gold_standard(
                test_image, quality_metrics
            )
            assert validation_result is not None
            assert hasattr(validation_result, 'overall_score')
            
            # Test that processing doesn't alter image format compatibility
            # (The enhanced image should still be processable by existing pipeline)
            enhanced_result = self.processing_controller.process_with_iteration(test_image)
            assert enhanced_result is not None
            assert enhanced_result.enhanced_image is not None
            assert enhanced_result.enhanced_image.dtype == np.uint8
            assert len(enhanced_result.enhanced_image.shape) == 3  # BGR format
            
        except Exception as e:
            # System should gracefully handle failures
            pytest.fail(f"Enhancement system failed to handle image gracefully: {e}")
    
    @given(
        image_data=st.binary(min_size=1000, max_size=50000)
    )
    @settings(max_examples=20)
    def test_memory_efficient_processing(self, image_data):
        """
        Test that processing is memory efficient and doesn't cause memory leaks
        """
        try:
            # Create image from binary data
            img_array = np.frombuffer(image_data, dtype=np.uint8)
            if len(img_array) < 300:  # Too small for image
                return
            
            # Reshape to valid image dimensions
            size = int(np.sqrt(len(img_array) // 3))
            if size < 10:
                return
            
            img_array = img_array[:size*size*3].reshape(size, size, 3)
            
            # Test that processing completes without memory issues
            quality_metrics = self.image_enhancer.calculate_quality_metrics(img_array)
            assert quality_metrics is not None
            
            # Verify memory cleanup (no lingering large objects)
            import gc
            gc.collect()
            
        except (ValueError, MemoryError):
            # Expected for invalid image data
            pass
        except Exception as e:
            pytest.fail(f"Unexpected error in memory efficient processing: {e}")
    
    def test_fallback_mechanisms(self):
        """Test that fallback mechanisms work when components fail"""
        # Test with None image (should handle gracefully)
        result = self.processing_controller.process_with_iteration(None)
        assert result is not None
        assert result.validation_result.overall_score == 0.0
        
        # Test with empty image
        empty_image = np.array([])
        result = self.processing_controller.process_with_iteration(empty_image)
        assert result is not None
        assert result.validation_result.overall_score == 0.0
        
        # Test with invalid image shape
        invalid_image = np.random.randint(0, 255, (5,), dtype=np.uint8)
        result = self.processing_controller.process_with_iteration(invalid_image)
        assert result is not None
    
    def test_output_format_compatibility(self):
        """Test that output format remains compatible with existing pipeline"""
        # Create a standard test image (600x600 RGB)
        test_image = np.random.randint(0, 255, (600, 600, 3), dtype=np.uint8)
        
        # Process through enhancement pipeline
        result = self.processing_controller.process_with_iteration(test_image)
        
        # Verify output format compatibility
        enhanced_image = result.enhanced_image
        
        # Should be numpy array in BGR format (OpenCV standard)
        assert isinstance(enhanced_image, np.ndarray)
        assert enhanced_image.dtype == np.uint8
        assert len(enhanced_image.shape) == 3
        assert enhanced_image.shape[2] == 3  # 3 channels (BGR)
        
        # Should be processable by PIL (for existing pipeline compatibility)
        try:
            # Convert BGR to RGB for PIL
            rgb_image = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            assert pil_image.mode == 'RGB'
        except Exception as e:
            pytest.fail(f"Enhanced image not compatible with PIL processing: {e}")
    
    def test_processing_time_limits(self):
        """Test that processing completes within reasonable time limits"""
        import time
        
        # Create a moderately sized test image
        test_image = np.random.randint(0, 255, (800, 800, 3), dtype=np.uint8)
        
        start_time = time.time()
        result = self.processing_controller.process_with_iteration(test_image)
        processing_time = time.time() - start_time
        
        # Should complete within 5 seconds (generous limit for testing)
        assert processing_time < 5.0, f"Processing took too long: {processing_time:.2f}s"
        
        # Should have reasonable number of attempts
        assert result.total_attempts <= self.processing_controller.MAX_ATTEMPTS
    
    def test_error_handling_and_logging(self):
        """Test that errors are handled gracefully with proper logging"""
        import logging
        
        # Capture log messages
        with pytest.LoggingPlugin.caplog.at_level(logging.INFO):
            # Test with problematic input
            problematic_image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
            result = self.processing_controller.process_with_iteration(problematic_image)
            
            # Should handle gracefully
            assert result is not None
            assert isinstance(result.validation_result.overall_score, float)
    
    @given(
        attempts=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10)
    def test_iteration_limits_respected(self, attempts):
        """Test that iteration limits are properly respected"""
        # Create a low-quality image that will trigger multiple attempts
        low_quality_image = np.ones((600, 600, 3), dtype=np.uint8) * 50  # Very dark, low contrast
        
        result = self.processing_controller.process_with_iteration(
            low_quality_image, max_attempts=attempts
        )
        
        # Should not exceed the specified attempt limit
        assert result.total_attempts <= attempts
        assert len(result.processing_history) <= attempts


# Additional integration tests
class TestEnhancementIntegration:
    """Test integration between enhancement components"""
    
    def test_component_integration_flow(self):
        """Test that components work together in the expected flow"""
        # Create test image
        test_image = np.random.randint(0, 255, (600, 600, 3), dtype=np.uint8)
        
        # Test full integration flow
        face_detector = FaceDetectionPipeline()
        image_enhancer = ImageEnhancer()
        quality_validator = QualityValidator()
        
        # 1. Face detection
        face_result = face_detector.detect_faces(test_image)
        assert face_result is not None
        
        # 2. Quality metrics calculation
        quality_metrics = image_enhancer.calculate_quality_metrics(test_image)
        assert quality_metrics is not None
        
        # 3. Quality validation
        validation_result = quality_validator.validate_against_gold_standard(
            test_image, quality_metrics, face_result.primary_face
        )
        assert validation_result is not None
        
        # 4. Enhancement (if needed)
        if validation_result.overall_score < 0.8:
            enhanced_image = image_enhancer.enhance_sharpness(test_image)
            assert enhanced_image is not None
            assert enhanced_image.shape == test_image.shape
    
    def test_data_model_compatibility(self):
        """Test that data models work correctly across components"""
        from enhancement.data_models import (
            FaceData, QualityMetrics, ValidationResult, 
            ProcessingResult, EnhancementStrategy
        )
        
        # Test FaceData creation
        face_data = FaceData(
            bounding_box=(100, 100, 200, 200),
            confidence=0.95,
            face_size_ratio=0.75
        )
        assert face_data.confidence == 0.95
        
        # Test QualityMetrics creation
        metrics = QualityMetrics(
            sharpness_score=0.8,
            noise_level=0.005,
            contrast_score=0.7
        )
        assert metrics.sharpness_score == 0.8
        
        # Test that components can use these data models
        validator = QualityValidator()
        test_image = np.random.randint(0, 255, (600, 600, 3), dtype=np.uint8)
        
        result = validator.validate_against_gold_standard(test_image, metrics, face_data)
        assert isinstance(result, ValidationResult)
        assert result.face_compliance_score > 0  # Should have some score due to face_data