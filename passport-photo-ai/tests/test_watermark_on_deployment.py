#!/usr/bin/env python3
"""
Test the watermark functionality on the deployed version
"""

import requests
import base64
from PIL import Image
import io

BASE_URL = "http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com"

def test_watermark():
    """Test watermark on deployed version"""
    try:
        # Create a test image with a clear background to see watermark
        test_img = Image.new('RGB', (800, 800), (240, 240, 240))  # Light gray background
        
        # Add a simple face-like shape
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_img)
        draw.ellipse([300, 200, 500, 600], fill=(220, 180, 140))  # Face color
        
        # Save to buffer
        img_buffer = io.BytesIO()
        test_img.save(img_buffer, format='JPEG', quality=95)
        img_buffer.seek(0)
        
        # Test WITHOUT background removal to see watermark clearly
        files = {'image': ('test.jpg', img_buffer, 'image/jpeg')}
        data = {'remove_background': 'false'}  # Keep background to see watermark
        
        response = requests.post(f"{BASE_URL}/api/full-workflow", files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Watermark test passed")
            print(f"✓ Processing time: {result.get('processing_time', 'N/A')} seconds")
            
            # Save the result to check watermark
            if result.get('processed_image'):
                img_data = base64.b64decode(result['processed_image'])
                with open('deployed_watermark_test.jpg', 'wb') as f:
                    f.write(img_data)
                print("✓ Saved result as deployed_watermark_test.jpg")
                print("✓ Check the image to verify 3x larger white PROOF watermark")
                return True
            else:
                print("✗ No processed image returned")
                return False
        else:
            print(f"✗ Watermark test failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Watermark test error: {e}")
        return False

def main():
    print("🎨 Testing Watermark on AWS Deployment")
    print("=" * 50)
    
    success = test_watermark()
    
    if success:
        print("\n🎉 Watermark test completed successfully!")
        print("📸 Check deployed_watermark_test.jpg to verify:")
        print("   • White PROOF text (not bold)")
        print("   • 3x larger than original size")
        print("   • Diagonal pattern covering entire image")
        print("   • Good visibility but not overwhelming")
    else:
        print("\n❌ Watermark test failed")

if __name__ == "__main__":
    main()