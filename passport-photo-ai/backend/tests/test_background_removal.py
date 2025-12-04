"""
Tests for background removal functionality.
Tests Requirements 4.2, 4.3, 4.4, 4.5 from the specification.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import tempfile
import numpy as np


class TestBackgroundRemoval:
    """Test background removal functionality."""
    
    def test_remove_background_method_exists(self):
        """Test that the remove_background method is available."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        assert hasattr(processor, 'remove_background')
        assert callable(processor.remove_background)
    
    def test_background_color_replacement(self):
        """
        Test that background pixels are replaced with white (255, 255, 255).
        Validates: Requirement 4.2 - WHEN the System removes a background 
        THEN the System SHALL replace it with a solid white background (RGB 255, 255, 255)
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create a test image
        test_img = Image.new('RGB', (100, 100), color=(100, 150, 200))
        
        # Mock rembg to return an image with alpha channel
        with patch('application.remove') as mock_remove:
            # Create a mock foreground with transparency
            foreground = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            # Add a small opaque region (simulating the subject)
            for x in range(40, 60):
                for y in range(40, 60):
                    foreground.putpixel((x, y), (100, 100, 100, 255))
            
            mock_remove.return_value = foreground
            
            result = processor.remove_background(test_img)
            
            # Verify result is RGB
            assert result.mode == 'RGB'
            assert result.size == (100, 100)
            
            # Check that background pixels are white (255, 255, 255)
            # Sample a corner pixel (should be background)
            pixel = result.getpixel((0, 0))
            assert pixel == (255, 255, 255), f"Background pixel should be white, got {pixel}"
    
    def test_foreground_preservation(self):
        """
        Test that foreground subject is preserved during background removal.
        Validates: Requirement 4.3 - WHEN background removal is enabled 
        THEN the System SHALL preserve the foreground subject with transparency information
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create a test image with a distinct subject
        test_img = Image.new('RGB', (100, 100), color=(200, 200, 200))
        
        with patch('application.remove') as mock_remove:
            # Create foreground with a distinct subject region
            foreground = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            # Subject in center (red color)
            for x in range(40, 60):
                for y in range(40, 60):
                    foreground.putpixel((x, y), (255, 0, 0, 255))
            
            mock_remove.return_value = foreground
            
            result = processor.remove_background(test_img)
            
            # Check that subject pixels are preserved (should be red)
            subject_pixel = result.getpixel((50, 50))
            assert subject_pixel[0] > 200, "Subject red channel should be preserved"
            
            # Background should be white
            bg_pixel = result.getpixel((10, 10))
            assert bg_pixel == (255, 255, 255)
    
    def test_background_removal_fallback_on_error(self):
        """
        Test that original image is returned when background removal fails.
        Validates: Requirement 4.4 - WHEN background removal fails 
        THEN the System SHALL return the original image without modification
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create a test image
        test_img = Image.new('RGB', (100, 100), color=(50, 100, 150))
        original_pixel = test_img.getpixel((50, 50))
        
        # Mock rembg to raise an exception
        with patch('application.remove', side_effect=Exception("Background removal failed")):
            result = processor.remove_background(test_img)
            
            # Verify original image is returned
            assert result.size == test_img.size
            assert result.mode == test_img.mode
            result_pixel = result.getpixel((50, 50))
            assert result_pixel == original_pixel, "Original image should be returned on error"
    
    def test_background_removal_toggle_on(self):
        """
        Test that background removal is applied when enabled.
        Validates: Requirement 4.1 - WHEN a user enables background removal 
        THEN the System SHALL use the rembg deep learning model to remove the background
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create a test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (600, 600), color='blue')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Mock face detection and background removal
            with patch.object(processor, 'remove_background') as mock_remove_bg:
                mock_remove_bg.return_value = Image.new('RGB', (600, 600), color='white')
                
                # Process with background removal enabled
                face_bbox = {'x': 100, 'y': 100, 'width': 200, 'height': 200}
                result = processor.process_to_passport_photo(tmp_path, face_bbox, remove_bg=True)
                
                # Verify remove_background was called
                assert mock_remove_bg.called, "Background removal should be called when enabled"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_background_removal_toggle_off(self):
        """
        Test that background removal is skipped when disabled.
        Validates: Requirement 4.5 - WHEN a user disables background removal 
        THEN the System SHALL process the photo with the original background intact
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create a test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (600, 600), color='green')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Mock background removal to track if it's called
            with patch.object(processor, 'remove_background') as mock_remove_bg:
                mock_remove_bg.return_value = Image.new('RGB', (600, 600), color='white')
                
                # Process with background removal disabled
                face_bbox = {'x': 100, 'y': 100, 'width': 200, 'height': 200}
                result = processor.process_to_passport_photo(tmp_path, face_bbox, remove_bg=False)
                
                # Verify remove_background was NOT called
                assert not mock_remove_bg.called, "Background removal should not be called when disabled"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestBackgroundRemovalIntegration:
    """Test background removal integration with the processing pipeline."""
    
    def test_rembg_library_available(self):
        """Test that rembg library is available."""
        try:
            from rembg import remove
            assert callable(remove)
        except ImportError:
            pytest.fail("rembg library is not installed")
    
    def test_background_removal_preserves_image_size(self):
        """Test that background removal preserves image dimensions."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Create test images of different sizes
        test_sizes = [(100, 100), (200, 150), (300, 400)]
        
        for size in test_sizes:
            test_img = Image.new('RGB', size, color='red')
            
            with patch('application.remove') as mock_remove:
                # Return a foreground with the same size
                foreground = Image.new('RGBA', size, (0, 0, 0, 0))
                mock_remove.return_value = foreground
                
                result = processor.remove_background(test_img)
                
                assert result.size == size, f"Size should be preserved: expected {size}, got {result.size}"
    
    def test_background_removal_output_mode(self):
        """Test that background removal output is in RGB mode."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        test_img = Image.new('RGB', (100, 100), color='yellow')
        
        with patch('application.remove') as mock_remove:
            foreground = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            mock_remove.return_value = foreground
            
            result = processor.remove_background(test_img)
            
            # Output should be RGB (not RGBA)
            assert result.mode == 'RGB', f"Output should be RGB mode, got {result.mode}"
    
    def test_background_removal_with_different_input_modes(self):
        """Test background removal with different input image modes."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Test with different modes
        test_modes = ['RGB', 'L', 'RGBA']
        
        for mode in test_modes:
            if mode == 'L':
                test_img = Image.new(mode, (100, 100), color=128)
            elif mode == 'RGBA':
                test_img = Image.new(mode, (100, 100), color=(100, 100, 100, 255))
            else:
                test_img = Image.new(mode, (100, 100), color=(100, 100, 100))
            
            with patch('application.remove') as mock_remove:
                foreground = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
                mock_remove.return_value = foreground
                
                result = processor.remove_background(test_img)
                
                # Should always return RGB
                assert result.mode == 'RGB'
                assert result.size == (100, 100)


class TestBackgroundRemovalQuality:
    """Test background removal quality and edge cases."""
    
    def test_white_background_color_values(self):
        """Test that white background has exact RGB values (255, 255, 255)."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        test_img = Image.new('RGB', (50, 50), color='blue')
        
        with patch('application.remove') as mock_remove:
            # Return fully transparent foreground (all background)
            foreground = Image.new('RGBA', (50, 50), (0, 0, 0, 0))
            mock_remove.return_value = foreground
            
            result = processor.remove_background(test_img)
            
            # Check multiple background pixels
            for x in [0, 25, 49]:
                for y in [0, 25, 49]:
                    pixel = result.getpixel((x, y))
                    assert pixel == (255, 255, 255), f"Pixel at ({x},{y}) should be (255,255,255), got {pixel}"
    
    def test_background_removal_with_partial_transparency(self):
        """Test background removal with partially transparent foreground."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        test_img = Image.new('RGB', (100, 100), color='gray')
        
        with patch('application.remove') as mock_remove:
            # Create foreground with partial transparency
            foreground = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            # Semi-transparent subject
            for x in range(40, 60):
                for y in range(40, 60):
                    foreground.putpixel((x, y), (200, 100, 50, 128))  # 50% transparent
            
            mock_remove.return_value = foreground
            
            result = processor.remove_background(test_img)
            
            # Result should be valid RGB image
            assert result.mode == 'RGB'
            assert result.size == (100, 100)
    
    def test_background_removal_error_message(self):
        """Test that error messages are printed when background removal fails."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        test_img = Image.new('RGB', (100, 100), color='red')
        
        # Mock rembg to raise an exception and capture print output
        with patch('application.remove', side_effect=Exception("Test error")):
            with patch('builtins.print') as mock_print:
                result = processor.remove_background(test_img)
                
                # Verify error was printed
                assert mock_print.called
                call_args = str(mock_print.call_args)
                assert 'error' in call_args.lower() or 'Error' in call_args
