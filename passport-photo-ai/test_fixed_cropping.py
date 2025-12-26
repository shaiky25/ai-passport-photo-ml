#!/usr/bin/env python3
"""
Test script to verify the fixed government-compliant cropping
"""

import requests
import json
import os

def test_cropping():
    """Test the fixed cropping implementation"""
    
    # Test with a real test image
    test_image_path = "backend/test_images/sample_image_1.jpg"  # Using different test image
    
    if not os.path.exists(test_image_path):
        print("❌ Test image not found. Please provide a test image.")
        return
    
    # Test the API
    url = "http://127.0.0.1:5000/api/full-workflow"
    
    print("🔍 Testing fixed cropping implementation...")
    
    try:
        # Upload the file
        with open(test_image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'use_learned_profile': 'true',
                'remove_bg': 'false',
                'remove_watermark': 'false'
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ API Response received")
            print(f"Success: {result.get('success', False)}")
            print(f"Feasible: {result.get('feasible', False)}")
            print(f"Message: {result.get('message', 'No message')}")
            
            # Check face detection results
            if 'analysis' in result and 'face_detection' in result['analysis']:
                face_data = result['analysis']['face_detection']
                print(f"\n📊 Face Detection Results:")
                print(f"  Faces detected: {face_data.get('faces_detected', 0)}")
                print(f"  Valid: {face_data.get('valid', False)}")
                print(f"  Head height %: {face_data.get('head_height_percent', 0)}")
                print(f"  Head height valid: {face_data.get('head_height_valid', False)}")
                print(f"  Face area %: {face_data.get('face_area_percent', 0)}")
                print(f"  Horizontally centered: {face_data.get('horizontally_centered', False)}")
                
                if 'government_compliance' in face_data:
                    gov_data = face_data['government_compliance']
                    print(f"\n🏛️ Government Compliance:")
                    print(f"  Cropping method: {gov_data.get('cropping_method', 'unknown')}")
                    print(f"  Face height ratio: {gov_data.get('face_height_ratio', 0)}")
                    print(f"  Meets 70-80% requirement: {gov_data.get('meets_70_80_requirement', False)}")
                
                if 'face_bbox' in face_data:
                    bbox = face_data['face_bbox']
                    print(f"\n📦 Face Bounding Box:")
                    print(f"  Position: ({bbox.get('x', 0)}, {bbox.get('y', 0)})")
                    print(f"  Size: {bbox.get('width', 0)}x{bbox.get('height', 0)}")
            
            # Check if processed image is present
            if 'processed_image' in result and result['processed_image']:
                print(f"\n✅ Processed image generated (length: {len(result['processed_image'])} chars)")
                
                # Save the processed image for verification
                try:
                    import base64
                    processed_image_data = base64.b64decode(result['processed_image'])
                    output_path = 'test_output_sample1_cropping.jpg'
                    with open(output_path, 'wb') as f:
                        f.write(processed_image_data)
                    print(f"✅ Processed image saved as '{output_path}'")
                    print("🔍 Please check the output image to verify cropping is working correctly")
                except Exception as e:
                    print(f"❌ Error saving processed image: {e}")
            else:
                print("❌ No processed image in response")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_cropping()