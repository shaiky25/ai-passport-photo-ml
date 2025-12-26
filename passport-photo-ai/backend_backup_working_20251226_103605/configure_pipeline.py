#!/usr/bin/env python3
"""
Pipeline Configuration Script
Easily toggle pipeline features on/off for debugging and testing
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from application import processor

def show_current_config():
    """Display current pipeline configuration"""
    print("\n🔧 Current Pipeline Configuration:")
    print("=" * 50)
    print(f"Enhanced Face Detection: {'✅ ON' if processor.ENABLE_ENHANCED_FACE_DETECTION else '❌ OFF'}")
    print(f"Background Removal:      {'✅ ON' if processor.ENABLE_BACKGROUND_REMOVAL else '❌ OFF'}")
    print(f"Intelligent Cropping:    {'✅ ON' if processor.ENABLE_INTELLIGENT_CROPPING else '❌ OFF'}")
    print(f"Image Enhancement:       {'✅ ON' if processor.ENABLE_IMAGE_ENHANCEMENT else '❌ OFF'}")
    print(f"Watermark:               {'✅ ON' if processor.ENABLE_WATERMARK else '❌ OFF'}")
    print(f"Learned Profile:         {'✅ ON' if processor.ENABLE_LEARNED_PROFILE else '❌ OFF'}")
    print("=" * 50)

def toggle_flag(flag_name):
    """Toggle a specific pipeline flag"""
    flag_map = {
        'face': 'ENABLE_ENHANCED_FACE_DETECTION',
        'bg': 'ENABLE_BACKGROUND_REMOVAL',
        'crop': 'ENABLE_INTELLIGENT_CROPPING',
        'enhance': 'ENABLE_IMAGE_ENHANCEMENT',
        'watermark': 'ENABLE_WATERMARK',
        'profile': 'ENABLE_LEARNED_PROFILE'
    }
    
    if flag_name not in flag_map:
        print(f"❌ Unknown flag: {flag_name}")
        print(f"Available flags: {', '.join(flag_map.keys())}")
        return
    
    attr_name = flag_map[flag_name]
    current_value = getattr(processor, attr_name)
    new_value = not current_value
    setattr(processor, attr_name, new_value)
    
    status = "✅ ON" if new_value else "❌ OFF"
    print(f"🔄 Toggled {flag_name}: {status}")

def main():
    if len(sys.argv) == 1:
        show_current_config()
        print("\nUsage:")
        print("  python configure_pipeline.py [flag]")
        print("\nAvailable flags:")
        print("  face      - Enhanced Face Detection")
        print("  bg        - Background Removal")
        print("  crop      - Intelligent Cropping")
        print("  enhance   - Image Enhancement")
        print("  watermark - Watermark")
        print("  profile   - Learned Profile")
        print("\nExamples:")
        print("  python configure_pipeline.py bg        # Toggle background removal")
        print("  python configure_pipeline.py crop      # Toggle intelligent cropping")
        return
    
    flag_name = sys.argv[1].lower()
    
    if flag_name == 'status':
        show_current_config()
    elif flag_name == 'all-off':
        processor.ENABLE_ENHANCED_FACE_DETECTION = False
        processor.ENABLE_BACKGROUND_REMOVAL = False
        processor.ENABLE_INTELLIGENT_CROPPING = False
        processor.ENABLE_IMAGE_ENHANCEMENT = False
        processor.ENABLE_WATERMARK = False
        processor.ENABLE_LEARNED_PROFILE = False
        print("🔄 All pipeline features disabled")
        show_current_config()
    elif flag_name == 'all-on':
        processor.ENABLE_ENHANCED_FACE_DETECTION = True
        processor.ENABLE_BACKGROUND_REMOVAL = True
        processor.ENABLE_INTELLIGENT_CROPPING = True
        processor.ENABLE_IMAGE_ENHANCEMENT = True
        processor.ENABLE_WATERMARK = True
        processor.ENABLE_LEARNED_PROFILE = True
        print("🔄 All pipeline features enabled")
        show_current_config()
    else:
        toggle_flag(flag_name)
        show_current_config()

if __name__ == "__main__":
    main()