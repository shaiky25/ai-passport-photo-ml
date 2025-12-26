"""
Image Quality Enhancement Engine
Implements sharpening, noise reduction, and contrast optimization
"""

import cv2
import numpy as np
from typing import Tuple
import logging
from .data_models import QualityMetrics


class ImageEnhancer:
    """Image quality enhancement with memory-efficient processing"""
    
    def __init__(self):
        # Pre-calculate kernels for efficiency
        self.sharpening_kernel = np.array([[-1, -1, -1],
                                         [-1,  9, -1],
                                         [-1, -1, -1]], dtype=np.float32)
        
        # Cache for expensive calculations
        self._gaussian_cache = {}
    
    def enhance_sharpness(self, image: np.ndarray, target_score: float = 0.7) -> np.ndarray:
        """
        Enhance image sharpness using optimized unsharp masking
        
        Args:
            image: Input image (BGR format)
            target_score: Target sharpness score (0.0-1.0)
            
        Returns:
            Sharpened image
        """
        if image is None or image.size == 0:
            return image
        
        try:
            # Calculate current sharpness
            current_sharpness = self.calculate_sharpness_score(image)
            
            if current_sharpness >= target_score:
                logging.info(f"Image already sharp enough: {current_sharpness:.3f} >= {target_score}")
                return image.copy()
            
            # Determine sharpening intensity based on current sharpness
            intensity_factor = min(2.0, (target_score - current_sharpness) * 3)
            
            # Apply unsharp masking
            enhanced = self._apply_unsharp_mask(image, intensity_factor)
            
            # Verify improvement
            new_sharpness = self.calculate_sharpness_score(enhanced)
            logging.info(f"Sharpness enhanced: {current_sharpness:.3f} -> {new_sharpness:.3f}")
            
            return enhanced
            
        except Exception as e:
            logging.error(f"Sharpness enhancement failed: {e}")
            return image.copy()
    
    def _apply_unsharp_mask(self, image: np.ndarray, intensity: float) -> np.ndarray:
        """Apply unsharp masking with given intensity"""
        # Convert to float for processing
        img_float = image.astype(np.float32)
        
        # Create Gaussian blur (use cache if available)
        blur_key = f"{image.shape}_{intensity}"
        if blur_key not in self._gaussian_cache:
            # Adaptive kernel size based on image size
            kernel_size = max(3, min(15, int(min(image.shape[:2]) / 100)))
            if kernel_size % 2 == 0:
                kernel_size += 1
            
            sigma = kernel_size / 3.0
            self._gaussian_cache[blur_key] = (kernel_size, sigma)
        
        kernel_size, sigma = self._gaussian_cache[blur_key]
        blurred = cv2.GaussianBlur(img_float, (kernel_size, kernel_size), sigma)
        
        # Unsharp mask formula: original + intensity * (original - blurred)
        mask = img_float - blurred
        enhanced = img_float + intensity * mask
        
        # Clip values and convert back to uint8
        enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
        
        return enhanced
    
    def reduce_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Reduce noise while preserving facial details using bilateral filtering
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Noise-reduced image
        """
        if image is None or image.size == 0:
            return image
        
        try:
            # Calculate current noise level
            current_noise = self._calculate_noise_level(image)
            
            if current_noise < 0.01:  # Already low noise
                logging.info(f"Image already has low noise: {current_noise:.4f}")
                return image.copy()
            
            # Apply bilateral filter (preserves edges while reducing noise)
            # Parameters: d=9 (diameter), sigmaColor=75, sigmaSpace=75
            denoised = cv2.bilateralFilter(image, 9, 75, 75)
            
            new_noise = self._calculate_noise_level(denoised)
            logging.info(f"Noise reduced: {current_noise:.4f} -> {new_noise:.4f}")
            
            return denoised
            
        except Exception as e:
            logging.error(f"Noise reduction failed: {e}")
            return image.copy()
    
    def optimize_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Optimize contrast and brightness for passport photo standards
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Contrast-optimized image
        """
        if image is None or image.size == 0:
            return image
        
        try:
            # Convert to LAB color space for better contrast adjustment
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_channel_enhanced = clahe.apply(l_channel)
            
            # Merge channels back
            lab_enhanced = cv2.merge([l_channel_enhanced, a_channel, b_channel])
            
            # Convert back to BGR
            enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
            
            # Calculate contrast improvement
            original_contrast = self._calculate_contrast_score(image)
            new_contrast = self._calculate_contrast_score(enhanced)
            
            logging.info(f"Contrast optimized: {original_contrast:.3f} -> {new_contrast:.3f}")
            
            return enhanced
            
        except Exception as e:
            logging.error(f"Contrast optimization failed: {e}")
            return image.copy()
    
    def calculate_sharpness_score(self, image: np.ndarray) -> float:
        """
        Calculate sharpness score using Laplacian variance method
        
        Args:
            image: Input image
            
        Returns:
            Sharpness score (higher = sharper)
        """
        if image is None or image.size == 0:
            return 0.0
        
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()
            
            # Normalize to 0-1 range (empirically determined scaling)
            normalized_score = min(1.0, variance / 1000.0)
            
            return float(normalized_score)
            
        except Exception as e:
            logging.error(f"Sharpness calculation failed: {e}")
            return 0.0
    
    def _calculate_noise_level(self, image: np.ndarray) -> float:
        """Calculate noise level using standard deviation in homogeneous regions"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply Gaussian blur to find homogeneous regions
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Calculate difference (noise)
            noise = cv2.absdiff(gray, blurred)
            
            # Return normalized noise level
            return float(np.std(noise) / 255.0)
            
        except Exception as e:
            logging.error(f"Noise calculation failed: {e}")
            return 0.0
    
    def _calculate_contrast_score(self, image: np.ndarray) -> float:
        """Calculate RMS contrast score"""
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Calculate RMS contrast
            mean_intensity = np.mean(gray)
            rms_contrast = np.sqrt(np.mean((gray - mean_intensity) ** 2))
            
            # Normalize to 0-1 range
            return float(rms_contrast / 127.5)
            
        except Exception as e:
            logging.error(f"Contrast calculation failed: {e}")
            return 0.0
    
    def calculate_quality_metrics(self, image: np.ndarray) -> QualityMetrics:
        """
        Calculate comprehensive quality metrics for an image
        
        Args:
            image: Input image
            
        Returns:
            QualityMetrics object with all calculated metrics
        """
        if image is None or image.size == 0:
            return QualityMetrics()
        
        try:
            sharpness = self.calculate_sharpness_score(image)
            noise = self._calculate_noise_level(image)
            contrast = self._calculate_contrast_score(image)
            
            # Calculate brightness (average luminance)
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            brightness = float(np.mean(gray) / 255.0)
            
            # Check dimensions (assuming passport photo should be square)
            height, width = image.shape[:2]
            dimension_compliance = (width == height and width >= 600)
            
            # Calculate background uniformity (simplified - check corners)
            background_uniformity = self._calculate_background_uniformity(image)
            
            return QualityMetrics(
                sharpness_score=sharpness,
                noise_level=noise,
                contrast_score=contrast,
                brightness_level=brightness,
                face_compliance_score=0.0,  # Will be set by face detection
                dimension_compliance=dimension_compliance,
                background_uniformity=background_uniformity
            )
            
        except Exception as e:
            logging.error(f"Quality metrics calculation failed: {e}")
            return QualityMetrics()
    
    def _calculate_background_uniformity(self, image: np.ndarray) -> float:
        """Calculate background uniformity by checking corner regions"""
        try:
            height, width = image.shape[:2]
            
            # Sample corner regions (10% of image size)
            corner_size = min(height, width) // 10
            
            # Extract corner regions
            corners = [
                image[0:corner_size, 0:corner_size],  # Top-left
                image[0:corner_size, -corner_size:],  # Top-right
                image[-corner_size:, 0:corner_size],  # Bottom-left
                image[-corner_size:, -corner_size:]   # Bottom-right
            ]
            
            # Calculate standard deviation across corners
            corner_means = [np.mean(corner) for corner in corners]
            uniformity = 1.0 - (np.std(corner_means) / 255.0)
            
            return max(0.0, float(uniformity))
            
        except Exception as e:
            logging.error(f"Background uniformity calculation failed: {e}")
            return 0.0