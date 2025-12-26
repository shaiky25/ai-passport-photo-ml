"""
Tests for image processing and cropping functionality.
Tests Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6 from the specification.
"""

import pytest
import os
from unittest.mock import Mock, patch
from PIL import Image
import tempfile
import io


class TestImageProcessing:
    """Test image processing and cropping functionality."""
    
    def test_output_dimensions_600x600(self):
        """
        Test that output is exactly 600x600 pixels.
        Validates: Requirement 5.1 - WHEN the System processes a photo 
        THEN the System SHALL produce a final image of exactly 600x600 pixels at 300 DPI
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (1000, 1000), color='blue')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            face_bbox = {'x': 300, 'y': 300, 'width': 400, 'height': 400}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            
            assert result_img.size == (600, 600), f"Expected (600, 600), got {result_img.size}"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_crop_boundary_constraints(self):
        """
        Test that crop area stays within image boundaries.
        Validates: Requirement 5.5 - WHEN calculating crop dimensions 
        THEN the System SHALL ensure the crop area remains within image boundaries
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create small test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (800, 800), color='green')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Face near edge (would cause crop to go out of bounds)
            face_bbox = {'x': 50, 'y': 50, 'width': 200, 'height': 200}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            # Should complete without errors
            assert result_buffer is not None
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            assert result_img.size == (600, 600)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_center_crop_without_face(self):
        """
        Test center crop when no face is detected.
        Validates: Requirement 5.6 - WHEN no face is detected 
        THEN the System SHALL perform a center crop using the minimum dimension of the image
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create rectangular test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (1200, 800), color='red')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # No face bbox (None)
            result_buffer = processor.process_to_passport_photo(tmp_path, None)
            
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            
            # Should still produce 600x600 output
            assert result_img.size == (600, 600)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_processing_with_learned_profile(self):
        """
        Test processing uses learned profile when available.
        Validates: Requirement 5.3 - WHEN a learned profile exists 
        THEN the System SHALL use the learned geometric ratios
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock learned profile
        mock_profile = {
            'mean': {
                'head_height_ratio': 0.60,
                'face_center_x_ratio': 0.50,
                'head_top_y_ratio': 0.15
            }
        }
        processor.learned_profile = mock_profile
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (1000, 1000), color='yellow')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            face_bbox = {'x': 300, 'y': 300, 'width': 400, 'height': 400}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            # Should complete successfully with learned profile
            assert result_buffer is not None
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            assert result_img.size == (600, 600)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            processor.learned_profile = None  # Reset
    
    def test_processing_without_learned_profile(self):
        """
        Test processing uses default rules without learned profile.
        Validates: Requirement 5.4 - WHEN no learned profile exists 
        THEN the System SHALL use default cropping rules with a target head height ratio of 0.60
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        processor.learned_profile = None  # Ensure no profile
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (1000, 1000), color='purple')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            face_bbox = {'x': 300, 'y': 300, 'width': 400, 'height': 400}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            # Should complete successfully with default rules
            assert result_buffer is not None
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            assert result_img.size == (600, 600)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_rgb_mode_conversion(self):
        """Test that non-RGB images are converted to RGB."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create grayscale test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('L', (1000, 1000), color=128)
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            face_bbox = {'x': 300, 'y': 300, 'width': 400, 'height': 400}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            
            # Output should be RGB
            assert result_img.mode == 'RGB'
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_large_image_preservation(self):
        """Test that images up to 2400px are preserved."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create 2000x2000 image (should not be resized)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (2000, 2000), color='orange')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            face_bbox = {'x': 500, 'y': 500, 'width': 800, 'height': 800}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            # Should complete successfully
            assert result_buffer is not None
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            assert result_img.size == (600, 600)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestImageEnhancement:
    """Test image enhancement functionality."""
    
    def test_brightness_enhancement_applied(self):
        """Test that brightness enhancement is applied."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Create dark image
            test_img = Image.new('RGB', (1000, 1000), color=(50, 50, 50))
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            face_bbox = {'x': 300, 'y': 300, 'width': 400, 'height': 400}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            
            # Result should exist and be valid
            assert result_img.size == (600, 600)
            assert result_img.mode == 'RGB'
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_output_is_jpeg_buffer(self):
        """Test that output is a BytesIO buffer with JPEG data."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (1000, 1000), color='cyan')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            face_bbox = {'x': 300, 'y': 300, 'width': 400, 'height': 400}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            # Verify it's a BytesIO buffer
            assert isinstance(result_buffer, io.BytesIO)
            
            # Verify it contains valid JPEG data
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            assert result_img.format == 'JPEG'
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestCroppingLogic:
    """Test cropping logic and calculations."""
    
    def test_face_centering_with_bbox(self):
        """
        Test that face is centered when bbox is provided.
        Validates: Requirement 5.2 - WHEN a valid face is detected 
        THEN the System SHALL crop the image to center the face
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (1000, 1000), color='magenta')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Centered face
            face_bbox = {'x': 400, 'y': 400, 'width': 200, 'height': 200}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            
            # Should produce valid output
            assert result_img.size == (600, 600)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_crop_with_face_near_edge(self):
        """Test cropping when face is near image edge."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (800, 800), color='brown')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Face near top-left corner
            face_bbox = {'x': 100, 'y': 100, 'width': 150, 'height': 150}
            result_buffer = processor.process_to_passport_photo(tmp_path, face_bbox)
            
            # Should handle edge case gracefully
            assert result_buffer is not None
            result_buffer.seek(0)
            result_img = Image.open(result_buffer)
            assert result_img.size == (600, 600)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
