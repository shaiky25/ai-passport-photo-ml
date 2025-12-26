#!/usr/bin/env python3
"""
Debug script to check enhanced processing availability
"""

import sys
import os
sys.path.append('backend')

print("🔍 ENHANCED PROCESSING DIAGNOSTIC")
print("=" * 50)

# Test 1: Check MediaPipe import
print("\n1. Testing MediaPipe import...")
try:
    import mediapipe as mp
    print("   ✅ MediaPipe imported successfully")
    print(f"   📦 MediaPipe version: {mp.__version__}")
except ImportError as e:
    print(f"   ❌ MediaPipe import failed: {e}")

# Test 2: Check enhanced modules import
print("\n2. Testing enhanced modules import...")
try:
    from enhancement.face_detection import FaceDetectionPipeline
    from enhancement.intelligent_cropping import IntelligentCropper
    print("   ✅ Enhanced modules imported successfully")
except ImportError as e:
    print(f"   ❌ Enhanced modules import failed: {e}")

# Test 3: Test initialization
print("\n3. Testing enhanced processing initialization...")
try:
    face_detector = FaceDetectionPipeline()
    intelligent_cropper = IntelligentCropper()
    print("   ✅ Enhanced processing initialized successfully")
    
    # Test 4: Test with sample image
    print("\n4. Testing with sample image...")
    from PIL import Image
    import numpy as np
    
    img_path = 'backend/test_images/sample_image_2.jpg'
    if os.path.exists(img_path):
        img = Image.open(img_path).convert('RGB')
        img_array = np.array(img)
        
        face_result = face_detector.detect_faces(img_array)
        print(f"   📸 Image: {img.size}")
        print(f"   👤 Faces detected: {len(face_result.faces)}")
        
        if face_result.primary_face:
            face_data = face_result.primary_face
            print(f"   🎯 Primary face confidence: {face_data.confidence:.1%}")
            print(f"   📏 Face size ratio: {face_data.face_size_ratio:.1%}")
            print(f"   👁️  Eye positions detected: {'Yes' if face_data.eye_positions else 'No'}")
            
            if face_data.eye_positions:
                icao_compliance = face_detector.validate_eye_compliance_icao(face_data, (img.height, img.width))
                print(f"   🏆 ICAO eye compliance: {'✅ PASS' if icao_compliance.icao_eye_compliance else '❌ FAIL'}")
        else:
            print("   ❌ No primary face detected")
    else:
        print(f"   ⚠️  Sample image not found: {img_path}")
        
except Exception as e:
    print(f"   ❌ Enhanced processing initialization failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check application processor
print("\n5. Testing application processor...")
try:
    from application import processor, ENHANCED_PROCESSING_AVAILABLE
    print(f"   📊 ENHANCED_PROCESSING_AVAILABLE: {ENHANCED_PROCESSING_AVAILABLE}")
    print(f"   🔧 Processor has enhanced_face_detector: {hasattr(processor, 'enhanced_face_detector')}")
    
    if hasattr(processor, 'enhanced_face_detector'):
        print(f"   🎯 Enhanced face detector is: {processor.enhanced_face_detector}")
        print(f"   ✅ Enhanced face detector available: {processor.enhanced_face_detector is not None}")
    
except Exception as e:
    print(f"   ❌ Application processor check failed: {e}")

print("\n✅ DIAGNOSTIC COMPLETED!")