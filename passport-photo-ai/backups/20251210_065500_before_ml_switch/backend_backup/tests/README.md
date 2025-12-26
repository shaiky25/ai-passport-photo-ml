# Backend Tests

This directory contains all backend tests for the Passport Photo Processor.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── test_setup.py            # Infrastructure verification tests
├── fixtures/                # Test images and data
│   ├── README.md           # Fixtures documentation
│   ├── create_test_images.py  # Script to generate test images
│   └── *.jpg, *.png        # Test image files
└── (additional test files will be added here)
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_setup.py
```

### Run tests matching a pattern
```bash
pytest -k "test_face_detection"
```

### Run with verbose output
```bash
pytest -v
```

## Property-Based Testing

This project uses **Hypothesis** for property-based testing. Property tests are configured to run a minimum of 100 iterations per test.

Each property-based test is tagged with a comment referencing the correctness property from the design document:
```python
# Feature: passport-photo-processor, Property 1: Format acceptance
# Validates: Requirements 1.1
```

## Test Fixtures

Test fixtures are located in `tests/fixtures/` and include:
- Images with various resolutions (small, valid, large)
- Images with different orientations (portrait, landscape, square)
- Images with different face counts (0, 1, multiple)
- Images in different formats (JPEG, PNG)

See `fixtures/README.md` for complete fixture documentation.

## Coverage

Coverage reports are generated in the `htmlcov/` directory. Open `htmlcov/index.html` in a browser to view detailed coverage information.

Target coverage: 80%+

## Dependencies

- pytest - Test framework
- hypothesis - Property-based testing
- pytest-mock - Mocking utilities
- pytest-cov - Coverage reporting
