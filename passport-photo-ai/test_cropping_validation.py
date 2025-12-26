#!/usr/bin/env python3
"""
Comprehensive test of government-compliant cropping with all test images
"""

import requests
import base64
import os
from PIL import Image, ImageDraw, ImageFont
import io

def test_all_images():
    """Test cropping with all images in test_images directory"""
    
    test_images_dir = "backend/test_images"
    url = "http://127.0.0.1:5000/api/full-workflow"
    
    # Get all image files
    image_files = []
    for file in os.listdir(test_images_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_files.append(os.path.join(test_images_dir, file))
    
    print(f"🔍 Testing {len(image_files)} images from test_images directory")
    print("=" * 80)
    
    results = []
    
    for i, test_image_path in enumerate(image_files, 1):
        filename = os.path.basename(test_image_path)
        print(f"\n📸 Test {i}/{len(image_files)}: {filename}")
        
        # Check original image dimensions
        try:
            original_img = Image.open(test_image_path)
            orig_width, orig_height = original_img.size
            print(f"  📏 Original: {orig_width}x{orig_height}")
        except Exception as e:
            print(f"  ❌ Error reading image: {e}")
            continue
        
        try:
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
                
                if result.get('success') and 'analysis' in result:
                    face_data = result['analysis']['face_detection']
                    
                    # Extract key metrics
                    faces_detected = face_data.get('faces_detected', 0)
                    valid = face_data.get('valid', False)
                    head_height_percent = face_data.get('head_height_percent', 0)
                    government_compliant = False
                    
                    if 'government_compliance' in face_data:
                        gov_data = face_data['government_compliance']
                        government_compliant = gov_data.get('meets_70_80_requirement', False)
                    
                    # Get face positioning details
                    original_face = face_data.get('original_face', {})
                    face_bbox = face_data.get('face_bbox', {})
                    
                    print(f"  👤 Faces detected: {faces_detected}")
                    print(f"  ✅ Valid: {valid}")
                    print(f"  📊 Head height: {head_height_percent:.1%}")
                    print(f"  🏛️ Government compliant: {government_compliant}")
                    
                    if original_face and face_bbox:
                        orig_face_x = original_face.get('x', 0)
                        orig_face_y = original_face.get('y', 0) 
                        orig_face_w = original_face.get('width', 0)
                        orig_face_h = original_face.get('height', 0)
                        
                        crop_x = face_bbox.get('x', 0)
                        crop_y = face_bbox.get('y', 0)
                        crop_w = face_bbox.get('width', 0)
                        crop_h = face_bbox.get('height', 0)
                        
                        # Calculate spacing analysis
                        space_above_face = orig_face_y - crop_y
                        space_above_ratio = space_above_face / crop_h if crop_h > 0 else 0
                        
                        face_bottom = orig_face_y + orig_face_h
                        crop_bottom = crop_y + crop_h
                        space_below_face = crop_bottom - face_bottom
                        space_below_ratio = space_below_face / crop_h if crop_h > 0 else 0
                        
                        print(f"  📐 Headroom: {space_above_ratio:.1%}, Shoulder space: {space_below_ratio:.1%}")
                        
                        # Evaluate quality
                        headroom_ok = 0.05 <= space_above_ratio <= 0.20
                        shoulder_ok = 0.10 <= space_below_ratio <= 0.25
                        
                        quality_score = "EXCELLENT" if (headroom_ok and shoulder_ok and government_compliant) else \
                                      "GOOD" if government_compliant else \
                                      "NEEDS IMPROVEMENT"
                        
                        print(f"  🎯 Quality: {quality_score}")
                    
                    # Save processed image
                    if 'processed_image' in result:
                        processed_image_data = base64.b64decode(result['processed_image'])
                        output_path = f'test_all_output_{i}_{filename.split(".")[0]}.jpg'
                        with open(output_path, 'wb') as f:
                            f.write(processed_image_data)
                        print(f"  💾 Saved: {output_path}")
                        
                        # Store results for summary
                        results.append({
                            'filename': filename,
                            'success': True,
                            'faces_detected': faces_detected,
                            'valid': valid,
                            'government_compliant': government_compliant,
                            'head_height_percent': head_height_percent,
                            'headroom_ratio': space_above_ratio if 'space_above_ratio' in locals() else 0,
                            'shoulder_ratio': space_below_ratio if 'space_below_ratio' in locals() else 0,
                            'quality_score': quality_score if 'quality_score' in locals() else 'UNKNOWN',
                            'output_file': output_path
                        })
                    else:
                        print(f"  ❌ No processed image in response")
                        results.append({
                            'filename': filename,
                            'success': False,
                            'error': 'No processed image'
                        })
                        
                else:
                    error_msg = result.get('message', 'Processing failed')
                    print(f"  ❌ Processing failed: {error_msg}")
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': error_msg
                    })
                    
            else:
                print(f"  ❌ API Error: {response.status_code}")
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': f'API Error {response.status_code}'
                })
                
        except Exception as e:
            print(f"  ❌ Error processing {filename}: {e}")
            results.append({
                'filename': filename,
                'success': False,
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY RESULTS")
    print("=" * 80)
    
    successful = [r for r in results if r.get('success', False)]
    government_compliant = [r for r in successful if r.get('government_compliant', False)]
    excellent_quality = [r for r in successful if r.get('quality_score') == 'EXCELLENT']
    
    print(f"✅ Successfully processed: {len(successful)}/{len(results)}")
    print(f"🏛️ Government compliant: {len(government_compliant)}/{len(successful)}")
    print(f"🎯 Excellent quality: {len(excellent_quality)}/{len(successful)}")
    
    if successful:
        avg_headroom = sum(r.get('headroom_ratio', 0) for r in successful) / len(successful)
        avg_shoulder = sum(r.get('shoulder_ratio', 0) for r in successful) / len(successful)
        print(f"📐 Average headroom: {avg_headroom:.1%}")
        print(f"📐 Average shoulder space: {avg_shoulder:.1%}")
    
    print(f"\n🔍 Detailed Results:")
    for r in results:
        if r.get('success'):
            status = "✅" if r.get('government_compliant') else "⚠️"
            print(f"  {status} {r['filename']}: {r.get('quality_score', 'UNKNOWN')} "
                  f"(H:{r.get('headroom_ratio', 0):.1%}, S:{r.get('shoulder_ratio', 0):.1%})")
        else:
            print(f"  ❌ {r['filename']}: {r.get('error', 'Unknown error')}")
    
    print(f"\n💾 All output images saved with prefix 'test_all_output_'")
    print(f"🔍 Review the images to verify head and shoulder positioning")

if __name__ == "__main__":
    test_all_images()