#!/usr/bin/env python3
"""
Test the web API using real images from backend/test_images/
This will help us debug the intelligent cropping issues
"""

import requests
import base64
import json
import os
from PIL import Image
import io

def prepare_image_for_testing(image_path):
    """Prepare image for testing by ensuring it meets minimum resolution requirements"""
    
    img = Image.open(image_path)
    width, height = img.size
    
    # Check if image meets minimum resolution (400x400)
    if width >= 400 and height >= 400:
        return img, image_path
    
    # Resize image to meet minimum requirements while maintaining aspect ratio
    min_size = 600  # Use 600 to be safe
    
    # Calculate new size maintaining aspect ratio
    if width > height:
        new_width = min_size
        new_height = int((height * min_size) / width)
    else:
        new_height = min_size
        new_width = int((width * min_size) / height)
    
    # Ensure both dimensions are at least min_size
    if new_width < min_size:
        new_width = min_size
    if new_height < min_size:
        new_height = min_size
    
    # Resize image
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Save temporary resized image
    temp_path = f"temp_resized_{os.path.basename(image_path)}"
    resized_img.save(temp_path, quality=95)
    
    print(f"📏 Resized {img.size} → {resized_img.size} to meet minimum resolution")
    
    return resized_img, temp_path

def test_api_with_image(image_path, api_url="http://localhost:5001/api/full-workflow"):
    """Test the API with a specific image"""
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return None
    
    print(f"\n📸 TESTING: {os.path.basename(image_path)}")
    print("-" * 60)
    
    # Prepare image for testing (resize if needed)
    img, test_path = prepare_image_for_testing(image_path)
    print(f"📐 Test image size: {img.size}")
    print(f"📊 Test image mode: {img.mode}")
    
    temp_file_created = test_path != image_path
    
    try:
        # Prepare the request
        with open(test_path, 'rb') as f:
            files = {'image': f}
            data = {
                'remove_background': 'true',  # Test with background removal
                'use_learned_profile': 'true'
            }
            
            print(f"🔗 Calling API: {api_url}")
            response = requests.post(api_url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ API call successful!")
            print(f"🎯 Success: {result.get('success', False)}")
            print(f"⏱️  Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"✂️  Intelligent cropping used: {result.get('intelligent_cropping_used', False)}")
            
            # Print full response for debugging
            if not result.get('success', False):
                print(f"⚠️  API returned success=False")
                print(f"📄 Full response: {json.dumps(result, indent=2)}")
            
            # Face detection analysis
            analysis = result.get('analysis')
            if analysis is None:
                print("❌ No analysis data in response")
                return result
                
            face_detection = analysis.get('face_detection', {})
            if face_detection:
                print(f"\n👤 FACE DETECTION:")
                print(f"   Faces detected: {face_detection.get('faces_detected', 0)}")
                print(f"   Valid: {face_detection.get('valid', False)}")
                print(f"   Confidence: {face_detection.get('confidence', 0):.1%}")
                print(f"   Head height: {face_detection.get('head_height_percent', 0):.1%}")
                print(f"   Eyes detected: {face_detection.get('eyes_detected', 0)}")
                
                if face_detection.get('error'):
                    print(f"   ⚠️  Error: {face_detection['error']}")
            
            # AI Analysis
            ai_analysis = analysis.get('ai_analysis', {})
            if ai_analysis:
                print(f"\n🤖 AI ANALYSIS:")
                print(f"   Compliant: {ai_analysis.get('compliant', False)}")
                issues = ai_analysis.get('issues', [])
                if issues:
                    print(f"   Issues: {len(issues)}")
                    for issue in issues:
                        print(f"     • {issue}")
                
                # Intelligent cropping info
                cropping_info = ai_analysis.get('intelligent_cropping', {})
                if cropping_info:
                    print(f"\n✂️  INTELLIGENT CROPPING:")
                    print(f"   Analysis performed: {cropping_info.get('analysis_performed', False)}")
                    print(f"   Cropping applied: {cropping_info.get('cropping_applied', False)}")
                    
                    if cropping_info.get('compliance_score') is not None:
                        print(f"   Compliance score: {cropping_info['compliance_score']:.1%}")
                    
                    if cropping_info.get('actions_taken'):
                        print(f"   Actions taken: {', '.join(cropping_info['actions_taken'])}")
                    
                    if cropping_info.get('reason'):
                        print(f"   Reason: {cropping_info['reason']}")
            
            # Save processed image
            if result.get('processed_image'):
                try:
                    processed_data = base64.b64decode(result['processed_image'])
                    processed_img = Image.open(io.BytesIO(processed_data))
                    
                    output_name = f"api_test_result_{os.path.basename(image_path)}"
                    processed_img.save(output_name, quality=95)
                    
                    print(f"\n💾 PROCESSED IMAGE:")
                    print(f"   Size: {processed_img.size}")
                    print(f"   Mode: {processed_img.mode}")
                    print(f"   Saved as: {output_name}")
                    
                    # Compare sizes
                    size_change = (processed_img.width * processed_img.height) / (img.width * img.height)
                    print(f"   Size change: {size_change:.2f}x")
                    
                except Exception as e:
                    print(f"❌ Failed to save processed image: {e}")
            
            return result
            
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing image: {e}")
        return None
    finally:
        # Clean up temporary resized file if created
        if temp_file_created and os.path.exists(test_path):
            os.remove(test_path)

def main():
    """Test all images in backend/test_images/"""
    
    print("🧪 TESTING WEB API WITH REAL IMAGES")
    print("=" * 80)
    
    # Test images
    test_images = [
        'backend/test_images/faiz.png',
        'backend/test_images/sample_image_1.jpg', 
        'backend/test_images/sample_image_2.jpg',
        'backend/test_images/faiz_with_glasses.png'
    ]
    
    results = []
    
    for img_path in test_images:
        result = test_api_with_image(img_path)
        if result:
            results.append({
                'image': os.path.basename(img_path),
                'success': result.get('success', False),
                'processing_time': result.get('processing_time', 0),
                'intelligent_cropping_used': result.get('intelligent_cropping_used', False),
                'face_valid': (result.get('analysis', {}) or {}).get('face_detection', {}).get('valid', False) if result.get('analysis') else False,
                'ai_compliant': (result.get('analysis', {}) or {}).get('ai_analysis', {}).get('compliant', False) if result.get('analysis') else False
            })
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 80)
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        cropping = "✂️" if result['intelligent_cropping_used'] else "➖"
        face = "👤" if result['face_valid'] else "❌"
        ai = "🤖" if result['ai_compliant'] else "⚠️"
        
        print(f"{status} {result['image']}")
        print(f"   {cropping} Cropping | {face} Face | {ai} AI | ⏱️ {result['processing_time']:.1f}s")
    
    print(f"\n✅ Testing completed! Check api_test_result_*.jpg files for processed images.")

if __name__ == "__main__":
    main()