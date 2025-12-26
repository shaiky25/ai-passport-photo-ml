#!/usr/bin/env python3
"""
Test the deployed Passport Photo AI application
Tests both frontend and backend connectivity
"""

import requests
import json
import sys
from PIL import Image, ImageDraw
import io
import base64

def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (800, 800), (100, 150, 200))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple face
    draw.ellipse([300, 200, 500, 600], fill=(220, 180, 140))  # Face
    draw.ellipse([350, 300, 370, 320], fill=(0, 0, 0))       # Left eye
    draw.ellipse([430, 300, 450, 320], fill=(0, 0, 0))       # Right eye
    
    # Save to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    return buffer

def test_backend_health():
    """Test backend health endpoint"""
    backend_url = "http://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api"
    
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend Health Check: PASS")
            print(f"   Message: {data['message']}")
            print(f"   OpenCV: {data['opencv_available']}")
            print(f"   HEIC Support: {data['heic_support']}")
            return True
        else:
            print(f"❌ Backend Health Check: FAIL ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Backend Health Check: ERROR - {e}")
        return False

def test_backend_processing():
    """Test backend image processing"""
    backend_url = "http://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api"
    
    try:
        # Create test image
        test_image = create_test_image()
        
        # Prepare request
        files = {'image': ('test.jpg', test_image, 'image/jpeg')}
        data = {
            'remove_background': 'true',
            'use_learned_profile': 'true'
        }
        
        response = requests.post(
            f"{backend_url}/full-workflow",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Backend Processing: PASS")
            print(f"   Success: {result['success']}")
            print(f"   Processing time: {result.get('processing_time', 'N/A')} seconds")
            print(f"   Face detection: {result['analysis']['face_detection']['faces_detected']} faces")
            print(f"   Processed image: {'Yes' if 'processed_image' in result else 'No'}")
            return True
        else:
            print(f"❌ Backend Processing: FAIL ({response.status_code})")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Backend Processing: ERROR - {e}")
        return False

def test_frontend(frontend_url):
    """Test frontend accessibility"""
    try:
        response = requests.get(frontend_url, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend Access: PASS")
            print(f"   Status: {response.status_code}")
            print(f"   Content length: {len(response.content)} bytes")
            
            # Check if it's our React app
            content = response.text.lower()
            if 'passport' in content or 'react' in content:
                print("   App detected: Passport Photo AI")
            else:
                print("   App detected: Unknown (may not be our app)")
            
            return True
        else:
            print(f"❌ Frontend Access: FAIL ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Frontend Access: ERROR - {e}")
        return False

def main():
    """Main testing function"""
    print("🧪 TESTING DEPLOYED PASSPORT PHOTO AI")
    print("=" * 50)
    
    # Test backend
    print("\n🔧 TESTING BACKEND")
    print("-" * 30)
    backend_health = test_backend_health()
    backend_processing = test_backend_processing() if backend_health else False
    
    # Test frontend (get URL from user)
    print("\n🌐 TESTING FRONTEND")
    print("-" * 30)
    frontend_url = input("Enter your Amplify app URL (e.g., https://main.d123.amplifyapp.com): ").strip()
    
    if frontend_url:
        frontend_ok = test_frontend(frontend_url)
    else:
        print("⚠️  No frontend URL provided, skipping frontend test")
        frontend_ok = None
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Backend Health", backend_health),
        ("Backend Processing", backend_processing),
        ("Frontend Access", frontend_ok)
    ]
    
    passed = 0
    total = 0
    
    for test_name, result in tests:
        if result is not None:
            total += 1
            if result:
                print(f"✅ {test_name}: PASS")
                passed += 1
            else:
                print(f"❌ {test_name}: FAIL")
        else:
            print(f"⚠️  {test_name}: SKIPPED")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total and total > 0:
        print("🎉 SUCCESS! Your Passport Photo AI is fully deployed and working!")
        if frontend_url:
            print(f"🌐 Your app is live at: {frontend_url}")
        print("🔧 Features working: Face detection, watermark (3x size), background removal")
    elif passed > 0:
        print("⚠️  PARTIAL SUCCESS: Some components are working")
        print("💡 Check the failed tests and try again")
    else:
        print("❌ DEPLOYMENT ISSUES: Please check your deployment")
    
    print(f"\n📋 NEXT STEPS:")
    if passed == total and total > 0:
        print("- Test the app with real photos")
        print("- Add custom domain: photo.faizuddinshaik.com")
        print("- Monitor costs with: python check_aws_costs.py")
    else:
        print("- Fix the failing components")
        print("- Check AWS console for errors")
        print("- Verify environment variables in Amplify")

if __name__ == "__main__":
    main()