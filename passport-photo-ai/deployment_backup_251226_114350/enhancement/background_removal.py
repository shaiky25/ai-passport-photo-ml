"""
Comprehensive Background Removal with Quality Evaluation
Combines rembg with quality assessment to ensure proper background removal
"""

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import io
import logging
from typing import Tuple, Optional, Dict, Any
from .data_models import FaceData

# Try to import rembg
try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
    logging.info("rembg available for background removal")
except ImportError:
    REMBG_AVAILABLE = False
    logging.warning("rembg not available - using fallback methods")

# Import lightweight fallback
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from lightweight_bg_removal import LightweightBackgroundRemover


class BackgroundRemovalQualityMetrics:
    """Metrics for evaluating background removal quality"""
    
    def __init__(self):
        self.edge_threshold = 0.1
        self.uniformity_threshold = 0.95
        self.person_preservation_threshold = 0.8
    
    def evaluate_background_uniformity(self, image: np.ndarray, face_data: Optional[FaceData] = None) -> float:
        """
        Evaluate how uniform the background is (should be white for passport photos)
        Returns score 0-1 where 1 is perfectly uniform white background
        """
        height, width = image.shape[:2]
        
        # Define background region (exclude person area if face detected)
        background_mask = np.ones((height, width), dtype=bool)
        
        if face_data:
            # Exclude face area and expand to approximate person area
            x, y, w, h = face_data.bounding_box
            # Expand face area to approximate full person (face is typically 1/7 of body height)
            person_height = int(h * 7)
            person_width = int(w * 2)
            person_x = max(0, x - person_width // 4)
            person_y = max(0, y - person_height // 8)
            person_x2 = min(width, person_x + person_width)
            person_y2 = min(height, person_y + person_height)
            
            background_mask[person_y:person_y2, person_x:person_x2] = False
        
        # Extract background pixels
        if len(image.shape) == 3:
            background_pixels = image[background_mask]
        else:
            background_pixels = image[background_mask].reshape(-1, 1)
        
        if len(background_pixels) == 0:
            return 0.0
        
        # Check uniformity - calculate standard deviation
        if len(image.shape) == 3:
            # For color images, check each channel
            std_r = np.std(background_pixels[:, 0])
            std_g = np.std(background_pixels[:, 1]) 
            std_b = np.std(background_pixels[:, 2])
            avg_std = (std_r + std_g + std_b) / 3
        else:
            avg_std = np.std(background_pixels)
        
        # Convert std to uniformity score (lower std = higher uniformity)
        uniformity_score = max(0, 1 - (avg_std / 50))  # Normalize by expected max std
        
        # Check if background is close to white (255, 255, 255)
        if len(image.shape) == 3:
            mean_color = np.mean(background_pixels, axis=0)
            whiteness_score = 1 - np.linalg.norm(mean_color - [255, 255, 255]) / (255 * np.sqrt(3))
        else:
            mean_gray = np.mean(background_pixels)
            whiteness_score = 1 - abs(mean_gray - 255) / 255
        
        # Combine uniformity and whiteness
        return (uniformity_score * 0.6 + whiteness_score * 0.4)
    
    def evaluate_edge_quality(self, image: np.ndarray, face_data: Optional[FaceData] = None) -> float:
        """
        Evaluate the quality of edges around the person (should be clean, not jagged)
        Returns score 0-1 where 1 is perfect edge quality
        """
        # Convert to grayscale for edge detection
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Detect edges using Canny
        edges = cv2.Canny(blurred, 50, 150)
        
        # Focus on person area if face detected
        if face_data:
            x, y, w, h = face_data.bounding_box
            # Expand to approximate person area
            person_height = int(h * 7)
            person_width = int(w * 2)
            person_x = max(0, x - person_width // 4)
            person_y = max(0, y - person_height // 8)
            person_x2 = min(image.shape[1], person_x + person_width)
            person_y2 = min(image.shape[0], person_y + person_height)
            
            # Create mask for person area
            person_mask = np.zeros_like(edges)
            person_mask[person_y:person_y2, person_x:person_x2] = 255
            edges = cv2.bitwise_and(edges, person_mask)
        
        # Analyze edge continuity and smoothness
        # Find contours from edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return 0.5  # No clear edges found
        
        # Evaluate largest contour (should be person outline)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate contour smoothness
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        
        # Smooth contours have fewer approximation points relative to arc length
        arc_length = cv2.arcLength(largest_contour, True)
        smoothness = 1 - min(1, len(approx) / (arc_length / 10))
        
        # Check for jagged edges by analyzing curvature
        if len(largest_contour) > 10:
            # Calculate local curvature variations
            curvatures = []
            for i in range(len(largest_contour)):
                p1 = largest_contour[i-1][0]
                p2 = largest_contour[i][0]
                p3 = largest_contour[(i+1) % len(largest_contour)][0]
                
                # Calculate angle between vectors
                v1 = p2 - p1
                v2 = p3 - p2
                
                if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                    cos_angle = np.clip(cos_angle, -1, 1)
                    angle = np.arccos(cos_angle)
                    curvatures.append(angle)
            
            if curvatures:
                curvature_variation = np.std(curvatures)
                curvature_score = max(0, 1 - curvature_variation)
            else:
                curvature_score = 0.5
        else:
            curvature_score = 0.5
        
        # Combine smoothness and curvature scores
        return (smoothness * 0.6 + curvature_score * 0.4)
    
    def evaluate_person_preservation(self, original: np.ndarray, processed: np.ndarray, face_data: Optional[FaceData] = None) -> float:
        """
        Evaluate how well the person is preserved (no parts cut off)
        Returns score 0-1 where 1 is perfect preservation
        """
        if face_data is None:
            # Without face data, use simple comparison
            return self._simple_preservation_check(original, processed)
        
        # Focus on person area around face
        x, y, w, h = face_data.bounding_box
        
        # Expand face area to approximate person area
        person_height = int(h * 7)
        person_width = int(w * 2)
        person_x = max(0, x - person_width // 4)
        person_y = max(0, y - person_height // 8)
        person_x2 = min(original.shape[1], person_x + person_width)
        person_y2 = min(original.shape[0], person_y + person_height)
        
        # Extract person regions
        orig_person = original[person_y:person_y2, person_x:person_x2]
        proc_person = processed[person_y:person_y2, person_x:person_x2]
        
        if orig_person.size == 0 or proc_person.size == 0:
            return 0.0
        
        # Calculate structural similarity
        if len(orig_person.shape) == 3:
            orig_gray = cv2.cvtColor(orig_person, cv2.COLOR_RGB2GRAY)
            proc_gray = cv2.cvtColor(proc_person, cv2.COLOR_RGB2GRAY)
        else:
            orig_gray = orig_person
            proc_gray = proc_person
        
        # Use normalized cross-correlation
        correlation = cv2.matchTemplate(orig_gray, proc_gray, cv2.TM_CCOEFF_NORMED)
        max_correlation = np.max(correlation) if correlation.size > 0 else 0
        
        # Check for missing parts by comparing edge density
        orig_edges = cv2.Canny(orig_gray, 50, 150)
        proc_edges = cv2.Canny(proc_gray, 50, 150)
        
        orig_edge_density = np.sum(orig_edges > 0) / orig_edges.size
        proc_edge_density = np.sum(proc_edges > 0) / proc_edges.size
        
        edge_preservation = min(1, proc_edge_density / (orig_edge_density + 1e-6))
        
        # Combine correlation and edge preservation
        return (max_correlation * 0.7 + edge_preservation * 0.3)
    
    def _simple_preservation_check(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Simple preservation check without face data"""
        # Convert to grayscale for comparison
        if len(original.shape) == 3:
            orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
        else:
            orig_gray = original
            
        if len(processed.shape) == 3:
            proc_gray = cv2.cvtColor(processed, cv2.COLOR_RGB2GRAY)
        else:
            proc_gray = processed
        
        # Calculate overall similarity
        correlation = cv2.matchTemplate(orig_gray, proc_gray, cv2.TM_CCOEFF_NORMED)
        return np.max(correlation) if correlation.size > 0 else 0.5


class ComprehensiveBackgroundRemover:
    """Comprehensive background removal with quality evaluation"""
    
    def __init__(self):
        self.quality_metrics = BackgroundRemovalQualityMetrics()
        self.fallback_remover = LightweightBackgroundRemover()
        
        # Initialize rembg session if available
        self.rembg_session = None
        if REMBG_AVAILABLE:
            try:
                # Use u2net model for better quality
                self.rembg_session = new_session('u2net')
                logging.info("rembg u2net session initialized")
            except Exception as e:
                logging.error(f"Failed to initialize rembg session: {e}")
                self.rembg_session = None
    
    def remove_background_rembg(self, image: Image.Image) -> Image.Image:
        """Remove background using rembg"""
        if not REMBG_AVAILABLE or self.rembg_session is None:
            raise RuntimeError("rembg not available")
        
        # Convert PIL to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Apply rembg
        result_bytes = remove(img_bytes.getvalue(), session=self.rembg_session)
        
        # Convert back to PIL
        result_img = Image.open(io.BytesIO(result_bytes))
        
        # Convert to RGB with white background
        if result_img.mode == 'RGBA':
            white_bg = Image.new('RGB', result_img.size, (255, 255, 255))
            white_bg.paste(result_img, mask=result_img.split()[-1])
            return white_bg
        else:
            return result_img.convert('RGB')
    
    def evaluate_removal_quality(self, original: Image.Image, processed: Image.Image, face_data: Optional[FaceData] = None) -> Dict[str, float]:
        """
        Comprehensive evaluation of background removal quality
        Returns dict with individual scores and overall quality
        """
        # Convert to numpy arrays
        orig_array = np.array(original)
        proc_array = np.array(processed)
        
        # Calculate individual metrics
        uniformity_score = self.quality_metrics.evaluate_background_uniformity(proc_array, face_data)
        edge_score = self.quality_metrics.evaluate_edge_quality(proc_array, face_data)
        preservation_score = self.quality_metrics.evaluate_person_preservation(orig_array, proc_array, face_data)
        
        # Calculate overall quality (weighted average)
        overall_quality = (
            uniformity_score * 0.4 +      # Background should be uniform white
            edge_score * 0.3 +             # Edges should be clean
            preservation_score * 0.3       # Person should be preserved
        )
        
        return {
            'background_uniformity': uniformity_score,
            'edge_quality': edge_score,
            'person_preservation': preservation_score,
            'overall_quality': overall_quality,
            'quality_grade': self._get_quality_grade(overall_quality)
        }
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade"""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def remove_background_adaptive(self, image: Image.Image, face_data: Optional[FaceData] = None) -> Tuple[Image.Image, Dict[str, float]]:
        """
        Adaptive background removal that tries multiple methods and returns the best result
        """
        results = []
        
        # Try rembg if available
        if REMBG_AVAILABLE and self.rembg_session is not None:
            try:
                rembg_result = self.remove_background_rembg(image)
                rembg_quality = self.evaluate_removal_quality(image, rembg_result, face_data)
                results.append(('rembg', rembg_result, rembg_quality))
                logging.info(f"rembg quality: {rembg_quality['overall_quality']:.3f}")
            except Exception as e:
                logging.error(f"rembg failed: {e}")
        
        # Try lightweight methods as fallback/comparison
        try:
            grabcut_result = self.fallback_remover.remove_background_grabcut(image)
            grabcut_quality = self.evaluate_removal_quality(image, grabcut_result, face_data)
            results.append(('grabcut', grabcut_result, grabcut_quality))
            logging.info(f"grabcut quality: {grabcut_quality['overall_quality']:.3f}")
        except Exception as e:
            logging.error(f"grabcut failed: {e}")
        
        try:
            edge_result = self.fallback_remover.remove_background_edge_detection(image)
            edge_quality = self.evaluate_removal_quality(image, edge_result, face_data)
            results.append(('edge_detection', edge_result, edge_quality))
            logging.info(f"edge detection quality: {edge_quality['overall_quality']:.3f}")
        except Exception as e:
            logging.error(f"edge detection failed: {e}")
        
        if not results:
            # If all methods failed, return original with white background
            if image.mode != 'RGB':
                fallback = image.convert('RGB')
            else:
                fallback = image
            fallback_quality = {
                'background_uniformity': 0.0,
                'edge_quality': 0.0,
                'person_preservation': 1.0,
                'overall_quality': 0.3,
                'quality_grade': 'F'
            }
            return fallback, fallback_quality
        
        # Select best result based on overall quality
        best_method, best_result, best_quality = max(results, key=lambda x: x[2]['overall_quality'])
        
        logging.info(f"Selected {best_method} with quality {best_quality['overall_quality']:.3f} ({best_quality['quality_grade']})")
        
        # If quality is still poor, try post-processing
        if best_quality['overall_quality'] < 0.7:
            try:
                enhanced_result = self._enhance_background_removal(best_result, face_data)
                enhanced_quality = self.evaluate_removal_quality(image, enhanced_result, face_data)
                
                if enhanced_quality['overall_quality'] > best_quality['overall_quality']:
                    logging.info(f"Post-processing improved quality to {enhanced_quality['overall_quality']:.3f}")
                    return enhanced_result, enhanced_quality
            except Exception as e:
                logging.error(f"Post-processing failed: {e}")
        
        return best_result, best_quality
    
    def _enhance_background_removal(self, image: Image.Image, face_data: Optional[FaceData] = None) -> Image.Image:
        """
        Post-process background removal to improve quality
        """
        # Convert to numpy for processing
        img_array = np.array(image)
        
        # Apply median filter to reduce noise
        if len(img_array.shape) == 3:
            for i in range(3):
                img_array[:, :, i] = cv2.medianBlur(img_array[:, :, i], 3)
        else:
            img_array = cv2.medianBlur(img_array, 3)
        
        # Enhance contrast slightly
        enhanced = Image.fromarray(img_array)
        enhancer = ImageEnhance.Contrast(enhanced)
        enhanced = enhancer.enhance(1.1)
        
        # Apply slight blur to soften edges
        enhanced = enhanced.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        return enhanced


# Factory function
def create_background_remover() -> ComprehensiveBackgroundRemover:
    """Create a comprehensive background remover instance"""
    return ComprehensiveBackgroundRemover()