#!/usr/bin/env python3
"""
Test the AWS deployment using HTTP instead of HTTPS
"""

import requests
import json

# Try HTTP instead of HTTPS
BASE_URL = "http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com"

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=30)
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

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=30)
        print(f"Root endpoint status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Root endpoint passed: {data.get('message')}")
            return True
        else:
            print(f"✗ Root endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Root endpoint error: {e}")
        return False

def main():
    print("🚀 Testing AWS Deployment with HTTP")
    print("=" * 50)
    
    # Test root endpoint first
    root_ok = test_root_endpoint()
    print()
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    print()
    
    if root_ok and health_ok:
        print("🎉 Basic endpoints are working!")
        print("✅ IndentationError fixed")
        print("✅ Flask routes registered")
        print("✅ Application is responding")
    else:
        print("❌ Some endpoints failed.")

if __name__ == "__main__":
    main()