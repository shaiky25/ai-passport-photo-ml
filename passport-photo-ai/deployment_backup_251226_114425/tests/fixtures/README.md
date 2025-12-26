# Test Fixtures

This directory contains test images for testing the passport photo processor.

## Image Inventory

### Resolution Tests
- `small_resolution.jpg` - 400x400px (below minimum, should be rejected)
- `min_valid_resolution.jpg` - 600x600px (minimum valid resolution)
- `large_resolution.jpg` - 2000x2000px (large image)
- `very_large_resolution.jpg` - 4000x3000px (very large image for performance testing)

### Orientation Tests
- `portrait_orientation.jpg` - 800x1200px (portrait)
- `landscape_orientation.jpg` - 1200x800px (landscape)
- `square_1000x1000.jpg` - 1000x1000px (square)

### Face Detection Tests
- `single_face_centered.jpg` - 1000x1000px with centered face
- `single_face_off_center.jpg` - 1000x1000px with off-center face
- `multiple_faces.jpg` - 1200x1000px with two faces
- `no_face.jpg` - 1000x1000px with no face

### Format Tests
- `valid_png.png` - 800x800px PNG format

## Regenerating Fixtures

To regenerate all test fixtures:

```bash
python create_test_images.py
```

Note: These are synthetic images for testing purposes. For more realistic testing,
consider adding actual photos to this directory.
