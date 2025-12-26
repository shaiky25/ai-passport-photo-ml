#!/usr/bin/env python3
"""
Test script to verify rembg works with real passport photos from training data
"""

import os
from PIL import Image
import io

def test_rembg_with_training_data():
    """Test rembg with actual passport photos from training data"""
    
    # Test import first
    try:
        from rembg import remove, new_session
        print("✅ rembg imported successfully")
    except ImportError as e:
        print(f"❌ rembg import failed: {e}")
        return False
    
    # Find training data
    training_dir = "backend/training_data"
    if not os.path.exists(training_dir):
        training_dir = "training_data"  # If running from backend directory
    
    if not os.path.exists(training_dir):
        print(f"❌ Training data directory not found")
        return False
    
    # Get first training image
    test_image_path = os.path.join(training_dir, "1.png")
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return False
    
    print(f"📸 Testing with training image: {test_image_path}")
    
    try:
        # Load the training image
        img = Image.open(test_image_path)
        print(f"✅ Loaded image: {img.size}, mode: {img.mode}")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
            print(f"✅ Converted to RGB")
        
        # Create rembg session with u2netp model (lightweight)
        session = new_session('u2netp')
        print("✅ u2netp session created successfully")
        
        # Convert PIL to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        input_data = img_buffer.getvalue()
        print(f"✅ Image converted to bytes: {len(input_data)} bytes")
        
        # Remove background
        print("🔄 Removing background...")
        output_data = remove(input_data, session=session)
        print(f"✅ Background removal completed: {len(output_data)} bytes")
        
        # Convert back to PIL
        result_img = Image.open(io.BytesIO(output_data))
        print(f"✅ Result image: {result_img.size}, mode: {result_img.mode}")
        
        # Save result for inspection
        if result_img.mode == 'RGBA':
            # Convert RGBA to RGB with white background (passport standard)
            white_bg = Image.new('RGB', result_img.size, (255, 255, 255))
            white_bg.paste(result_img, mask=result_img.split()[-1])
            final_img = white_bg
            print("✅ Converted RGBA to RGB with white background")
        else:
            final_img = result_img
        
        # Save test result
        output_path = "test_bg_removal_result.jpg"
        final_img.save(output_path, format='JPEG', quality=95)
        print(f"✅ Saved result to: {output_path}")
        
        print("🎉 Background removal test successful with training data!")
        return True
        
    except Exception as e:
        print(f"❌ Background removal failed: {e}")
        return False

def test_passport_compliance():
    """Test if the result meets passport photo standards"""
    
    # Check if result file exists
    result_path = "test_bg_removal_result.jpg"
    if not os.path.exists(result_path):
        print("❌ No result file to test compliance")
        return False
    
    try:
        img = Image.open(result_path)
        width, height = img.size
        
        print(f"📏 Result dimensions: {width}x{height}")
        
        # Check if it's square (passport requirement)
        if width == height:
            print("✅ Square format (passport compliant)")
        else:
            print(f"⚠️  Not square: {width}x{height}")
        
        # Check resolution
        if width >= 600 and height >= 600:
            print("✅ High resolution (≥600x600)")
        else:
            print(f"⚠️  Low resolution: {width}x{height}")
        
        # Check if background appears white/plain
        # Sample corners to check background
        corners = [
            img.getpixel((10, 10)),
            img.getpixel((width-10, 10)),
            img.getpixel((10, height-10)),
            img.getpixel((width-10, height-10))
        ]
        
        print(f"🎨 Corner colors: {corners}")
        
        # Check if corners are light (indicating plain background)
        light_corners = 0
        for corner in corners:
            if isinstance(corner, tuple):
                avg_color = sum(corner) / len(corner)
            else:
                avg_color = corner
            
            if avg_color > 200:  # Light background
                light_corners += 1
        
        if light_corners >= 3:
            print("✅ Plain/light background detected")
        else:
            print("⚠️  Background may not be plain enough")
        
        return True
        
    except Exception as e:
        print(f"❌ Compliance test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing rembg with passport photo training data")
    print("=" * 50)
    
    success = test_rembg_with_training_data()
    
    if success:
        print("\n📋 Testing passport compliance...")
        test_passport_compliance()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Tests failed - rembg may not be working properly")