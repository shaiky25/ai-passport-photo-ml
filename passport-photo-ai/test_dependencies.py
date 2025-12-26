#!/usr/bin/env python3
"""
Test script to verify all dependencies are working correctly
"""

def test_core_dependencies():
    """Test core Flask and image processing dependencies"""
    print("🔍 Testing core dependencies...")
    
    try:
        import flask
        print(f"  ✅ Flask: {flask.__version__}")
    except ImportError as e:
        print(f"  ❌ Flask: {e}")
        return False
    
    try:
        import PIL
        print(f"  ✅ Pillow: {PIL.__version__}")
    except ImportError as e:
        print(f"  ❌ Pillow: {e}")
        return False
    
    try:
        import numpy as np
        print(f"  ✅ NumPy: {np.__version__}")
    except ImportError as e:
        print(f"  ❌ NumPy: {e}")
        return False
    
    return True

def test_opencv_dependencies():
    """Test OpenCV and computer vision dependencies"""
    print("\n🔍 Testing OpenCV dependencies...")
    
    try:
        import cv2
        print(f"  ✅ OpenCV: {cv2.__version__}")
        
        # Test basic OpenCV functionality
        test_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if test_cascade.empty():
            print(f"  ❌ OpenCV face cascade not loaded")
            return False
        else:
            print(f"  ✅ OpenCV face cascade loaded")
            
    except ImportError as e:
        print(f"  ❌ OpenCV: {e}")
        return False
    
    return True

def test_mediapipe_dependencies():
    """Test MediaPipe dependencies"""
    print("\n🔍 Testing MediaPipe dependencies...")
    
    try:
        import mediapipe as mp
        print(f"  ✅ MediaPipe: {mp.__version__}")
        
        # Test MediaPipe face detection initialization
        mp_face_detection = mp.solutions.face_detection
        detector = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.3)
        print(f"  ✅ MediaPipe face detection initialized")
        detector.close()
        
    except ImportError as e:
        print(f"  ❌ MediaPipe: {e}")
        return False
    except Exception as e:
        print(f"  ❌ MediaPipe initialization: {e}")
        return False
    
    return True

def test_enhanced_processing():
    """Test enhanced processing modules"""
    print("\n🔍 Testing enhanced processing modules...")
    
    try:
        from backend.enhancement.face_detection import FaceDetectionPipeline
        print(f"  ✅ FaceDetectionPipeline imported")
        
        # Test initialization
        pipeline = FaceDetectionPipeline()
        print(f"  ✅ FaceDetectionPipeline initialized")
        
    except ImportError as e:
        print(f"  ❌ Enhanced processing import: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Enhanced processing initialization: {e}")
        return False
    
    return True

def test_aws_dependencies():
    """Test AWS dependencies"""
    print("\n🔍 Testing AWS dependencies...")
    
    try:
        import boto3
        print(f"  ✅ Boto3: {boto3.__version__}")
    except ImportError as e:
        print(f"  ❌ Boto3: {e}")
        return False
    
    return True

def test_optional_dependencies():
    """Test optional dependencies"""
    print("\n🔍 Testing optional dependencies...")
    
    try:
        import rembg
        print(f"  ✅ rembg available")
    except ImportError as e:
        print(f"  ⚠️ rembg: {e} (optional)")
    
    try:
        from pillow_heif import register_heif_opener
        print(f"  ✅ pillow-heif available")
    except ImportError as e:
        print(f"  ⚠️ pillow-heif: {e} (optional)")
    
    try:
        import hypothesis
        print(f"  ✅ hypothesis: {hypothesis.__version__}")
    except ImportError as e:
        print(f"  ⚠️ hypothesis: {e} (optional)")
    
    return True

def main():
    """Run all dependency tests"""
    print("🚀 DEPENDENCY TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_core_dependencies,
        test_opencv_dependencies,
        test_mediapipe_dependencies,
        test_enhanced_processing,
        test_aws_dependencies,
        test_optional_dependencies
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results[:5] if r)  # Only count critical tests
    total_critical = 5
    
    print(f"Critical Tests: {passed}/{total_critical}")
    
    if passed == total_critical:
        print("🎉 All critical dependencies are working!")
        print("✅ Ready for deployment")
        return True
    else:
        print("⚠️ Some critical dependencies failed")
        print("❌ NOT ready for deployment")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)