#!/usr/bin/env python3
"""
Compare input and output images to analyze the intelligent cropping results
"""

import os
from PIL import Image
import numpy as np

def analyze_image_quality(img_path):
    """Analyze basic image quality metrics"""
    if not os.path.exists(img_path):
        return None
    
    img = Image.open(img_path)
    
    # Convert to numpy for analysis
    img_array = np.array(img)
    
    # Basic quality metrics
    if len(img_array.shape) == 3:
        # Color image
        brightness = np.mean(img_array)
        contrast = np.std(img_array)
    else:
        # Grayscale
        brightness = np.mean(img_array)
        contrast = np.std(img_array)
    
    # Calculate sharpness (Laplacian variance)
    gray = img.convert('L')
    gray_array = np.array(gray)
    
    # Simple sharpness metric using gradient
    grad_x = np.gradient(gray_array, axis=1)
    grad_y = np.gradient(gray_array, axis=0)
    sharpness = np.sqrt(grad_x**2 + grad_y**2).mean()
    
    return {
        'size': img.size,
        'mode': img.mode,
        'brightness': brightness,
        'contrast': contrast,
        'sharpness': sharpness,
        'file_size': os.path.getsize(img_path)
    }

def compare_images():
    """Compare input and output images"""
    
    print("🔍 IMAGE COMPARISON ANALYSIS")
    print("=" * 80)
    
    # Define input/output pairs
    comparisons = [
        {
            'name': 'faiz.png',
            'input': 'backend/test_images/faiz.png',
            'output': 'api_test_result_faiz.png'
        },
        {
            'name': 'sample_image_1.jpg',
            'input': 'backend/test_images/sample_image_1.jpg',
            'output': 'api_test_result_sample_image_1.jpg'
        },
        {
            'name': 'sample_image_2.jpg',
            'input': 'backend/test_images/sample_image_2.jpg',
            'output': 'api_test_result_sample_image_2.jpg'
        },
        {
            'name': 'faiz_with_glasses.png',
            'input': 'backend/test_images/faiz_with_glasses.png',
            'output': 'api_test_result_faiz_with_glasses.png'
        }
    ]
    
    for comp in comparisons:
        print(f"\n📸 COMPARING: {comp['name']}")
        print("-" * 60)
        
        # Analyze input
        input_metrics = analyze_image_quality(comp['input'])
        output_metrics = analyze_image_quality(comp['output'])
        
        if not input_metrics:
            print(f"❌ Input image not found: {comp['input']}")
            continue
            
        if not output_metrics:
            print(f"❌ Output image not found: {comp['output']}")
            continue
        
        print(f"📐 INPUT  | Size: {input_metrics['size']} | Mode: {input_metrics['mode']}")
        print(f"📐 OUTPUT | Size: {output_metrics['size']} | Mode: {output_metrics['mode']}")
        
        # Size change
        input_pixels = input_metrics['size'][0] * input_metrics['size'][1]
        output_pixels = output_metrics['size'][0] * output_metrics['size'][1]
        size_change = output_pixels / input_pixels
        print(f"📊 Size change: {size_change:.2f}x ({input_pixels:,} → {output_pixels:,} pixels)")
        
        # Quality metrics comparison
        brightness_change = (output_metrics['brightness'] - input_metrics['brightness']) / input_metrics['brightness'] * 100
        contrast_change = (output_metrics['contrast'] - input_metrics['contrast']) / input_metrics['contrast'] * 100
        sharpness_change = (output_metrics['sharpness'] - input_metrics['sharpness']) / input_metrics['sharpness'] * 100
        
        print(f"💡 Brightness: {input_metrics['brightness']:.1f} → {output_metrics['brightness']:.1f} ({brightness_change:+.1f}%)")
        print(f"🎨 Contrast:   {input_metrics['contrast']:.1f} → {output_metrics['contrast']:.1f} ({contrast_change:+.1f}%)")
        print(f"🔍 Sharpness:  {input_metrics['sharpness']:.1f} → {output_metrics['sharpness']:.1f} ({sharpness_change:+.1f}%)")
        
        # File size
        size_change_mb = (output_metrics['file_size'] - input_metrics['file_size']) / (1024*1024)
        print(f"💾 File size:  {input_metrics['file_size']/1024:.1f}KB → {output_metrics['file_size']/1024:.1f}KB ({size_change_mb:+.1f}MB)")
        
        # Quality assessment
        quality_issues = []
        if sharpness_change < -20:
            quality_issues.append("⚠️ Significant sharpness loss")
        if brightness_change > 20 or brightness_change < -20:
            quality_issues.append("⚠️ Significant brightness change")
        if contrast_change < -30:
            quality_issues.append("⚠️ Significant contrast loss")
        if size_change > 10:
            quality_issues.append("⚠️ Excessive upscaling")
        
        if quality_issues:
            print(f"🚨 Quality Issues:")
            for issue in quality_issues:
                print(f"   {issue}")
        else:
            print(f"✅ No major quality issues detected")
    
    print(f"\n📁 OUTPUT FILES LOCATION:")
    print(f"   All processed images are saved in the current directory")
    print(f"   Files: api_test_result_*.jpg/png")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   1. Open the output images to visually inspect quality")
    print(f"   2. Compare face positioning and cropping results")
    print(f"   3. Check for artifacts, distortion, or quality loss")
    print(f"   4. Verify that intelligent cropping improved passport compliance")

def create_side_by_side_info():
    """Create a text file with detailed comparison info"""
    
    info_content = """
# IMAGE COMPARISON RESULTS

## Files to Check:

### Input Images (Original):
- backend/test_images/faiz.png
- backend/test_images/sample_image_1.jpg  
- backend/test_images/sample_image_2.jpg
- backend/test_images/faiz_with_glasses.png

### Output Images (Processed):
- api_test_result_faiz.png
- api_test_result_sample_image_1.jpg
- api_test_result_sample_image_2.jpg
- api_test_result_faiz_with_glasses.png

## What to Look For:

1. **Face Positioning**: Is the face better centered and sized for passport photos?
2. **Image Quality**: Are there artifacts, pixelation, or distortion?
3. **Background**: Is the background properly removed and replaced with white?
4. **Eye Visibility**: Are the eyes clearly visible and properly positioned?
5. **Overall Compliance**: Does the output look more passport-ready?

## Test Results Summary:

- faiz.png: 50.0% compliance score (intelligent cropping applied)
- sample_image_1.jpg: 75.0% compliance score (no cropping needed)
- sample_image_2.jpg: 25.0% compliance score (intelligent cropping applied)  
- faiz_with_glasses.png: 0.0% compliance score (intelligent cropping applied) ⚠️ CONCERNING

## Key Concerns:

The faiz_with_glasses.png result shows 0.0% compliance - this suggests the intelligent 
cropping algorithm may be too aggressive or has bugs that need fixing.
"""
    
    with open('image_comparison_guide.txt', 'w') as f:
        f.write(info_content)
    
    print(f"\n📄 Created image_comparison_guide.txt with detailed analysis instructions")

if __name__ == "__main__":
    compare_images()
    create_side_by_side_info()