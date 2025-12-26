#!/usr/bin/env python3
"""
Project Organization Script
Cleans up and organizes files to maintain a clean project structure
"""

import os
import shutil
import glob
from datetime import datetime


class ProjectOrganizer:
    """Organizes project files into appropriate directories"""
    
    def __init__(self):
        self.root_dir = "."
        self.backup_dir = "archived_files"
        self.temp_outputs_dir = "temp_outputs"
        
    def create_directories(self):
        """Create organization directories if they don't exist"""
        dirs_to_create = [
            self.backup_dir,
            self.temp_outputs_dir,
            "archived_test_files",
            "archived_images",
            "archived_scripts"
        ]
        
        for dir_name in dirs_to_create:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                print(f"✅ Created directory: {dir_name}")
    
    def move_test_output_images(self):
        """Move test output images to temp_outputs directory"""
        print("\n📁 Organizing test output images...")
        
        # Patterns for test output images
        test_image_patterns = [
            "test_*.jpg",
            "test_*.png", 
            "debug_*.jpg",
            "debug_*.png",
            "user_*.jpg",
            "*_result.jpg",
            "*_output.jpg",
            "*_removed.jpg"
        ]
        
        moved_count = 0
        for pattern in test_image_patterns:
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    dest_path = os.path.join(self.temp_outputs_dir, os.path.basename(file_path))
                    shutil.move(file_path, dest_path)
                    print(f"  Moved: {file_path} → {dest_path}")
                    moved_count += 1
        
        print(f"✅ Moved {moved_count} test output images")
    
    def organize_debug_scripts(self):
        """Move debug and test scripts to appropriate directories"""
        print("\n📁 Organizing debug and test scripts...")
        
        # Debug scripts to move
        debug_scripts = [
            "debug_face_detection_detailed.py",
            "debug_synthetic_face.py",
            "test_comprehensive_local.py",
            "test_face_detection_simple.py", 
            "test_full_workflow_local.py",
            "test_like_real_user.py",
            "test_real_image.py",
            "test_rembg_local.py",
            "test_small_models.py",
            "evaluate_against_gold_standard.py"
        ]
        
        moved_count = 0
        for script in debug_scripts:
            if os.path.exists(script):
                dest_path = os.path.join("archived_test_files", script)
                shutil.move(script, dest_path)
                print(f"  Moved: {script} → {dest_path}")
                moved_count += 1
        
        print(f"✅ Moved {moved_count} debug/test scripts")
    
    def organize_deployment_files(self):
        """Organize deployment and configuration files"""
        print("\n📁 Organizing deployment files...")
        
        # Create deployment subdirectories
        deployment_dirs = ["deployment/scripts", "deployment/docs", "deployment/configs"]
        for dir_name in deployment_dirs:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
        
        # Move deployment scripts
        deployment_scripts = [
            "deploy_railway.sh",
            "deploy_s3_static.sh", 
            "deploy_vercel.sh",
            "deploy-backend.sh",
            "deploy-email-backend.sh",
            "deploy-email-simple.sh",
            "deploy-frontend.sh",
            "deploy-full-app.sh",
            "check-aws-costs.sh",
            "fix_https_mixed_content.sh"
        ]
        
        moved_count = 0
        for script in deployment_scripts:
            if os.path.exists(script):
                dest_path = os.path.join("deployment/scripts", script)
                shutil.move(script, dest_path)
                print(f"  Moved: {script} → {dest_path}")
                moved_count += 1
        
        # Move deployment docs
        deployment_docs = [
            "AWS_NATIVE_SOLUTIONS.md",
            "COST_ANALYSIS_SOLUTIONS.md", 
            "ESSENTIAL_ONLY.md",
            "QUICK_HTTPS_FIX.md",
            "README_SIMPLE.md",
            "VERCEL_DEPLOYMENT.md",
            "backend_frontend_binding.md",
            "configure_vercel_app.md",
            "fix_vercel_auth.md"
        ]
        
        for doc in deployment_docs:
            if os.path.exists(doc):
                dest_path = os.path.join("deployment/docs", doc)
                shutil.move(doc, dest_path)
                print(f"  Moved: {doc} → {dest_path}")
                moved_count += 1
        
        print(f"✅ Organized {moved_count} deployment files")
    
    def clean_backend_directory(self):
        """Clean up backend directory"""
        print("\n📁 Cleaning backend directory...")
        
        backend_dir = "backend"
        
        # Move old application versions to archived
        old_applications = [
            "application_fixed.py",
            "application_hybrid_bg.py", 
            "application_lightweight.py",
            "application_minimal.py",
            "application-complete.py",
            "application-full.py",
            "application-hybrid-backup.py",
            "application-hybrid.py",
            "application-simple-backup.py",
            "application-with-email.py"
        ]
        
        archived_backend_dir = os.path.join("archived_files", "backend_versions")
        if not os.path.exists(archived_backend_dir):
            os.makedirs(archived_backend_dir)
        
        moved_count = 0
        for app_file in old_applications:
            app_path = os.path.join(backend_dir, app_file)
            if os.path.exists(app_path):
                dest_path = os.path.join(archived_backend_dir, app_file)
                shutil.move(app_path, dest_path)
                print(f"  Moved: {app_path} → {dest_path}")
                moved_count += 1
        
        # Move old test files
        old_test_files = [
            "test_deployed_app_backup.py",
            "test_deployed_app.py",
            "test_hybrid_functionality_backup.py", 
            "test_hybrid_functionality.py"
        ]
        
        for test_file in old_test_files:
            test_path = os.path.join(backend_dir, test_file)
            if os.path.exists(test_path):
                dest_path = os.path.join("archived_test_files", test_file)
                shutil.move(test_path, dest_path)
                print(f"  Moved: {test_path} → {dest_path}")
                moved_count += 1
        
        # Move test output images from backend
        backend_test_images = [
            "test_bg_removal_local.jpg",
            "test_person_image.jpg",
            "test_processed_output.jpg", 
            "test_watermark_3x_local.jpg"
        ]
        
        for img_file in backend_test_images:
            img_path = os.path.join(backend_dir, img_file)
            if os.path.exists(img_path):
                dest_path = os.path.join(self.temp_outputs_dir, img_file)
                shutil.move(img_path, dest_path)
                print(f"  Moved: {img_path} → {dest_path}")
                moved_count += 1
        
        print(f"✅ Cleaned {moved_count} files from backend directory")
    
    def create_readme_files(self):
        """Create README files for organized directories"""
        print("\n📝 Creating README files...")
        
        readme_contents = {
            self.temp_outputs_dir: """# Temporary Test Outputs

This directory contains temporary output files from tests and debugging:
- Test images generated during development
- Debug output files
- Temporary processing results

These files can be safely deleted periodically to save space.
""",
            
            "archived_test_files": """# Archived Test Files

This directory contains old test scripts and debugging files:
- Legacy test scripts
- Debug utilities
- Development tools

These are kept for reference but are not part of the main codebase.
""",
            
            "archived_files": """# Archived Files

This directory contains archived versions of files:
- Old application versions
- Legacy configurations
- Backup files

These are kept for historical reference and rollback purposes.
""",
            
            "deployment": """# Deployment Files

This directory contains all deployment-related files:
- `scripts/` - Deployment and maintenance scripts
- `docs/` - Deployment documentation and guides
- `configs/` - Configuration files for different environments

Use these files for deploying and managing the application in various environments.
"""
        }
        
        for dir_name, content in readme_contents.items():
            if os.path.exists(dir_name):
                readme_path = os.path.join(dir_name, "README.md")
                with open(readme_path, 'w') as f:
                    f.write(content)
                print(f"  Created: {readme_path}")
    
    def update_gitignore(self):
        """Update .gitignore to exclude temporary files"""
        print("\n📝 Updating .gitignore...")
        
        gitignore_additions = [
            "\n# Temporary test outputs",
            "temp_outputs/",
            "test_*.jpg",
            "test_*.png", 
            "debug_*.jpg",
            "debug_*.png",
            "user_*.jpg",
            "*_result.jpg",
            "*_output.jpg",
            "\n# Coverage reports",
            "htmlcov/",
            ".coverage",
            "\n# Pytest cache",
            ".pytest_cache/",
            "__pycache__/",
            "\n# Hypothesis cache", 
            ".hypothesis/"
        ]
        
        # Read current .gitignore
        gitignore_path = ".gitignore"
        existing_content = ""
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                existing_content = f.read()
        
        # Add new entries if they don't exist
        updated = False
        for entry in gitignore_additions:
            if entry.strip() and entry.strip() not in existing_content:
                existing_content += entry + "\n"
                updated = True
        
        if updated:
            with open(gitignore_path, 'w') as f:
                f.write(existing_content)
            print("✅ Updated .gitignore with temporary file patterns")
        else:
            print("✅ .gitignore already up to date")
    
    def generate_summary(self):
        """Generate organization summary"""
        print("\n" + "="*60)
        print("📊 PROJECT ORGANIZATION SUMMARY")
        print("="*60)
        
        # Count files in each directory
        directories = {
            "Main Project": ".",
            "Backend": "backend", 
            "Frontend": "frontend",
            "Tests": "backend/tests",
            "Enhancement": "backend/enhancement",
            "Temp Outputs": self.temp_outputs_dir,
            "Archived Files": "archived_files",
            "Archived Tests": "archived_test_files",
            "Deployment": "deployment"
        }
        
        for name, path in directories.items():
            if os.path.exists(path):
                file_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
                dir_count = len([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
                print(f"{name:15}: {file_count:3} files, {dir_count:2} directories")
        
        print("\n✅ Project organization completed!")
        print("📁 Temporary files moved to temp_outputs/")
        print("📚 Old files archived appropriately") 
        print("📖 README files created for organization")
    
    def run_organization(self):
        """Run the complete organization process"""
        print("🧹 Starting Project Organization")
        print("="*50)
        
        self.create_directories()
        self.move_test_output_images()
        self.organize_debug_scripts()
        self.organize_deployment_files()
        self.clean_backend_directory()
        self.create_readme_files()
        self.update_gitignore()
        self.generate_summary()


if __name__ == "__main__":
    organizer = ProjectOrganizer()
    organizer.run_organization()