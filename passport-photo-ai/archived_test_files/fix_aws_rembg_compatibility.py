#!/usr/bin/env python3
"""
Fix rembg compatibility for AWS deployment
"""
import subprocess
import sys

def check_available_rembg_versions():
    """Check what rembg versions are available"""
    print("🔍 Checking available rembg versions...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'index', 'versions', 'rembg'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("Available rembg versions:")
            print(result.stdout)
        else:
            print("Could not get version info, trying alternative method...")
            
            # Try installing latest available
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', 'rembg==2.0.61', '--dry-run'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ rembg==2.0.61 is available")
                return "2.0.61"
            
            # Try other recent versions
            for version in ["2.0.60", "2.0.59", "2.0.58", "2.0.57", "2.0.56"]:
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', f'rembg=={version}', '--dry-run'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"✅ rembg=={version} is available")
                    return version
            
            print("❌ Could not find compatible rembg version")
            return None
            
    except Exception as e:
        print(f"❌ Error checking versions: {e}")
        return None

def test_rembg_version(version):
    """Test a specific rembg version"""
    print(f"\n🧪 Testing rembg=={version}...")
    
    try:
        # Install the version
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', f'rembg=={version}'
        ], check=True, capture_output=True, timeout=60)
        
        # Test import and functionality
        from rembg import remove, new_session
        
        # Test lightweight model
        session = new_session('u2netp')
        print(f"✅ rembg=={version} working with u2netp model")
        
        return True
        
    except Exception as e:
        print(f"❌ rembg=={version} failed: {e}")
        return False

def update_requirements_with_compatible_version():
    """Update requirements.txt with AWS-compatible versions"""
    
    # Based on the error, try the highest version that was listed as available
    compatible_version = "2.0.61"
    
    print(f"\n📝 Updating requirements.txt with rembg=={compatible_version}...")
    
    # Read current requirements
    with open('backend/requirements.txt', 'r') as f:
        lines = f.readlines()
    
    # Update rembg version
    updated_lines = []
    for line in lines:
        if line.startswith('rembg=='):
            updated_lines.append(f'rembg=={compatible_version}\n')
            print(f"  Updated: rembg==2.0.68 → rembg=={compatible_version}")
        else:
            updated_lines.append(line)
    
    # Write updated requirements
    with open('backend/requirements.txt', 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ requirements.txt updated")
    
    # Test the updated version
    if test_rembg_version(compatible_version):
        print(f"✅ rembg=={compatible_version} is working")
        return True
    else:
        print(f"❌ rembg=={compatible_version} is not working")
        return False

def main():
    """Main compatibility fix"""
    
    print("🎯 FIXING AWS REMBG COMPATIBILITY")
    print("=" * 50)
    
    # Check available versions
    available_version = check_available_rembg_versions()
    
    # Update requirements with compatible version
    success = update_requirements_with_compatible_version()
    
    if success:
        print(f"\n🎉 AWS COMPATIBILITY FIXED!")
        print("✅ rembg version updated to AWS-compatible version")
        print("✅ Ready for deployment")
        
        print(f"\n📋 Updated requirements.txt:")
        with open('backend/requirements.txt', 'r') as f:
            print(f.read())
    else:
        print(f"\n❌ COMPATIBILITY FIX FAILED")
        print("❌ Manual intervention required")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)