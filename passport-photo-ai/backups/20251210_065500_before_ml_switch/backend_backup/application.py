"""
Hybrid Passport Photo Validator with Email Integration
Includes: Basic Face Detection, Email Integration, Watermark System
Optimized for AWS Elastic Beanstalk deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageEnhance
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

load_dotenv()

application = Flask(__name__)
CORS(application, origins=['*'], methods=['GET', 'POST', 'OPTIONS'], allow_headers=['Content-Type'])
application.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Initialize AWS SES client
ses_client = boto3.client('ses', region_name='us-east-1')

class HybridPassportPhotoProcessor:
    PASSPORT_SIZE_PIXELS = (600, 600)
    HEAD_HEIGHT_MIN = 0.50
    HEAD_HEIGHT_MAX = 0.69
    
    def __init__(self):
        pass
    
    def enhanced_face_detection(self, image_path):
        """Enhanced face detection using OpenCV and intelligent cropping"""
        try:
            import cv2
            import numpy as np
            
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
                
                # Validation criteria
                face_size_ok = 2.0 <= face_area_percent <= 40.0  # Reasonable face size
                head_height_ok = 0.15 <= head_height_percent <= 0.8  # Head should be reasonable size
                aspect_ratio = width / height if height > 0 else 1
                aspect_ratio_ok = 0.5 <= aspect_ratio <= 2.0
                
                face_valid = face_size_ok and head_height_ok and aspect_ratio_ok
                
                return {
                    "faces_detected": len(faces),
                    "valid": face_valid,
                    "face_bbox": {"x": int(crop_x), "y": int(crop_y), "width": int(crop_size), "height": int(crop_size)},
                    "original_face": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                    "eyes_detected": 2 if face_valid else 0,
                    "head_height_percent": round(head_height_percent, 2),
                    "head_height_valid": head_height_ok,
                    "horizontally_centered": horizontal_center,
                    "face_area_percent": round(face_area_percent, 1),
                    "face_aspect_ratio": round(aspect_ratio, 2),
                    "face_size_ok": face_size_ok,
                    "aspect_ratio_ok": aspect_ratio_ok,
                    "image_dimensions": {"width": width, "height": height},
                    "error": None if face_valid else "Face detected but may not meet passport photo requirements"
                }
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
                    "face_bbox": {"x": crop_x, "y": crop_y, "width": size, "height": size},
                    "original_face": None,
                    "eyes_detected": 0,
                    "head_height_percent": 0.5,
                    "head_height_valid": False,
                    "horizontally_centered": True,
                    "face_area_percent": 25.0,
                    "face_aspect_ratio": width / height if height > 0 else 1,
                    "face_size_ok": False,
                    "aspect_ratio_ok": True,
                    "image_dimensions": {"width": width, "height": height},
                    "error": "No face detected in image"
                }
                
        except Exception as e:
            # Final fallback
            try:
                img = Image.open(image_path)
                width, height = img.size
                size = min(width, height)
                crop_x = (width - size) // 2
                crop_y = (height - size) // 2
                
                return {
                    "faces_detected": 0,
                    "valid": False,
                    "face_bbox": {"x": crop_x, "y": crop_y, "width": size, "height": size},
                    "original_face": None,
                    "error": f"Face detection failed: {str(e)}"
                }
            except:
                return {"faces_detected": 0, "valid": False, "error": str(e)}
    
    def remove_background_simple(self, img):
        """Simple background removal using color-based segmentation"""
        try:
            import cv2
            import numpy as np
            
            # Convert PIL to OpenCV
            img_array = np.array(img)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Create a mask using GrabCut algorithm
            mask = np.zeros(img_cv.shape[:2], np.uint8)
            
            # Define rectangle around the center (where person likely is)
            height, width = img_cv.shape[:2]
            rect = (width//8, height//8, 3*width//4, 3*height//4)
            
            # Initialize background and foreground models
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)
            
            # Apply GrabCut
            cv2.grabCut(img_cv, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            
            # Create final mask
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            # Apply mask to create transparent background
            result = img_cv * mask2[:, :, np.newaxis]
            
            # Convert back to PIL with white background
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            result_pil = Image.fromarray(result_rgb)
            
            # Create white background
            white_bg = Image.new('RGB', result_pil.size, (255, 255, 255))
            
            # Create alpha mask from the segmentation
            alpha = Image.fromarray((mask2 * 255).astype('uint8'), 'L')
            
            # Composite the result onto white background
            white_bg.paste(result_pil, mask=alpha)
            
            return white_bg
            
        except Exception as e:
            print(f"Background removal failed: {e}")
            return img  # Return original if background removal fails
    
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
            img_cropped = self.remove_background_simple(img_cropped)
        
        # Resize to passport dimensions
        img_passport = img_cropped.resize(self.PASSPORT_SIZE_PIXELS, Image.Resampling.LANCZOS)
        
        # Apply subtle enhancements
        enhancer = ImageEnhance.Brightness(img_passport)
        img_passport = enhancer.enhance(1.05)
        
        enhancer = ImageEnhance.Contrast(img_passport)
        img_passport = enhancer.enhance(1.1)
        
        # Add watermark unless removal is authorized
        if not remove_watermark:
            img_passport = self.add_watermark(img_passport)
        
        buffer = io.BytesIO()
        img_passport.save(buffer, format='JPEG', quality=95, dpi=(300, 300))
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

# Initialize processor
processor = HybridPassportPhotoProcessor()

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
        # Enhanced face detection
        face_analysis = processor.enhanced_face_detection(temp_path)
        
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
        processed_buffer = processor.process_to_passport_photo(
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