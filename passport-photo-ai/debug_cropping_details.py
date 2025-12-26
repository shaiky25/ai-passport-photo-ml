#!/usr/bin/env python3
"""
Debug script to analyze cropping coordinates and face positioning in detail
"""

import requests
import base64
import os
from PIL import Image, ImageDraw, ImageFont
import io

def debug_cropping():
    """Debug cropping with detailed coordinate analysis"""
    
    test_image_path = "backend/test_images/faiz.png"
    url = "http://127.0.0.1:5000/api/full-workflow"
    
    if not os.path.exists(test_image_path):
        print("❌ Test image not found")
        return
    
    print(f"🔍 Debugging cropping for: {os.path.basename(test_image_path)}")
    
    # First, let's see the original image dimensions
    original_img = Image.open(test_image_path)
    orig_width, orig_height = original_img.size
    print(f"📏 Original image: {orig_width}x{orig_height}")
    
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
                
                # Get face detection details
                face_bbox = face_data.get('face_bbox', {})
                original_face = face_data.get('original_face', {})
                
                print(f"\n📊 Face Detection Analysis:")
                print(f"  Original face: ({original_face.get('x', 0)}, {original_face.get('y', 0)}) size {original_face.get('width', 0)}x{original_face.get('height', 0)}")
                print(f"  Crop bbox: ({face_bbox.get('x', 0)}, {face_bbox.get('y', 0)}) size {face_bbox.get('width', 0)}x{face_bbox.get('height', 0)}")
                
                # Calculate what this means in terms of head/shoulder coverage
                if original_face and face_bbox:
                    orig_face_x = original_face['x']
                    orig_face_y = original_face['y'] 
                    orig_face_w = original_face['width']
                    orig_face_h = original_face['height']
                    
                    crop_x = face_bbox['x']
                    crop_y = face_bbox['y']
                    crop_w = face_bbox['width']
                    crop_h = face_bbox['height']
                    
                    # Calculate how much space is above the face (for head/hair)
                    space_above_face = orig_face_y - crop_y
                    space_above_ratio = space_above_face / crop_h if crop_h > 0 else 0
                    
                    # Calculate how much space is below the face (for shoulders)
                    face_bottom = orig_face_y + orig_face_h
                    crop_bottom = crop_y + crop_h
                    space_below_face = crop_bottom - face_bottom
                    space_below_ratio = space_below_face / crop_h if crop_h > 0 else 0
                    
                    print(f"\n📐 Cropping Analysis:")
                    print(f"  Space above face: {space_above_face}px ({space_above_ratio:.1%} of crop)")
                    print(f"  Face height: {orig_face_h}px ({orig_face_h/crop_h:.1%} of crop)")
                    print(f"  Space below face: {space_below_face}px ({space_below_ratio:.1%} of crop)")
                    
                    # Determine if this looks correct
                    if space_above_ratio < 0.05:
                        print(f"  ⚠️  WARNING: Very little headroom - top of head may be cropped")
                    elif space_above_ratio > 0.20:
                        print(f"  ⚠️  WARNING: Too much headroom - inefficient use of space")
                    else:
                        print(f"  ✅ Headroom looks appropriate")
                        
                    if space_below_ratio < 0.10:
                        print(f"  ⚠️  WARNING: Very little space below face - shoulders may be missing")
                    elif space_below_ratio > 0.25:
                        print(f"  ⚠️  WARNING: Too much space below face")
                    else:
                        print(f"  ✅ Shoulder space looks appropriate")
                
                # Save processed image with annotations
                if 'processed_image' in result:
                    processed_image_data = base64.b64decode(result['processed_image'])
                    
                    # Load processed image and add annotations
                    processed_img = Image.open(io.BytesIO(processed_image_data))
                    draw = ImageDraw.Draw(processed_img)
                    
                    # Draw face rectangle on processed image (scaled to new dimensions)
                    if original_face and face_bbox:
                        # Calculate face position in processed image
                        scale_x = processed_img.width / crop_w
                        scale_y = processed_img.height / crop_h
                        
                        face_in_processed_x = (orig_face_x - crop_x) * scale_x
                        face_in_processed_y = (orig_face_y - crop_y) * scale_y
                        face_in_processed_w = orig_face_w * scale_x
                        face_in_processed_h = orig_face_h * scale_y
                        
                        # Draw face rectangle
                        draw.rectangle([
                            face_in_processed_x, 
                            face_in_processed_y,
                            face_in_processed_x + face_in_processed_w,
                            face_in_processed_y + face_in_processed_h
                        ], outline='red', width=3)
                        
                        # Add text annotations
                        try:
                            font = ImageFont.load_default()
                        except:
                            font = None
                            
                        draw.text((10, 10), f"Face: {space_above_ratio:.0%} above, {space_below_ratio:.0%} below", 
                                fill='red', font=font)
                    
                    # Save annotated image
                    output_path = 'debug_cropping_annotated.jpg'
                    processed_img.save(output_path, quality=95)
                    print(f"\n💾 Annotated image saved as: {output_path}")
                    print(f"🔍 Red rectangle shows detected face area")
                    print(f"🔍 Check if full head and shoulders are visible")
                
            else:
                print(f"❌ Processing failed: {result.get('message', 'Unknown error')}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_cropping()