#!/usr/bin/env python3
"""
Comprehensive test of the intelligent photo processing workflow with real person images.
This demonstrates the complete system: face detection -> eye validation -> intelligent cropping -> quality assessment.
"""

import sys
import os
sys.path.append('backend')

from enhancement.face_detection import FaceDetectionPipeline
from enhancement.intelligent_cropping import IntelligentCropper
from PIL import Image
import numpy as np

def test_complete_workflow():
    """Test the complete intelligent photo processing workflow"""
    
    print("🧪 COMPREHENSIVE REAL PERSON PHOTO PROCESSING TEST")
    print("=" * 80)
    print("Testing: Face Detection → Eye Validation → Intelligent Cropping → Quality Assessment")
    print()
    
    # Initialize components
    face_detector = FaceDetectionPipeline()
    intelligent_cropper = IntelligentCropper()
    
    # Test images
    test_images = [
        'backend/test_images/faiz.png',
        'backend/test_images/sample_image_1.jpg', 
        'backend/test_images/sample_image_2.jpg'
    ]
    
    results = []
    
    for img_path in test_images:
        if not os.path.exists(img_path):
            print(f"❌ Image not found: {img_path}")
            continue
            
        print(f"📸 PROCESSING: {os.path.basename(img_path)}")
        print("-" * 60)
        
        # Load image
        img = Image.open(img_path).convert('RGB')
        width, height = img.size
        print(f"📐 Original dimensions: {width}x{height}")
        
        # STEP 1: Face Detection
        print("\n🔍 STEP 1: Face Detection")
        img_array = np.array(img)
        face_result = face_detector.detect_faces(img_array)
        
        if not face_result.primary_face:
            print("   ❌ No face detected - cannot process")
            continue
            
        face_data = face_result.primary_face
        print(f"   ✅ Face detected with {face_data.confidence:.1%} confidence")
        print(f"   📏 Face size: {face_data.face_size_ratio:.1%} of image height")
        print(f"   👥 Multiple faces: {'Yes' if face_result.multiple_faces_detected else 'No'}")
        
        # STEP 2: Eye Validation (ICAO Standards)
        print("\n👁️  STEP 2: Eye Validation (ICAO Standards)")
        if face_data.eye_positions:
            icao_compliance = face_detector.validate_eye_compliance_icao(face_data, (height, width))
            print(f"   👀 Eyes detected: {'Yes' if icao_compliance.eyes_detected else 'No'}")
            print(f"   📐 Eye level valid: {'Yes' if icao_compliance.eye_level_valid else 'No'}")
            print(f"   📏 Eye distance valid: {'Yes' if icao_compliance.eye_distance_valid else 'No'}")
            print(f"   ⚖️  Eye symmetry valid: {'Yes' if icao_compliance.eye_symmetry_valid else 'No'}")
            print(f"   👁️  Eye visibility valid: {'Yes' if icao_compliance.eye_visibility_valid else 'No'}")
            print(f"   🏆 ICAO compliance: {'✅ PASS' if icao_compliance.icao_eye_compliance else '❌ FAIL'}")
            
            if icao_compliance.eye_validation_details:
                details = icao_compliance.eye_validation_details
                print(f"   📊 Eye level ratio: {details.get('eye_level_ratio', 0):.3f}")
                print(f"   📊 Eye distance ratio: {details.get('eye_distance_ratio', 0):.3f}")
        else:
            print("   ❌ No eye positions detected")
            icao_compliance = None
        
        # STEP 3: Intelligent Cropping Analysis
        print("\n🎯 STEP 3: Intelligent Cropping Analysis")
        analysis = intelligent_cropper.analyze_cropping_needs(img, face_data)
        
        print(f"   📊 Current compliance score: {analysis['compliance_score']:.1%}")
        print(f"   🎯 Target face ratio: {analysis['target_metrics']['head_height_ratio']:.1%}")
        print(f"   📏 Current face ratio: {analysis['current_metrics']['head_height_ratio']:.1%}")
        print(f"   🏛️  Using government standards: {'Yes' if analysis.get('using_government_standards') else 'No'}")
        
        # Decision logic
        face_too_small = face_data.face_size_ratio < 0.6
        compliance_low = analysis['compliance_score'] < 0.8
        needs_processing = analysis['needs_cropping'] or analysis['needs_reframing']
        significant_deviation = abs(face_data.face_size_ratio - intelligent_cropper.target_head_height_ratio) > 0.2
        
        should_crop = face_too_small or (compliance_low and needs_processing) or significant_deviation
        
        print(f"   🔍 Face too small (<60%): {'Yes' if face_too_small else 'No'}")
        print(f"   📉 Compliance low (<80%): {'Yes' if compliance_low else 'No'}")
        print(f"   ⚙️  Needs processing: {'Yes' if needs_processing else 'No'}")
        print(f"   📐 Significant deviation: {'Yes' if significant_deviation else 'No'}")
        print(f"   ➡️  Decision: {'APPLY CROPPING' if should_crop else 'NO CROPPING NEEDED'}")
        
        # STEP 4: Apply Intelligent Cropping (if needed)
        if should_crop:
            print("\n✂️  STEP 4: Applying Intelligent Cropping")
            
            try:
                cropped_img, updated_face_data, processing_info = intelligent_cropper.intelligent_crop_and_reframe(img, face_data)
                
                print(f"   🔧 Actions taken: {', '.join(processing_info['actions_taken'])}")
                print(f"   📐 New dimensions: {cropped_img.size[0]}x{cropped_img.size[1]}")
                print(f"   📏 New face ratio: {updated_face_data.face_size_ratio:.1%}")
                
                # Verify improvement
                new_analysis = intelligent_cropper.analyze_cropping_needs(cropped_img, updated_face_data)
                improvement = new_analysis['compliance_score'] - analysis['compliance_score']
                
                print(f"   📊 New compliance: {new_analysis['compliance_score']:.1%}")
                print(f"   📈 Improvement: {improvement:+.1%}")
                
                # Add diagnostic information for limited improvement
                if improvement <= 0.1:
                    print(f"   🔍 Diagnostic info:")
                    print(f"      • Face confidence: {face_data.confidence:.1%}")
                    print(f"      • Original face size: {face_data.face_size_ratio:.1%} of image height")
                    print(f"      • Target face size: {intelligent_cropper.target_head_height_ratio:.1%}")
                    
                    if face_data.confidence < 0.8:
                        print(f"      ⚠️  Low face confidence may indicate visibility issues")
                    if face_data.face_size_ratio < 0.3:
                        print(f"      ⚠️  Very small face in original image limits improvement")
                    if not face_data.eye_positions:
                        print(f"      ⚠️  Eye positions not clearly detected")
                
                # Status determination - focus on the final result quality and user guidance
                if new_analysis['compliance_score'] >= 0.8:
                    status = "🏆 PASSPORT READY"
                    status_color = "✅"
                elif improvement > 0.2:
                    status = "🚀 MAJOR IMPROVEMENT"
                    status_color = "✅"
                elif improvement > 0.1:
                    status = "📈 GOOD IMPROVEMENT"
                    status_color = "✅"
                elif improvement > 0:
                    status = "📊 MINOR IMPROVEMENT"
                    status_color = "✅"
                elif new_analysis['compliance_score'] >= 0.5:
                    status = "✂️  INTELLIGENTLY CROPPED (Consider better photo)"
                    status_color = "⚠️"
                else:
                    status = "⚠️  LIMITED IMPROVEMENT (Try different photo)"
                    status_color = "⚠️"
                
                print(f"   🎯 Result: {status_color} {status}")
                
                # Save processed image
                output_name = f"final_processed_{os.path.basename(img_path)}"
                cropped_img.save(output_name, quality=95)
                print(f"   💾 Saved: {output_name}")
                
                final_img = cropped_img
                final_face_data = updated_face_data
                final_compliance = new_analysis['compliance_score']
                
            except Exception as e:
                print(f"   ❌ Cropping failed: {e}")
                final_img = img
                final_face_data = face_data
                final_compliance = analysis['compliance_score']
                improvement = 0
                status = "❌ PROCESSING FAILED"
        else:
            print("\n✅ STEP 4: No cropping needed - image already suitable")
            final_img = img
            final_face_data = face_data
            final_compliance = analysis['compliance_score']
            improvement = 0
            
            if final_compliance >= 0.8:
                status = "🏆 ALREADY PASSPORT READY"
            elif final_compliance >= 0.5:
                status = "✅ GOOD QUALITY IMAGE"
            else:
                status = "⚠️  MANUAL REVIEW NEEDED"
        
        # STEP 5: Final Quality Assessment
        print("\n📋 STEP 5: Final Quality Assessment")
        print(f"   📊 Final compliance score: {final_compliance:.1%}")
        print(f"   📏 Final face ratio: {final_face_data.face_size_ratio:.1%}")
        print(f"   🎯 Overall status: {status}")
        
        # Store results
        results.append({
            'image': os.path.basename(img_path),
            'original_compliance': analysis['compliance_score'],
            'final_compliance': final_compliance,
            'improvement': improvement,
            'status': status,
            'cropping_applied': should_crop,
            'icao_compliant': icao_compliance.icao_eye_compliance if icao_compliance else False
        })
        
        print()
    
    # FINAL SUMMARY
    print("📊 FINAL PROCESSING SUMMARY")
    print("=" * 80)
    
    for result in results:
        print(f"📸 {result['image']}:")
        print(f"   📊 Compliance: {result['original_compliance']:.1%} → {result['final_compliance']:.1%} ({result['improvement']:+.1%})")
        print(f"   ✂️  Cropping: {'Applied' if result['cropping_applied'] else 'Not needed'}")
        print(f"   👁️  ICAO Eyes: {'✅ Pass' if result['icao_compliant'] else '❌ Fail'}")
        print(f"   🎯 Status: {result['status']}")
        print()
    
    # Statistics
    total_images = len(results)
    cropped_images = sum(1 for r in results if r['cropping_applied'])
    passport_ready = sum(1 for r in results if r['final_compliance'] >= 0.8)
    icao_compliant = sum(1 for r in results if r['icao_compliant'])
    
    print("📈 PROCESSING STATISTICS:")
    print(f"   📸 Total images processed: {total_images}")
    print(f"   ✂️  Images cropped: {cropped_images}/{total_images} ({cropped_images/total_images:.1%})")
    print(f"   🏆 Passport ready: {passport_ready}/{total_images} ({passport_ready/total_images:.1%})")
    print(f"   👁️  ICAO eye compliant: {icao_compliant}/{total_images} ({icao_compliant/total_images:.1%})")
    
    print("\n✅ COMPREHENSIVE WORKFLOW TEST COMPLETED!")
    print("📁 Check final_processed_*.jpg files for results")

if __name__ == "__main__":
    test_complete_workflow()