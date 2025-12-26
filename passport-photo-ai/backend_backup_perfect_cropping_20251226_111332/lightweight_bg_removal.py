"""
Lightweight Background Removal for Passport Photos
Alternative to rembg for better Elastic Beanstalk compatibility
"""

import cv2
import numpy as np
from PIL import Image
import io


class LightweightBackgroundRemover:
    """Lightweight background removal using OpenCV and traditional computer vision"""
    
    def __init__(self):
        self.initialized = True
    
    def remove_background_grabcut(self, image: Image.Image) -> Image.Image:
        """
        Remove background using GrabCut algorithm
        Good for images with clear subject-background separation
        """
        # Convert PIL to OpenCV
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_cv = img_array
        
        height, width = img_cv.shape[:2]
        
        # Create mask
        mask = np.zeros((height, width), np.uint8)
        
        # Define rectangle around the center (assuming subject is centered)
        # Use 80% of image area, centered
        margin_x = int(width * 0.1)
        margin_y = int(height * 0.1)
        rect = (margin_x, margin_y, width - 2*margin_x, height - 2*margin_y)
        
        # Initialize foreground and background models
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        # Apply GrabCut
        cv2.grabCut(img_cv, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        
        # Create final mask
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        
        # Apply mask to create RGBA image
        img_rgba = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGBA)
        img_rgba[:, :, 3] = mask2 * 255
        
        # Convert back to PIL
        result_img = Image.fromarray(cv2.cvtColor(img_rgba, cv2.COLOR_BGRA2RGBA))
        
        # Convert to RGB with white background (passport standard)
        white_bg = Image.new('RGB', result_img.size, (255, 255, 255))
        if result_img.mode == 'RGBA':
            white_bg.paste(result_img, mask=result_img.split()[-1])
        else:
            white_bg = result_img
        
        return white_bg
    
    def remove_background_edge_detection(self, image: Image.Image) -> Image.Image:
        """
        Remove background using edge detection and flood fill
        Good for images with uniform backgrounds
        """
        # Convert to OpenCV
        img_array = np.array(image)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilate edges to close gaps
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create mask
        mask = np.zeros(gray.shape, np.uint8)
        
        if contours:
            # Find largest contour (assuming it's the person)
            largest_contour = max(contours, key=cv2.contourArea)
            cv2.fillPoly(mask, [largest_contour], 255)
        
        # Apply morphological operations to clean up mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Apply Gaussian blur to soften edges
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        # Create RGBA image
        img_rgba = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGBA)
        img_rgba[:, :, 3] = mask
        
        # Convert back to PIL and apply white background
        result_img = Image.fromarray(cv2.cvtColor(img_rgba, cv2.COLOR_BGRA2RGBA))
        white_bg = Image.new('RGB', result_img.size, (255, 255, 255))
        if result_img.mode == 'RGBA':
            white_bg.paste(result_img, mask=result_img.split()[-1])
        else:
            white_bg = result_img
        
        return white_bg
    
    def remove_background_adaptive(self, image: Image.Image) -> Image.Image:
        """
        Adaptive background removal that tries multiple methods
        """
        try:
            # Try GrabCut first (usually better for portraits)
            result = self.remove_background_grabcut(image)
            
            # Basic quality check - if result is mostly white, try edge detection
            result_array = np.array(result)
            white_pixels = np.sum(np.all(result_array > 240, axis=2))
            total_pixels = result_array.shape[0] * result_array.shape[1]
            
            if white_pixels / total_pixels > 0.8:  # If more than 80% white, try alternative
                result = self.remove_background_edge_detection(image)
            
            return result
            
        except Exception as e:
            print(f"Background removal failed: {e}")
            # Return original image with white background if all methods fail
            if image.mode != 'RGB':
                return image.convert('RGB')
            return image


def create_simple_background_remover():
    """Factory function to create background remover"""
    return LightweightBackgroundRemover()


# Test function
def test_lightweight_bg_removal():
    """Test the lightweight background removal"""
    try:
        # Create test image
        test_img = Image.new('RGB', (400, 400), 'lightblue')
        
        # Add a simple "person" shape
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_img)
        draw.ellipse([150, 100, 250, 300], fill='brown')  # Head/body
        draw.ellipse([175, 120, 225, 170], fill='peach')  # Face
        
        # Test background removal
        remover = LightweightBackgroundRemover()
        result = remover.remove_background_adaptive(test_img)
        
        # Save result
        result.save('test_lightweight_bg_removal.jpg', quality=95)
        print("✅ Lightweight background removal test successful!")
        print("   Saved: test_lightweight_bg_removal.jpg")
        
        return True
        
    except Exception as e:
        print(f"❌ Lightweight background removal test failed: {e}")
        return False


if __name__ == "__main__":
    test_lightweight_bg_removal()