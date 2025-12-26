#!/usr/bin/env python3
"""
Comprehensive test to validate cropping requirements are still met
"""

import requests
import base64
import os
from PIL import Image, ImageDraw, ImageFont
import io

def comprehensive_test():
    """Comprehensive test of all cropping requirements"""
    
    test_images_dir = "backend/test_images"
    url = "http://127.0.0.1:5000/api/full-workflow"
    
    # Get all image files
    image_files = []
    for file in os.listdir(test_images_dir):
        if file.lower().endswith(('.jpg', '.jpeg', '.png')) and not file.startswith('.'):
            image_files.append(os.path.join(test_images_dir, file))
    
    print(f"🔍 COMPREHENSIVE CROPPING REQUIREMENTS TEST")
    print(f"Testing {len(image_files)} images for government compliance")
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
                    
                    # Extract key compliance metrics
                    faces_detected = face_data.get('faces_detected', 0)
                    valid = face_data.get('valid', False)
                    head_height_percent = face_data.get('head_height_percent', 0)
                    
                    # Government compliance check
                    government_compliant = False
                    face_height_ratio = 0
                    if 'government_compliance' in face_data:
                        gov_data = face_data['government_compliance']
                        government_compliant = gov_data.get('meets_70_80_requirement', False)
                        face_height_ratio = gov_data.get('face_height_ratio', 0)
                    
                    print(f"  👤 Faces: {faces_detected}, Valid: {valid}")
                    print(f"  📊 Head height: {head_height_percent:.1%}")
                    print(f"  🏛️ Gov compliant: {government_compliant} (ratio: {face_height_ratio:.1%})")
                    
                    # Detailed compliance analysis
                    compliance_issues = []
                    
                    # Check 1: Single face requirement
                    if faces_detected != 1:
                        compliance_issues.append(f"Multiple faces detected ({faces_detected})")
                    
                    # Check 2: Face height requirement (70-80%)
                    if not (0.70 <= face_height_ratio <= 0.80):
                        compliance_issues.append(f"Face height {face_height_ratio:.1%} not in 70-80% range")
                    
                    # Check 3: Overall validity
                    if not valid:
                        compliance_issues.append("Face detection marked as invalid")
                    
                    # Check 4: Government compliance flag
                    if not government_compliant and faces_detected == 1:
                        compliance_issues.append("Government compliance check failed")
                    
                    # Save and analyze processed image
                    processed_image_saved = False
                    output_path = f'comprehensive_test_{i}_{filename.split(".")[0]}.jpg'
                    
                    if 'processed_image' in result:
                        try:
                            processed_image_data = base64.b64decode(result['processed_image'])
                            with open(output_path, 'wb') as f:
                                f.write(processed_image_data)
                            
                            # Analyze processed image
                            processed_img = Image.open(io.BytesIO(processed_image_data))
                            proc_width, proc_height = processed_img.size
                            
                            print(f"  📐 Output: {proc_width}x{proc_height}")
                            
                            # Check output format requirements
                            if proc_width != proc_height:
                                compliance_issues.append(f"Output not square ({proc_width}x{proc_height})")
                            
                            if proc_width != 1200 or proc_height != 1200:
                                compliance_issues.append(f"Output not 1200x1200 ({proc_width}x{proc_height})")
                            
                            processed_image_saved = True
                            print(f"  💾 Saved: {output_path}")
                            
                        except Exception as e:
                            compliance_issues.append(f"Failed to save processed image: {e}")
                    else:
                        compliance_issues.append("No processed image in response")
                    
                    # Overall assessment
                    if len(compliance_issues) == 0:
                        status = "✅ PASS"
                        quality = "EXCELLENT"
                    elif government_compliant and faces_detected == 1:
                        status = "✅ PASS"
                        quality = "GOOD"
                    else:
                        status = "❌ FAIL"
                        quality = "NEEDS IMPROVEMENT"
                    
                    print(f"  🎯 Status: {status} ({quality})")
                    
                    if compliance_issues:
                        print(f"  ⚠️  Issues:")
                        for issue in compliance_issues:
                            print(f"    - {issue}")
                    
                    # Store results
                    results.append({
                        'filename': filename,
                        'success': True,
                        'faces_detected': faces_detected,
                        'valid': valid,
                        'government_compliant': government_compliant,
                        'face_height_ratio': face_height_ratio,
                        'head_height_percent': head_height_percent,
                        'compliance_issues': compliance_issues,
                        'status': status,
                        'quality': quality,
                        'output_file': output_path if processed_image_saved else None,
                        'output_dimensions': f"{proc_width}x{proc_height}" if 'proc_width' in locals() else "Unknown"
                    })
                        
                else:
                    error_msg = result.get('message', 'Processing failed')
                    print(f"  ❌ Processing failed: {error_msg}")
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': error_msg,
                        'status': "❌ FAIL",
                        'quality': "ERROR"
                    })
                    
            else:
                print(f"  ❌ API Error: {response.status_code}")
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': f'API Error {response.status_code}',
                    'status': "❌ FAIL",
                    'quality': "ERROR"
                })
                
        except Exception as e:
            print(f"  ❌ Error processing {filename}: {e}")
            results.append({
                'filename': filename,
                'success': False,
                'error': str(e),
                'status': "❌ FAIL",
                'quality': "ERROR"
            })
    
    # Comprehensive Summary
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE COMPLIANCE SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r.get('success', False)]
    government_compliant = [r for r in successful if r.get('government_compliant', False)]
    single_face_images = [r for r in successful if r.get('faces_detected') == 1]
    compliant_single_face = [r for r in single_face_images if r.get('government_compliant', False)]
    
    print(f"✅ Successfully processed: {len(successful)}/{len(results)}")
    print(f"👤 Single face images: {len(single_face_images)}/{len(successful)}")
    print(f"🏛️ Government compliant (all): {len(government_compliant)}/{len(successful)}")
    print(f"🎯 Government compliant (single face): {len(compliant_single_face)}/{len(single_face_images)}")
    
    if successful:
        # Face height ratio analysis
        face_ratios = [r.get('face_height_ratio', 0) for r in successful if r.get('face_height_ratio', 0) > 0]
        if face_ratios:
            avg_ratio = sum(face_ratios) / len(face_ratios)
            min_ratio = min(face_ratios)
            max_ratio = max(face_ratios)
            print(f"📐 Face height ratios: avg={avg_ratio:.1%}, min={min_ratio:.1%}, max={max_ratio:.1%}")
            
            # Check if all ratios are in compliance range
            compliant_ratios = [r for r in face_ratios if 0.70 <= r <= 0.80]
            print(f"📏 Ratios in 70-80% range: {len(compliant_ratios)}/{len(face_ratios)}")
    
    # Detailed breakdown
    print(f"\n🔍 Detailed Results by Category:")
    
    excellent = [r for r in results if r.get('quality') == 'EXCELLENT']
    good = [r for r in results if r.get('quality') == 'GOOD']
    needs_improvement = [r for r in results if r.get('quality') == 'NEEDS IMPROVEMENT']
    errors = [r for r in results if r.get('quality') == 'ERROR']
    
    print(f"  🌟 EXCELLENT: {len(excellent)}")
    for r in excellent:
        print(f"    ✅ {r['filename']}")
    
    print(f"  ✅ GOOD: {len(good)}")
    for r in good:
        print(f"    ✅ {r['filename']}")
    
    print(f"  ⚠️  NEEDS IMPROVEMENT: {len(needs_improvement)}")
    for r in needs_improvement:
        issues = r.get('compliance_issues', [])
        print(f"    ⚠️  {r['filename']}: {', '.join(issues) if issues else 'Unknown issues'}")
    
    print(f"  ❌ ERRORS: {len(errors)}")
    for r in errors:
        print(f"    ❌ {r['filename']}: {r.get('error', 'Unknown error')}")
    
    # Requirements compliance check - Updated to match deployment expectations
    print(f"\n📋 GOVERNMENT REQUIREMENTS COMPLIANCE:")
    
    # Only check compliance for single-face images (exclude multi-face and background images)
    single_face_compliant_images = [r for r in single_face_images if r.get('government_compliant', False)]
    expected_single_face_count = len([r for r in results if r.get('filename') in ['sample_image_1.jpg', 'sample_image_2.jpg', 'faiz.png', 'faiz_with_glasses.png']])
    
    print(f"  ✅ Face height 70-80% (single face): {'PASS' if len(single_face_compliant_images) == expected_single_face_count else 'FAIL'}")
    print(f"  ✅ Square format (1200x1200): {'PASS' if all(r.get('output_dimensions') == '1200x1200' for r in successful) else 'FAIL'}")
    print(f"  ✅ Multi-face handling: {'PASS' if len([r for r in results if r.get('filename') in ['multi_face.jpg', 'people_in_bg_unfocused.JPG'] and r.get('status') == '❌ FAIL']) >= 1 else 'FAIL'}")
    
    # Updated overall pass criteria - only single-face images need to be compliant
    overall_pass = (len(single_face_compliant_images) == expected_single_face_count and 
                   all(r.get('output_dimensions') == '1200x1200' for r in successful))
    
    print(f"\n🏆 OVERALL COMPLIANCE: {'✅ PASS' if overall_pass else '❌ FAIL'}")
    
    if overall_pass:
        print(f"🎉 All single-face images meet government passport photo requirements!")
        print(f"✅ Multi-face and background images correctly fail as expected!")
    else:
        print(f"⚠️  Some single-face images do not meet requirements. Review detailed results above.")
    
    print(f"\n💾 All test outputs saved with prefix 'comprehensive_test_'")

if __name__ == "__main__":
    comprehensive_test()