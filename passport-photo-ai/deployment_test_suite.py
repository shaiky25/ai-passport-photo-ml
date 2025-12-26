#!/usr/bin/env python3
"""
Deployment Test Suite - Critical tests that must pass before deployment
"""

import requests
import base64
import os
import sys
import time
from PIL import Image
import io

class DeploymentTestSuite:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.test_results = []
        self.critical_failures = []
        
    def log_test(self, test_name, passed, message="", critical=False):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'message': message,
            'critical': critical
        })
        
        if not passed and critical:
            self.critical_failures.append(test_name)
            
        print(f"  {status} {test_name}")
        if message:
            print(f"    {message}")
    
    def test_server_health(self):
        """Test basic server health"""
        print("\n🔍 Testing Server Health")
        print("-" * 30)
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test("Server Health Check", True, "Server is healthy", critical=True)
                    
                    # Check system availability
                    opencv_ok = data.get('opencv_available', False)
                    rembg_ok = data.get('rembg_available', False)
                    heic_ok = data.get('heic_support', False)
                    
                    self.log_test("OpenCV Available", opencv_ok, critical=True)
                    self.log_test("REMBG Available", rembg_ok, critical=True)
                    self.log_test("HEIC Support", heic_ok, critical=False)
                else:
                    self.log_test("Server Health Check", False, f"Status: {data.get('status')}", critical=True)
            else:
                self.log_test("Server Health Check", False, f"HTTP {response.status_code}", critical=True)
                
        except Exception as e:
            self.log_test("Server Health Check", False, f"Connection error: {e}", critical=True)
    
    def test_pipeline_configuration(self):
        """Test pipeline configuration"""
        print("\n🔍 Testing Pipeline Configuration")
        print("-" * 35)
        
        try:
            response = requests.get(f"{self.base_url}/api/pipeline-config", timeout=10)
            if response.status_code == 200:
                data = response.json()
                flags = data.get('pipeline_flags', {})
                
                # Critical flags that must be enabled
                critical_flags = {
                    'enhanced_face_detection': True,
                    'intelligent_cropping': True,
                    'image_enhancement': True
                }
                
                for flag, expected in critical_flags.items():
                    actual = flags.get(flag, False)
                    self.log_test(f"Pipeline Flag: {flag}", actual == expected, 
                                f"Expected: {expected}, Got: {actual}", critical=True)
                
                # Optional flags
                optional_flags = {
                    'background_removal': False,  # Should be disabled for stability
                    'watermark': True,
                    'learned_profile': True
                }
                
                for flag, expected in optional_flags.items():
                    actual = flags.get(flag, False)
                    self.log_test(f"Optional Flag: {flag}", actual == expected, 
                                f"Expected: {expected}, Got: {actual}", critical=False)
                    
            else:
                self.log_test("Pipeline Configuration", False, f"HTTP {response.status_code}", critical=True)
                
        except Exception as e:
            self.log_test("Pipeline Configuration", False, f"Error: {e}", critical=True)
    
    def test_government_compliance(self):
        """Test government compliance with sample images"""
        print("\n🔍 Testing Government Compliance")
        print("-" * 35)
        
        # Test images that SHOULD pass government compliance (single face, good quality)
        expected_pass_images = [
            "backend/test_images/faiz.png",
            "backend/test_images/sample_image_1.jpg", 
            "backend/test_images/sample_image_2.jpg",
            "backend/test_images/faiz_with_glasses.png"
        ]
        
        # Test images that are EXPECTED to fail (but system should handle gracefully)
        expected_fail_images = [
            "backend/test_images/multi_face.jpg",  # Multiple faces of same clarity - acceptable to fail
            "backend/test_images/people_in_bg_unfocused.JPG"  # Background unfocused faces - must fail
        ]
        
        compliant_count = 0
        total_valid_images = 0
        
        # Test images that should pass
        print("  📋 Testing images that SHOULD pass government compliance:")
        for image_path in expected_pass_images:
            if not os.path.exists(image_path):
                continue
                
            filename = os.path.basename(image_path)
            
            try:
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    data = {
                        'use_learned_profile': 'true',
                        'remove_bg': 'false',
                        'remove_watermark': 'false'
                    }
                    
                    response = requests.post(f"{self.base_url}/api/full-workflow", 
                                           files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('success'):
                        face_data = result['analysis']['face_detection']
                        faces_detected = face_data.get('faces_detected', 0)
                        
                        if faces_detected == 1:
                            total_valid_images += 1
                            government_compliant = False
                            
                            if 'government_compliance' in face_data:
                                gov_data = face_data['government_compliance']
                                government_compliant = gov_data.get('meets_70_80_requirement', False)
                                face_ratio = gov_data.get('face_height_ratio', 0)
                                
                                if government_compliant:
                                    compliant_count += 1
                                    self.log_test(f"Compliance: {filename}", True, 
                                                f"Face ratio: {face_ratio:.1%}", critical=True)
                                else:
                                    self.log_test(f"Compliance: {filename}", False, 
                                                f"Face ratio: {face_ratio:.1%}", critical=True)
                            else:
                                self.log_test(f"Compliance: {filename}", False, 
                                            "No government compliance data", critical=True)
                        else:
                            self.log_test(f"Face Detection: {filename}", faces_detected == 1, 
                                        f"Faces detected: {faces_detected}", critical=True)
                    else:
                        self.log_test(f"Processing: {filename}", False, 
                                    result.get('message', 'Unknown error'), critical=True)
                else:
                    self.log_test(f"API Call: {filename}", False, 
                                f"HTTP {response.status_code}", critical=True)
                    
            except Exception as e:
                self.log_test(f"Test: {filename}", False, f"Error: {e}", critical=True)
        
        # Test images that are expected to fail (but should be handled gracefully)
        print("  📋 Testing images that are EXPECTED to fail (graceful handling):")
        for image_path in expected_fail_images:
            if not os.path.exists(image_path):
                continue
                
            filename = os.path.basename(image_path)
            
            try:
                with open(image_path, 'rb') as f:
                    files = {'image': f}
                    data = {
                        'use_learned_profile': 'true',
                        'remove_bg': 'false',
                        'remove_watermark': 'false'
                    }
                    
                    response = requests.post(f"{self.base_url}/api/full-workflow", 
                                           files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('success'):
                        face_data = result['analysis']['face_detection']
                        faces_detected = face_data.get('faces_detected', 0)
                        government_compliant = False
                        
                        if 'government_compliance' in face_data:
                            gov_data = face_data['government_compliance']
                            government_compliant = gov_data.get('meets_70_80_requirement', False)
                        
                        # For multi-face or background images, we expect them to fail compliance
                        # but the system should handle them gracefully (return success=true but compliant=false)
                        expected_behavior = not government_compliant  # Should be non-compliant
                        
                        self.log_test(f"Graceful Handling: {filename}", expected_behavior, 
                                    f"Faces: {faces_detected}, Compliant: {government_compliant} (expected non-compliant)", 
                                    critical=False)
                    else:
                        # It's also acceptable if processing fails for these images
                        self.log_test(f"Graceful Handling: {filename}", True, 
                                    f"Processing failed as expected: {result.get('message', 'Unknown')}", 
                                    critical=False)
                else:
                    self.log_test(f"Graceful Handling: {filename}", False, 
                                f"HTTP {response.status_code}", critical=False)
                    
            except Exception as e:
                self.log_test(f"Graceful Handling: {filename}", False, f"Error: {e}", critical=False)
        
        # Overall compliance check - all expected-to-pass images should pass
        if total_valid_images > 0:
            compliance_rate = compliant_count / total_valid_images
            self.log_test("Overall Compliance Rate (Expected Pass Images)", compliance_rate == 1.0, 
                        f"{compliant_count}/{total_valid_images} ({compliance_rate:.1%})", critical=True)
        else:
            self.log_test("Overall Compliance Rate (Expected Pass Images)", False, "No valid test images", critical=True)
    
    def test_performance(self):
        """Test basic performance metrics"""
        print("\n🔍 Testing Performance")
        print("-" * 25)
        
        # Test health endpoint response time
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                self.log_test("Health Endpoint Speed", response_time < 1.0, 
                            f"Response time: {response_time:.3f}s", critical=False)
            else:
                self.log_test("Health Endpoint Speed", False, 
                            f"HTTP {response.status_code}", critical=True)
                
        except Exception as e:
            self.log_test("Health Endpoint Speed", False, f"Error: {e}", critical=True)
        
        # Test image processing performance (if we have test images)
        test_image = "backend/test_images/faiz.png"
        if os.path.exists(test_image):
            try:
                start_time = time.time()
                
                with open(test_image, 'rb') as f:
                    files = {'image': f}
                    data = {'use_learned_profile': 'true', 'remove_bg': 'false'}
                    
                    response = requests.post(f"{self.base_url}/api/full-workflow", 
                                           files=files, data=data, timeout=30)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.log_test("Image Processing Speed", processing_time < 5.0, 
                                    f"Processing time: {processing_time:.3f}s", critical=False)
                    else:
                        self.log_test("Image Processing Speed", False, 
                                    "Processing failed", critical=True)
                else:
                    self.log_test("Image Processing Speed", False, 
                                f"HTTP {response.status_code}", critical=True)
                    
            except Exception as e:
                self.log_test("Image Processing Speed", False, f"Error: {e}", critical=True)
    
    def run_all_tests(self):
        """Run all deployment tests"""
        print("🚀 DEPLOYMENT TEST SUITE")
        print("=" * 50)
        
        self.test_server_health()
        self.test_pipeline_configuration()
        self.test_government_compliance()
        self.test_performance()
        
        # Summary
        print("\n📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['passed']])
        critical_tests = len([t for t in self.test_results if t['critical']])
        critical_passed = len([t for t in self.test_results if t['critical'] and t['passed']])
        
        print(f"Total Tests: {passed_tests}/{total_tests}")
        print(f"Critical Tests: {critical_passed}/{critical_tests}")
        print(f"Critical Failures: {len(self.critical_failures)}")
        
        if self.critical_failures:
            print(f"\n❌ CRITICAL FAILURES:")
            for failure in self.critical_failures:
                print(f"  - {failure}")
        
        # Determine overall result
        deployment_ready = len(self.critical_failures) == 0
        
        print(f"\n🏆 DEPLOYMENT READINESS: {'✅ READY' if deployment_ready else '❌ NOT READY'}")
        
        if deployment_ready:
            print("🎉 All critical tests passed! Safe to deploy.")
        else:
            print("⚠️ Critical tests failed! DO NOT DEPLOY until issues are resolved.")
        
        return deployment_ready

def main():
    """Main function"""
    # Check if server URL is provided
    base_url = "http://127.0.0.1:5000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"Testing server at: {base_url}")
    
    # Run test suite
    test_suite = DeploymentTestSuite(base_url)
    deployment_ready = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if deployment_ready else 1)

if __name__ == "__main__":
    main()