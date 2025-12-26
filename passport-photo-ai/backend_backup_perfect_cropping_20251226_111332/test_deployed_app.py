#!/usr/bin/env python3
"""
Test script to verify the deployed passport photo application works end-to-end
"""

import requests
import base64
from PIL import Image, ImageDraw
import io
import json
import time

# Configuration
BACKEND_URL = "http://passport-photo-backend.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com"
FRONTEND_URL = "https://d3v43yp22urrfn.cloudfront.net"

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
    
    # Save to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    return buffer

def test_backend_health():
    """Test backend health endpoint"""
    print("Testing backend health...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print("✅ Backend health check passed")
                return True
            else:
                print(f"❌ Backend unhealthy: {data}")
                return False
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False

def test_frontend_accessibility():
    """Test frontend accessibility"""
    print("Testing frontend accessibility...")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        
        if response.status_code == 200:
            if "AI Passport Photo Converter" in response.text:
                print("✅ Frontend accessible and contains expected content")
                return True
            else:
                print("❌ Frontend accessible but missing expected content")
                return False
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend accessibility error: {e}")
        return False

def test_photo_processing():
    """Test photo processing endpoint"""
    print("Testing photo processing...")
    
    try:
        # Create test image
        test_image = create_test_image(800, 800)
        
        # Prepare the request
        files = {
            'image': ('test_photo.jpg', test_image, 'image/jpeg')
        }
        
        data = {
            'remove_background': 'false',
            'email': ''
        }
        
        response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success') and result.get('feasible'):
                print("✅ Photo processing successful")
                
                # Check analysis results
                analysis = result.get('analysis', {})
                face_detection = analysis.get('face_detection', {})
                
                print(f"  Face detection: {face_detection.get('faces_detected', 0)} faces")
                print(f"  Valid: {face_detection.get('valid', False)}")
                print(f"  Head height: {face_detection.get('head_height_percent', 0)}%")
                
                # Check processed image
                processed_image = result.get('processed_image')
                if processed_image:
                    print(f"  Processed image size: {len(processed_image)} characters (base64)")
                    
                    # Verify it's valid base64 and can be decoded
                    try:
                        image_data = base64.b64decode(processed_image)
                        img = Image.open(io.BytesIO(image_data))
                        
                        if img.size == (600, 600):
                            print("✅ Processed image has correct dimensions (600x600)")
                        else:
                            print(f"❌ Wrong dimensions: {img.size}")
                            
                        if img.mode == 'RGB':
                            print("✅ Processed image is RGB")
                        else:
                            print(f"❌ Wrong mode: {img.mode}")
                            
                        return True
                        
                    except Exception as e:
                        print(f"❌ Could not decode processed image: {e}")
                        return False
                else:
                    print("❌ No processed image returned")
                    return False
            else:
                print(f"❌ Photo processing failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Photo processing request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Photo processing error: {e}")
        return False

def test_analytics_logging():
    """Test analytics logging endpoint"""
    print("Testing analytics logging...")
    
    try:
        event_data = {
            'event': 'test_event',
            'timestamp': '2025-12-10T00:00:00Z',
            'user_agent': 'test-script',
            'details': {
                'test': True
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/log-event", 
            json=event_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Analytics logging working")
                return True
            else:
                print(f"❌ Analytics logging failed: {result}")
                return False
        else:
            print(f"❌ Analytics logging request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analytics logging error: {e}")
        return False

def test_cors_headers():
    """Test CORS headers for frontend integration"""
    print("Testing CORS headers...")
    
    try:
        # Test preflight request
        headers = {
            'Origin': FRONTEND_URL,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{BACKEND_URL}/api/full-workflow", headers=headers, timeout=10)
        
        # Check if CORS is properly configured (should not fail)
        if response.status_code in [200, 204]:
            print("✅ CORS preflight request handled")
        else:
            print(f"⚠️  CORS preflight returned: {response.status_code}")
        
        # Test actual request with Origin header
        test_image = create_test_image(600, 600)
        files = {'image': ('test.jpg', test_image, 'image/jpeg')}
        data = {'remove_background': 'false'}
        headers = {'Origin': FRONTEND_URL}
        
        response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Cross-origin requests working")
            return True
        else:
            print(f"❌ Cross-origin request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("Testing error handling...")
    
    try:
        # Test with no image
        response = requests.post(f"{BACKEND_URL}/api/full-workflow", timeout=10)
        
        if response.status_code == 400:
            result = response.json()
            if 'error' in result and 'image' in result['error'].lower():
                print("✅ Proper error handling for missing image")
                return True
            else:
                print(f"❌ Unexpected error response: {result}")
                return False
        else:
            print(f"❌ Expected 400 error, got: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def run_all_tests():
    """Run all deployment tests"""
    print("Running Deployed Application Tests")
    print("=" * 50)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Frontend Accessibility", test_frontend_accessibility),
        ("Photo Processing", test_photo_processing),
        ("Analytics Logging", test_analytics_logging),
        ("CORS Headers", test_cors_headers),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All deployment tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)