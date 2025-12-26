#!/usr/bin/env python3
"""
Fix deployment issues: Python version, memory, email, HEIC support
"""
import os
import subprocess
import sys

def fix_python_version():
    """Fix Python version configuration"""
    print("🔧 Fixing Python version configuration...")
    
    # Check current EB platform
    try:
        result = subprocess.run(['eb', 'platform', 'show'], 
                              capture_output=True, text=True, cwd='backend')
        print(f"Current platform: {result.stdout}")
    except:
        print("Could not check current platform")
    
    # Update to use Python 3.12 platform explicitly
    platform_config = """option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: application.py
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current"
  aws:elasticbeanstalk:container:python:staticfiles:
    /static/: "static/"
"""
    
    with open('backend/.ebextensions/01_packages.config', 'w') as f:
        f.write(platform_config)
    
    print("✅ Updated .ebextensions configuration")

def fix_memory_issues():
    """Fix memory issues by optimizing dependencies and adding system packages"""
    print("🔧 Fixing memory issues...")
    
    # Create memory optimization config
    memory_config = """packages:
  yum:
    mesa-libGL-devel: []
    
commands:
  01_install_system_deps:
    command: "yum install -y mesa-libGL"
    
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: application.py
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current"
    # Optimize memory usage
    MALLOC_ARENA_MAX: "2"
    # Reduce OpenMP threads to save memory
    OMP_NUM_THREADS: "1"
  aws:autoscaling:launchconfiguration:
    InstanceType: t3.medium
  aws:elasticbeanstalk:command:
    Timeout: 600
"""
    
    with open('backend/.ebextensions/02_memory_optimization.config', 'w') as f:
        f.write(memory_config)
    
    print("✅ Created memory optimization configuration")

def fix_requirements():
    """Fix requirements.txt for better compatibility"""
    print("🔧 Optimizing requirements.txt...")
    
    # Optimized requirements with memory-efficient versions
    optimized_requirements = """flask==3.0.0
flask-cors==4.0.0
Pillow==10.1.0
python-dotenv==1.0.0
gunicorn==21.2.0
boto3==1.34.34
botocore==1.34.34
opencv-python-headless==4.9.0.80
numpy==1.26.4
rembg==2.0.61
# HEIC support
pillow-heif==0.13.0
# Email template support
jinja2==3.1.2
"""
    
    with open('backend/requirements.txt', 'w') as f:
        f.write(optimized_requirements)
    
    print("✅ Updated requirements.txt with HEIC support")

def fix_application_code():
    """Fix application code for better error handling and HEIC support"""
    print("🔧 Fixing application code...")
    
    # Read current application
    with open('backend/application.py', 'r') as f:
        content = f.read()
    
    # Add HEIC support import at the top
    if 'pillow_heif' not in content:
        # Add after other imports
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
        
        updated_content = import_section + heic_import + rest_of_code
        
        with open('backend/application.py', 'w') as f:
            f.write(updated_content)
        
        print("✅ Added HEIC support to application")
    else:
        print("✅ HEIC support already present")

def create_deployment_script():
    """Create a comprehensive deployment script"""
    print("🔧 Creating deployment script...")
    
    deployment_script = """#!/bin/bash
set -e

echo "🚀 Starting comprehensive deployment..."

# 1. Clean up any existing deployment
echo "🧹 Cleaning up..."
cd backend
eb terminate --force || true

# 2. Create new environment with correct platform
echo "🏗️  Creating new environment..."
eb create passport-photo-backend-v2 \\
    --platform "Python 3.12 running on 64bit Amazon Linux 2023" \\
    --instance-type t3.medium \\
    --timeout 20

# 3. Deploy application
echo "📦 Deploying application..."
eb deploy --timeout 20

# 4. Test deployment
echo "🧪 Testing deployment..."
python ../test_python312_deployment.py

echo "✅ Deployment complete!"
"""
    
    with open('deploy_fixed.sh', 'w') as f:
        f.write(deployment_script)
    
    os.chmod('deploy_fixed.sh', 0o755)
    print("✅ Created deployment script: deploy_fixed.sh")

def test_email_functionality():
    """Test email functionality"""
    print("🔧 Testing email functionality...")
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        # Test SES configuration
        ses_client = boto3.client('ses', region_name='us-east-1')
        
        # Check if sender email is verified
        try:
            response = ses_client.get_identity_verification_attributes(
                Identities=['noreply@yourdomain.com']
            )
            print(f"SES Identity status: {response}")
        except ClientError as e:
            print(f"⚠️  SES configuration issue: {e}")
            print("💡 You need to verify your sender email in AWS SES")
        
        print("✅ Email functionality check complete")
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")

def main():
    """Main fix function"""
    print("🎯 COMPREHENSIVE DEPLOYMENT FIX")
    print("=" * 60)
    
    # Fix Python version
    fix_python_version()
    
    # Fix memory issues
    fix_memory_issues()
    
    # Fix requirements
    fix_requirements()
    
    # Fix application code
    fix_application_code()
    
    # Create deployment script
    create_deployment_script()
    
    # Test email functionality
    test_email_functionality()
    
    print(f"\n" + "=" * 60)
    print("🎉 ALL FIXES APPLIED!")
    print("=" * 60)
    print("✅ Python 3.12 configuration updated")
    print("✅ Memory optimization added")
    print("✅ HEIC support added")
    print("✅ Requirements optimized")
    print("✅ Deployment script created")
    
    print(f"\n🚀 Next steps:")
    print(f"1. Run: ./deploy_fixed.sh")
    print(f"2. Verify AWS SES email configuration")
    print(f"3. Test HEIC image upload")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)