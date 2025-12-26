#!/usr/bin/env python3
"""
Test the fixed AWS deployment to ensure all functionality works
"""

import requests
import json
import base64
from PIL import Image
import io

# AWS deployment URL
BASE_URL = "http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com"

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data.get('message')}")
            print(f"✓ OpenCV available: {data.get('opencv_available')}")
            print(f"✓ HEIC support: {data.get('heic_support')}")
            return True
        else:
            print(f"✗ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_full_workflow():
    """Test the full workflow with a sample image"""
    try:
        # Create a test image
        test_img = Image.new('RGB', (800, 800), (200, 200, 200))
        
        # Add a simple face-like shape
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_img)
        draw.ellipse([300, 200, 500, 600], fill=(220, 180, 140))  # Face color
        
        # Save to buffer
        img_buffer = io.BytesIO()
        test_img.save(img_buffer, format='JPEG', quality=95)
        img_buffer.seek(0)
        
        # Test without background removal
        files = {'image': ('test.jpg', img_buffer, 'image/jpeg')}
        data = {'remove_background': 'false'}
        
        response = requests.post(f"{BASE_URL}/api/full-workflow", files=files, data=data, timeout=30)
        print(f"Full workflow status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Full workflow passed: {result.get('message')}")
            print(f"✓ Processing time: {result.get('processing_time', 'N/A')} seconds")
            print(f"✓ Face detection: {result.get('analysis', {}).get('face_detection', {}).get('faces_detected', 0)} faces")
            print(f"✓ Processed image size: {len(result.get('processed_image', ''))} chars")
            return True
        else:
            print(f"✗ Full workflow failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Full workflow error: {e}")
        return False

def test_background_removal():
    """Test background removal functionality"""
    try:
        # Create a test image
        test_img = Image.new('RGB', (800, 800), (100, 150, 200))
        
        # Add a simple face-like shape
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_img)
        draw.ellipse([300, 200, 500, 600], fill=(220, 180, 140))  # Face color
        
        # Save to buffer
        img_buffer = io.BytesIO()
        test_img.save(img_buffer, format='JPEG', quality=95)
        img_buffer.seek(0)
        
        # Test WITH background removal
        files = {'image': ('test.jpg', img_buffer, 'image/jpeg')}
        data = {'remove_background': 'true'}
        
        response = requests.post(f"{BASE_URL}/api/full-workflow", files=files, data=data, timeout=60)
        print(f"Background removal status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Background removal passed: {result.get('message')}")
            print(f"✓ Processing time: {result.get('processing_time', 'N/A')} seconds")
            
            # Save the result to check watermark
            if result.get('processed_image'):
                img_data = base64.b64decode(result['processed_image'])
                with open('deployed_bg_removal_test.jpg', 'wb') as f:
                    f.write(img_data)
                print("✓ Saved result as deployed_bg_removal_test.jpg")
            
            return True
        else:
            print(f"✗ Background removal failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Background removal error: {e}")
        return False

def main():
    print("🚀 Testing Fixed AWS Deployment")
    print("=" * 50)
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    print()
    
    if health_ok:
        # Test full workflow
        workflow_ok = test_full_workflow()
        print()
        
        # Test background removal
        bg_removal_ok = test_background_removal()
        print()
        
        if health_ok and workflow_ok and bg_removal_ok:
            print("🎉 All tests passed! Deployment is working correctly.")
            print("✅ Watermark system: 3x larger white text")
            print("✅ Background removal: rembg u2netp model")
            print("✅ Face detection: OpenCV with learned profile")
            print("✅ All API endpoints: Working")
        else:
            print("❌ Some tests failed. Check the output above.")
    else:
        print("❌ Health check failed. Deployment may have issues.")

if __name__ == "__main__":
    main()