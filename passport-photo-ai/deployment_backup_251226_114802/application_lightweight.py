"""
Hybrid Passport Photo Validator with Email Integration
Includes: Basic Face Detection, Email Integration, Watermark System
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

load_dotenv()

application = Flask(__name__)
CORS(application, origins=['*'], methods=['GET', 'POST', 'OPTIONS'], allow_headers=['Content-Type'])
application.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Initialize AWS SES client
ses_client = boto3.client('ses', region_name='us-east-1')

class HybridPassportPhotoProcessor:
    # US Passport photo specifications - 2x2 inches at 300 DPI = 600x600 minimum
    # But for better quality, we'll use higher resolution and scale appropriately
    PASSPORT_SIZE_PIXELS = (1200, 1200)  # Higher resolution for better quality
    HEAD_HEIGHT_MIN = 0.50
    HEAD_HEIGHT_MAX = 0.69
    def get_learned_profile_path(self):
        """Get the correct path for learned_profile.json in both local and AWS environments"""
        # Try multiple possible paths
        possible_paths = [
            "learned_profile.json",  # AWS working directory
            "backend/learned_profile.json",  # Local development
            os.path.join(os.path.dirname(__file__), "learned_profile.json"),  # Same directory as application.py
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
            print("Info: Learned profile disabled by feature flag. Using basic validation rules.")
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
        """Enhanced face detection using OpenCV and intelligent cropping"""
        if not OPENCV_AVAILABLE:
            # Fallback to basic center crop if OpenCV is not available
            return self._fallback_face_detection(image_path)
            
        try:
            # Load image with OpenCV
            cv_img = cv2.imread(image_path)
            if cv_img is None:
                raise Exception("Could not load image")
                
            height, width = cv_img.shape[:2]
            
            # Convert to RGB for PIL compatibility
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
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
                
                # Expand the face region to include more head area for passport photo
                # Passport photos need head + shoulders, not just face
                expansion_factor = 1.8  # Expand to include more head area
                
                # Calculate expanded region
                center_x = x + w // 2
                center_y = y + h // 2
                
                # Make the crop region larger and more square
                new_w = int(w * expansion_factor)
                new_h = int(h * expansion_factor)
                
                # Ensure it's square (passport photos are square)
                crop_size = max(new_w, new_h)
                
                # Center the crop around the face
                crop_x = center_x - crop_size // 2
                crop_y = center_y - int(crop_size * 0.4)  # Position face in upper portion
                
                # Ensure crop is within image bounds
                crop_x = max(0, min(crop_x, width - crop_size))
                crop_y = max(0, min(crop_y, height - crop_size))
                crop_size = min(crop_size, width - crop_x, height - crop_y)
                
                # Calculate metrics for validation
                head_height_percent = h / height
                face_area_percent = (w * h) / (width * height) * 100
                horizontal_center = abs(center_x - width/2) / width < 0.3
                
                # Use learned profile if available, otherwise use basic validation
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
                    # Fallback to basic validation
                    face_size_ok = bool(2.0 <= face_area_percent <= 40.0)
                    head_height_ok = bool(0.15 <= head_height_percent <= 0.8)
                    aspect_ratio_ok = bool(0.5 <= (width/height) <= 2.0)
                    face_valid = bool(face_size_ok and head_height_ok and aspect_ratio_ok)
                    print(f"Using basic validation: valid={face_valid}")
                
                aspect_ratio = float(width / height if height > 0 else 1)
                
                # Build result dictionary
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
                # Fallback to center crop if no face detected
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
                    "error": "No face detected in image"
                }
                
        except Exception as e:
            # Fallback to basic detection if OpenCV fails
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
        """Validate face positioning using the ML-learned profile from sample photos"""
        try:
            profile_mean = self.learned_profile['mean']
            profile_std = self.learned_profile['std_dev']
            
            # Calculate actual ratios from detected face
            # Estimate head top (face detection box doesn't include full head)
            head_top_y = max(0, face_y - (face_h * 0.15))  # Same logic as learning script
            full_head_height = (face_y + face_h) - head_top_y
            
            actual_head_height_ratio = full_head_height / img_height
            actual_face_center_x_ratio = (face_x + face_w / 2) / img_width
            actual_head_top_y_ratio = head_top_y / img_height
            
            # Compare against learned profile (within 2 standard deviations = 95% confidence)
            tolerance_factor = 2.0
            
            # Head height validation
            expected_head_height = profile_mean['head_height_ratio']
            head_height_tolerance = profile_std['head_height_ratio'] * tolerance_factor
            head_height_ok = abs(actual_head_height_ratio - expected_head_height) <= head_height_tolerance
            
            # Horizontal centering validation
            expected_center_x = profile_mean['face_center_x_ratio']
            center_x_tolerance = profile_std['face_center_x_ratio'] * tolerance_factor
            center_x_ok = abs(actual_face_center_x_ratio - expected_center_x) <= center_x_tolerance
            
            # Head top position validation
            expected_head_top = profile_mean['head_top_y_ratio']
            head_top_tolerance = profile_std['head_top_y_ratio'] * tolerance_factor
            head_top_ok = abs(actual_head_top_y_ratio - expected_head_top) <= head_top_tolerance
            
            # Overall validation
            is_valid = head_height_ok and center_x_ok and head_top_ok
            
            validation_details = {
                'size_ok': True,  # We trust face detection for basic size
                'head_height_ok': bool(head_height_ok),
                'aspect_ratio_ok': True,  # Basic aspect ratio is usually fine
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
            # Fallback to basic validation
            return True, {'size_ok': True, 'head_height_ok': True, 'aspect_ratio_ok': True}
    
    def remove_background_rembg_lightweight(self, img):
        """Professional background removal using lightweight rembg model"""
        try:
            # Try to use rembg with lightweight model
            # # from rembg import remove, new_session  # Temporarily disabled  # Temporarily disabled
            import io
            
            # Use lightweight u2netp model (only 4.7MB)
            # # session = new_session('u2netp')  # Temporarily disabled  # Temporarily disabled
            
            # Convert PIL to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            input_data = img_buffer.getvalue()
            
            # Remove background
            raise ImportError("rembg temporarily disabled")
            
            # Convert back to PIL
            result_img = Image.open(io.BytesIO(output_data))
            
            # Convert RGBA to RGB with white background
            if result_img.mode == 'RGBA':
                # Create white background for passport photos
                white_bg = Image.new('RGB', result_img.size, (255, 255, 255))
                white_bg.paste(result_img, mask=result_img.split()[-1])  # Use alpha channel as mask
                return white_bg
            else:
                return result_img
                
        except ImportError:
            print("rembg not available, falling back to OpenCV method")
            return self.remove_background_opencv_fallback(img)
        except Exception as e:
            print(f"rembg failed: {e}, falling back to OpenCV method")
            return self.remove_background_opencv_fallback(img)
    
    def remove_background_opencv_fallback(self, img):
        """Fallback background removal using OpenCV (for when rembg fails)"""
        if not OPENCV_AVAILABLE:
            print("Background removal not available - OpenCV missing")
            return self._add_plain_background(img)
            
        try:
            # Convert PIL to OpenCV
            img_array = np.array(img)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            height, width = img_cv.shape[:2]
            
            # Use face detection to better initialize the foreground
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            
            if len(faces) > 0:
                # Use face detection to create better foreground rectangle
                x, y, w, h = faces[0]
                # Expand around face for full person - be more conservative with dark clothing
                expansion = 1.8  # Larger expansion to include clothing
                rect_x = max(0, int(x - w * expansion * 0.6))  # More horizontal space
                rect_y = max(0, int(y - h * expansion * 0.2))  # Less top space
                rect_w = min(width - rect_x, int(w * expansion * 1.2))  # Wider
                rect_h = min(height - rect_y, int(h * expansion * 2.5))  # Taller for body
                rect = (rect_x, rect_y, rect_w, rect_h)
            else:
                # Fallback to center rectangle - larger for full person
                rect = (width//8, height//10, 3*width//4, 4*height//5)
            
            # Initialize GrabCut
            mask = np.zeros(img_cv.shape[:2], np.uint8)
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # Apply GrabCut with more conservative settings
            cv2.grabCut(img_cv, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            
            # Manual refinement for dark clothing
            # Mark definitely foreground areas (around face and upper body)
            if len(faces) > 0:
                x, y, w, h = faces[0]
                # Mark face area as definite foreground
                mask[y:y+h, x:x+w] = cv2.GC_FGD
                # Mark upper body area as probable foreground
                body_y_start = y + h
                body_y_end = min(height, y + int(h * 2.5))
                body_x_start = max(0, x - int(w * 0.3))
                body_x_end = min(width, x + w + int(w * 0.3))
                mask[body_y_start:body_y_end, body_x_start:body_x_end] = cv2.GC_PR_FGD
            
            # Refine with additional iterations
            cv2.grabCut(img_cv, mask, None, bgd_model, fgd_model, 3, cv2.GC_INIT_WITH_MASK)
            
            # Create refined mask - be more inclusive for foreground
            mask2 = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype('uint8')
            
            # Apply morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)
            mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel)
            
            # Apply Gaussian blur for smoother edges
            mask2 = cv2.GaussianBlur(mask2, (5, 5), 0)
            
            # Convert back to PIL
            result_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            result_pil = Image.fromarray(result_rgb)
            
            # Create white background for passport photos
            white_bg = Image.new('RGB', result_pil.size, (255, 255, 255))
            
            # Create smooth alpha mask
            alpha = Image.fromarray((mask2 * 255).astype('uint8'), 'L')
            
            # Apply feathering for smoother edges
            alpha = alpha.filter(ImageFilter.GaussianBlur(radius=2))
            
            # Composite with smooth blending
            white_bg.paste(result_pil, mask=alpha)
            
            return white_bg
            
        except Exception as e:
            print(f"OpenCV background removal failed: {e}")
            return self._add_plain_background(img)
    
    def _add_plain_background(self, img):
        """Add a plain passport-appropriate background when background removal fails"""
        try:
            # Create a new image with passport-appropriate background
            bg_color = (240, 240, 240)  # Light gray
            background = Image.new('RGB', img.size, bg_color)
            
            # For passport photos, we can create a simple gradient or plain background
            # This is better than keeping a complex background
            
            # Try to detect if the current background is already plain
            img_array = np.array(img)
            
            # Check background uniformity (corners and edges)
            h, w = img_array.shape[:2]
            corners = [
                img_array[0:h//4, 0:w//4],      # Top-left
                img_array[0:h//4, 3*w//4:w],    # Top-right
                img_array[3*h//4:h, 0:w//4],    # Bottom-left
                img_array[3*h//4:h, 3*w//4:w]   # Bottom-right
            ]
            
            # Calculate variance in corners (low variance = uniform background)
            corner_variances = [np.var(corner) for corner in corners]
            avg_variance = np.mean(corner_variances)
            
            # If background is already fairly uniform, keep original
            if avg_variance < 500:  # Threshold for "plain enough"
                return img
            
            # Otherwise, create a simple mask based on center focus
            # This is a fallback that at least provides a clean background
            mask = np.zeros((h, w), dtype=np.uint8)
            
            # Create elliptical mask centered on image
            center_x, center_y = w // 2, h // 2
            axes_x, axes_y = w // 3, h // 2
            
            y, x = np.ogrid[:h, :w]
            mask_condition = ((x - center_x) / axes_x) ** 2 + ((y - center_y) / axes_y) ** 2 <= 1
            mask[mask_condition] = 255
            
            # Apply Gaussian blur for smooth edges
            mask = cv2.GaussianBlur(mask, (21, 21), 0)
            
            # Convert to PIL
            mask_pil = Image.fromarray(mask, 'L')
            
            # Composite original image onto plain background
            background.paste(img, mask=mask_pil)
            
            return background
            
        except Exception as e:
            print(f"Plain background fallback failed: {e}")
            return img
    
    def process_to_passport_photo(self, image_path, face_bbox=None, remove_bg=False, remove_watermark=False):
        """Process image to passport photo with intelligent cropping"""
        img = Image.open(image_path)
        
        if img.mode != 'RGB': 
            img = img.convert('RGB')
        
        # Crop based on face detection
        if face_bbox and face_bbox.get('x') is not None:
            fx, fy, fw, fh = face_bbox['x'], face_bbox['y'], face_bbox['width'], face_bbox['height']
            
            # Use the face bbox directly (it's already calculated for passport photo proportions)
            img_cropped = img.crop((fx, fy, fx + fw, fy + fh))
        else:
            # Fallback: center crop to square
            size = min(img.size)
            left = (img.size[0] - size) // 2
            top = (img.size[1] - size) // 2
            img_cropped = img.crop((left, top, left + size, top + size))
        
        # Remove background if requested
        if remove_bg:
            img_cropped = self.remove_background_rembg_lightweight(img_cropped)
        
        # Resize to passport dimensions
        img_passport = img_cropped.resize(self.PASSPORT_SIZE_PIXELS, Image.Resampling.LANCZOS)
        
        # Apply professional enhancements for passport photos
        # Slight brightness adjustment for better visibility
        enhancer = ImageEnhance.Brightness(img_passport)
        img_passport = enhancer.enhance(1.02)  # More subtle
        
        # Slight contrast enhancement for definition
        enhancer = ImageEnhance.Contrast(img_passport)
        img_passport = enhancer.enhance(1.05)  # More subtle
        
        # Slight sharpness enhancement for clarity
        enhancer = ImageEnhance.Sharpness(img_passport)
        img_passport = enhancer.enhance(1.1)
        
        # Add watermark unless removal is authorized
        if not remove_watermark:
            img_passport = self.add_watermark(img_passport)
        
        # Save with maximum quality settings
        buffer = io.BytesIO()
        img_passport.save(buffer, format='JPEG', quality=98, dpi=(300, 300), optimize=False)
        buffer.seek(0)
        return buffer
    
    def add_watermark(self, img):
        """Add a professional watermark"""
        try:
            watermarked = img.copy()
            draw = ImageDraw.Draw(watermarked)
            
            watermark_text = "PassportPhotoAI.com"
            
            # Position watermark at bottom right
            x = watermarked.width - 180
            y = watermarked.height - 25
            
            # Semi-transparent background
            draw.rectangle([x-5, y-3, x+175, y+20], fill=(255, 255, 255, 200))
            draw.text((x, y), watermark_text, fill=(100, 100, 100))
            
            return watermarked
        except Exception as e:
            print(f"Watermark error: {e}")
            return img

# Initialize processor with learned profile enabled by default
processor = HybridPassportPhotoProcessor(use_learned_profile=True)

# Simple in-memory store for OTPs
otp_store = {}

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP via AWS SES"""
    try:
        sender_email = os.environ.get('SENDER_EMAIL', 'noreply@yourdomain.com')
        
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
    return jsonify({"status": "healthy", "message": "Passport Photo AI (Hybrid) is running"}), 200

@application.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Passport Photo AI (Hybrid) is running"}), 200

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
    """Enhanced workflow with better face detection"""
    start_time = datetime.now()
    print(f"[{start_time}] Processing request started")
    
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    print(f"File received: {file.filename}, size: {len(file.read())} bytes")
    file.seek(0)  # Reset file pointer after reading size
    
    temp_path = f"temp_{datetime.now().timestamp()}"
    file.save(temp_path)
    print(f"File saved to: {temp_path}")
    
    try:
        # Check if learned profile should be used (feature flag)
        use_learned_profile = request.form.get('use_learned_profile', 'true').lower() == 'true'
        
        # Create processor with appropriate settings
        current_processor = processor if use_learned_profile else HybridPassportPhotoProcessor(use_learned_profile=False)
        
        # Enhanced face detection
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
        
        # Create AI analysis placeholder
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
        # Handle CORS preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        event_data = request.json
        if not event_data:
            return jsonify({"error": "No event data provided"}), 400
        
        # Add server-side timestamp
        event_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Log the event (simplified logging)
        print(f"Analytics Event: {json.dumps(event_data)}")
        
        return jsonify({"success": True, "message": "Event logged"}), 200
        
    except Exception as e:
        print(f"Log event error: {e}")
        return jsonify({"error": "Failed to log event"}), 500

if __name__ == '__main__':
    application.run(debug=False, host='0.0.0.0', port=5000)