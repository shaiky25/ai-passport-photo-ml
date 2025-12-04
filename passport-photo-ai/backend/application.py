"""
Complete Passport Photo Validator and Processor with AI Integration
Includes: AI Vision Analysis, Face Detection, Background Removal, REST API
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageEnhance, ImageOps
import cv2
import numpy as np
import io
import base64
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pillow_heif import register_heif_opener
from rembg import remove
import logging

# Register HEIF opener with Pillow
register_heif_opener()

load_dotenv()

# --- Analytics Setup ---
# This setup creates a simple JSON logger.
# Each line in the log file will be a self-contained JSON object.
analytics_logger = logging.getLogger('analytics')
analytics_logger.setLevel(logging.INFO)
if not os.path.exists('../passport-photo-ai/backend/logs'):
    os.makedirs('../passport-photo-ai/backend/logs')
file_handler = logging.FileHandler('../passport-photo-ai/backend/logs/analytics.log')
# We use a simple formatter that just logs the message itself.
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
analytics_logger.addHandler(file_handler)


application = Flask(__name__)
CORS(application)
application.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

def convert_heic_to_jpeg(heic_file_path):
    """
    Converts a HEIC file to a high-quality JPEG file.
    
    Quality settings optimized for passport photos:
    - JPEG quality: 95% (high quality, minimal compression artifacts)
    - Subsampling: 4:4:4 (no chroma subsampling for maximum color fidelity)
    - Optimize: True (optimal Huffman coding for smaller file size without quality loss)
    
    Args:
        heic_file_path: Path to the HEIC file
        
    Returns:
        Path to the converted JPEG file, or None if conversion fails
    """
    try:
        # pillow-heif registers itself with Pillow, so we can use Image.open directly
        image = Image.open(heic_file_path)
        
        # Convert to RGB if necessary (HEIC might be in different color space)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Generate output path
        jpeg_file_path = heic_file_path.rsplit('.', 1)[0] + '.jpg'
        
        # Save as high-quality JPEG with optimal settings
        image.save(
            jpeg_file_path, 
            "JPEG",
            quality=95,           # High quality (1-100, default is 75)
            subsampling=0,        # 4:4:4 subsampling (no chroma subsampling)
            optimize=True         # Optimize Huffman coding
        )
        
        return jpeg_file_path
    except Exception as e:
        print(f"Could not convert HEIC file: {e}")
        return None

class PassportPhotoProcessor:
    # US Passport photo specifications
    PASSPORT_SIZE_PIXELS = (600, 600)
    HEAD_HEIGHT_MIN = 0.50
    HEAD_HEIGHT_MAX = 0.69
    GOLDEN_SAMPLE_PATH = "golden_sample.png"
    LEARNED_PROFILE_PATH = "../passport-photo-ai/backend/learned_profile.json"
    
    def __init__(self):
        # Load OpenCV's pre-trained face detector (Haar Cascade)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Also load eye cascade for eye detection
        eye_cascade_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
        
        self.golden_sample = self.load_golden_sample()
        self.learned_profile = self.load_learned_profile()

    def load_golden_sample(self):
        """Loads the golden sample image."""
        try:
            if os.path.exists(self.GOLDEN_SAMPLE_PATH):
                return Image.open(self.GOLDEN_SAMPLE_PATH).convert("RGBA")
        except Exception as e:
            print(f"Could not load golden sample: {e}")
        return None

    def load_learned_profile(self):
        """Loads the learned geometric profile."""
        if os.path.exists(self.LEARNED_PROFILE_PATH):
            try:
                with open(self.LEARNED_PROFILE_PATH, 'r') as f:
                    profile = json.load(f)
                    print("Successfully loaded learned profile.")
                    return profile
            except Exception as e:
                print(f"Warning: Could not load or parse learned_profile.json: {e}")
        print("Info: No learned profile found. Falling back to default cropping rules.")
        return None
    
    def detect_face_and_features(self, image_path):
        """
        Detect face, eyes, and analyze positioning using OpenCV Haar Cascades.
        Optimized to resize large images before detection for performance.
        """
        img = cv2.imread(image_path)
        if img is None:
            return None

        original_height, original_width = img.shape[:2]
        
        # Performance optimization: resize image if it's very large
        max_dim = 1024
        if max(original_height, original_width) > max_dim:
            scale_ratio = max_dim / max(original_height, original_width)
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            img_resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        else:
            img_resized = img
            scale_ratio = 1.0

        # Convert to grayscale for Haar Cascade detection
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using Haar Cascade
        # Parameters tuned for passport photos: scaleFactor, minNeighbors, minSize
        # Higher minNeighbors (5) reduces false positives, larger minSize for quality faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) == 0:
            return {"faces_detected": 0, "valid": False, "error": "No face detected"}
        
        if len(faces) > 1:
            return {"faces_detected": len(faces), "valid": False, "error": "Multiple faces detected"}
        
        # Get the single detected face
        x, y, w, h = faces[0]
        
        # Detect eyes within the face region for additional validation
        face_roi_gray = gray[y:y+h, x:x+w]
        eyes = self.eye_cascade.detectMultiScale(face_roi_gray, scaleFactor=1.1, minNeighbors=3)
        eyes_detected = len(eyes)
        
        # Scale bounding box back to original image dimensions
        if scale_ratio != 1.0:
            x = int(x / scale_ratio)
            y = int(y / scale_ratio)
            w = int(w / scale_ratio)
            h = int(h / scale_ratio)

        face_center_x = x + w / 2
        face_center_y = y + h / 2
        head_height_percent = h / original_height
        horizontal_center = abs(face_center_x - original_width / 2) / original_width < 0.3
        
        return {
            "faces_detected": 1, "valid": True,
            "face_bbox": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
            "eyes_detected": eyes_detected,
            "head_height_percent": round(head_height_percent, 2),
            "head_height_valid": bool(self.HEAD_HEIGHT_MIN <= head_height_percent <= self.HEAD_HEIGHT_MAX),
            "horizontally_centered": bool(horizontal_center),
            "image_dimensions": {"width": int(original_width), "height": int(original_height)}
        }

    async def analyze_with_ai(self, image_path):
        """Use Claude AI to validate passport photo requirements."""
        try:
            with open(image_path, "rb") as img_file:
                image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
            
            ext = os.path.splitext(image_path)[1].lower()
            media_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}
            media_type = media_types.get(ext, 'image/jpeg')
            
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            
            prompt_text = """
Analyze this photo for U.S. visa photo compliance. Respond in JSON format only.
Rules:
1. Background: Must be plain white or off-white.
2. View/Expression: Full-face view, neutral expression, both eyes open.
3. Head Coverings: No hats/head coverings unless for religious purposes (full face visible, no shadows).
4. Eyeglasses: Not allowed.
5. Other Items: No headphones or similar devices.
6. Lighting: Well-lit, no shadows on the face.
7. Quality: In color, clear, not a copy/scan.

Respond with this structure:
{
  "compliant": true/false,
  "issues": ["List of specific issues found."],
  "analysis_details": {
    "background_ok": true/false, "expression_neutral": true/false, "eyes_open": true/false,
    "no_eyeglasses": true/false, "no_head_covering_issue": true/false, "lighting_ok": true/false
  }
}
"""
            message = client.messages.create(
                model="claude-3-sonnet-20240229", max_tokens=1024,
                messages=[{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}}, {"type": "text", "text": prompt_text}]}]
            )
            
            response_text = message.content[0].text
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            
            return {"success": True, "ai_analysis": json.loads(response_text.strip())}
        except Exception as e:
            return {"success": False, "error": str(e), "ai_analysis": None}
    
    def remove_background(self, img):
        """Remove background using rembg."""
        try:
            foreground = remove(img)
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(foreground, (0, 0), foreground)
            return background
        except Exception as e:
            print(f"Rembg background removal error: {e}. Returning original image.")
            return img
    
    def process_to_passport_photo(self, image_path, face_bbox, remove_bg=False):
        """
        Convert image to passport photo with intelligent cropping.
        
        Quality optimizations:
        - Uses LANCZOS resampling for highest quality resizing
        - Preserves maximum resolution until final resize
        - Applies minimal enhancement (brightness 1.05, contrast 1.1)
        - Outputs at 300 DPI with 95% JPEG quality
        - Uses 4:4:4 chroma subsampling (no color degradation)
        """
        img = Image.open(image_path)
        
        # Only resize if image is very large (preserve quality)
        # Increased threshold from 1200 to 2400 to preserve more detail
        max_dimension = max(img.size)
        if max_dimension > 2400:
            # Use high-quality LANCZOS resampling
            img.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
        
        if img.mode != 'RGB': 
            img = img.convert('RGB')
        
        if remove_bg: 
            img = self.remove_background(img)

        if face_bbox:
            fx, fy, fw, fh = face_bbox['x'], face_bbox['y'], face_bbox['width'], face_bbox['height']
            orig_w, orig_h = Image.open(image_path).size
            w_ratio, h_ratio = img.size[0] / orig_w, img.size[1] / orig_h
            fx, fy, fw, fh = int(fx*w_ratio), int(fy*h_ratio), int(fw*w_ratio), int(fh*h_ratio)

            if self.learned_profile:
                profile = self.learned_profile['mean']
                head_top_y = max(0, fy - (fh * 0.15))
                head_h = (fy + fh) - head_top_y
                crop_size = int(head_h / profile['head_height_ratio'])
                face_center_x = fx + fw / 2
                crop_x = int(face_center_x - (crop_size * profile['face_center_x_ratio']))
                crop_y = int(head_top_y - (crop_size * profile['head_top_y_ratio']))
            else:
                target_ratio = 0.60
                crop_size = int(fh / target_ratio)
                face_center_x = fx + fw / 2
                crop_x = int(face_center_x - crop_size / 2)
                crop_y = int(fy - (crop_size * 0.18))

            crop_x = max(0, crop_x)
            crop_y = max(0, crop_y)
            if crop_x + crop_size > img.size[0]: crop_size = img.size[0] - crop_x
            if crop_y + crop_size > img.size[1]: crop_size = img.size[1] - crop_y
            crop_size = min(crop_size, img.size[0] - crop_x, img.size[1] - crop_y)
            img_cropped = img.crop((crop_x, crop_y, crop_x + crop_size, crop_y + crop_size))
        else:
            size = min(img.size)
            left, top = (img.size[0] - size) // 2, (img.size[1] - size) // 2
            img_cropped = img.crop((left, top, left + size, top + size))
        
        # Resize to exact passport dimensions using highest quality resampling
        img_passport = img_cropped.resize(self.PASSPORT_SIZE_PIXELS, Image.Resampling.LANCZOS)
        
        # Apply subtle enhancements (government standards require natural appearance)
        enhancer = ImageEnhance.Brightness(img_passport)
        img_passport = enhancer.enhance(1.05)  # Slight brightness boost
        
        enhancer = ImageEnhance.Contrast(img_passport)
        img_passport = enhancer.enhance(1.1)   # Slight contrast boost
        
        # Save with maximum quality settings for government submission
        buffer = io.BytesIO()
        img_passport.save(
            buffer, 
            format='JPEG',
            quality=95,           # High quality (government standard)
            dpi=(300, 300),       # 300 DPI required for passport photos
            subsampling=0,        # 4:4:4 chroma subsampling (no color loss)
            optimize=True         # Optimize encoding without quality loss
        )
        buffer.seek(0)
        return buffer

# Initialize processor
processor = PassportPhotoProcessor()

# --- API Endpoints ---

@application.route('/api/log-event', methods=['POST'])
def log_event():
    """Log a structured analytics event from the frontend."""
    event_data = request.json
    # Add a server-side timestamp for accuracy
    event_data['timestamp'] = datetime.now(timezone.utc).isoformat()
    # Log the entire JSON object as a single line
    analytics_logger.info(json.dumps(event_data))
    return jsonify({"status": "logged"}), 200

@application.route('/api/full-workflow', methods=['POST'])
def full_workflow():
    """Main endpoint for processing and analyzing a photo."""
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    temp_path = f"temp_{datetime.now().timestamp()}"
    file.save(temp_path)

    if file.filename.lower().endswith('.heic'):
        new_path = convert_heic_to_jpeg(temp_path)
        if not new_path:
            return jsonify({"error": "Could not convert HEIC image"}), 500
        os.remove(temp_path)
        temp_path = new_path
    
    try:
        face_analysis = processor.detect_face_and_features(temp_path)
        
        use_ai = request.form.get('use_ai', 'false').lower() == 'true'
        ai_result = None
        if use_ai:
            import asyncio
            ai_result = asyncio.run(processor.analyze_with_ai(temp_path))
        
        img = Image.open(temp_path)
        width, height = img.size
        
        if not (width >= 600 and height >= 600):
            return jsonify({
                "success": False, "feasible": False,
                "analysis": {"face_detection": face_analysis, "ai_analysis": ai_result},
                "message": "Photo cannot be processed. Resolution is too low (must be at least 600x600 pixels)."
            })
        
        valid_face_bbox = face_analysis.get("face_bbox") if face_analysis and face_analysis.get("valid") else None
        processed_buffer = processor.process_to_passport_photo(temp_path, face_bbox=valid_face_bbox, remove_bg=request.form.get('remove_background', 'false').lower() == 'true')
        
        return jsonify({
            "success": True, "feasible": True,
            "analysis": {"face_detection": face_analysis, "ai_analysis": ai_result},
            "processed_image": base64.b64encode(processed_buffer.getvalue()).decode('utf-8'),
            "message": "Photo successfully processed. Please review analysis for compliance."
        })
        
    except Exception as e:
        print(f"An unexpected error occurred in full-workflow: {e}")
        return jsonify({
            "success": False, "feasible": False,
            "message": "An unexpected error occurred during processing. Please try again with a different image."
        }), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5000)
