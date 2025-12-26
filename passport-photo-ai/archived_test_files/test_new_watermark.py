#!/usr/bin/env python3
"""
Test the new full-image watermark design before deploying
"""
from PIL import Image, ImageDraw, ImageFont
import os

def add_full_image_watermark(img):
    """Add a professional full-image watermark that covers the entire photo"""
    try:
        # Create a copy of the image
        watermarked = img.copy().convert('RGBA')
        
        # Create a transparent overlay
        overlay = Image.new('RGBA', watermarked.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Watermark text
        watermark_text = "PassportPhotoAI.com"
        
        # Try to use a larger font, fallback to default if not available
        try:
            # Try different font sizes
            font_size = max(watermarked.width // 15, 24)  # Responsive font size
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Get text dimensions
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate positions for diagonal watermarks across the image
        img_width, img_height = watermarked.size
        
        # Create multiple watermarks in a diagonal pattern
        positions = []
        
        # Calculate spacing
        x_spacing = text_width + 50
        y_spacing = text_height + 30
        
        # Start positions to cover the entire image
        start_x = -text_width // 2
        start_y = -text_height // 2
        
        # Generate positions in a diagonal grid pattern
        y = start_y
        while y < img_height + text_height:
            x = start_x
            while x < img_width + text_width:
                positions.append((x, y))
                x += x_spacing
            y += y_spacing
            # Offset every other row for better coverage
            start_x = -text_width // 2 if start_x == -text_width // 4 else -text_width // 4
        
        # Draw watermarks at all positions
        for x, y in positions:
            # Semi-transparent text
            draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 80))  # White with transparency
            # Add a subtle shadow for better visibility
            draw.text((x+1, y+1), watermark_text, font=font, fill=(0, 0, 0, 40))    # Black shadow
        
        # Composite the overlay onto the original image
        watermarked = Image.alpha_composite(watermarked, overlay)
        
        # Convert back to RGB
        final_image = Image.new('RGB', watermarked.size, (255, 255, 255))
        final_image.paste(watermarked, mask=watermarked.split()[-1])
        
        return final_image
        
    except Exception as e:
        print(f"Watermark error: {e}")
        return img

def add_old_watermark(img):
    """Current small watermark for comparison"""
    try:
        watermarked = img.copy()
        draw = ImageDraw.Draw(watermarked)
        
        watermark_text = "PassportPhotoAI.com"
        
        # Position watermark at bottom right
        x = watermarked.width - 180
        y = watermarked.height - 25
        
        # Semi-transparent background
        draw.rectangle([x-5, y-3, x+175, y+20], fill=(255, 255, 255, 200))
        draw.text((x, y), watermark_text, fill=(100, 100, 100))
        
        return watermarked
    except Exception as e:
        print(f"Watermark error: {e}")
        return img

def test_watermark_designs():
    """Test both watermark designs"""
    print("🎨 TESTING NEW WATERMARK DESIGN")
    print("=" * 50)
    
    # Find a test image
    test_images = [
        'test_high_res_face.jpg',
        'final_test_no_watermark.jpg',
        'test_app_output.jpg',
        'deployed_no_bg_removal.jpg'
    ]
    
    test_image = None
    for img_path in test_images:
        if os.path.exists(img_path):
            test_image = img_path
            break
    
    if not test_image:
        print("❌ No test image found. Please make sure you have one of these files:")
        for img in test_images:
            print(f"   - {img}")
        return False
    
    print(f"📸 Using test image: {test_image}")
    
    try:
        # Load the test image
        original_img = Image.open(test_image)
        print(f"📏 Original size: {original_img.size}")
        
        # Create old watermark version
        print("\n🔄 Creating old watermark (current)...")
        old_watermark_img = add_old_watermark(original_img)
        old_watermark_img.save('watermark_old_design.jpg', quality=95)
        print("💾 Saved: watermark_old_design.jpg")
        
        # Create new watermark version
        print("\n🔄 Creating new watermark (full coverage)...")
        new_watermark_img = add_full_image_watermark(original_img)
        new_watermark_img.save('watermark_new_design.jpg', quality=95)
        print("💾 Saved: watermark_new_design.jpg")
        
        # Create no watermark version for comparison
        print("\n🔄 Creating no watermark version...")
        original_img.save('watermark_none.jpg', quality=95)
        print("💾 Saved: watermark_none.jpg")
        
        print(f"\n✅ All watermark samples created successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating watermark samples: {e}")
        return False

def print_comparison_guide():
    """Print guide for comparing watermarks"""
    print(f"\n" + "=" * 50)
    print("📊 WATERMARK COMPARISON GUIDE")
    print("=" * 50)
    
    print(f"\n📸 Generated Files:")
    print(f"  1. watermark_none.jpg        - No watermark (clean)")
    print(f"  2. watermark_old_design.jpg  - Current small watermark")
    print(f"  3. watermark_new_design.jpg  - New full-coverage watermark")
    
    print(f"\n🔍 What to Look For:")
    print(f"  ✅ NEW DESIGN should have:")
    print(f"     • Watermarks covering the entire image")
    print(f"     • Semi-transparent text that doesn't obscure the face")
    print(f"     • Professional diagonal pattern")
    print(f"     • Impossible to crop out or remove easily")
    
    print(f"  ❌ OLD DESIGN problems:")
    print(f"     • Small watermark in corner only")
    print(f"     • Easy to crop out")
    print(f"     • Doesn't protect the full image")
    
    print(f"\n🎯 Benefits of New Design:")
    print(f"  ✅ Covers entire image - can't be cropped out")
    print(f"  ✅ Semi-transparent - doesn't ruin the photo")
    print(f"  ✅ Professional appearance")
    print(f"  ✅ Clear incentive for email verification")
    print(f"  ✅ Protects your work and encourages payment")
    
    print(f"\n💡 Next Steps:")
    print(f"  1. Open the generated images and compare them")
    print(f"  2. If you like the new design, I'll deploy it")
    print(f"  3. Test the email verification to remove watermarks")

def main():
    """Main test function"""
    
    success = test_watermark_designs()
    print_comparison_guide()
    
    print(f"\n" + "=" * 50)
    print("📊 WATERMARK TEST SUMMARY")
    print("=" * 50)
    
    if success:
        print("🎉 WATERMARK SAMPLES CREATED!")
        print("📸 Check the generated images:")
        print("   - watermark_old_design.jpg (current)")
        print("   - watermark_new_design.jpg (proposed)")
        print("   - watermark_none.jpg (clean version)")
        
        print(f"\n🔍 Please review the images and let me know:")
        print(f"   • Do you like the new full-coverage watermark?")
        print(f"   • Is the transparency level good?")
        print(f"   • Should I adjust anything before deploying?")
        
    else:
        print("❌ WATERMARK TEST FAILED")
        print("💡 Make sure you have a test image available")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)