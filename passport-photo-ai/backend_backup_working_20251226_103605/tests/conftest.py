"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import application module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Get the fixtures directory path
FIXTURES_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture
def fixtures_dir():
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def small_resolution_image(fixtures_dir):
    """Return path to small resolution test image (400x400)."""
    return str(fixtures_dir / 'small_resolution.jpg')


@pytest.fixture
def min_valid_resolution_image(fixtures_dir):
    """Return path to minimum valid resolution test image (600x600)."""
    return str(fixtures_dir / 'min_valid_resolution.jpg')


@pytest.fixture
def large_resolution_image(fixtures_dir):
    """Return path to large resolution test image (2000x2000)."""
    return str(fixtures_dir / 'large_resolution.jpg')


@pytest.fixture
def very_large_resolution_image(fixtures_dir):
    """Return path to very large resolution test image (4000x3000)."""
    return str(fixtures_dir / 'very_large_resolution.jpg')


@pytest.fixture
def portrait_orientation_image(fixtures_dir):
    """Return path to portrait orientation test image (800x1200)."""
    return str(fixtures_dir / 'portrait_orientation.jpg')


@pytest.fixture
def landscape_orientation_image(fixtures_dir):
    """Return path to landscape orientation test image (1200x800)."""
    return str(fixtures_dir / 'landscape_orientation.jpg')


@pytest.fixture
def single_face_centered_image(fixtures_dir):
    """Return path to single centered face test image."""
    return str(fixtures_dir / 'single_face_centered.jpg')


@pytest.fixture
def single_face_off_center_image(fixtures_dir):
    """Return path to single off-center face test image."""
    return str(fixtures_dir / 'single_face_off_center.jpg')


@pytest.fixture
def multiple_faces_image(fixtures_dir):
    """Return path to multiple faces test image."""
    return str(fixtures_dir / 'multiple_faces.jpg')


@pytest.fixture
def no_face_image(fixtures_dir):
    """Return path to no face test image."""
    return str(fixtures_dir / 'no_face.jpg')


@pytest.fixture
def valid_png_image(fixtures_dir):
    """Return path to valid PNG format test image."""
    return str(fixtures_dir / 'valid_png.png')


@pytest.fixture
def square_image(fixtures_dir):
    """Return path to square test image (1000x1000)."""
    return str(fixtures_dir / 'square_1000x1000.jpg')


# Hypothesis settings for property-based tests
from hypothesis import settings, Verbosity

# Register a profile for property-based tests with minimum 100 iterations
settings.register_profile("pbt_default", max_examples=100, verbosity=Verbosity.verbose)
settings.load_profile("pbt_default")
