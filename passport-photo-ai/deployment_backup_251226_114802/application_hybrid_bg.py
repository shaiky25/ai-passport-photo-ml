"""
Hybrid Passport Photo Application with Robust Background Removal
Uses rembg if available, falls back to lightweight OpenCV-based removal
Optimized for AWS Elastic Beanstalk deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import io
import base64
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging
import random
import string

# Try to import OpenCV (required)
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
    print("✅ OpenCV loaded successfully")
except ImportError as e:
    print(f"❌ OpenCV not available: {e}")
    OPENCV_AVAILABLE = False

# Try to import rembg (preferred but optional)
try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
    print("✅ rembg available - using AI background removal")
except ImportError as e:
    print(f"⚠️  rembg not available: {e}")
    print("   Will use lightweight OpenCV-based background removal")
    REMBG_AVAILABLE = False

# Import our lightweight background removal
if OPENCV_AVAILABLE:
    from lightweight_bg_removal import LightweightBackgroundRemover

# HEIC image support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORT = True
    print("✅ HEIC support enabled")
except ImportError:
    HEIC_SUPPORT = False
    print("⚠️  HEIC support not available")

load_dotenv()

application = Flask(__name__)
CORS(application, origins=['*'], methods=['GET', 'POST', 'OPTIONS'], allow_headers=['Content-Type'])
application.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Initialize background removal
if REMBG_AVAILABLE:
    try:
        # Use lightweight u2netp model for better Elastic Beanstalk compatibility
        rembg_session = new_session('u2netp')
        print("✅ rembg u2netp session initialized")
        BG_REMOVAL_METHOD = "rembg"
    except Exception as e:
        print(f"⚠️  rembg session creation failed: {e}")
        REMBG_AVAILABLE = False
        BG_REMOVAL_METHOD = "opencv"
else:
    BG_REMOVAL_METHOD = "opencv"

if not REMBG_AVAILABLE and OPENCV_AVAILABLE:
    lightweight_remover = LightweightBackgroundRemover()
    print("✅ Lightweight OpenCV background remover initialized")

print(f"🎯 Background removal method: {BG_REMOVAL_METHOD}")


class PassportPhotoProcessor:
    """Enhanced passport photo processor with robust background removal"""
    
    def __init__(self):
        self.target_size = (1200, 1200)
        self.face_cascade = None
        self._load_face_detector()
    
    def _load_face_detector(self):
        """Load OpenCV face detector"""
        if OPENCV_AVAILABLE:
            try:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                if self.face_cascade.empty():
                    self.face_cascade = None
                    print("⚠️  Face cascade not loaded")
                else:
                    print("✅ Face detector loaded")
            except Exception as e:
                print(f"⚠️  Face detector loading failed: {e}")
    
    def remove_background_robust(self, image: Image.Image) -> Image.Image:
        """
        Robust background removal with fallback options
        """
        if REMBG_AVAILABLE:
            return self._remove_background_rembg(image)
        elif OPENCV_AVAILABLE:
            return self._remove_background_opencv(image)
        else:
            print("⚠️  No background removal available, returning original")
            return image
    
    def _remove_background_rembg(self, image: Image.Image) -> Image.Image:
        """Remove background using rembg"""
        try:
            # Convert PIL to bytes
            img_buffer = io.BytesIO()
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            input_data = img_buffer.getvalue()
            
            # Remove background
            output_data = remove(input_data, session=rembg_session)
            
            # Convert back to PIL
            result_img = Image.open(io.BytesIO(output_data))
            
            # Convert RGBA to RGB with white background
            if result_img.mode == 'RGBA':
                white_bg = Image.new('RGB', result_img.size, (255, 255, 255))
                white_bg.paste(result_img, mask=result_img.split()[-1])
                return white_bg
            else:
                return result_img.convert('RGB')
                
        except Exception as e:
            print(f"⚠️  rembg failed, falling back to OpenCV: {e}")
            return self._remove_background_opencv(image)
    
    def _remove_background_opencv(self, image: Image.Image) -> Image.Image:
        """Remove background using lightweight OpenCV method"""
        try:
            return lightweight_remover.remove_background_adaptive(image)
        except Exception as e:
            print(f"⚠️  OpenCV background removal failed: {e}")
            return image.convert('RGB') if image.mode != 'RGB' else image
    
    def detect_faces(self, image: Image.Image) -> list:
        """Detect faces in the image"""
        if not self.face_cascade:
            return []
        
        try:
            # Convert PIL to OpenCV
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
            )
            
            return faces.tolist() if len(faces) > 0 else []
            
        except Exception as e:
            print(f"Face detection error: {e}")
            return []
    
    def add_watermark(self, image: Image.Image) -> Image.Image:
        """Add watermark to the image"""
        try:
            # Create a copy to avoid modifying original
            watermarked = image.copy()
            draw = ImageDraw.Draw(watermarked)
            
            # Calculate watermark size and position
            width, height = watermarked.size
            watermark_text = "AI Enhanced"
            
            # Use larger font size (3x larger)
            font_size = max(24, width // 25)  # Minimum 24px, scales with image
            
            try:
                # Try to use a system font
                from PIL import ImageFont
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position in bottom right with margin
            margin = 20
            x = width - text_width - margin
            y = height - text_height - margin
            
            # Draw white text with black outline for visibility
            outline_width = 2
            for adj_x in range(-outline_width, outline_width + 1):
                for adj_y in range(-outline_width, outline_width + 1):
                    if adj_x != 0 or adj_y != 0:
                        draw.text((x + adj_x, y + adj_y), watermark_text, 
                                font=font, fill=(0, 0, 0))  # Black outline
            
            # Draw main white text
            draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255))
            
            return watermarked
            
        except Exception as e:
            print(f"Watermark error: {e}")
            return image
    
    def process_passport_photo(self, image: Image.Image, remove_bg: bool = True) -> dict:
        """Process passport photo with all enhancements"""
        try:
            start_time = datetime.now()
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to target size
            image = image.resize(self.target_size, Image.Resampling.LANCZOS)
            
            # Detect faces
            faces = self.detect_faces(image)
            face_count = len(faces)
            
            # Check for multiple faces
            if face_count > 1:
                return {
                    'success': False,
                    'error': f'Image must contain only 1 person. Multiple faces detected with high confidence.',
                    'face_count': face_count,
                    'processing_time': (datetime.now() - start_time).total_seconds()
                }
            elif face_count == 0:
                return {
                    'success': False,
                    'error': 'No faces detected in the image. Please ensure the image contains a clear face.',
                    'face_count': 0,
                    'processing_time': (datetime.now() - start_time).total_seconds()
                }
            
            # Remove background if requested
            if remove_bg:
                image = self.remove_background_robust(image)
            
            # Add watermark
            image = self.add_watermark(image)
            
            # Convert to base64
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'image': img_base64,
                'face_count': face_count,
                'background_removed': remove_bg,
                'bg_removal_method': BG_REMOVAL_METHOD,
                'processing_time': processing_time,
                'message': f'Photo processed successfully using {BG_REMOVAL_METHOD} background removal'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Processing failed: {str(e)}',
                'processing_time': (datetime.now() - start_time).total_seconds()
            }


# Initialize processor
processor = PassportPhotoProcessor()


@application.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'opencv_available': OPENCV_AVAILABLE,
        'rembg_available': REMBG_AVAILABLE,
        'heic_support': HEIC_SUPPORT,
        'bg_removal_method': BG_REMOVAL_METHOD,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@application.route('/api/process', methods=['POST'])
def process_image():
    """Process passport photo"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # Get options
        remove_bg = request.form.get('remove_background', 'true').lower() == 'true'
        
        # Load and process image
        image = Image.open(file.stream)
        result = processor.process_passport_photo(image, remove_bg=remove_bg)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@application.route('/api/test-bg-removal', methods=['GET'])
def test_background_removal():
    """Test background removal capabilities"""
    try:
        # Create a simple test image
        test_img = Image.new('RGB', (400, 400), 'lightblue')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_img)
        draw.ellipse([150, 100, 250, 300], fill='brown')
        
        # Test background removal
        if REMBG_AVAILABLE:
            result = processor._remove_background_rembg(test_img)
            method = "rembg"
        elif OPENCV_AVAILABLE:
            result = processor._remove_background_opencv(test_img)
            method = "opencv"
        else:
            return jsonify({'error': 'No background removal available'}), 500
        
        # Convert result to base64
        img_buffer = io.BytesIO()
        result.save(img_buffer, format='JPEG', quality=95)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'method': method,
            'test_image': img_base64,
            'message': f'Background removal test successful using {method}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Test failed: {str(e)}'}), 500


if __name__ == '__main__':
    print(f"🚀 Starting Passport Photo AI Server")
    print(f"   Background removal: {BG_REMOVAL_METHOD}")
    print(f"   OpenCV: {'✅' if OPENCV_AVAILABLE else '❌'}")
    print(f"   rembg: {'✅' if REMBG_AVAILABLE else '❌'}")
    print(f"   HEIC: {'✅' if HEIC_SUPPORT else '❌'}")
    application.run(debug=False, host='0.0.0.0', port=5001)  # Use port 5001 to avoid conflicts