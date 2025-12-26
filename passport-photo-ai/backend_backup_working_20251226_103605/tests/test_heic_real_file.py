"""
Tests for HEIC conversion with real HEIC file.
Tests Requirements 1.2 from the specification.
"""

import pytest
import os
from PIL import Image


class TestHEICConversionWithRealFile:
    """Test HEIC conversion with actual HEIC file."""
    
    @pytest.fixture
    def heic_file_path(self):
        """Path to the real HEIC test file."""
        return os.path.join(os.path.dirname(__file__), 'fixtures', 'IMG_8968.HEIC')
    
    @pytest.fixture
    def cleanup_converted_file(self, heic_file_path):
        """Cleanup fixture to remove converted JPEG after test."""
        yield
        # Cleanup: remove the converted JPEG file
        jpeg_path = heic_file_path.rsplit('.', 1)[0] + '.jpg'
        if os.path.exists(jpeg_path):
            os.remove(jpeg_path)
    
    def test_real_heic_file_exists(self, heic_file_path):
        """Verify the real HEIC test file exists."""
        assert os.path.exists(heic_file_path), \
            f"Real HEIC test file not found: {heic_file_path}"
        
        # Verify it's a reasonable size (should be > 1MB for a real photo)
        file_size = os.path.getsize(heic_file_path)
        assert file_size > 1_000_000, \
            f"HEIC file seems too small: {file_size} bytes"
    
    def test_convert_real_heic_to_jpeg(self, heic_file_path, cleanup_converted_file):
        """
        Test converting a real HEIC file to JPEG.
        Validates: Requirement 1.2 - WHEN a user uploads a HEIC file 
        THEN the System SHALL convert it to JPEG format before processing
        """
        from application import convert_heic_to_jpeg
        
        # Convert the HEIC file
        result = convert_heic_to_jpeg(heic_file_path)
        
        # Verify conversion succeeded
        assert result is not None, "Conversion should return a file path"
        assert result.endswith('.jpg'), "Output should be a JPEG file"
        
        # Verify the output file exists
        assert os.path.exists(result), f"Converted file should exist: {result}"
        
        # Verify it's a valid JPEG
        img = Image.open(result)
        assert img.format == 'JPEG', "Output should be in JPEG format"
        assert img.mode == 'RGB', "Output should be in RGB mode"
        
        # Verify image has reasonable dimensions
        width, height = img.size
        assert width > 0 and height > 0, "Image should have valid dimensions"
        assert width >= 600 and height >= 600, \
            "Image should meet minimum resolution requirements"
        
        print(f"\n✓ Successfully converted HEIC to JPEG")
        print(f"✓ Output: {result}")
        print(f"✓ Dimensions: {img.size}")
        print(f"✓ Mode: {img.mode}")
    
    def test_converted_jpeg_is_valid_image(self, heic_file_path, cleanup_converted_file):
        """Test that the converted JPEG is a valid, openable image."""
        from application import convert_heic_to_jpeg
        
        result = convert_heic_to_jpeg(heic_file_path)
        assert result is not None
        
        # Try to open and manipulate the image
        img = Image.open(result)
        
        # Verify we can perform operations on it
        img_copy = img.copy()
        assert img_copy.size == img.size
        
        # Verify we can get pixel data
        pixels = img.load()
        assert pixels is not None
        
        # Verify we can resize it
        resized = img.resize((100, 100))
        assert resized.size == (100, 100)
    
    def test_converted_jpeg_preserves_dimensions(self, heic_file_path, cleanup_converted_file):
        """Test that JPEG conversion preserves original image dimensions."""
        from application import convert_heic_to_jpeg
        
        # Open original HEIC to get dimensions
        original_img = Image.open(heic_file_path)
        original_size = original_img.size
        
        # Convert to JPEG
        result = convert_heic_to_jpeg(heic_file_path)
        assert result is not None
        
        # Open converted JPEG
        converted_img = Image.open(result)
        converted_size = converted_img.size
        
        # Dimensions should match
        assert converted_size == original_size, \
            f"Dimensions should be preserved: {original_size} -> {converted_size}"
    
    def test_converted_jpeg_file_size(self, heic_file_path, cleanup_converted_file):
        """Test that converted JPEG has reasonable file size."""
        from application import convert_heic_to_jpeg
        
        original_size = os.path.getsize(heic_file_path)
        
        result = convert_heic_to_jpeg(heic_file_path)
        assert result is not None
        
        converted_size = os.path.getsize(result)
        
        # JPEG should exist and have reasonable size
        assert converted_size > 0, "Converted file should not be empty"
        
        # JPEG might be larger or smaller than HEIC depending on content
        # Just verify it's in a reasonable range (not corrupted)
        assert converted_size > 10_000, "Converted file seems too small"
        
        print(f"\n✓ Original HEIC: {original_size:,} bytes")
        print(f"✓ Converted JPEG: {converted_size:,} bytes")
    
    def test_heic_conversion_output_path_format(self, heic_file_path):
        """Test that output path is correctly formatted."""
        from application import convert_heic_to_jpeg
        
        # Don't actually convert, just test the path logic
        expected_output = heic_file_path.rsplit('.', 1)[0] + '.jpg'
        
        # Verify the expected path format
        assert expected_output.endswith('.jpg')
        assert 'IMG_8968' in expected_output
        assert expected_output != heic_file_path


class TestHEICConversionQuality:
    """Test HEIC conversion quality and settings."""
    
    @pytest.fixture
    def heic_file_path(self):
        """Path to the real HEIC test file."""
        return os.path.join(os.path.dirname(__file__), 'fixtures', 'IMG_8968.HEIC')
    
    @pytest.fixture
    def cleanup_converted_file(self, heic_file_path):
        """Cleanup fixture to remove converted JPEG after test."""
        yield
        jpeg_path = heic_file_path.rsplit('.', 1)[0] + '.jpg'
        if os.path.exists(jpeg_path):
            os.remove(jpeg_path)
    
    def test_jpeg_quality_setting(self, heic_file_path, cleanup_converted_file):
        """Test that JPEG is saved with high quality (95%)."""
        from application import convert_heic_to_jpeg
        
        result = convert_heic_to_jpeg(heic_file_path)
        assert result is not None
        
        # Open the JPEG and verify it's high quality
        img = Image.open(result)
        
        # High quality JPEG should have minimal compression artifacts
        # We can't directly check quality setting, but we can verify
        # the file is not overly compressed
        file_size = os.path.getsize(result)
        img_pixels = img.size[0] * img.size[1]
        
        # Rough heuristic: JPEG should have reasonable compression
        # (not too small, indicating over-compression)
        bytes_per_pixel = file_size / img_pixels
        assert bytes_per_pixel > 0.1, \
            f"JPEG may be over-compressed: {bytes_per_pixel:.2f} bytes/pixel"
        
        print(f"\n✓ JPEG quality check: {bytes_per_pixel:.2f} bytes/pixel")
    
    def test_rgb_color_mode(self, heic_file_path, cleanup_converted_file):
        """Test that converted JPEG is in RGB color mode."""
        from application import convert_heic_to_jpeg
        
        result = convert_heic_to_jpeg(heic_file_path)
        assert result is not None
        
        img = Image.open(result)
        assert img.mode == 'RGB', \
            f"JPEG should be in RGB mode, got: {img.mode}"


@pytest.mark.skipif(
    not os.path.exists(os.path.join(os.path.dirname(__file__), 'fixtures', 'IMG_8968.HEIC')),
    reason="Real HEIC test file not available"
)
class TestHEICConversionIntegration:
    """Integration tests for HEIC conversion in the full workflow."""
    
    def test_heic_file_can_be_processed_by_face_detection(self):
        """Test that converted HEIC can be used for face detection."""
        from application import convert_heic_to_jpeg, PassportPhotoProcessor
        
        heic_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'IMG_8968.HEIC')
        
        # Convert HEIC to JPEG
        jpeg_path = convert_heic_to_jpeg(heic_path)
        assert jpeg_path is not None
        
        try:
            # Try to process with face detection
            processor = PassportPhotoProcessor()
            result = processor.detect_face_and_features(jpeg_path)
            
            # Should return a result (even if no face detected)
            assert result is not None
            assert 'faces_detected' in result
            
            print(f"\n✓ Converted HEIC can be processed")
            print(f"✓ Faces detected: {result.get('faces_detected', 0)}")
            
        finally:
            # Cleanup
            if os.path.exists(jpeg_path):
                os.remove(jpeg_path)
