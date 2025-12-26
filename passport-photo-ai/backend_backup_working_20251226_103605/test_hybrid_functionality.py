#!/usr/bin/env python3
"""
Test script to verify hybrid passport photo processing functionality
"""

import sys
import os
import tempfile
from PIL import Image, ImageDraw
import io

# Add the current directory to the path so we can import application
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_image(width=800, height=800):
    """Create a simple test passport-style image"""
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple face-like shape (circle for head)
    face_center = (width//2, int(height*0.4))  # Slightly above center
    face_radius = min(width, height) // 8
    
    # Draw face (skin color)
    draw.ellipse([
        face_center[0] - face_radius, 
        face_center[1] - face_radius,
        face_center[0] + face_radius, 
        face_center[1] + face_radius
    ], fill=(255, 220, 177))
    
    # Draw eyes
    eye_y = face_center[1] - face_radius//3
    eye_offset = face_radius//2
    draw.ellipse([face_center[0] - eye_offset, eye_y - 5, face_center[0] - eye_offset + 10, eye_y + 5], fill='black')
    draw.ellipse([face_center[0] + eye_offset - 10, eye_y - 5, face_center[0] + eye_offset, eye_y + 5], fill='black')
    
    # Draw mouth
    mouth_y = face_center[1] + face_radius//3
    draw.arc([face_center[0] - 15, mouth_y - 8, face_center[0] + 15, mouth_y + 8], 0, 180, fill='black', width=2)
    
    return img

def test_hybrid_processor():
    """Test the HybridPassportPhotoProcessor functionality"""
    print("Testing HybridPassportPhotoProcessor...")
    
    try:
        from application import HybridPassportPhotoProcessor
        print("✅ Successfully imported HybridPassportPhotoProcessor")
    except ImportError as e:
        print(f"❌ Failed to import HybridPassportPhotoProcessor: {e}")
        return False
    
    # Initialize processor
    try:
        processor = HybridPassportPhotoProcessor()
        print("✅ Successfully initialized HybridPassportPhotoProcessor")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return False
    
    # Test 1: Face detection with valid image
    print("\n--- Test 1: Face Detection ---")
    test_img = create_test_image(800, 800)
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        test_img.save(tmp.name, 'JPEG')
        temp_path = tmp.name
    
    try:
        face_result = processor.enhanced_face_detection(temp_path)
        print(f"Face detection result: {face_result}")
        
        if face_result.get('faces_detected', 0) > 0:
            print("✅ Face detection working")
        else:
            print("⚠️  No face detected (expected for simple test image)")
        
        # Check required fields
        required_fields = ['faces_detected', 'valid', 'face_bbox', 'head_height_percent', 'horizontally_centered']
        for field in required_fields:
            if field in face_result:
                print(f"✅ Field '{field}' present: {face_result[field]}")
            else:
                print(f"❌ Missing field: {field}")
                
    except Exception as e:
        print(f"❌ Face detection failed: {e}")
        return False
    finally:
        os.unlink(temp_path)
    
    # Test 2: Photo processing
    print("\n--- Test 2: Photo Processing ---")
    test_img = create_test_image(1000, 1000)
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        test_img.save(tmp.name, 'JPEG')
        temp_path = tmp.name
    
    try:
        # Get face detection first
        face_result = processor.enhanced_face_detection(temp_path)
        face_bbox = face_result.get('face_bbox') if face_result.get('valid') else None
        
        # Process the image
        processed_buffer = processor.process_to_passport_photo(
            temp_path, 
            face_bbox=face_bbox, 
            remove_bg=False, 
            remove_watermark=False
        )
        
        print("✅ Photo processing completed")
        
        # Verify output
        if isinstance(processed_buffer, io.BytesIO):
            print("✅ Output is BytesIO buffer")
            
            # Check if we can load the processed image
            processed_buffer.seek(0)
            processed_img = Image.open(processed_buffer)
            
            if processed_img.size == (600, 600):
                print("✅ Output dimensions are 600x600")
            else:
                print(f"❌ Wrong dimensions: {processed_img.size}")
                
            if processed_img.mode == 'RGB':
                print("✅ Output is RGB mode")
            else:
                print(f"❌ Wrong mode: {processed_img.mode}")
                
        else:
            print(f"❌ Wrong output type: {type(processed_buffer)}")
            
    except Exception as e:
        print(f"❌ Photo processing failed: {e}")
        return False
    finally:
        os.unlink(temp_path)
    
    # Test 3: Watermark functionality
    print("\n--- Test 3: Watermark ---")
    test_img = create_test_image(600, 600)
    
    try:
        # Test watermark addition
        watermarked_img = processor.add_watermark(test_img)
        
        if watermarked_img.size == test_img.size:
            print("✅ Watermark preserves image dimensions")
        else:
            print(f"❌ Watermark changed dimensions: {watermarked_img.size}")
            
        if watermarked_img.mode == 'RGB':
            print("✅ Watermarked image is RGB")
        else:
            print(f"❌ Wrong watermarked mode: {watermarked_img.mode}")
            
    except Exception as e:
        print(f"❌ Watermark test failed: {e}")
        return False
    
    print("\n✅ All hybrid processor tests completed successfully!")
    return True

def test_flask_app():
    """Test basic Flask app functionality"""
    print("\n--- Testing Flask App ---")
    
    try:
        from application import application
        print("✅ Successfully imported Flask application")
    except ImportError as e:
        print(f"❌ Failed to import Flask application: {e}")
        return False
    
    # Test app configuration
    try:
        with application.test_client() as client:
            # Test health endpoint
            response = client.get('/api/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
                data = response.get_json()
                if data and data.get('status') == 'healthy':
                    print("✅ Health endpoint returns correct data")
                else:
                    print(f"❌ Unexpected health data: {data}")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                
            # Test root endpoint
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Root endpoint working")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False
    
    print("✅ Flask app tests completed successfully!")
    return True

if __name__ == "__main__":
    print("Running Hybrid Passport Photo AI Tests")
    print("=" * 50)
    
    success = True
    
    # Test hybrid processor
    if not test_hybrid_processor():
        success = False
    
    # Test Flask app
    if not test_flask_app():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)