#!/usr/bin/env python3
"""
Test the glasses image specifically to debug head cropping
"""

import requests
import base64
import os
from PIL import Image, ImageDraw
import io

def test_glasses_image():
    """Test the glasses image specifically"""
    
    test_image_path = "backend/test_images/faiz_with_glasses.png"
    url = "http://127.0.0.1:5000/api/full-workflow"
    
    if not os.path.exists(test_image_path):
        print("❌ Test image not found")
        return
    
    # Check original image
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
                original_face = face_data.get('original_face', {})
                
                print(f"\n📊 Face Detection Details:")
                print(f"  Original face: ({original_face.get('x', 0)}, {original_face.get('y', 0)}) size {original_face.get('width', 0)}x{original_face.get('height', 0)}")
                
                # From server logs, we know the NEW crop area is: (290, 276) to (847, 833) = 557x557
                # Face position: (465, 465) size 209x209
                # Face at 33.9% from top of cropped image
                
                crop_x, crop_y = 290, 276
                crop_w, crop_h = 557, 557
                face_x, face_y = 465, 465
                face_w, face_h = 209, 209
                
                print(f"\n📐 Cropping Analysis:")
                print(f"  Crop area: ({crop_x}, {crop_y}) to ({crop_x + crop_w}, {crop_y + crop_h})")
                print(f"  Crop size: {crop_w}x{crop_h}")
                
                # Calculate how much space above the detected face
                space_above_face = face_y - crop_y
                space_above_ratio = space_above_face / crop_h
                
                print(f"  Space above detected face: {space_above_face}px ({space_above_ratio:.1%})")
                
                # The detected face starts at y=465, crop starts at y=355
                # So we have 110px above the detected face
                # But if the person's hair/head extends higher, this might not be enough
                
                # Let's visualize this on the original image
                original_img_copy = original_img.copy().convert('RGB')  # Convert to RGB for JPEG
                draw = ImageDraw.Draw(original_img_copy)
                
                # Draw detected face (red)
                draw.rectangle([face_x, face_y, face_x + face_w, face_y + face_h], outline='red', width=3)
                
                # Draw crop area (blue)
                draw.rectangle([crop_x, crop_y, crop_x + crop_w, crop_y + crop_h], outline='blue', width=3)
                
                # Draw estimated head top (green line) - this is where we think the head starts
                estimated_head_top = face_y - (face_h * 0.5)  # Our NEW estimation (more conservative)
                draw.line([crop_x, estimated_head_top, crop_x + crop_w, estimated_head_top], fill='green', width=2)
                
                # Save annotated original
                original_img_copy.save('debug_glasses_original_annotated.jpg', quality=95)
                print(f"  💾 Annotated original saved as: debug_glasses_original_annotated.jpg")
                print(f"  🔍 Red = detected face, Blue = crop area, Green = estimated head top")
                
                # Save processed image
                if 'processed_image' in result:
                    processed_image_data = base64.b64decode(result['processed_image'])
                    with open('debug_glasses_processed.jpg', 'wb') as f:
                        f.write(processed_image_data)
                    print(f"  💾 Processed image saved as: debug_glasses_processed.jpg")
                
                # Analysis
                print(f"\n🔍 Analysis:")
                print(f"  Current estimation puts head top at y={estimated_head_top:.0f}")
                print(f"  Crop starts at y={crop_y}")
                print(f"  Headroom above estimated head: {crop_y - estimated_head_top:.0f}px")
                
                if crop_y > estimated_head_top:
                    print(f"  ⚠️  WARNING: Crop may be cutting off top of head!")
                    print(f"  💡 Suggestion: Increase headroom or adjust head estimation")
                
            else:
                print(f"❌ Processing failed: {result.get('message', 'Unknown error')}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_glasses_image()