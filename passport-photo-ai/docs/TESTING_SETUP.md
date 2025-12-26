# Testing Infrastructure Setup

This document describes the testing infrastructure for the Passport Photo Processor application.

## Overview

The testing infrastructure supports both **unit testing** and **property-based testing** for both backend (Python/Flask) and frontend (React) components.

## Backend Testing (Python)

### Dependencies
- **pytest** - Test framework
- **hypothesis** - Property-based testing library
- **pytest-mock** - Mocking utilities
- **pytest-cov** - Coverage reporting

### Configuration Files
- `backend/pytest.ini` - Pytest configuration with coverage settings
- `backend/.coveragerc` - Coverage reporting configuration
- `backend/tests/conftest.py` - Shared fixtures and Hypothesis settings

### Test Structure
```
backend/tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_setup.py            # Infrastructure verification tests
├── fixtures/                # Test images and data
│   ├── README.md           # Fixtures documentation
│   ├── create_test_images.py  # Script to generate test images
│   └── *.jpg, *.png        # 12 test image files
└── README.md               # Backend testing documentation
```

### Running Backend Tests
```bash
cd passport-photo-ai/backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_setup.py -v
```

### Test Fixtures
The `tests/fixtures/` directory contains 12 test images:
- **Resolution tests**: small (400x400), minimum valid (600x600), large (2000x2000), very large (4000x3000)
- **Orientation tests**: portrait (800x1200), landscape (1200x800), square (1000x1000)
- **Face detection tests**: single centered face, single off-center face, multiple faces, no face
- **Format tests**: PNG format

## Frontend Testing (React)

### Dependencies
- **Jest** - Test framework (included with Create React App)
- **React Testing Library** - Component testing utilities
- **@testing-library/jest-dom** - Custom Jest matchers
- **@testing-library/user-event** - User interaction simulation
- **fast-check** - Property-based testing library

### Configuration Files
- `frontend/jest.config.js` - Jest configuration with coverage thresholds
- `frontend/src/setupTests.js` - Jest setup file

### Test Structure
```
frontend/src/__tests__/
├── setup.test.js           # Infrastructure verification tests
└── README.md              # Frontend testing documentation
```

### Running Frontend Tests
```bash
cd passport-photo-ai/frontend

# Run all tests (single run)
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

## Property-Based Testing

Both backend and frontend use property-based testing to verify universal properties across many inputs.

### Configuration
- **Minimum iterations**: 100 runs per property test
- **Backend**: Hypothesis with custom profile in `conftest.py`
- **Frontend**: fast-check with `numRuns: 100` configuration

### Tagging Convention
Each property-based test must be tagged with:
```python
# Feature: passport-photo-processor, Property {number}: {property_text}
# Validates: Requirements {requirement_id}
```

Example:
```python
# Feature: passport-photo-processor, Property 1: Format acceptance
# Validates: Requirements 1.1
def test_property_format_acceptance():
    # Test implementation
```

## Coverage Targets

### Backend
- Target: 80%+ coverage
- Reports generated in `backend/htmlcov/`

### Frontend
- Branches: 70%
- Functions: 70%
- Lines: 70%
- Statements: 70%
- Reports generated in `frontend/coverage/`

## Verification

The testing infrastructure has been verified with setup tests:

### Backend Verification ✓
```bash
$ pytest tests/test_setup.py -v
================================= test session starts =================================
collected 4 items

tests/test_setup.py::test_fixtures_directory_exists PASSED                      [ 25%]
tests/test_setup.py::test_fixture_images_exist PASSED                           [ 50%]
tests/test_setup.py::test_pytest_hypothesis_available PASSED                    [ 75%]
tests/test_setup.py::test_pytest_mock_available PASSED                          [100%]

================================== 4 passed in 0.14s ==================================
```

### Frontend Verification ✓
```bash
$ npm test -- --testPathPattern=setup.test.js
PASS src/__tests__/setup.test.js
  Testing Infrastructure Setup
    ✓ React Testing Library is available
    ✓ fast-check is available for property-based testing
    ✓ jest-dom matchers are available

Test Suites: 1 passed, 1 total
Tests:       3 passed, 3 total
```

## Next Steps

The testing infrastructure is now ready for implementing:
1. Unit tests for specific functionality
2. Property-based tests for universal correctness properties
3. Integration tests for end-to-end workflows

Refer to the design document (`.kiro/specs/passport-photo-processor/design.md`) for the complete list of correctness properties to implement.
