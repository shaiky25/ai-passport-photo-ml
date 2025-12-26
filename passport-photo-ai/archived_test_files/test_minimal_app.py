#!/usr/bin/env python3

# Test if the application can be imported and routes are registered
import sys
sys.path.append('backend')

try:
    print("Importing application...")
    import application
    print("✅ Application imported successfully")
    
    print("\nChecking Flask app...")
    app = application.application
    print(f"Flask app: {app}")
    
    print("\nChecking routes...")
    for rule in app.url_map.iter_rules():
        print(f"Route: {rule.rule} -> {rule.endpoint}")
    
    print("\nTesting app context...")
    with app.test_client() as client:
        response = client.get('/')
        print(f"Root endpoint status: {response.status_code}")
        print(f"Root endpoint response: {response.get_json()}")
        
        # Test API endpoint
        response = client.get('/api/health')
        print(f"Health endpoint status: {response.status_code}")
        print(f"Health endpoint response: {response.get_json()}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()