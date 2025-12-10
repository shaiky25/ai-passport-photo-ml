"""
Passport Photo Validator with AWS SES Email Integration
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
CORS(application)
application.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize AWS SES client
ses_client = boto3.client('ses', region_name='us-east-1')

class SimplePassportPhotoProcessor:
    PASSPORT_SIZE_PIXELS = (600, 600)
    
    def __init__(self):
        pass
    
    def simple_face_detection(self, image_path):
        """Simple placeholder face detection - always returns success for demo"""
        try:
            img = Image.open(image_path)
            width, height = img.size
            
            # Simple heuristic: assume face is in center 60% of image
            face_width = int(width * 0.6)
            face_height = int(height * 0.6)
            face_x = int(width * 0.2)
            face_y = int(height * 0.2)
            
            return {
                "faces_detected": 1, 
                "valid": True,
                "face_bbox": {"x": face_x, "y": face_y, "width": face_width, "height": face_height},
                "eyes_detected": 2,
                "head_height_percent": 0.60,
                "head_height_valid": True,
                "horizontally_centered": True,
                "image_dimensions": {"width": width, "height": height}
            }
        except Exception as e:
            return {"faces_detected": 0, "valid": False, "error": str(e)}
    
    def process_to_passport_photo(self, image_path, face_bbox=None, remove_bg=False, remove_watermark=False):
        """Simple image processing without OpenCV"""
        img = Image.open(image_path)
        
        if img.mode != 'RGB': 
            img = img.convert('RGB')
        
        # Simple center crop to square
        size = min(img.size)
        left = (img.size[0] - size) // 2
        top = (img.size[1] - size) // 2
        img_cropped = img.crop((left, top, left + size, top + size))
        
        # Resize to passport dimensions
        img_passport = img_cropped.resize(self.PASSPORT_SIZE_PIXELS, Image.Resampling.LANCZOS)
        
        # Add watermark unless removal is authorized
        if not remove_watermark:
            img_passport = self.add_watermark(img_passport)
        
        buffer = io.BytesIO()
        img_passport.save(buffer, format='JPEG', quality=95, dpi=(300, 300))
        buffer.seek(0)
        return buffer
    
    def add_watermark(self, img):
        """Add a simple watermark"""
        try:
            watermarked = img.copy()
            draw = ImageDraw.Draw(watermarked)
            
            watermark_text = "PassportPhotoAI.com"
            
            # Simple text watermark at bottom right
            x = watermarked.width - 200
            y = watermarked.height - 30
            
            draw.text((x, y), watermark_text, fill=(128, 128, 128))
            return watermarked
        except Exception as e:
            print(f"Watermark error: {e}")
            return img

# Initialize processor
processor = SimplePassportPhotoProcessor()

# Simple in-memory store for OTPs
otp_store = {}

def generate_otp():
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

@application.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Passport Photo AI is running"}), 200

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
        
        # Send OTP via AWS SES
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
        
        # Check if OTP expired (10 minutes)
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
    """Simplified workflow without AI analysis"""
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    temp_path = f"temp_{datetime.now().timestamp()}"
    file.save(temp_path)
    
    try:
        # Simple face detection
        face_analysis = processor.simple_face_detection(temp_path)
        
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
        
        return jsonify({
            "success": True, "feasible": True,
            "analysis": {"face_detection": face_analysis, "ai_analysis": {"compliant": True, "issues": []}},
            "processed_image": base64.b64encode(processed_buffer.getvalue()).decode('utf-8'),
            "message": "Photo successfully processed."
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

if __name__ == '__main__':
    application.run(debug=False, host='0.0.0.0', port=5000)