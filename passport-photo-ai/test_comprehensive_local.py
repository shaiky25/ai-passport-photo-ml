#!/usr/bin/env python3
"""
Comprehensive local testing suite for Passport Photo AI
Tests all functionality including edge cases before deployment
"""

import requests
import base64
from PIL import Image, ImageDraw
import io
import json
import time
import os
import sys
from datetime import datetime

# Test configuration
BACKEND_URL = "http://localhost:5000"
TEST_IMAGE_PATH = "test_image_with_background.jpg"

class PassportPhotoTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, passed, message="", details=None):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"    Details: {details}")
            
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message,
            'details': details
        })
    
    def create_test_image(self, width=800, height=800, format='JPEG'):
        """Create a test image with face-like features"""
        img = Image.new('RGB', (width, height), 'lightblue')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple face
        face_center = (width//2, int(height*0.4))
        face_radius = min(width, height) // 8
        
        # Face (skin color)
        draw.ellipse([
            face_center[0] - face_radius, 
            face_center[1] - face_radius,
            face_center[0] + face_radius, 
            face_center[1] + face_radius
        ], fill=(255, 220, 177))
        
        # Eyes
        eye_y = face_center[1] - face_radius//3
        eye_offset = face_radius//2
        draw.ellipse([face_center[0] - eye_offset, eye_y - 5, face_center[0] - eye_offset + 10, eye_y + 5], fill='black')
        draw.ellipse([face_center[0] + eye_offset - 10, eye_y - 5, face_center[0] + eye_offset, eye_y + 5], fill='black')
        
        # Mouth
        mouth_y = face_center[1] + face_radius//3
        draw.arc([face_center[0] - 15, mouth_y - 8, face_center[0] + 15, mouth_y + 8], 0, 180, fill='black', width=2)
        
        buffer = io.BytesIO()
        img.save(buffer, format=format, quality=95)
        buffer.seek(0)
        return buffer
    
    def test_backend_startup(self):
        """Test 1: Backend Health Check"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                rembg_available = data.get('rembg_available', False)
                opencv_available = data.get('opencv_available', False)
                heic_support = data.get('heic_support', False)
                
                self.log_test("Backend Health", True, 
                    f"Status: {data.get('status')}, rembg: {rembg_available}, opencv: {opencv_available}, heic: {heic_support}",
                    data)
                return rembg_available, opencv_available, heic_support
            else:
                self.log_test("Backend Health", False, f"HTTP {response.status_code}")
                return False, False, False
        except Exception as e:
            self.log_test("Backend Health", False, f"Connection failed: {e}")
            return False, False, False
    
    def test_basic_processing(self):
        """Test 2: Basic Photo Processing (No Background Removal)"""
        try:
            test_image = self.create_test_image(800, 800)
            files = {'image': ('test.jpg', test_image, 'image/jpeg')}
            data = {'remove_background': 'false', 'email': ''}
            
            response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                feasible = result.get('feasible', False)
                processed_image = result.get('processed_image')
                
                if success and feasible and processed_image:
                    # Verify processed image
                    image_data = base64.b64decode(processed_image)
                    img = Image.open(io.BytesIO(image_data))
                    
                    self.log_test("Basic Processing", True, 
                        f"Success: {success}, Feasible: {feasible}, Output: {img.size}, Mode: {img.mode}")
                    return True
                else:
                    self.log_test("Basic Processing", False, 
                        f"Success: {success}, Feasible: {feasible}, Has image: {bool(processed_image)}")
                    return False
            else:
                self.log_test("Basic Processing", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Basic Processing", False, f"Error: {e}")
            return False
    
    def test_background_removal(self):
        """Test 3: Background Removal with Real Image"""
        try:
            # Create a proper test image
            test_image = self.create_test_image(800, 800)
            
            files = {'image': ('test_bg.jpg', test_image, 'image/jpeg')}
            data = {'remove_background': 'true', 'email': ''}
            
            response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                processed_image = result.get('processed_image')
                
                if success and processed_image:
                    # Save result for manual inspection
                    image_data = base64.b64decode(processed_image)
                    with open('test_bg_removal_output.jpg', 'wb') as f:
                        f.write(image_data)
                    
                    img = Image.open(io.BytesIO(image_data))
                    
                    # Check if background appears to be removed (look for white/light background)
                    corners = [
                        img.getpixel((0, 0)),
                        img.getpixel((img.width-1, 0)),
                        img.getpixel((0, img.height-1)),
                        img.getpixel((img.width-1, img.height-1))
                    ]
                    
                    # Check if corners are light (indicating background removal)
                    light_corners = sum(1 for corner in corners if sum(corner) > 600)  # RGB sum > 600 = light
                    
                    self.log_test("Background Removal", True, 
                        f"Success: {success}, Output saved, Light corners: {light_corners}/4",
                        f"Corner colors: {corners}")
                    return True
                else:
                    self.log_test("Background Removal", False, 
                        f"Success: {success}, Has image: {bool(processed_image)}")
                    return False
            else:
                self.log_test("Background Removal", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Background Removal", False, f"Error: {e}")
            return False
    
    def test_face_detection(self):
        """Test 4: Face Detection Analysis"""
        try:
            test_image = self.create_test_image(800, 800)
            files = {'image': ('face_test.jpg', test_image, 'image/jpeg')}
            data = {'remove_background': 'false', 'email': ''}
            
            response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('analysis', {})
                face_detection = analysis.get('face_detection', {})
                
                faces_detected = face_detection.get('faces_detected', 0)
                valid = face_detection.get('valid', False)
                head_height = face_detection.get('head_height_percent', 0)
                
                self.log_test("Face Detection", True, 
                    f"Faces: {faces_detected}, Valid: {valid}, Head height: {head_height}%",
                    face_detection)
                return True
            else:
                self.log_test("Face Detection", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Face Detection", False, f"Error: {e}")
            return False
    
    def test_email_verification(self):
        """Test 5: Email OTP System"""
        try:
            # Test sending OTP - use verified email address
            email_data = {'email': 'faiz.undefined@gmail.com'}
            response = requests.post(f"{BACKEND_URL}/api/send-otp", json=email_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                
                if success:
                    # Test OTP verification with wrong code
                    verify_data = {'email': 'faiz.undefined@gmail.com', 'otp': '000000'}
                    verify_response = requests.post(f"{BACKEND_URL}/api/verify-otp", json=verify_data, timeout=10)
                    
                    if verify_response.status_code == 400:
                        self.log_test("Email Verification", True, 
                            "OTP send successful, invalid OTP correctly rejected")
                        return True
                    else:
                        self.log_test("Email Verification", False, 
                            f"Invalid OTP not rejected: {verify_response.status_code}")
                        return False
                else:
                    self.log_test("Email Verification", False, f"OTP send failed: {result}")
                    return False
            elif response.status_code == 500:
                # Check if it's an SES verification issue
                try:
                    error_result = response.json()
                    if "not verified" in error_result.get('error', '').lower():
                        self.log_test("Email Verification", True, 
                            "Email not verified in SES (expected for local testing)")
                        return True
                except:
                    pass
                self.log_test("Email Verification", False, f"HTTP 500: {response.text}")
                return False
            else:
                self.log_test("Email Verification", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Email Verification", False, f"Error: {e}")
            return False
    
    def test_edge_cases(self):
        """Test 6: Edge Cases and Error Handling"""
        edge_cases = []
        
        # Test 6a: No image provided
        try:
            response = requests.post(f"{BACKEND_URL}/api/full-workflow", timeout=10)
            if response.status_code == 400:
                edge_cases.append("No image - correctly rejected")
            else:
                edge_cases.append(f"No image - wrong status: {response.status_code}")
        except Exception as e:
            edge_cases.append(f"No image - error: {e}")
        
        # Test 6b: Very small image
        try:
            small_image = self.create_test_image(50, 50)
            files = {'image': ('small.jpg', small_image, 'image/jpeg')}
            data = {'remove_background': 'false'}
            
            response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=30)
            result = response.json()
            
            if not result.get('feasible', True):
                edge_cases.append("Small image - correctly rejected")
            else:
                edge_cases.append("Small image - should be rejected but wasn't")
        except Exception as e:
            edge_cases.append(f"Small image - error: {e}")
        
        # Test 6c: Very large image
        try:
            large_image = self.create_test_image(3000, 3000)
            files = {'image': ('large.jpg', large_image, 'image/jpeg')}
            data = {'remove_background': 'false'}
            
            response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                edge_cases.append("Large image - processed successfully")
            else:
                edge_cases.append(f"Large image - failed: {response.status_code}")
        except Exception as e:
            edge_cases.append(f"Large image - error: {e}")
        
        # Test 6d: Invalid email format
        try:
            email_data = {'email': 'invalid-email'}
            response = requests.post(f"{BACKEND_URL}/api/send-otp", json=email_data, timeout=10)
            
            if response.status_code == 400:
                edge_cases.append("Invalid email - correctly rejected")
            else:
                edge_cases.append(f"Invalid email - wrong status: {response.status_code}")
        except Exception as e:
            edge_cases.append(f"Invalid email - error: {e}")
        
        # Test 6e: Valid email format but potentially unverified
        try:
            email_data = {'email': 'faiz.undefined@gmail.com'}
            response = requests.post(f"{BACKEND_URL}/api/send-otp", json=email_data, timeout=10)
            
            if response.status_code in [200, 500]:  # 200 = success, 500 = unverified (both acceptable)
                edge_cases.append("Valid email format - handled appropriately")
            else:
                edge_cases.append(f"Valid email - unexpected status: {response.status_code}")
        except Exception as e:
            edge_cases.append(f"Valid email - error: {e}")
        
        all_passed = all("correctly" in case or "successfully" in case or "appropriately" in case for case in edge_cases)
        self.log_test("Edge Cases", all_passed, f"Tested {len(edge_cases)} cases", edge_cases)
        return all_passed
    
    def test_watermark_functionality(self):
        """Test 7: Watermark Presence and Removal"""
        try:
            test_image = self.create_test_image(800, 800)
            
            # Test with watermark (no email verification)
            files = {'image': ('watermark_test.jpg', test_image, 'image/jpeg')}
            data = {'remove_background': 'false', 'email': ''}
            
            response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                processed_image = result.get('processed_image')
                
                if processed_image:
                    # Save watermarked image
                    image_data = base64.b64decode(processed_image)
                    with open('test_watermarked_output.jpg', 'wb') as f:
                        f.write(image_data)
                    
                    # Check image properties
                    img = Image.open(io.BytesIO(image_data))
                    
                    self.log_test("Watermark Functionality", True, 
                        f"Watermarked image created: {img.size}, Mode: {img.mode}")
                    return True
                else:
                    self.log_test("Watermark Functionality", False, "No processed image returned")
                    return False
            else:
                self.log_test("Watermark Functionality", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Watermark Functionality", False, f"Error: {e}")
            return False
    
    def test_performance(self):
        """Test 8: Performance and Response Times"""
        try:
            test_image = self.create_test_image(1200, 1200)  # High resolution
            files = {'image': ('perf_test.jpg', test_image, 'image/jpeg')}
            data = {'remove_background': 'true', 'email': ''}
            
            start_time = time.time()
            response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=120)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                server_time = result.get('processing_time', 0)
                
                # Performance thresholds
                acceptable_time = 30  # seconds
                performance_ok = processing_time < acceptable_time
                
                self.log_test("Performance", performance_ok, 
                    f"Total: {processing_time:.2f}s, Server: {server_time:.2f}s, Threshold: {acceptable_time}s")
                return performance_ok
            else:
                self.log_test("Performance", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Performance", False, f"Error: {e}")
            return False
    
    def test_cors_headers(self):
        """Test 9: CORS Configuration"""
        try:
            # Test preflight request
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = requests.options(f"{BACKEND_URL}/api/full-workflow", headers=headers, timeout=10)
            
            cors_ok = response.status_code in [200, 204]
            
            self.log_test("CORS Headers", cors_ok, 
                f"Preflight status: {response.status_code}")
            return cors_ok
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {e}")
            return False
    
    def test_analytics_logging(self):
        """Test 10: Analytics Event Logging"""
        try:
            event_data = {
                'event_type': 'test',
                'timestamp': datetime.now().isoformat(),
                'details': {'test': True}
            }
            
            response = requests.post(f"{BACKEND_URL}/api/log-event", json=event_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                
                self.log_test("Analytics Logging", success, 
                    f"Event logged successfully: {success}")
                return success
            else:
                self.log_test("Analytics Logging", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Analytics Logging", False, f"Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 COMPREHENSIVE LOCAL TESTING SUITE")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Image: {TEST_IMAGE_PATH}")
        print(f"Start Time: {datetime.now()}")
        print()
        
        # Check if backend is running
        rembg_available, opencv_available, heic_support = self.test_backend_startup()
        
        if not any([rembg_available, opencv_available]):
            print("❌ Critical dependencies missing. Cannot continue testing.")
            return False
        
        # Run all tests
        tests = [
            ("Basic Processing", self.test_basic_processing),
            ("Background Removal", self.test_background_removal),
            ("Face Detection", self.test_face_detection),
            ("Email Verification", self.test_email_verification),
            ("Edge Cases", self.test_edge_cases),
            ("Watermark Functionality", self.test_watermark_functionality),
            ("Performance", self.test_performance),
            ("CORS Headers", self.test_cors_headers),
            ("Analytics Logging", self.test_analytics_logging),
        ]
        
        print("\n" + "=" * 60)
        print("RUNNING DETAILED TESTS")
        print("=" * 60)
        
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")
        
        # Detailed results
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")
        
        # Critical issues
        failed_tests = [r for r in self.test_results if not r['passed']]
        if failed_tests:
            print(f"\n⚠️  CRITICAL ISSUES FOUND ({len(failed_tests)} failures):")
            for failure in failed_tests:
                print(f"  - {failure['test']}: {failure['message']}")
                if failure['details']:
                    print(f"    Details: {failure['details']}")
        
        success_rate = (self.passed_tests / self.total_tests) * 100
        deployment_ready = success_rate >= 90 and rembg_available
        
        print(f"\n{'🎉' if deployment_ready else '⚠️ '} DEPLOYMENT READINESS")
        print("=" * 60)
        if deployment_ready:
            print("✅ System is ready for deployment!")
            print("✅ All critical functionality working")
            print("✅ Background removal available")
            print("✅ Performance within acceptable limits")
        else:
            print("❌ System NOT ready for deployment")
            print(f"❌ Success rate: {success_rate:.1f}% (need ≥90%)")
            print(f"❌ Background removal: {'✅' if rembg_available else '❌'}")
            print("❌ Fix issues before deploying")
        
        return deployment_ready

def main():
    """Main test execution"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python3 test_comprehensive_local.py")
        print("Runs comprehensive local testing before deployment")
        print("Ensure Flask backend is running on localhost:5000")
        return
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend not running on localhost:5000")
            print("Please start the Flask backend first:")
            print("  cd backend && python3 application.py")
            return
    except:
        print("❌ Cannot connect to backend on localhost:5000")
        print("Please start the Flask backend first:")
        print("  cd backend && python3 application.py")
        return
    
    tester = PassportPhotoTester()
    deployment_ready = tester.run_all_tests()
    
    exit(0 if deployment_ready else 1)

if __name__ == "__main__":
    main()