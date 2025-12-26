#!/usr/bin/env python3
"""
Quick fix for critical issues without creating new environment
"""
import os

def main():
    print("🎯 QUICK FIX FOR CRITICAL ISSUES")
    print("=" * 50)
    
    # 1. Create lightweight requirements (remove rembg temporarily)
    print("🔧 Creating lightweight requirements...")
    lightweight_requirements = """flask==3.0.0
flask-cors==4.0.0
Pillow==10.1.0
python-dotenv==1.0.0
gunicorn==21.2.0
boto3==1.34.34
opencv-python-headless==4.9.0.80
numpy==1.26.4
pillow-heif==0.13.0
jinja2==3.1.2"""
    
    with open('backend/requirements.txt', 'w') as f:
        f.write(lightweight_requirements)
    print("✅ Removed rembg temporarily to fix memory issues")
    
    # 2. Update application to handle missing rembg gracefully
    print("🔧 Updating application for graceful rembg handling...")
    
    with open('backend/application.py', 'r') as f:
        content = f.read()
    
    # Add HEIC support if not present
    if 'pillow_heif' not in content:
        import_section = content.split('load_dotenv()')[0]
        rest_of_code = 'load_dotenv()' + content.split('load_dotenv()')[1]
        
        heic_import = """
# HEIC image support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORT = True
    print("HEIC support enabled")
except ImportError:
    HEIC_SUPPORT = False
    print("HEIC support not available")

"""
        
        content = import_section + heic_import + rest_of_code
    
    # Make rembg import optional
    content = content.replace(
        'from rembg import remove, new_session',
        '''try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
    print("rembg available")
except ImportError:
    REMBG_AVAILABLE = False
    print("rembg not available - background removal disabled")'''
    )
    
    # Update the background removal method
    content = content.replace(
        'def remove_background_rembg_lightweight(self, img):',
        '''def remove_background_rembg_lightweight(self, img):'''
    )
    
    # Add rembg availability check
    if 'if not REMBG_AVAILABLE:' not in content:
        content = content.replace(
            '"""Professional background removal using lightweight rembg model"""',
            '''"""Professional background removal using lightweight rembg model"""
        if not REMBG_AVAILABLE:
            print("rembg not available, using OpenCV fallback")
            return self.remove_background_opencv_fallback(img)'''
        )
    
    with open('backend/application.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated application for graceful rembg handling")
    
    # 3. Update email configuration
    print("🔧 Updating email configuration...")
    
    # Update the sender email in application
    content = content.replace(
        "sender_email = os.environ.get('SENDER_EMAIL', 'noreply@yourdomain.com')",
        "sender_email = os.environ.get('SENDER_EMAIL', 'faiz.24365@gmail.com')"
    )
    
    with open('backend/application.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated email configuration")
    
    # 4. Create memory optimization config
    print("🔧 Creating memory optimization...")
    
    memory_config = """option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: application.py
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current"
    SENDER_EMAIL: "faiz.24365@gmail.com"
    MALLOC_ARENA_MAX: "2"
    OMP_NUM_THREADS: "1"
  aws:elasticbeanstalk:command:
    Timeout: 600
"""
    
    with open('backend/.ebextensions/01_memory_optimization.config', 'w') as f:
        f.write(memory_config)
    
    print("✅ Created memory optimization config")
    
    print(f"\n" + "=" * 50)
    print("🎉 QUICK FIXES APPLIED!")
    print("=" * 50)
    print("✅ Removed rembg (memory issue)")
    print("✅ Added HEIC support")
    print("✅ Fixed email configuration")
    print("✅ Added memory optimization")
    print("✅ Graceful error handling")
    
    print(f"\n🚀 Ready to deploy:")
    print(f"cd backend && eb deploy")
    
    return True

if __name__ == "__main__":
    main()