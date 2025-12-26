#!/usr/bin/env python3

import requests

def test_backend_status():
    """Test if the backend is responding"""
    
    base_url = 'http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com'
    
    # Test root endpoint
    try:
        print("Testing root endpoint...")
        response = requests.get(base_url, timeout=10)
        print(f"Root status: {response.status_code}")
        print(f"Root response: {response.text[:200]}...")
    except Exception as e:
        print(f"Root endpoint failed: {e}")
    
    # Test API root
    try:
        print("\nTesting API root...")
        response = requests.get(f"{base_url}/api", timeout=10)
        print(f"API root status: {response.status_code}")
        print(f"API root response: {response.text[:200]}...")
    except Exception as e:
        print(f"API root failed: {e}")
    
    # Test health endpoint if it exists
    try:
        print("\nTesting health endpoint...")
        response = requests.get(f"{base_url}/api/health", timeout=10)
        print(f"Health status: {response.status_code}")
        print(f"Health response: {response.text[:200]}...")
    except Exception as e:
        print(f"Health endpoint failed: {e}")
    
    # Test full-workflow endpoint with GET (should return method not allowed)
    try:
        print("\nTesting full-workflow endpoint with GET...")
        response = requests.get(f"{base_url}/api/full-workflow", timeout=10)
        print(f"Full-workflow GET status: {response.status_code}")
        print(f"Full-workflow GET response: {response.text[:200]}...")
    except Exception as e:
        print(f"Full-workflow GET failed: {e}")

if __name__ == "__main__":
    test_backend_status()