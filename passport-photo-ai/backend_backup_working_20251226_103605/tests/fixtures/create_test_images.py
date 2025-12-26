"""
Script to generate test fixture images for testing.
Creates images with various sizes and simulated face scenarios.
"""
from PIL import Image, ImageDraw
import os

def create_test_images():
    """Create test fixture images with various properties."""
    fixtures_dir = os.path.dirname(__file__)
    
    # 1. Small resolution image (below 600x600) - should be rejected
    small_img = Image.new('RGB', (400, 400), color='white')
    small_img.save(os.path.join(fixtures_dir, 'small_resolution.jpg'))
    
    # 2. Minimum valid resolution (600x600)
    min_valid = Image.new('RGB', (600, 600), color='white')
    min_valid.save(os.path.join(fixtures_dir, 'min_valid_resolution.jpg'))
    
    # 3. Large resolution image (2000x2000)
    large_img = Image.new('RGB', (2000, 2000), color='white')
    large_img.save(os.path.join(fixtures_dir, 'large_resolution.jpg'))
    
    # 4. Very large image (4000x3000)
    very_large = Image.new('RGB', (4000, 3000), color='white')
    very_large.save(os.path.join(fixtures_dir, 'very_large_resolution.jpg'))
    
    # 5. Portrait orientation (800x1200)
    portrait = Image.new('RGB', (800, 1200), color='white')
    portrait.save(os.path.join(fixtures_dir, 'portrait_orientation.jpg'))
    
    # 6. Landscape orientation (1200x800)
    landscape = Image.new('RGB', (1200, 800), color='white')
    landscape.save(os.path.join(fixtures_dir, 'landscape_orientation.jpg'))
    
    # 7. Image with simulated single face (centered)
    single_face = Image.new('RGB', (1000, 1000), color='white')
    draw = ImageDraw.Draw(single_face)
    # Draw a simple face representation (circle for head)
    face_center = (500, 400)
    face_radius = 150
    draw.ellipse([face_center[0]-face_radius, face_center[1]-face_radius,
                  face_center[0]+face_radius, face_center[1]+face_radius],
                 fill='beige', outline='black', width=2)
    # Eyes
    draw.ellipse([450, 370, 470, 390], fill='black')
    draw.ellipse([530, 370, 550, 390], fill='black')
    # Mouth
    draw.arc([460, 420, 540, 460], 0, 180, fill='black', width=2)
    single_face.save(os.path.join(fixtures_dir, 'single_face_centered.jpg'))
    
    # 8. Image with simulated single face (off-center)
    off_center_face = Image.new('RGB', (1000, 1000), color='white')
    draw = ImageDraw.Draw(off_center_face)
    face_center = (300, 400)
    draw.ellipse([face_center[0]-face_radius, face_center[1]-face_radius,
                  face_center[0]+face_radius, face_center[1]+face_radius],
                 fill='beige', outline='black', width=2)
    draw.ellipse([250, 370, 270, 390], fill='black')
    draw.ellipse([330, 370, 350, 390], fill='black')
    draw.arc([260, 420, 340, 460], 0, 180, fill='black', width=2)
    off_center_face.save(os.path.join(fixtures_dir, 'single_face_off_center.jpg'))
    
    # 9. Image with simulated multiple faces
    multiple_faces = Image.new('RGB', (1200, 1000), color='white')
    draw = ImageDraw.Draw(multiple_faces)
    # First face
    face1_center = (350, 400)
    draw.ellipse([face1_center[0]-100, face1_center[1]-100,
                  face1_center[0]+100, face1_center[1]+100],
                 fill='beige', outline='black', width=2)
    draw.ellipse([320, 380, 335, 395], fill='black')
    draw.ellipse([365, 380, 380, 395], fill='black')
    # Second face
    face2_center = (850, 400)
    draw.ellipse([face2_center[0]-100, face2_center[1]-100,
                  face2_center[0]+100, face2_center[1]+100],
                 fill='beige', outline='black', width=2)
    draw.ellipse([820, 380, 835, 395], fill='black')
    draw.ellipse([865, 380, 880, 395], fill='black')
    multiple_faces.save(os.path.join(fixtures_dir, 'multiple_faces.jpg'))
    
    # 10. Image with no face (plain background)
    no_face = Image.new('RGB', (1000, 1000), color='lightblue')
    draw = ImageDraw.Draw(no_face)
    # Draw some non-face objects
    draw.rectangle([300, 300, 700, 700], fill='gray', outline='black', width=2)
    no_face.save(os.path.join(fixtures_dir, 'no_face.jpg'))
    
    # 11. PNG format image
    png_img = Image.new('RGB', (800, 800), color='white')
    png_img.save(os.path.join(fixtures_dir, 'valid_png.png'))
    
    # 12. Image with different aspect ratio (square)
    square = Image.new('RGB', (1000, 1000), color='white')
    square.save(os.path.join(fixtures_dir, 'square_1000x1000.jpg'))
    
    print("Test fixture images created successfully!")
    print(f"Location: {fixtures_dir}")

if __name__ == '__main__':
    create_test_images()
