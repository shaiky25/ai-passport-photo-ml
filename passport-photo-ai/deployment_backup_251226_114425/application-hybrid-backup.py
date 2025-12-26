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
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from botocore.exceptions import ClientError

# Register HEIF opener with Pillow
register_heif_opener()

load_dotenv()

# --- Analytics Setup ---
# This setup creates a simple JSON logger.
# Each line in the log file will be a self-contained JSON object.
analytics_logger = logging.getLogger('analytics')
analytics_logger.setLevel(logging.INFO)
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = logging.FileHandler('logs/analytics.log')
# We use a simple formatter that just logs the message itself.
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
analytics_logger.addHandler(file_handler)


application = Flask(__name__)
CORS(application)
application.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize AWS SES client
ses_client = boto3.client('ses', region_name='us-east-1')

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
    LEARNED_PROFILE_PATH = "learned_profile.json"
    
    def __init__(self):
        # Load multiple OpenCV face detectors for better coverage
        cascade_base = cv2.data.haarcascades
        
        # Primary face detectors (in order of preference)
        self.face_cascades = [
            cv2.CascadeClassifier(cascade_base + 'haarcascade_frontalface_default.xml'),
            cv2.CascadeClassifier(cascade_base + 'haarcascade_frontalface_alt.xml'),
            cv2.CascadeClassifier(cascade_base + 'haarcascade_frontalface_alt2.xml'),
            cv2.CascadeClassifier(cascade_base + 'haarcascade_frontalface_alt_tree.xml'),
        ]
        
        # Keep the primary cascade for backward compatibility
        self.face_cascade = self.face_cascades[0]
        
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
        Enhanced face detection using multiple approaches and robust parameters.
        Uses Haar Cascades with multiple parameter sets and DNN face detection as fallback.
        """
        img = cv2.imread(image_path)
        if img is None:
            return {"faces_detected": 0, "valid": False, "error": "Could not load image"}

        original_height, original_width = img.shape[:2]
        
        # Performance optimization: resize image if it's very large
        max_dim = 1200  # Increased from 1024 for better detection
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
        
        # Apply multiple preprocessing techniques for better detection
        # 1. Histogram equalization to improve contrast
        gray_eq = cv2.equalizeHist(gray)
        
        # 2. Apply Gaussian blur to reduce noise
        gray_blur = cv2.GaussianBlur(gray_eq, (3, 3), 0)
        
        # 3. Try both original and processed versions
        gray_versions = [gray_blur, gray_eq, gray]
        
        # Try multiple detection approaches with different cascades and parameters
        detection_configs = [
            # More sensitive detection for clear photos
            {"scaleFactor": 1.05, "minNeighbors": 3, "minSize": (60, 60)},
            # Standard detection
            {"scaleFactor": 1.1, "minNeighbors": 4, "minSize": (80, 80)},
            # Less sensitive for difficult photos
            {"scaleFactor": 1.15, "minNeighbors": 3, "minSize": (50, 50)},
            # Very sensitive for small faces
            {"scaleFactor": 1.03, "minNeighbors": 2, "minSize": (40, 40)},
        ]
        
        faces = []
        cascade_used = None
        
        # Try each cascade with each configuration and each preprocessing version
        for cascade_idx, cascade in enumerate(self.face_cascades):
            for gray_version_idx, gray_version in enumerate(gray_versions):
                for config in detection_configs:
                    faces = cascade.detectMultiScale(
                        gray_version,
                        scaleFactor=config["scaleFactor"],
                        minNeighbors=config["minNeighbors"],
                        minSize=config["minSize"],
                        flags=cv2.CASCADE_SCALE_IMAGE
                    )
                    
                    # If we found exactly one face, use it
                    if len(faces) == 1:
                        cascade_used = cascade_idx
                        preprocessing_used = ["blur+eq", "equalized", "original"][gray_version_idx]
                        print(f"Face detected with cascade {cascade_idx}, preprocessing: {preprocessing_used}, config: {config}")
                        break
                    # If we found multiple faces, try next config (might be false positives)
                    elif len(faces) > 1:
                        print(f"Multiple faces detected with cascade {cascade_idx}, preprocessing: {['blur+eq', 'equalized', 'original'][gray_version_idx]}, config: {config}, trying next...")
                        continue
                
                # If we found a face with this preprocessing, stop trying others
                if len(faces) == 1:
                    break
            
            # If we found a face with this cascade, stop trying others
            if len(faces) == 1:
                break
        
        # If still no faces found, try with more aggressive settings
        if len(faces) == 0:
            print("No faces found with standard settings, trying aggressive detection...")
            for cascade in self.face_cascades:
                # Very aggressive settings for difficult cases
                faces = cascade.detectMultiScale(
                    gray_versions[0],  # Use best preprocessed version
                    scaleFactor=1.02,
                    minNeighbors=1,
                    minSize=(30, 30),
                    maxSize=(int(min(img_resized.shape[:2]) * 0.8), int(min(img_resized.shape[:2]) * 0.8)),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                if len(faces) > 0:
                    print(f"Face detected with aggressive settings using cascade {self.face_cascades.index(cascade)}")
                    break
        
        # If still no faces found, try DNN-based detection as fallback
        if len(faces) == 0:
            try:
                faces = self._detect_face_with_dnn(img_resized)
                if len(faces) > 0:
                    print("Face detected using DNN fallback method")
            except Exception as e:
                print(f"DNN detection failed: {e}")
        
        if len(faces) == 0:
            # Provide more detailed error information
            img_stats = {
                "dimensions": f"{original_width}x{original_height}",
                "brightness": np.mean(gray),
                "contrast": np.std(gray)
            }
            print(f"Face detection failed. Image stats: {img_stats}")
            return {
                "faces_detected": 0, 
                "valid": False, 
                "error": f"No face detected. Image: {img_stats['dimensions']}, brightness: {img_stats['brightness']:.1f}, contrast: {img_stats['contrast']:.1f}",
                "image_dimensions": {"width": int(original_width), "height": int(original_height)}
            }
        
        if len(faces) > 1:
            # If multiple faces, choose the largest one (likely the main subject)
            face_areas = [(f[2] * f[3], f) for f in faces]
            face_areas.sort(reverse=True)
            faces = [face_areas[0][1]]
            print(f"Multiple faces detected ({len(face_areas)}), using largest one (area: {face_areas[0][0]})")
        
        # Get the detected face
        x, y, w, h = faces[0]
        
        # Detect eyes within the face region for additional validation
        # Use the best preprocessing version that worked for face detection
        best_gray = gray_versions[0] if 'gray_versions' in locals() else gray
        face_roi_gray = best_gray[y:y+h, x:x+w]
        
        # Try multiple eye detection configurations
        eye_configs = [
            {"scaleFactor": 1.1, "minNeighbors": 2, "minSize": (10, 10)},
            {"scaleFactor": 1.05, "minNeighbors": 1, "minSize": (8, 8)},
            {"scaleFactor": 1.2, "minNeighbors": 3, "minSize": (15, 15)},
        ]
        
        eyes_detected = 0
        for eye_config in eye_configs:
            eyes = self.eye_cascade.detectMultiScale(
                face_roi_gray, 
                scaleFactor=eye_config["scaleFactor"], 
                minNeighbors=eye_config["minNeighbors"],
                minSize=eye_config["minSize"]
            )
            eyes_detected = len(eyes)
            if eyes_detected >= 2:  # Found both eyes
                print(f"Eyes detected with config: {eye_config}")
                break
        
        # Scale bounding box back to original image dimensions
        if scale_ratio != 1.0:
            x = int(x / scale_ratio)
            y = int(y / scale_ratio)
            w = int(w / scale_ratio)
            h = int(h / scale_ratio)

        face_center_x = x + w / 2
        face_center_y = y + h / 2
        head_height_percent = h / original_height
        horizontal_center = abs(face_center_x - original_width / 2) / original_width < 0.35  # Slightly more lenient
        
        # Calculate face quality metrics
        face_area = w * h
        image_area = original_width * original_height
        face_area_percent = (face_area / image_area) * 100
        
        # Check if face is too small or too large
        face_size_ok = 1.0 <= face_area_percent <= 50.0  # Face should be 1-50% of image
        
        # Calculate face aspect ratio (should be close to 1.0 for frontal faces)
        face_aspect_ratio = w / h
        aspect_ratio_ok = 0.7 <= face_aspect_ratio <= 1.4
        
        print(f"Face detection results: bbox=({x},{y},{w},{h}), head_height={head_height_percent:.2f}, centered={horizontal_center}, eyes={eyes_detected}")
        print(f"Face quality: area={face_area_percent:.1f}%, aspect_ratio={face_aspect_ratio:.2f}, size_ok={face_size_ok}, aspect_ok={aspect_ratio_ok}")
        
        # Determine overall validity
        face_valid = face_size_ok and aspect_ratio_ok
        
        return {
            "faces_detected": 1, 
            "valid": face_valid,
            "face_bbox": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
            "eyes_detected": eyes_detected,
            "head_height_percent": round(head_height_percent, 2),
            "head_height_valid": bool(self.HEAD_HEIGHT_MIN <= head_height_percent <= self.HEAD_HEIGHT_MAX),
            "horizontally_centered": bool(horizontal_center),
            "face_area_percent": round(face_area_percent, 1),
            "face_aspect_ratio": round(face_aspect_ratio, 2),
            "face_size_ok": face_size_ok,
            "aspect_ratio_ok": aspect_ratio_ok,
            "image_dimensions": {"width": int(original_width), "height": int(original_height)},
            "error": None if face_valid else f"Face quality issues: size_ok={face_size_ok}, aspect_ok={aspect_ratio_ok}"
        }
    
    def _detect_face_with_dnn(self, img):
        """
        Fallback face detection using OpenCV's DNN face detector.
        More robust than Haar cascades for difficult lighting/angles.
        """
        try:
            # Create blob from image
            blob = cv2.dnn.blobFromImage(img, 1.0, (300, 300), [104, 117, 123])
            
            # Load DNN model (using OpenCV's built-in face detection)
            # This is a simplified version - in production you'd load a proper model file
            h, w = img.shape[:2]
            
            # For now, return empty list as DNN models need to be properly loaded
            # This is a placeholder for future enhancement
            return []
            
        except Exception as e:
            print(f"DNN face detection error: {e}")
            return []

    async def analyze_with_ai(self, image_path):
        """Use Claude AI to validate passport photo requirements."""
        try:
            # Resize image if too large for Claude API (5MB limit)
            with open(image_path, "rb") as f:
                file_size = len(f.read())
            
            if file_size > 4 * 1024 * 1024:  # If larger than 4MB, resize to be safe
                # Resize image for AI analysis while keeping original for processing
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to reasonable size for AI analysis
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                temp_ai_path = f"{image_path}_ai_temp.jpg"
                img.save(temp_ai_path, "JPEG", quality=85)
                
                with open(temp_ai_path, "rb") as img_file:
                    image_data = base64.standard_b64encode(img_file.read()).decode("utf-8")
                
                # Clean up temp file
                os.remove(temp_ai_path)
            else:
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
                model="claude-3-5-sonnet-20241022", max_tokens=1024,
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
    
    def process_to_passport_photo(self, image_path, face_bbox, remove_bg=False, remove_watermark=False):
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
        
        # Add watermark unless removal is authorized
        if not remove_watermark:
            img_passport = self.add_watermark(img_passport)
        
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
    
    def add_watermark(self, img):
        """Add a semi-transparent watermark to the image."""
        try:
            # Create a copy to avoid modifying the original
            watermarked = img.copy()
            
            # Create watermark text
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(watermarked)
            
            # Try to use a nice font, fall back to default if not available
            try:
                font = ImageFont.truetype("Arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Watermark text
            watermark_text = "PassportPhotoAI.com"
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position watermark at bottom right
            x = watermarked.width - text_width - 10
            y = watermarked.height - text_height - 10
            
            # Create semi-transparent overlay
            overlay = Image.new('RGBA', watermarked.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Draw semi-transparent white background for text
            overlay_draw.rectangle([x-5, y-2, x+text_width+5, y+text_height+2], 
                                 fill=(255, 255, 255, 180))
            
            # Draw text
            overlay_draw.text((x, y), watermark_text, font=font, fill=(0, 0, 0, 200))
            
            # Composite the overlay onto the image
            watermarked = Image.alpha_composite(watermarked.convert('RGBA'), overlay)
            return watermarked.convert('RGB')
            
        except Exception as e:
            print(f"Watermark error: {e}")
            return img  # Return original if watermarking fails

# Initialize processor
processor = PassportPhotoProcessor()

# Simple in-memory store for OTPs (in production, use Redis or database)
otp_store = {}

def generate_otp():
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP via AWS SES"""
    try:
        sender_email = os.environ.get('SENDER_EMAIL', 'noreply@yourdomain.com')
        
        # Email content
        subject = "Your PassportPhotoAI Verification Code"
        body_text = f"""
Your verification code is: {otp}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
PassportPhotoAI Team
        """
        
        body_html = f"""
        <html>
        <head></head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #4F46E5;">PassportPhotoAI Verification</h2>
                <p>Your verification code is:</p>
                <div style="background-color: #F3F4F6; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 3px; margin: 20px 0;">
                    {otp}
                </div>
                <p style="color: #6B7280;">This code will expire in 10 minutes.</p>
                <p style="color: #6B7280; font-size: 12px;">If you didn't request this code, please ignore this email.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #E5E7EB;">
                <p style="color: #9CA3AF; font-size: 12px;">Best regards,<br>PassportPhotoAI Team</p>
            </div>
        </body>
        </html>
        """
        
        # Send email
        response = ses_client.send_email(
            Destination={
                'ToAddresses': [email],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': 'UTF-8',
                        'Data': body_html,
                    },
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': body_text,
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject,
                },
            },
            Source=sender_email,
        )
        
        print(f"Email sent successfully to {email}. Message ID: {response['MessageId']}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'MessageRejected':
            print(f"Email rejected: {e.response['Error']['Message']}")
            print("Make sure your email is verified in AWS SES")
        else:
            print(f"SES error: {error_code} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"Email sending error: {e}")
        return False

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

@application.route('/api/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to email for watermark removal."""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        # Basic email validation
        if not email or '@' not in email or '.' not in email:
            return jsonify({"error": "Invalid email address"}), 400
        
        # Generate and store OTP
        otp = generate_otp()
        otp_store[email] = {
            'otp': otp,
            'timestamp': datetime.now(timezone.utc).timestamp(),
            'verified': False
        }
        
        # Send OTP
        if send_otp_email(email, otp):
            return jsonify({"success": True, "message": "OTP sent to your email"}), 200
        else:
            return jsonify({"error": "Failed to send email"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@application.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and mark email as verified."""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({"error": "Email and OTP required"}), 400
        
        # Check if email exists in store
        if email not in otp_store:
            return jsonify({"error": "No OTP found for this email"}), 400
        
        stored_data = otp_store[email]
        
        # Check if OTP expired (10 minutes)
        if datetime.now(timezone.utc).timestamp() - stored_data['timestamp'] > 600:
            del otp_store[email]
            return jsonify({"error": "OTP expired"}), 400
        
        # Verify OTP
        if stored_data['otp'] == otp:
            otp_store[email]['verified'] = True
            return jsonify({"success": True, "message": "Email verified successfully"}), 200
        else:
            return jsonify({"error": "Invalid OTP"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@application.route('/api/remove-watermark', methods=['POST'])
def remove_watermark():
    """Remove watermark from image if email is verified."""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({"error": "Email required"}), 400
        
        # Check if email is verified
        if email not in otp_store or not otp_store[email].get('verified', False):
            return jsonify({"error": "Email not verified"}), 400
        
        # For now, return success - the frontend will handle re-processing without watermark
        return jsonify({"success": True, "message": "Watermark removal authorized"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        # Check if watermark removal is authorized
        email = request.form.get('email', '').strip().lower()
        remove_watermark = False
        if email and email in otp_store and otp_store[email].get('verified', False):
            remove_watermark = True
        
        valid_face_bbox = face_analysis.get("face_bbox") if face_analysis and face_analysis.get("valid") else None
        processed_buffer = processor.process_to_passport_photo(
            temp_path, 
            face_bbox=valid_face_bbox, 
            remove_bg=request.form.get('remove_background', 'false').lower() == 'true',
            remove_watermark=remove_watermark
        )
        
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
    application.run(debug=False, host='0.0.0.0', port=5000)
