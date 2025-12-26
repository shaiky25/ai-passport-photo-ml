#!/usr/bin/env python3
"""
Create a test image with proper resolution for API testing
"""
from PIL import Image, ImageDraw
import os

def create_high_res_test_image():
    """Create a high resolution test image with a face-like pattern"""
    # Create a 800x800 image (meets 600x600 requirement)
    img = Image.new('RGB', (800, 800), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw a realistic face pattern
    # Head (large oval)
    head_x, head_y = 250, 150
    head_w, head_h = 300, 400
    draw.ellipse([head_x, head_y, head_x + head_w, head_y + head_h], 
                 fill='peachpuff', outline='black', width=3)
    
    # Eyes
    eye_y = head_y + 120
    left_eye_x = head_x + 80
    right_eye_x = head_x + 200
    draw.ellipse([left_eye_x, eye_y, left_eye_x + 30, eye_y + 20], fill='black')
    draw.ellipse([right_eye_x, eye_y, right_eye_x + 30, eye_y + 20], fill='black')
    
    # Nose
    nose_x = head_x + 140
    nose_y = eye_y + 60
    draw.line([nose_x, nose_y, nose_x, nose_y + 40], fill='black', width=3)
    
    # Mouth
    mouth_x = head_x + 100
    mouth_y = nose_y + 60
    draw.arc([mouth_x, mouth_y, mouth_x + 100, mouth_y + 40], 0, 180, fill='black', width=3)
    
    # Hair
    draw.ellipse([head_x - 20, head_y - 50, head_x + head_w + 20, head_y + 100], 
                 fill='brown', outline='black', width=2)
    
    # Shoulders
    draw.rectangle([head_x - 100, head_y + head_h - 50, head_x + head_w + 100, 800], 
                   fill='blue', outline='black', width=2)
    
    # Save the image
    output_path = 'test_high_res_face.jpg'
    img.save(output_path, 'JPEG', quality=95)
    
    print(f"Created high resolution test image: {output_path}")
    print(f"Resolution: {img.size}")
    
    return output_path

def upscale_existing_image():
    """Upscale an existing training image to meet resolution requirements"""
    source_path = 'backend/training_data/1.png'
    if not os.path.exists(source_path):
        print("Source image not found")
        return None
    
    # Open and upscale the image
    img = Image.open(source_path)
    original_size = img.size
    
    # Calculate scale factor to reach at least 600x600
    scale_factor = max(600 / original_size[0], 600 / original_size[1])
    new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
    
    # Upscale using high-quality resampling
    upscaled_img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert to RGB if needed (for JPEG compatibility)
    if upscaled_img.mode in ('RGBA', 'LA', 'P'):
        upscaled_img = upscaled_img.convert('RGB')
    
    # Save the upscaled image
    output_path = 'test_upscaled_face.jpg'
    upscaled_img.save(output_path, 'JPEG', quality=95)
    
    print(f"Upscaled existing image: {source_path}")
    print(f"Original size: {original_size}")
    print(f"New size: {new_size}")
    print(f"Saved as: {output_path}")
    
    return output_path

if __name__ == "__main__":
    print("🖼️  CREATING HIGH RESOLUTION TEST IMAGES")
    print("=" * 50)
    
    # Create synthetic high-res image
    synthetic_path = create_high_res_test_image()
    
    # Upscale existing training image
    upscaled_path = upscale_existing_image()
    
    print(f"\n✅ Test images created:")
    if synthetic_path:
        print(f"  - Synthetic: {synthetic_path}")
    if upscaled_path:
        print(f"  - Upscaled: {upscaled_path}")
    
    print(f"\nUse these images for API testing to meet 600x600 resolution requirement")