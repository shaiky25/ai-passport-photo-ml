"""
Test to verify the testing infrastructure is set up correctly.
"""
import pytest
from pathlib import Path


def test_fixtures_directory_exists(fixtures_dir):
    """Verify that the fixtures directory exists and contains test images."""
    assert Path(fixtures_dir).exists()
    assert Path(fixtures_dir).is_dir()


def test_fixture_images_exist(fixtures_dir):
    """Verify that all expected test fixture images exist."""
    expected_files = [
        'small_resolution.jpg',
        'min_valid_resolution.jpg',
        'large_resolution.jpg',
        'very_large_resolution.jpg',
        'portrait_orientation.jpg',
        'landscape_orientation.jpg',
        'single_face_centered.jpg',
        'single_face_off_center.jpg',
        'multiple_faces.jpg',
        'no_face.jpg',
        'valid_png.png',
        'square_1000x1000.jpg',
    ]
    
    for filename in expected_files:
        filepath = Path(fixtures_dir) / filename
        assert filepath.exists(), f"Expected fixture file not found: {filename}"


def test_pytest_hypothesis_available():
    """Verify that Hypothesis is available for property-based testing."""
    try:
        from hypothesis import given, strategies as st
        assert True
    except ImportError:
        pytest.fail("Hypothesis not available for property-based testing")


def test_pytest_mock_available():
    """Verify that pytest-mock is available."""
    try:
        import pytest_mock
        assert True
    except ImportError:
        pytest.fail("pytest-mock not available")
