#!/usr/bin/env python3
"""
Pre-deployment verification checklist
Ensures everything is ready for AWS deployment
"""

import os
import json
import subprocess
import sys

def check_backend_ready():
    """Check if backend is ready for deployment"""
    print("🔍 CHECKING BACKEND READINESS")
    print("-" * 40)
    
    checks = []
    
    # Check if application.py exists and imports correctly
    try:
        sys.path.append('backend')
        import application
        checks.append(("✅", "Backend imports successfully"))
    except Exception as e:
        checks.append(("❌", f"Backend import failed: {e}"))
    
    # Check requirements.txt
    if os.path.exists('backend/requirements.txt'):
        with open('backend/requirements.txt', 'r') as f:
            requirements = f.read()
            if 'rembg==2.0.61' in requirements:
                checks.append(("✅", "rembg dependency included"))
            else:
                checks.append(("❌", "rembg dependency missing"))
            
            if 'opencv-python-headless' in requirements:
                checks.append(("✅", "OpenCV dependency included"))
            else:
                checks.append(("❌", "OpenCV dependency missing"))
    else:
        checks.append(("❌", "requirements.txt missing"))
    
    # Check if learned_profile.json exists
    if os.path.exists('backend/learned_profile.json'):
        checks.append(("✅", "learned_profile.json exists"))
    else:
        checks.append(("⚠️", "learned_profile.json missing (will use basic validation)"))
    
    for status, message in checks:
        print(f"{status} {message}")
    
    return all(status == "✅" for status, _ in checks if status != "⚠️")

def check_frontend_ready():
    """Check if frontend is ready for deployment"""
    print("\n🔍 CHECKING FRONTEND READINESS")
    print("-" * 40)
    
    checks = []
    
    # Check if build exists
    if os.path.exists('frontend/build'):
        checks.append(("✅", "Frontend build directory exists"))
        
        # Check if index.html exists in build
        if os.path.exists('frontend/build/index.html'):
            checks.append(("✅", "index.html exists in build"))
        else:
            checks.append(("❌", "index.html missing in build"))
    else:
        checks.append(("❌", "Frontend build directory missing"))
    
    # Check if deployment zip exists
    if os.path.exists('frontend/passport-photo-frontend.zip'):
        checks.append(("✅", "Deployment zip created"))
    else:
        checks.append(("❌", "Deployment zip missing"))
    
    # Check package.json
    if os.path.exists('frontend/package.json'):
        with open('frontend/package.json', 'r') as f:
            package_data = json.load(f)
            if 'build' in package_data.get('scripts', {}):
                checks.append(("✅", "Build script exists"))
            else:
                checks.append(("❌", "Build script missing"))
    else:
        checks.append(("❌", "package.json missing"))
    
    # Check amplify.yml
    if os.path.exists('frontend/amplify.yml'):
        checks.append(("✅", "amplify.yml configuration exists"))
    else:
        checks.append(("❌", "amplify.yml missing"))
    
    for status, message in checks:
        print(f"{status} {message}")
    
    return all(status == "✅" for status, _ in checks)

def check_deployment_scripts():
    """Check if deployment scripts are ready"""
    print("\n🔍 CHECKING DEPLOYMENT SCRIPTS")
    print("-" * 40)
    
    checks = []
    
    scripts = [
        'deploy_without_s3.sh',
        'deploy_amplify_frontend.sh',
        'DEPLOYMENT_GUIDE.md'
    ]
    
    for script in scripts:
        if os.path.exists(script):
            checks.append(("✅", f"{script} exists"))
        else:
            checks.append(("❌", f"{script} missing"))
    
    for status, message in checks:
        print(f"{status} {message}")
    
    return all(status == "✅" for status, _ in checks)

def main():
    """Run all pre-deployment checks"""
    print("🚀 PRE-DEPLOYMENT VERIFICATION")
    print("=" * 50)
    
    backend_ready = check_backend_ready()
    frontend_ready = check_frontend_ready()
    scripts_ready = check_deployment_scripts()
    
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT READINESS SUMMARY")
    print("=" * 50)
    
    print(f"{'✅' if backend_ready else '❌'} Backend Ready: {backend_ready}")
    print(f"{'✅' if frontend_ready else '❌'} Frontend Ready: {frontend_ready}")
    print(f"{'✅' if scripts_ready else '❌'} Scripts Ready: {scripts_ready}")
    
    all_ready = backend_ready and frontend_ready and scripts_ready
    
    if all_ready:
        print("\n🎉 ALL SYSTEMS GO! Ready for deployment!")
        print("\n📋 DEPLOYMENT STEPS:")
        print("1. Deploy Backend: ./deploy_without_s3.sh")
        print("2. Deploy Frontend: ./deploy_amplify_frontend.sh")
        print("3. Follow DEPLOYMENT_GUIDE.md for detailed instructions")
        return True
    else:
        print("\n⚠️  Some checks failed. Fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)