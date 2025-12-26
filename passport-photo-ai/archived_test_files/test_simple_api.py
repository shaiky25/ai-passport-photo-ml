#!/usr/bin/env python3

import requests

def test_simple_api():
    """Test the API with a simple request"""
    
    base_url = 'http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com'
    
    # Test with a simple image upload
    try:
        print("Testing simple image upload...")
        
        # Create a simple test image
        from PIL import Image
        import io
        
        # Create a simple 600x600 test image
        test_img = Image.new('RGB', (600, 600), (255, 0, 0))  # Red background
        
        # Save to bytes
        img_buffer = io.BytesIO()
        test_img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        
        # Test the API
        files = {'image': ('test.jpg', img_buffer, 'image/jpeg')}
        data = {
            'remove_background': 'false',  # Don't try background removal
            'use_ai': 'true'
        }
        
        response = requests.post(f"{base_url}/api/full-workflow", files=files, data=data, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API is working!")
            print(f"Success: {result.get('success')}")
            print(f"Face detected: {result.get('analysis', {}).get('face_detection', {}).get('valid')}")
            return True
        else:
            print("❌ API returned error")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_simple_api()