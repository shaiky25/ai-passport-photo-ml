#!/usr/bin/env python3

import requests
import base64
from PIL import Image
import io

def test_strong_watermark():
    """Test the new strong watermark implementation"""
    
    # Create a test image (blue sky with white clouds like the example)
    test_img = Image.new('RGB', (600, 600), (135, 206, 235))  # Sky blue
    
    # Add some white "clouds" to make it more like the example
    from PIL import ImageDraw
    draw = ImageDraw.Draw(test_img)
    
    # Draw some cloud-like shapes
    draw.ellipse([100, 100, 200, 150], fill=(255, 255, 255))
    draw.ellipse([300, 80, 450, 140], fill=(255, 255, 255))
    draw.ellipse([150, 200, 280, 250], fill=(255, 255, 255))
    draw.ellipse([400, 180, 520, 230], fill=(255, 255, 255))
    draw.ellipse([50, 300, 180, 350], fill=(255, 255, 255))
    draw.ellipse([350, 320, 480, 370], fill=(255, 255, 255))
    
    # Save test image
    test_img.save('test_sky_image.jpg', 'JPEG')
    print("Created test sky image: test_sky_image.jpg")
    
    # Test the watermark locally first
    try:
        # Import the processor
        import sys
        sys.path.append('backend')
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        watermarked_img = processor.add_watermark(test_img)
        watermarked_img.save('test_strong_watermark_local.jpg', 'JPEG')
        print("✅ Local watermark test successful: test_strong_watermark_local.jpg")
        
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        return False
    
    # Test via API
    try:
        url = 'http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com/api/full-workflow'
        
        with open('test_sky_image.jpg', 'rb') as f:
            files = {'image': f}
            data = {
                'remove_background': 'false',  # Keep background to see watermark clearly
                'use_ai': 'true'
            }
            
            print("Testing strong watermark via API...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('processed_image'):
                    # Decode and save the result
                    img_data = base64.b64decode(result['processed_image'])
                    with open('test_strong_watermark_api.jpg', 'wb') as f:
                        f.write(img_data)
                    
                    print("✅ API watermark test successful: test_strong_watermark_api.jpg")
                    print(f"Face detection: {result.get('analysis', {}).get('face_detection', {}).get('valid', 'Unknown')}")
                    return True
                else:
                    print(f"❌ API returned success=False: {result}")
                    return False
            else:
                print(f"❌ API request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_strong_watermark()