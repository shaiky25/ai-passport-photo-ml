#!/usr/bin/env python3
"""
Evaluate output quality against gold standard passport photo requirements
"""

import requests
import base64
from PIL import Image, ImageStat
import io
import json
import os
import numpy as np

BACKEND_URL = "http://localhost:5000"

class PassportPhotoEvaluator:
    def __init__(self):
        # Official passport photo standards (US/International)
        self.GOLD_STANDARDS = {
            'dimensions': {
                'min_pixels': (600, 600),
                'preferred_pixels': (1200, 1200),
                'aspect_ratio': 1.0,  # Square
                'dpi': 300
            },
            'head_positioning': {
                'head_height_min': 0.50,  # 50% of image height
                'head_height_max': 0.69,  # 69% of image height
                'head_center_tolerance': 0.1,  # Within 10% of center
                'eye_level_min': 0.56,  # Eyes at 56% from bottom
                'eye_level_max': 0.69   # Eyes at 69% from bottom
            },
            'background': {
                'color_uniformity': 0.95,  # 95% uniform
                'brightness_min': 200,     # Light background (0-255)
                'brightness_max': 255,
                'contrast_ratio': 3.0      # Minimum contrast with subject
            },
            'image_quality': {
                'sharpness_min': 0.7,     # Sharpness metric
                'noise_max': 0.1,         # Maximum noise level
                'compression_quality_min': 90  # JPEG quality
            },
            'lighting': {
                'even_illumination': 0.8,  # Even lighting score
                'no_shadows': True,
                'no_red_eye': True
            }
        }
    
    def load_test_images(self):
        """Load our generated test images"""
        images = {}
        test_files = [
            'user_test_photo.jpg',           # Original
            'user_result_no_bg_removal.jpg', # Basic processing
            'user_result_with_bg_removal.jpg', # With background removal
            'user_final_result.jpg'          # Final result
        ]
        
        for filename in test_files:
            if os.path.exists(filename):
                try:
                    img = Image.open(filename)
                    images[filename] = img
                    print(f"✅ Loaded: {filename} ({img.size})")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")
            else:
                print(f"⚠️  File not found: {filename}")
        
        return images
    
    def evaluate_dimensions(self, img, filename):
        """Evaluate image dimensions against standards"""
        width, height = img.size
        aspect_ratio = width / height
        
        standards = self.GOLD_STANDARDS['dimensions']
        
        # Check minimum size
        min_size_ok = width >= standards['min_pixels'][0] and height >= standards['min_pixels'][1]
        
        # Check preferred size
        preferred_size_ok = width >= standards['preferred_pixels'][0] and height >= standards['preferred_pixels'][1]
        
        # Check aspect ratio
        aspect_ratio_ok = abs(aspect_ratio - standards['aspect_ratio']) < 0.05
        
        score = 0
        max_score = 4
        
        if min_size_ok: score += 1
        if preferred_size_ok: score += 1
        if aspect_ratio_ok: score += 2  # More important
        
        return {
            'category': 'Dimensions',
            'score': score / max_score,
            'details': {
                'size': f"{width}x{height}",
                'aspect_ratio': round(aspect_ratio, 3),
                'min_size_ok': min_size_ok,
                'preferred_size_ok': preferred_size_ok,
                'aspect_ratio_ok': aspect_ratio_ok
            }
        }
    
    def evaluate_background(self, img, filename):
        """Evaluate background quality"""
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Sample background areas (corners and edges)
        width, height = img.size
        background_samples = []
        
        # Corner samples
        corner_size = min(50, width//10, height//10)
        corners = [
            (0, 0, corner_size, corner_size),  # Top-left
            (width-corner_size, 0, width, corner_size),  # Top-right
            (0, height-corner_size, corner_size, height),  # Bottom-left
            (width-corner_size, height-corner_size, width, height)  # Bottom-right
        ]
        
        for corner in corners:
            corner_img = img.crop(corner)
            avg_color = ImageStat.Stat(corner_img).mean
            background_samples.append(avg_color)
        
        # Calculate uniformity
        if background_samples:
            # Calculate variance in background colors
            r_values = [sample[0] for sample in background_samples]
            g_values = [sample[1] for sample in background_samples]
            b_values = [sample[2] for sample in background_samples]
            
            r_var = np.var(r_values)
            g_var = np.var(g_values)
            b_var = np.var(b_values)
            
            # Average brightness
            avg_brightness = np.mean([sum(sample)/3 for sample in background_samples])
            
            # Uniformity score (lower variance = higher uniformity)
            max_variance = 50  # Threshold for acceptable variance
            uniformity = max(0, 1 - (r_var + g_var + b_var) / (3 * max_variance))
            
            # Brightness score
            standards = self.GOLD_STANDARDS['background']
            brightness_ok = standards['brightness_min'] <= avg_brightness <= standards['brightness_max']
            
            score = 0
            max_score = 3
            
            if uniformity >= 0.8: score += 1
            if brightness_ok: score += 1
            if uniformity >= 0.95 and brightness_ok: score += 1  # Bonus for excellent background
            
            return {
                'category': 'Background',
                'score': score / max_score,
                'details': {
                    'uniformity': round(uniformity, 3),
                    'avg_brightness': round(avg_brightness, 1),
                    'brightness_ok': brightness_ok,
                    'corner_colors': [(round(r), round(g), round(b)) for r, g, b in background_samples]
                }
            }
        
        return {
            'category': 'Background',
            'score': 0,
            'details': {'error': 'Could not analyze background'}
        }
    
    def evaluate_image_quality(self, img, filename):
        """Evaluate overall image quality"""
        # Convert to grayscale for analysis
        gray_img = img.convert('L')
        img_array = np.array(gray_img)
        
        # Sharpness estimation (using Laplacian variance)
        from scipy import ndimage
        try:
            laplacian = ndimage.laplace(img_array)
            sharpness = np.var(laplacian) / 10000  # Normalize
            sharpness = min(1.0, sharpness)  # Cap at 1.0
        except:
            sharpness = 0.5  # Default if scipy not available
        
        # Noise estimation (using local variance)
        try:
            # Simple noise estimation
            noise_kernel = np.ones((3,3)) / 9
            smoothed = ndimage.convolve(img_array.astype(float), noise_kernel)
            noise = np.mean(np.abs(img_array - smoothed)) / 255
        except:
            noise = 0.05  # Default low noise
        
        # Overall quality score
        score = 0
        max_score = 3
        
        if sharpness >= 0.3: score += 1  # Basic sharpness
        if sharpness >= 0.7: score += 1  # Good sharpness
        if noise <= 0.1: score += 1     # Low noise
        
        return {
            'category': 'Image Quality',
            'score': score / max_score,
            'details': {
                'sharpness': round(sharpness, 3),
                'noise_level': round(noise, 3),
                'sharpness_ok': sharpness >= 0.3,
                'noise_ok': noise <= 0.1
            }
        }
    
    def evaluate_face_compliance(self, filename):
        """Get face compliance from our backend"""
        try:
            with open(filename, 'rb') as f:
                files = {'image': (filename, f, 'image/jpeg')}
                data = {'remove_background': 'false', 'email': ''}
                
                response = requests.post(f"{BACKEND_URL}/api/full-workflow", files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result.get('analysis', {})
                    face_detection = analysis.get('face_detection', {})
                    
                    # Extract key metrics
                    faces_detected = face_detection.get('faces_detected', 0)
                    valid = face_detection.get('valid', False)
                    head_height = face_detection.get('head_height_percent', 0)
                    centered = face_detection.get('horizontally_centered', False)
                    
                    # Calculate compliance score
                    score = 0
                    max_score = 4
                    
                    if faces_detected > 0: score += 1
                    if valid: score += 2  # Most important
                    if 0.5 <= head_height <= 0.7: score += 1  # Proper head size
                    
                    return {
                        'category': 'Face Compliance',
                        'score': score / max_score,
                        'details': {
                            'faces_detected': faces_detected,
                            'valid': valid,
                            'head_height_percent': head_height,
                            'horizontally_centered': centered,
                            'compliance_issues': face_detection.get('error', 'None')
                        }
                    }
        except Exception as e:
            pass
        
        return {
            'category': 'Face Compliance',
            'score': 0,
            'details': {'error': 'Could not analyze face compliance'}
        }
    
    def calculate_overall_score(self, evaluations):
        """Calculate weighted overall score"""
        weights = {
            'Dimensions': 0.15,
            'Background': 0.35,      # Most important for passport photos
            'Image Quality': 0.25,
            'Face Compliance': 0.25
        }
        
        weighted_score = 0
        total_weight = 0
        
        for eval_result in evaluations:
            category = eval_result['category']
            if category in weights:
                weighted_score += eval_result['score'] * weights[category]
                total_weight += weights[category]
        
        return weighted_score / total_weight if total_weight > 0 else 0
    
    def get_grade(self, score):
        """Convert score to letter grade"""
        if score >= 0.9: return 'A+'
        elif score >= 0.8: return 'A'
        elif score >= 0.7: return 'B+'
        elif score >= 0.6: return 'B'
        elif score >= 0.5: return 'C+'
        elif score >= 0.4: return 'C'
        elif score >= 0.3: return 'D'
        else: return 'F'
    
    def evaluate_all_images(self):
        """Evaluate all test images against gold standards"""
        print("🏆 PASSPORT PHOTO GOLD STANDARD EVALUATION")
        print("=" * 60)
        print("Comparing our output against professional passport photo standards")
        print()
        
        images = self.load_test_images()
        
        if not images:
            print("❌ No test images found. Run test_like_real_user.py first.")
            return
        
        results = {}
        
        for filename, img in images.items():
            print(f"\n📊 Evaluating: {filename}")
            print("-" * 40)
            
            evaluations = []
            
            # Run all evaluations
            evaluations.append(self.evaluate_dimensions(img, filename))
            evaluations.append(self.evaluate_background(img, filename))
            evaluations.append(self.evaluate_image_quality(img, filename))
            evaluations.append(self.evaluate_face_compliance(filename))
            
            # Calculate overall score
            overall_score = self.calculate_overall_score(evaluations)
            grade = self.get_grade(overall_score)
            
            results[filename] = {
                'evaluations': evaluations,
                'overall_score': overall_score,
                'grade': grade
            }
            
            # Display results
            for eval_result in evaluations:
                score_percent = eval_result['score'] * 100
                print(f"  {eval_result['category']}: {score_percent:.1f}% {self.get_score_emoji(eval_result['score'])}")
                
                # Show key details
                details = eval_result['details']
                if eval_result['category'] == 'Background' and 'corner_colors' in details:
                    print(f"    Uniformity: {details['uniformity']:.2f}, Brightness: {details['avg_brightness']:.1f}")
                elif eval_result['category'] == 'Face Compliance' and 'faces_detected' in details:
                    print(f"    Faces: {details['faces_detected']}, Valid: {details['valid']}, Head: {details['head_height_percent']:.1f}%")
                elif eval_result['category'] == 'Image Quality':
                    print(f"    Sharpness: {details['sharpness']:.2f}, Noise: {details['noise_level']:.3f}")
            
            print(f"\n  🎯 Overall Score: {overall_score*100:.1f}% (Grade: {grade})")
        
        # Summary comparison
        print("\n" + "=" * 60)
        print("📈 COMPARATIVE ANALYSIS")
        print("=" * 60)
        
        # Find best performing image
        best_image = max(results.keys(), key=lambda k: results[k]['overall_score'])
        best_score = results[best_image]['overall_score']
        
        print(f"🥇 Best Result: {best_image}")
        print(f"   Score: {best_score*100:.1f}% (Grade: {results[best_image]['grade']})")
        
        # Show improvement from original to final
        if 'user_test_photo.jpg' in results and 'user_final_result.jpg' in results:
            original_score = results['user_test_photo.jpg']['overall_score']
            final_score = results['user_final_result.jpg']['overall_score']
            improvement = ((final_score - original_score) / original_score) * 100
            
            print(f"\n📊 Processing Improvement:")
            print(f"   Original: {original_score*100:.1f}%")
            print(f"   Final: {final_score*100:.1f}%")
            print(f"   Improvement: {improvement:+.1f}%")
        
        # Professional standards compliance
        print(f"\n🎖️  PROFESSIONAL COMPLIANCE:")
        for filename, result in results.items():
            score = result['overall_score']
            if score >= 0.8:
                compliance = "✅ Professional Quality"
            elif score >= 0.6:
                compliance = "⚠️  Acceptable with minor issues"
            elif score >= 0.4:
                compliance = "❌ Needs improvement"
            else:
                compliance = "❌ Not suitable for passport use"
            
            print(f"   {filename}: {compliance}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if best_score >= 0.8:
            print("✅ Output quality meets professional passport photo standards")
            print("✅ Ready for official document use")
        elif best_score >= 0.6:
            print("⚠️  Good quality but could be improved:")
            print("   - Consider better face detection for positioning")
            print("   - Ensure more uniform background")
        else:
            print("❌ Significant improvements needed:")
            print("   - Improve face detection accuracy")
            print("   - Better background removal/replacement")
            print("   - Enhanced image quality processing")
        
        return results
    
    def get_score_emoji(self, score):
        """Get emoji for score"""
        if score >= 0.9: return "🟢"
        elif score >= 0.7: return "🟡"
        elif score >= 0.5: return "🟠"
        else: return "🔴"

def main():
    evaluator = PassportPhotoEvaluator()
    results = evaluator.evaluate_all_images()
    
    if results:
        # Find the best result
        best_result = max(results.values(), key=lambda x: x['overall_score'])
        best_score = best_result['overall_score']
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        print(f"Best output achieves {best_score*100:.1f}% compliance with gold standards")
        
        if best_score >= 0.8:
            print("🎉 EXCELLENT: Ready for professional use!")
            return True
        elif best_score >= 0.6:
            print("👍 GOOD: Acceptable quality with room for improvement")
            return True
        else:
            print("⚠️  NEEDS WORK: Significant improvements required")
            return False
    
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)