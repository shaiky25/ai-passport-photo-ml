#!/usr/bin/env python3
"""
Test the enhanced photo processing system against the 24 gold standard passport photos
used to create the learned_profile.json. This validates our system against government-approved images.
"""

import sys
import os
import json
import glob
sys.path.append('backend')

from enhancement.face_detection import FaceDetectionPipeline
from enhancement.intelligent_cropping import IntelligentCropper
from PIL import Image
import numpy as np
from datetime import datetime

def load_gold_standard_images():
    """Load the 24 gold standard passport photos"""
    # Look for gold standard images in common locations
    possible_paths = [
        'backend/gold_standard_images/',
        'backend/training_data/',
        'backend/sample_photos/',
        'gold_standard_images/',
        'training_data/',
        'sample_photos/'
    ]
    
    gold_images = []
    
    for base_path in possible_paths:
        if os.path.exists(base_path):
            # Look for common image formats
            patterns = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
            for pattern in patterns:
                images = glob.glob(os.path.join(base_path, pattern))
                gold_images.extend(images)
    
    # Also check if we have the learned profile to understand what images were used
    profile_path = 'backend/learned_profile.json'
    if os.path.exists(profile_path):
        with open(profile_path, 'r') as f:
            profile = json.load(f)
            print(f"📊 Learned profile based on {profile['sample_size']} approved passport photos")
            print(f"🎯 Target standards:")
            print(f"   Head height ratio: {profile['mean']['head_height_ratio']:.3f} ± {profile['std_dev']['head_height_ratio']:.3f}")
            print(f"   Face center X: {profile['mean']['face_center_x_ratio']:.3f} ± {profile['std_dev']['face_center_x_ratio']:.3f}")
            print(f"   Head top Y: {profile['mean']['head_top_y_ratio']:.3f} ± {profile['std_dev']['head_top_y_ratio']:.3f}")
    
    return sorted(list(set(gold_images)))  # Remove duplicates and sort

def analyze_image_quality(image_path, face_detector, intelligent_cropper):
    """Analyze a single image and return comprehensive metrics"""
    try:
        # Load image
        img = Image.open(image_path).convert('RGB')
        width, height = img.size
        img_array = np.array(img)
        
        # Face detection
        face_result = face_detector.detect_faces(img_array)
        
        if not face_result.primary_face:
            return {
                'image': os.path.basename(image_path),
                'status': 'NO_FACE_DETECTED',
                'face_detected': False,
                'error': 'No face detected'
            }
        
        face_data = face_result.primary_face
        
        # ICAO eye validation
        icao_compliance = None
        if face_data.eye_positions:
            icao_compliance = face_detector.validate_eye_compliance_icao(face_data, (height, width))
        
        # Intelligent cropping analysis
        cropping_analysis = intelligent_cropper.analyze_cropping_needs(img, face_data)
        
        # Calculate quality metrics
        x, y, w, h = face_data.bounding_box
        face_center_x = (x + w/2) / width
        face_center_y = (y + h/2) / height
        head_height_ratio = h / height
        
        # Distance from government standards
        target_head_height = intelligent_cropper.target_head_height_ratio
        target_center_x = intelligent_cropper.target_face_center_x_ratio
        
        head_height_deviation = abs(head_height_ratio - target_head_height)
        center_x_deviation = abs(face_center_x - target_center_x)
        
        return {
            'image': os.path.basename(image_path),
            'status': 'SUCCESS',
            'face_detected': True,
            'dimensions': {'width': width, 'height': height},
            'face_metrics': {
                'confidence': face_data.confidence,
                'face_size_ratio': face_data.face_size_ratio,
                'head_height_ratio': head_height_ratio,
                'face_center_x': face_center_x,
                'face_center_y': face_center_y,
                'bounding_box': face_data.bounding_box
            },
            'government_compliance': {
                'compliance_score': cropping_analysis['compliance_score'],
                'head_height_deviation': head_height_deviation,
                'center_x_deviation': center_x_deviation,
                'needs_cropping': cropping_analysis['needs_cropping'],
                'needs_reframing': cropping_analysis['needs_reframing']
            },
            'icao_eyes': {
                'eyes_detected': icao_compliance.eyes_detected if icao_compliance else False,
                'eye_level_valid': icao_compliance.eye_level_valid if icao_compliance else False,
                'eye_distance_valid': icao_compliance.eye_distance_valid if icao_compliance else False,
                'eye_symmetry_valid': icao_compliance.eye_symmetry_valid if icao_compliance else False,
                'eye_visibility_valid': icao_compliance.eye_visibility_valid if icao_compliance else False,
                'icao_compliant': icao_compliance.icao_eye_compliance if icao_compliance else False
            }
        }
        
    except Exception as e:
        return {
            'image': os.path.basename(image_path),
            'status': 'ERROR',
            'face_detected': False,
            'error': str(e)
        }

def test_gold_standard_images():
    """Test our system against gold standard passport photos"""
    
    print("🏆 GOLD STANDARD PASSPORT PHOTO ANALYSIS")
    print("=" * 80)
    print("Testing our enhanced processing system against government-approved passport photos")
    print()
    
    # Initialize components
    face_detector = FaceDetectionPipeline()
    intelligent_cropper = IntelligentCropper()
    
    # Load gold standard images
    gold_images = load_gold_standard_images()
    
    if not gold_images:
        print("❌ No gold standard images found!")
        print("📁 Please place government-approved passport photos in one of these directories:")
        print("   - backend/gold_standard_images/")
        print("   - backend/training_data/")
        print("   - backend/sample_photos/")
        return
    
    print(f"📸 Found {len(gold_images)} gold standard images")
    print()
    
    # Analyze each image
    results = []
    successful_analyses = 0
    
    for i, img_path in enumerate(gold_images, 1):
        print(f"📸 [{i}/{len(gold_images)}] Analyzing: {os.path.basename(img_path)}")
        
        result = analyze_image_quality(img_path, face_detector, intelligent_cropper)
        results.append(result)
        
        if result['status'] == 'SUCCESS':
            successful_analyses += 1
            metrics = result['face_metrics']
            compliance = result['government_compliance']
            icao = result['icao_eyes']
            
            print(f"   ✅ Face: {metrics['confidence']:.1%} confidence, {metrics['face_size_ratio']:.1%} of image")
            print(f"   📊 Compliance: {compliance['compliance_score']:.1%}")
            print(f"   👁️  ICAO Eyes: {'✅' if icao['icao_compliant'] else '❌'}")
            print(f"   🎯 Deviations: Head±{compliance['head_height_deviation']:.3f}, Center±{compliance['center_x_deviation']:.3f}")
        else:
            print(f"   ❌ {result['status']}: {result.get('error', 'Unknown error')}")
        
        print()
    
    # Generate comprehensive report
    print("📊 GOLD STANDARD ANALYSIS REPORT")
    print("=" * 80)
    
    if successful_analyses == 0:
        print("❌ No successful analyses - system may have issues")
        return
    
    # Calculate statistics for successful analyses
    successful_results = [r for r in results if r['status'] == 'SUCCESS']
    
    # Face detection statistics
    face_confidences = [r['face_metrics']['confidence'] for r in successful_results]
    face_size_ratios = [r['face_metrics']['face_size_ratio'] for r in successful_results]
    compliance_scores = [r['government_compliance']['compliance_score'] for r in successful_results]
    
    # ICAO compliance statistics
    icao_compliant = sum(1 for r in successful_results if r['icao_eyes']['icao_compliant'])
    eyes_detected = sum(1 for r in successful_results if r['icao_eyes']['eyes_detected'])
    
    # Government standard deviations
    head_deviations = [r['government_compliance']['head_height_deviation'] for r in successful_results]
    center_deviations = [r['government_compliance']['center_x_deviation'] for r in successful_results]
    
    print(f"📈 SYSTEM PERFORMANCE ON GOLD STANDARD IMAGES:")
    print(f"   📸 Images processed: {successful_analyses}/{len(gold_images)} ({successful_analyses/len(gold_images):.1%})")
    print(f"   🎯 Average face confidence: {np.mean(face_confidences):.1%}")
    print(f"   📏 Average face size ratio: {np.mean(face_size_ratios):.1%}")
    print(f"   🏛️  Average compliance score: {np.mean(compliance_scores):.1%}")
    print()
    
    print(f"👁️  ICAO EYE VALIDATION PERFORMANCE:")
    print(f"   👀 Eyes detected: {eyes_detected}/{successful_analyses} ({eyes_detected/successful_analyses:.1%})")
    print(f"   ✅ ICAO compliant: {icao_compliant}/{successful_analyses} ({icao_compliant/successful_analyses:.1%})")
    print()
    
    print(f"📐 GOVERNMENT STANDARD DEVIATIONS:")
    print(f"   📏 Head height deviation: {np.mean(head_deviations):.3f} ± {np.std(head_deviations):.3f}")
    print(f"   🎯 Center X deviation: {np.mean(center_deviations):.3f} ± {np.std(center_deviations):.3f}")
    print()
    
    # Quality assessment
    high_compliance = sum(1 for score in compliance_scores if score >= 0.8)
    medium_compliance = sum(1 for score in compliance_scores if 0.6 <= score < 0.8)
    low_compliance = sum(1 for score in compliance_scores if score < 0.6)
    
    print(f"🏆 QUALITY DISTRIBUTION:")
    print(f"   🥇 High compliance (≥80%): {high_compliance}/{successful_analyses} ({high_compliance/successful_analyses:.1%})")
    print(f"   🥈 Medium compliance (60-80%): {medium_compliance}/{successful_analyses} ({medium_compliance/successful_analyses:.1%})")
    print(f"   🥉 Low compliance (<60%): {low_compliance}/{successful_analyses} ({low_compliance/successful_analyses:.1%})")
    print()
    
    # Recommendations
    print("💡 SYSTEM ASSESSMENT:")
    avg_compliance = np.mean(compliance_scores)
    icao_pass_rate = icao_compliant / successful_analyses
    
    if avg_compliance >= 0.8 and icao_pass_rate >= 0.8:
        print("   ✅ EXCELLENT: System performs very well on gold standard images")
    elif avg_compliance >= 0.7 and icao_pass_rate >= 0.7:
        print("   ✅ GOOD: System performs well with minor room for improvement")
    elif avg_compliance >= 0.6 and icao_pass_rate >= 0.6:
        print("   ⚠️  FAIR: System needs improvement to match gold standard quality")
    else:
        print("   ❌ POOR: System requires significant improvements")
    
    print()
    print("📁 Detailed results saved for further analysis")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"gold_standard_analysis_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'total_images': len(gold_images),
            'successful_analyses': successful_analyses,
            'summary_statistics': {
                'avg_face_confidence': float(np.mean(face_confidences)),
                'avg_face_size_ratio': float(np.mean(face_size_ratios)),
                'avg_compliance_score': float(np.mean(compliance_scores)),
                'icao_pass_rate': float(icao_pass_rate),
                'avg_head_deviation': float(np.mean(head_deviations)),
                'avg_center_deviation': float(np.mean(center_deviations))
            },
            'detailed_results': results
        }, f, indent=2)
    
    print(f"💾 Results saved to: {results_file}")

if __name__ == "__main__":
    test_gold_standard_images()