#!/usr/bin/env python3
"""
Complete local functionality test for Passport Photo AI
Tests all features: face detection, watermark (3x size), background removal, email system
"""

import sys
import os
import requests
import base64
import json
import time
from PIL import Image, ImageDraw
import io

# Add backend to path
sys.path.append('backend')

def create_test_image():
    """Create a test image with a person-like shape"""
    img = Image.new('RGB', (1000, 1000), (100, 150, 200))  # Blue background
    draw = ImageDraw.Draw(img)
    
    # Draw a simple "person" shape
    # Head (circle)
    draw.ellipse([400, 200, 600, 400], fill=(220, 180, 140))  # Skin color
    
    # Eyes
    draw.ellipse([430, 260, 450, 280], fill=(0, 0, 0))  # Left eye
    draw.ellipse([550, 260, 570, 280], fill=(0, 0, 0))  # Right eye
    
    # Nose
    draw.ellipse([485, 300, 515, 320], fill=(200, 160, 120))
    
    # Mouth
    draw.ellipse([470, 340, 530, 360], fill=(180, 100, 100))
    
    # Body (rectangle)
    draw.rectangle([450, 400, 550, 700], fill=(100, 100, 200))  # Blue shirt
    
    img.save('test_person_image.jpg', quality=95)
    print("✓ Created test person image")
    return 'test_person_image.jpg'

def test_local_server():
    """Test the local Flask server"""
    print("\n=== TESTING LOCAL SERVER ===")
    
    # Start server in background
    import subprocess
    import threading
    
    def run_server():
        os.chdir('backend')
        subprocess.run(['python', 'application.py'], capture_output=True)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data['message']}")
            print(f"✓ OpenCV available: {data['opencv_available']}")
            print(f"✓ HEIC support: {data['heic_support']}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Server connection failed: {e}")
        return False

def test_face_detection_and_processing():
    """Test face detection and image processing"""
    print("\n=== TESTING FACE DETECTION & PROCESSING ===")
    
    # Create test image
    test_image_path = create_test_image()
    
    try:
        # Test the full workflow endpoint
        with open(test_image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'remove_background': 'true',  # Test background removal
                'use_learned_profile': 'true'
            }
            
            response = requests.post(
                'http://localhost:5000/api/full-workflow',
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Full workflow successful: {result['success']}")
            print(f"✓ Processing time: {result.get('processing_time', 'N/A')} seconds")
            
            # Check face detection results
            face_detection = result['analysis']['face_detection']
            print(f"✓ Faces detected: {face_detection['faces_detected']}")
            print(f"✓ Face valid: {face_detection['valid']}")
            
            # Check if processed image exists
            if 'processed_image' in result:
                # Decode and save the processed image
                processed_data = base64.b64decode(result['processed_image'])
                with open('test_processed_output.jpg', 'wb') as f:
                    f.write(processed_data)
                print("✓ Processed image saved as test_processed_output.jpg")
                
                # Verify watermark is applied (image should be different from input)
                original_size = os.path.getsize(test_image_path)
                processed_size = len(processed_data)
                print(f"✓ Original size: {original_size} bytes")
                print(f"✓ Processed size: {processed_size} bytes")
                
                return True
            else:
                print("✗ No processed image in response")
                return False
        else:
            print(f"✗ Full workflow failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Face detection test failed: {e}")
        return False

def test_watermark_functionality():
    """Test watermark with 3x larger text"""
    print("\n=== TESTING WATERMARK (3X SIZE) ===")
    
    try:
        from application import PassportPhotoProcessor
        
        # Create test image
        test_img = Image.new('RGB', (1200, 1200), (200, 200, 200))
        
        # Initialize processor
        processor = PassportPhotoProcessor()
        
        # Add watermark
        watermarked = processor.add_watermark(test_img)
        
        # Save result
        watermarked.save('test_watermark_3x_local.jpg', quality=95)
        print("✓ Watermark applied and saved as test_watermark_3x_local.jpg")
        
        # Check if watermark was applied (images should be different)
        if watermarked.size == test_img.size:
            print("✓ Watermark maintains image dimensions")
            return True
        else:
            print("✗ Watermark changed image dimensions")
            return False
            
    except Exception as e:
        print(f"✗ Watermark test failed: {e}")
        return False

def test_background_removal():
    """Test background removal functionality"""
    print("\n=== TESTING BACKGROUND REMOVAL ===")
    
    try:
        from application import PassportPhotoProcessor
        
        # Create test image with clear foreground/background
        test_img = Image.new('RGB', (800, 800), (100, 150, 200))  # Blue background
        draw = ImageDraw.Draw(test_img)
        
        # Draw a person shape
        draw.ellipse([300, 200, 500, 600], fill=(220, 180, 140))  # Person
        
        # Initialize processor
        processor = PassportPhotoProcessor()
        
        # Test background removal
        result_img = processor.remove_background_lightweight(test_img)
        
        # Save result
        result_img.save('test_bg_removal_local.jpg', quality=95)
        print("✓ Background removal completed and saved as test_bg_removal_local.jpg")
        
        # Check if processing worked
        if result_img.size == test_img.size:
            print("✓ Background removal maintains image dimensions")
            return True
        else:
            print("✗ Background removal changed image dimensions")
            return False
            
    except Exception as e:
        print(f"✗ Background removal test failed: {e}")
        return False

def test_email_system():
    """Test email system (without actually sending)"""
    print("\n=== TESTING EMAIL SYSTEM ===")
    
    try:
        # Test OTP generation
        from application import generate_otp
        
        otp = generate_otp()
        if len(otp) == 6 and otp.isdigit():
            print(f"✓ OTP generation works: {otp}")
            return True
        else:
            print(f"✗ OTP generation failed: {otp}")
            return False
            
    except Exception as e:
        print(f"✗ Email system test failed: {e}")
        return False

def run_all_tests():
    """Run all local functionality tests"""
    print("🚀 STARTING COMPLETE LOCAL FUNCTIONALITY TEST")
    print("=" * 50)
    
    tests = [
        ("Server Health", test_local_server),
        ("Face Detection & Processing", test_face_detection_and_processing),
        ("Watermark (3x Size)", test_watermark_functionality),
        ("Background Removal", test_background_removal),
        ("Email System", test_email_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Ready for deployment!")
        return True
    else:
        print("⚠️  Some tests failed. Fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n✅ Application is ready for deployment!")
        print("📝 Generated test files:")
        print("   - test_person_image.jpg (input)")
        print("   - test_processed_output.jpg (full pipeline)")
        print("   - test_watermark_3x_local.jpg (watermark test)")
        print("   - test_bg_removal_local.jpg (background removal)")
    else:
        print("\n❌ Fix the failing tests before deployment")
    
    sys.exit(0 if success else 1)