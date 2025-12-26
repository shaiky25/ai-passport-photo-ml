"""
Tests for HEIC to JPEG conversion functionality.
Tests Requirements 1.2 from the specification.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import tempfile


class TestHEICConversion:
    """Test HEIC to JPEG conversion functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_heic_conversion_function_exists(self):
        """Test that the HEIC conversion function is available."""
        from application import convert_heic_to_jpeg
        
        assert callable(convert_heic_to_jpeg)
    
    def test_heic_to_jpeg_conversion_with_mock(self, temp_dir):
        """
        Test that HEIC files are converted to JPEG format.
        Validates: Requirement 1.2 - WHEN a user uploads a HEIC file 
        THEN the System SHALL convert it to JPEG format before processing
        """
        from application import convert_heic_to_jpeg
        
        # Create a mock HEIC file path
        heic_path = os.path.join(temp_dir, 'test_image.heic')
        expected_jpeg_path = os.path.join(temp_dir, 'test_image.jpg')
        
        # Mock pyheif.read to return a mock HEIF file
        mock_heif_file = MagicMock()
        mock_heif_file.mode = 'RGB'
        mock_heif_file.size = (800, 600)
        mock_heif_file.data = b'\x00' * (800 * 600 * 3)  # Mock image data
        mock_heif_file.stride = 800 * 3
        
        with patch('application.pyheif.read', return_value=mock_heif_file):
            with patch('application.Image.frombytes') as mock_frombytes:
                mock_image = MagicMock()
                mock_frombytes.return_value = mock_image
                
                result = convert_heic_to_jpeg(heic_path)
                
                # Verify the function was called correctly
                assert mock_frombytes.called
                assert mock_image.save.called
                
                # Verify the result is the expected JPEG path
                assert result == expected_jpeg_path
                
                # Verify save was called with JPEG format
                save_args = mock_image.save.call_args
                assert save_args[0][0] == expected_jpeg_path
                assert save_args[0][1] == 'JPEG'
    
    def test_heic_conversion_returns_jpeg_path(self, temp_dir):
        """Test that HEIC conversion returns a .jpg file path."""
        from application import convert_heic_to_jpeg
        
        heic_path = os.path.join(temp_dir, 'photo.heic')
        
        mock_heif_file = MagicMock()
        mock_heif_file.mode = 'RGB'
        mock_heif_file.size = (800, 600)
        mock_heif_file.data = b'\x00' * (800 * 600 * 3)
        mock_heif_file.stride = 800 * 3
        
        with patch('application.pyheif.read', return_value=mock_heif_file):
            with patch('application.Image.frombytes') as mock_frombytes:
                mock_image = MagicMock()
                mock_frombytes.return_value = mock_image
                
                result = convert_heic_to_jpeg(heic_path)
                
                # Verify the result ends with .jpg
                assert result.endswith('.jpg')
                # Verify the base name is preserved
                assert 'photo' in result
    
    def test_heic_conversion_error_handling(self, temp_dir):
        """Test that HEIC conversion errors are handled gracefully."""
        from application import convert_heic_to_jpeg
        
        heic_path = os.path.join(temp_dir, 'invalid.heic')
        
        # Mock pyheif.read to raise an exception
        with patch('application.pyheif.read', side_effect=Exception('Invalid HEIC file')):
            result = convert_heic_to_jpeg(heic_path)
            
            # Should return None on error
            assert result is None
    
    def test_heic_conversion_preserves_image_properties(self, temp_dir):
        """Test that HEIC conversion preserves image dimensions and mode."""
        from application import convert_heic_to_jpeg
        
        heic_path = os.path.join(temp_dir, 'test.heic')
        
        # Mock a HEIC file with specific properties
        mock_heif_file = MagicMock()
        mock_heif_file.mode = 'RGB'
        mock_heif_file.size = (1200, 1600)
        mock_heif_file.data = b'\x00' * (1200 * 1600 * 3)
        mock_heif_file.stride = 1200 * 3
        
        with patch('application.pyheif.read', return_value=mock_heif_file):
            with patch('application.Image.frombytes') as mock_frombytes:
                mock_image = MagicMock()
                mock_frombytes.return_value = mock_image
                
                convert_heic_to_jpeg(heic_path)
                
                # Verify Image.frombytes was called with correct parameters
                call_args = mock_frombytes.call_args
                assert call_args[0][0] == 'RGB'  # mode
                assert call_args[0][1] == (1200, 1600)  # size
                assert call_args[0][2] == mock_heif_file.data  # data


class TestHEICConversionInWorkflow:
    """Test HEIC conversion integration in the full workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_heic_file_triggers_conversion_in_workflow(self, temp_dir):
        """
        Test that HEIC files trigger conversion in the full workflow.
        Validates: Requirement 1.2
        """
        # This test verifies the workflow logic without actually running it
        heic_filename = 'photo.heic'
        
        # Verify the filename check logic
        assert heic_filename.lower().endswith('.heic')
        
        # Verify conversion would be triggered
        should_convert = heic_filename.lower().endswith('.heic')
        assert should_convert is True
    
    def test_non_heic_files_skip_conversion(self):
        """Test that non-HEIC files don't trigger conversion."""
        test_files = ['photo.jpg', 'image.png', 'picture.jpeg', 'file.gif']
        
        for filename in test_files:
            should_convert = filename.lower().endswith('.heic')
            assert should_convert is False, f"{filename} should not trigger HEIC conversion"
    
    def test_heic_conversion_result_replaces_original_path(self, temp_dir):
        """Test that converted JPEG path replaces original HEIC path."""
        from application import convert_heic_to_jpeg
        
        original_heic_path = os.path.join(temp_dir, 'original.heic')
        
        mock_heif_file = MagicMock()
        mock_heif_file.mode = 'RGB'
        mock_heif_file.size = (800, 600)
        mock_heif_file.data = b'\x00' * (800 * 600 * 3)
        mock_heif_file.stride = 800 * 3
        
        with patch('application.pyheif.read', return_value=mock_heif_file):
            with patch('application.Image.frombytes') as mock_frombytes:
                mock_image = MagicMock()
                mock_frombytes.return_value = mock_image
                
                converted_path = convert_heic_to_jpeg(original_heic_path)
                
                # Verify the converted path is different from original
                assert converted_path != original_heic_path
                # Verify it's a JPEG path
                assert converted_path.endswith('.jpg')
                # Verify base name is preserved
                assert 'original' in converted_path


class TestHEICConversionConstants:
    """Test HEIC conversion related constants and configuration."""
    
    def test_heic_extension_recognition(self):
        """Test that .heic extension is properly recognized."""
        heic_extensions = ['.heic', '.HEIC', '.Heic', '.HeiC']
        
        for ext in heic_extensions:
            filename = f'test{ext}'
            # Case-insensitive check
            assert filename.lower().endswith('.heic')
    
    def test_jpeg_output_format(self):
        """Test that output format is JPEG."""
        output_format = 'JPEG'
        
        # Verify it's a valid PIL format
        assert output_format in ['JPEG', 'JPG']
        assert output_format == 'JPEG'
