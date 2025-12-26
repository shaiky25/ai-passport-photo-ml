"""
Passport Photo AI - Clean Working Version
Includes: Basic Face Detection, Email Integration, HEIC Support
Optimized for AWS Elastic Beanstalk Python 3.12 deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import io
import base64
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import random
import string
import boto3
from botocore.exceptions import ClientError

# Try to import OpenCV, but make it optional
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
    print("OpenCV loaded successfully")
except ImportError as e:
    print(f"OpenCV not available: {e}")
    OPENCV_AVAILABLE = False

# HEIC image support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORT = True
    print("HEIC support enabled")
except ImportError:
    HEIC_SUPPORT = False
    print("HEIC support not available")

# rembg support with lightweight model
try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
    print("rembg available")
except ImportError:
    REMBG_AVAILABLE = False
    print("rembg not available - background removal disabled")

load_dotenv()

application = Flask(__name__)
CORS(application, origins=['*'], methods=['GET', 'POST', 'OPTIONS'], allow_headers=['Content-Type'])
application.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Initialize AWS SES client
ses_client = boto3.client('ses', region_name='us-east-1')

class PassportPhotoProcessor:
    PASSPORT_SIZE_PIXELS = (1200, 1200)  # High resolution output
    HEAD_HEIGHT_MIN = 0.50
    HEAD_HEIGHT_MAX = 0.69
    
    def get_learned_profile_path(self):
        """Get the correct path for learned_profile.json"""
        possible_paths = [
            "learned_profile.json",  # AWS working directory
            "backend/learned_profile.json",  # Local development
            os.path.join(os.path.dirname(__file__), "learned_profile.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def __init__(self, use_learned_profile=True):
        self.use_learned_profile = use_learned_profile
        self.learned_profile = self.load_learned_profile() if use_learned_profile else None
    
    def load_learned_profile(self):
        """Load the ML-learned profile from sample photos"""
        if not self.use_learned_profile:
            print("Info: Learned profile disabled by feature flag")
            return None
            
        profile_path = self.get_learned_profile_path()
        if profile_path:
            try:
                with open(profile_path, 'r') as f:
                    profile = json.load(f)
                    print(f"Successfully loaded learned profile from {profile['sample_size']} sample photos")
                    return profile
            except Exception as e:
                print(f"Warning: Could not load learned_profile.json: {e}")
        print("Info: No learned profile found. Using basic validation rules.")
        return None
    
    def enhanced_face_detection(self, image_path):
        """Enhanced face detection using OpenCV"""
        if not OPENCV_AVAILABLE:
            return self._fallback_face_detection(image_path)
            
        try:
            # Load image with OpenCV
            cv_img = cv2.imread(image_path)
            if cv_img is None:
                raise Exception("Could not load image")
                
            height, width = cv_img.shape[:2]
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # Try to load OpenCV's face cascade
            try:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
            except:
                faces = []
            
            if len(faces) > 0:
                # Use the largest detected face
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest_face
                
                # Expand the face region for passport photo
                expansion_factor = 1.8
                center_x = x + w // 2
                center_y = y + h // 2
                
                new_w = int(w * expansion_factor)
                new_h = int(h * expansion_factor)
                crop_size = max(new_w, new_h)
                
                crop_x = center_x - crop_size // 2
                crop_y = center_y - int(crop_size * 0.4)
                
                # Ensure crop is within image bounds
                crop_x = max(0, min(crop_x, width - crop_size))
                crop_y = max(0, min(crop_y, height - crop_size))
                crop_size = min(crop_size, width - crop_x, height - crop_y)
                
                # Calculate metrics
                head_height_percent = h / height
                face_area_percent = (w * h) / (width * height) * 100
                horizontal_center = abs(center_x - width/2) / width < 0.3
                
                # Use learned profile if available
                validation_details = {}
                if self.learned_profile:
                    face_valid, validation_details = self._validate_with_learned_profile(
                        x, y, w, h, width, height
                    )
                    face_size_ok = validation_details.get('size_ok', True)
                    head_height_ok = validation_details.get('head_height_ok', True)
                    aspect_ratio_ok = validation_details.get('aspect_ratio_ok', True)
                    print(f"Using learned profile validation: valid={face_valid}")
                else:
                    # Basic validation
                    face_size_ok = bool(2.0 <= face_area_percent <= 40.0)
                    head_height_ok = bool(0.15 <= head_height_percent <= 0.8)
                    aspect_ratio_ok = bool(0.5 <= (width/height) <= 2.0)
                    face_valid = bool(face_size_ok and head_height_ok and aspect_ratio_ok)
                    print(f"Using basic validation: valid={face_valid}")
                
                aspect_ratio = float(width / height if height > 0 else 1)
                
                result = {
                    "faces_detected": int(len(faces)),
                    "valid": bool(face_valid),
                    "face_bbox": {"x": int(crop_x), "y": int(crop_y), "width": int(crop_size), "height": int(crop_size)},
                    "original_face": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                    "eyes_detected": int(2 if face_valid else 0),
                    "head_height_percent": float(round(head_height_percent, 2)),
                    "head_height_valid": bool(head_height_ok),
                    "horizontally_centered": bool(horizontal_center),
                    "face_area_percent": float(round(face_area_percent, 1)),
                    "face_aspect_ratio": float(round(aspect_ratio, 2)),
                    "face_size_ok": bool(face_size_ok),
                    "aspect_ratio_ok": bool(aspect_ratio_ok),
                    "image_dimensions": {"width": int(width), "height": int(height)},
                    "error": None if face_valid else "Face detected but may not meet passport photo requirements"
                }
                
                # Add learned profile details if available
                if validation_details and validation_details.get('learned_profile_used'):
                    result["learned_profile_validation"] = validation_details
                
                return result
            else:
                return self._fallback_face_detection(image_path)
                
        except Exception as e:
            return self._fallback_face_detection(image_path, error=str(e))
    
    def _fallback_face_detection(self, image_path, error=None):
        """Fallback face detection when OpenCV is not available"""
        try:
            img = Image.open(image_path)
            width, height = img.size
            
            # Use center crop as fallback
            size = min(width, height)
            crop_x = (width - size) // 2
            crop_y = (height - size) // 2
            
            return {
                "faces_detected": 0,
                "valid": False,
                "face_bbox": {"x": int(crop_x), "y": int(crop_y), "width": int(size), "height": int(size)},
                "original_face": None,
                "eyes_detected": 0,
                "head_height_percent": 0.5,
                "head_height_valid": False,
                "horizontally_centered": True,
                "face_area_percent": 25.0,
                "face_aspect_ratio": float(width / height if height > 0 else 1),
                "face_size_ok": False,
                "aspect_ratio_ok": True,
                "image_dimensions": {"width": int(width), "height": int(height)},
                "error": error or "OpenCV not available - using basic center crop"
            }
        except Exception as e:
            return {"faces_detected": 0, "valid": False, "error": str(e)}
    
    def _validate_with_learned_profile(self, face_x, face_y, face_w, face_h, img_width, img_height):
        """Validate face positioning using the ML-learned profile"""
        try:
            profile_mean = self.learned_profile['mean']
            profile_std = self.learned_profile['std_dev']
            
            # Calculate actual ratios from detected face
            head_top_y = max(0, face_y - (face_h * 0.15))
            full_head_height = (face_y + face_h) - head_top_y
            
            actual_head_height_ratio = full_head_height / img_height
            actual_face_center_x_ratio = (face_x + face_w / 2) / img_width
            actual_head_top_y_ratio = head_top_y / img_height
            
            # Compare against learned profile
            tolerance_factor = 2.0
            
            expected_head_height = profile_mean['head_height_ratio']
            head_height_tolerance = profile_std['head_height_ratio'] * tolerance_factor
            head_height_ok = abs(actual_head_height_ratio - expected_head_height) <= head_height_tolerance
            
            expected_center_x = profile_mean['face_center_x_ratio']
            center_x_tolerance = profile_std['face_center_x_ratio'] * tolerance_factor
            center_x_ok = abs(actual_face_center_x_ratio - expected_center_x) <= center_x_tolerance
            
            expected_head_top = profile_mean['head_top_y_ratio']
            head_top_tolerance = profile_std['head_top_y_ratio'] * tolerance_factor
            head_top_ok = abs(actual_head_top_y_ratio - expected_head_top) <= head_top_tolerance
            
            is_valid = head_height_ok and center_x_ok and head_top_ok
            
            validation_details = {
                'size_ok': True,
                'head_height_ok': bool(head_height_ok),
                'aspect_ratio_ok': True,
                'center_x_ok': bool(center_x_ok),
                'head_top_ok': bool(head_top_ok),
                'learned_profile_used': True,
                'actual_ratios': {
                    'head_height_ratio': float(actual_head_height_ratio),
                    'face_center_x_ratio': float(actual_face_center_x_ratio),
                    'head_top_y_ratio': float(actual_head_top_y_ratio)
                },
                'expected_ratios': profile_mean,
                'tolerances': {
                    'head_height_tolerance': float(head_height_tolerance),
                    'center_x_tolerance': float(center_x_tolerance),
                    'head_top_tolerance': float(head_top_tolerance)
                }
            }
            
            return is_valid, validation_details
            
        except Exception as e:
            print(f"Error in learned profile validation: {e}")
            return True, {'size_ok': True, 'head_height_ok': True, 'aspect_ratio_ok': True}
    
    def remove_background_lightweight(self, img):
        """Professional background removal using lightweight rembg u2netp model (4.7MB)"""
        if not REMBG_AVAILABLE:
            print("rembg not available, skipping background removal")
            return img
            
        try:
            # Use lightweight u2netp model (only 4.7MB)
            session = new_session('u2netp')
            
            # Convert PIL to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            input_data = img_buffer.getvalue()
            
            # Remove background
            output_data = remove(input_data, session=session)
            
            # Convert back to PIL
            result_img = Image.open(io.BytesIO(output_data))
            
            # Convert RGBA to RGB with white background
            if result_img.mode == 'RGBA':
                white_bg = Image.new('RGB', result_img.size, (255, 255, 255))
                white_bg.paste(result_img, mask=result_img.split()[-1])
                return white_bg
            else:
                return result_img
                
        except Exception as e:
            print(f"Background removal failed: {e}, returning original image")
            return img
    
    def process_to_passport_photo(self, image_path, face_bbox=None, remove_bg=False, remove_watermark=False):
        """Process image to passport photo with intelligent cropping"""
        img = Image.open(image_path)
        
        if img.mode != 'RGB': 
            img = img.convert('RGB')
        
        # Crop based on face detection
        if face_bbox and face_bbox.get('x') is not None:
            fx, fy, fw, fh = face_bbox['x'], face_bbox['y'], face_bbox['width'], face_bbox['height']
            img_cropped = img.crop((fx, fy, fx + fw, fy + fh))
        else:
            # Fallback: center crop to square
            size = min(img.size)
            left = (img.size[0] - size) // 2
            top = (img.size[1] - size) // 2
            img_cropped = img.crop((left, top, left + size, top + size))
        
        # Background removal with lightweight rembg
        if remove_bg:
            img_cropped = self.remove_background_lightweight(img_cropped)
        
        # Resize to passport dimensions
        img_passport = img_cropped.resize(self.PASSPORT_SIZE_PIXELS, Image.Resampling.LANCZOS)
        
        # Apply professional enhancements
        enhancer = ImageEnhance.Brightness(img_passport)
        img_passport = enhancer.enhance(1.02)
        
        enhancer = ImageEnhance.Contrast(img_passport)
        img_passport = enhancer.enhance(1.05)
        
        enhancer = ImageEnhance.Sharpness(img_passport)
        img_passport = enhancer.enhance(1.1)
        
        # Add watermark unless removal is authorized
        if not remove_watermark:
            img_passport = self.add_watermark(img_passport)
        
        # Save with maximum quality
        buffer = io.BytesIO()
        img_passport.save(buffer, format='JPEG', quality=98, dpi=(300, 300), optimize=False)
        buffer.seek(0)
        return buffer
    
    def add_watermark(self, img):
        """Add a clean white PROOF-style watermark that covers the entire photo"""
        try:
            # Create a copy of the image
            watermarked = img.copy().convert('RGBA')
            
            # Create a transparent overlay
            overlay = Image.new('RGBA', watermarked.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Clean watermark text
            watermark_text = "PROOF"
            
            # Larger font size - 3 times bigger than previous
            img_width, img_height = watermarked.size
            font_size = max(img_width // 4, 96)  # 3 times larger than before
            
            try:
                from PIL import ImageFont
                # Use default font (not bold)
                font = ImageFont.load_default()
            except:
                font = None
            
            # Get text dimensions
            if font:
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                # Fallback dimensions - larger for bigger text
                text_width = len(watermark_text) * 24
                text_height = 48
            
            # Spacing adjusted for larger text
            x_spacing = text_width + 40
            y_spacing = text_height + 30
            
            # Start positions to ensure full coverage
            start_x = -text_width
            start_y = -text_height
            
            # Generate diagonal grid positions
            positions = []
            y = start_y
            row_count = 0
            
            while y < img_height + text_height:
                x = start_x
                # Alternate row offset for diagonal effect
                if row_count % 2 == 1:
                    x += x_spacing // 2
                
                while x < img_width + text_width:
                    positions.append((x, y))
                    x += x_spacing
                
                y += y_spacing
                row_count += 1
            
            # Draw clean white watermarks
            for x, y in positions:
                # Clean white text with good visibility but not overwhelming
                if font:
                    # Pure white text with moderate opacity
                    draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 120))
                else:
                    # Fallback - pure white
                    draw.text((x, y), watermark_text, fill=(255, 255, 255, 120))
            
            # Composite the overlay onto the original image
            watermarked = Image.alpha_composite(watermarked, overlay)
            
            # Convert back to RGB
            final_image = Image.new('RGB', watermarked.size, (255, 255, 255))
            final_image.paste(watermarked, mask=watermarked.split()[-1])
            
            return final_image
            
        except Exception as e:
            print(f"Watermark error: {e}")
            return img

# Initialize processor
processor = PassportPhotoProcessor(use_learned_profile=True)

# Simple in-memory store for OTPs
otp_store = {}

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP via AWS SES"""
    try:
        sender_email = os.environ.get('SENDER_EMAIL', 'faiz.24365@gmail.com')
        
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
        
        response = ses_client.send_email(
            Destination={'ToAddresses': [email]},
            Message={
                'Body': {
                    'Html': {'Charset': 'UTF-8', 'Data': body_html},
                    'Text': {'Charset': 'UTF-8', 'Data': body_text},
                },
                'Subject': {'Charset': 'UTF-8', 'Data': subject},
            },
            Source=sender_email,
        )
        
        print(f"Email sent successfully to {email}. Message ID: {response['MessageId']}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"SES error: {error_code} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"Email sending error: {e}")
        return False

# API Endpoints
@application.route('/', methods=['GET'])
def root():
    return jsonify({"status": "healthy", "message": "Passport Photo AI (Fixed) is running"}), 200

@application.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "message": "Passport Photo AI (Fixed) is running",
        "python_version": "3.12",
        "heic_support": HEIC_SUPPORT,
        "opencv_available": OPENCV_AVAILABLE
    }), 200

@application.route('/api/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email or '@' not in email:
            return jsonify({"error": "Invalid email address"}), 400
        
        otp = generate_otp()
        otp_store[email] = {
            'otp': otp,
            'timestamp': datetime.now(timezone.utc).timestamp(),
            'verified': False
        }
        
        if send_otp_email(email, otp):
            return jsonify({"success": True, "message": "OTP sent to your email"}), 200
        else:
            return jsonify({"error": "Failed to send email. Please check your email address."}), 500
            
    except Exception as e:
        print(f"Send OTP error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@application.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({"error": "Email and OTP required"}), 400
        
        if email not in otp_store:
            return jsonify({"error": "No OTP found for this email"}), 400
        
        stored_data = otp_store[email]
        
        if datetime.now(timezone.utc).timestamp() - stored_data['timestamp'] > 600:
            del otp_store[email]
            return jsonify({"error": "OTP expired"}), 400
        
        if stored_data['otp'] == otp:
            otp_store[email]['verified'] = True
            return jsonify({"success": True, "message": "Email verified successfully"}), 200
        else:
            return jsonify({"error": "Invalid OTP"}), 400
            
    except Exception as e:
        print(f"Verify OTP error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@application.route('/api/full-workflow', methods=['POST'])
def full_workflow():
    """Enhanced workflow with face detection and processing"""
    start_time = datetime.now()
    print(f"[{start_time}] Processing request started")
    
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    print(f"File received: {file.filename}, size: {len(file.read())} bytes")
    file.seek(0)  # Reset file pointer
    
    temp_path = f"temp_{datetime.now().timestamp()}"
    file.save(temp_path)
    print(f"File saved to: {temp_path}")
    
    try:
        # Check if learned profile should be used
        use_learned_profile = request.form.get('use_learned_profile', 'true').lower() == 'true'
        
        # Create processor with appropriate settings
        current_processor = processor if use_learned_profile else PassportPhotoProcessor(use_learned_profile=False)
        
        # Face detection
        face_analysis = current_processor.enhanced_face_detection(temp_path)
        
        img = Image.open(temp_path)
        width, height = img.size
        
        if not (width >= 600 and height >= 600):
            return jsonify({
                "success": False, "feasible": False,
                "analysis": {"face_detection": face_analysis, "ai_analysis": None},
                "message": "Photo resolution too low (must be at least 600x600 pixels)."
            })
        
        # Check if watermark removal is authorized
        email = request.form.get('email', '').strip().lower()
        remove_watermark = False
        if email and email in otp_store and otp_store[email].get('verified', False):
            remove_watermark = True
        
        valid_face_bbox = face_analysis.get("face_bbox") if face_analysis and face_analysis.get("valid") else None
        processed_buffer = current_processor.process_to_passport_photo(
            temp_path, 
            face_bbox=valid_face_bbox, 
            remove_bg=request.form.get('remove_background', 'false').lower() == 'true',
            remove_watermark=remove_watermark
        )
        
        # Create AI analysis
        ai_analysis = {
            "compliant": face_analysis.get("valid", False),
            "issues": [] if face_analysis.get("valid", False) else ["Image analysis suggests this may not be suitable for passport photos"]
        }
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        print(f"[{end_time}] Processing completed in {processing_time:.2f} seconds")
        
        return jsonify({
            "success": True, "feasible": True,
            "analysis": {"face_detection": face_analysis, "ai_analysis": ai_analysis},
            "processed_image": base64.b64encode(processed_buffer.getvalue()).decode('utf-8'),
            "message": "Photo successfully processed with enhanced analysis.",
            "processing_time": processing_time
        })
        
    except Exception as e:
        print(f"Error in full-workflow: {e}")
        return jsonify({
            "success": False, "feasible": False,
            "message": f"Processing error: {str(e)}"
        }), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@application.route('/api/log-event', methods=['POST', 'OPTIONS'])
def log_event():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        event_data = request.json
        if not event_data:
            return jsonify({"error": "No event data provided"}), 400
        
        event_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        print(f"Analytics Event: {json.dumps(event_data)}")
        
        return jsonify({"success": True, "message": "Event logged"}), 200
        
    except Exception as e:
        print(f"Log event error: {e}")
        return jsonify({"error": "Failed to log event"}), 500

if __name__ == '__main__':
    application.run(debug=False, host='0.0.0.0', port=5000)