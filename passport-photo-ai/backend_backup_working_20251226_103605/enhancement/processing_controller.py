"""
Iterative Processing Controller
Manages the enhancement pipeline with iteration limits and smart strategy selection
"""

import cv2
import numpy as np
import time
from typing import List
import logging
from .data_models import (
    ProcessingResult, ProcessingAttempt, QualityMetrics, 
    ValidationResult, EnhancementStrategy
)
from .image_enhancer import ImageEnhancer
from .quality_validator import QualityValidator


class ProcessingController:
    """Controls iterative processing with smart enhancement strategies"""
    
    MAX_ATTEMPTS = 2  # As per requirements (reduced from 3 for resource efficiency)
    TARGET_SCORE = 0.8  # 80% compliance target
    
    def __init__(self):
        self.enhancer = ImageEnhancer()
        self.validator = QualityValidator()
        self.processing_history = []
    
    def process_with_iteration(self, image: np.ndarray, max_attempts: int = None) -> ProcessingResult:
        """
        Process image with iterative enhancement until target quality is reached
        
        Args:
            image: Input image (BGR format)
            max_attempts: Maximum processing attempts (defaults to MAX_ATTEMPTS)
            
        Returns:
            ProcessingResult with enhanced image and processing history
        """
        if max_attempts is None:
            max_attempts = self.MAX_ATTEMPTS
        
        if image is None or image.size == 0:
            return self._create_error_result("Invalid input image")
        
        start_time = time.time()
        attempts = []
        best_result = None
        best_score = 0.0
        current_image = image.copy()
        
        logging.info(f"Starting iterative processing (max {max_attempts} attempts)")
        
        for attempt_num in range(1, max_attempts + 1):
            attempt_start = time.time()
            
            # Calculate initial metrics for this attempt
            initial_metrics = self.enhancer.calculate_quality_metrics(current_image)
            initial_score = self.validator.calculate_compliance_score(initial_metrics)
            
            logging.info(f"Attempt {attempt_num}: Initial score {initial_score:.1%}")
            
            # Quick assessment - if already good enough, skip enhancement
            if initial_score >= self.TARGET_SCORE:
                logging.info(f"Target score reached without enhancement: {initial_score:.1%}")
                break
            
            # Select enhancement strategy
            strategy = self.select_enhancement_strategy(initial_metrics, initial_score)
            
            # Apply enhancements
            enhanced_image, enhancements_applied = self._apply_enhancements(current_image, strategy)
            
            # Calculate final metrics
            final_metrics = self.enhancer.calculate_quality_metrics(enhanced_image)
            final_score = self.validator.calculate_compliance_score(final_metrics)
            
            # Record attempt
            attempt_time = time.time() - attempt_start
            attempt = ProcessingAttempt(
                attempt_number=attempt_num,
                initial_metrics=initial_metrics,
                final_metrics=final_metrics,
                enhancements_applied=enhancements_applied,
                processing_time=attempt_time,
                success=final_score > initial_score
            )
            attempts.append(attempt)
            
            logging.info(f"Attempt {attempt_num} completed: {initial_score:.1%} -> {final_score:.1%} "
                        f"({attempt_time:.2f}s)")
            
            # Track best result
            if final_score > best_score:
                best_result = enhanced_image.copy()
                best_score = final_score
            
            # Early termination if target reached
            if final_score >= self.TARGET_SCORE:
                logging.info(f"Target score reached: {final_score:.1%}")
                break
            
            # Prepare for next iteration
            current_image = enhanced_image
        
        # Use best result if available, otherwise original
        if best_result is not None:
            final_image = best_result
        else:
            final_image = image.copy()
            best_score = self.validator.calculate_compliance_score(
                self.enhancer.calculate_quality_metrics(image)
            )
        
        # Create final validation result
        final_metrics = self.enhancer.calculate_quality_metrics(final_image)
        validation_result = self.validator.validate_against_gold_standard(
            final_image, final_metrics
        )
        
        # Calculate improvement percentage
        original_score = self.validator.calculate_compliance_score(
            self.enhancer.calculate_quality_metrics(image)
        )
        improvement_percentage = ((best_score - original_score) / original_score * 100) if original_score > 0 else 0
        
        total_time = time.time() - start_time
        
        result = ProcessingResult(
            enhanced_image=final_image,
            validation_result=validation_result,
            processing_history=attempts,
            total_attempts=len(attempts),
            improvement_percentage=improvement_percentage
        )
        
        # Store in processing history
        self.processing_history.append(result)
        
        logging.info(f"Processing completed: {len(attempts)} attempts, "
                    f"{improvement_percentage:.1f}% improvement, {total_time:.2f}s total")
        
        return result
    
    def select_enhancement_strategy(self, current_metrics: QualityMetrics, 
                                  current_score: float) -> EnhancementStrategy:
        """
        Select optimal enhancement strategy based on current image quality
        
        Args:
            current_metrics: Current image quality metrics
            current_score: Current compliance score
            
        Returns:
            EnhancementStrategy with selected enhancements
        """
        # Determine processing path based on current score
        if current_score > 0.6:
            processing_path = "fast"
        elif current_score > 0.3:
            processing_path = "standard"
        else:
            processing_path = "heavy"
        
        # Determine which enhancements to apply
        apply_sharpening = current_metrics.sharpness_score < 0.7
        apply_noise_reduction = current_metrics.noise_level > 0.01
        apply_contrast_optimization = current_metrics.contrast_score < 0.3
        
        # Adjust intensity based on processing path
        if processing_path == "fast":
            sharpening_intensity = 0.5
        elif processing_path == "standard":
            sharpening_intensity = 1.0
        else:  # heavy
            sharpening_intensity = 1.5
        
        strategy = EnhancementStrategy(
            apply_sharpening=apply_sharpening,
            apply_noise_reduction=apply_noise_reduction,
            apply_contrast_optimization=apply_contrast_optimization,
            sharpening_intensity=sharpening_intensity,
            processing_path=processing_path
        )
        
        logging.info(f"Selected {processing_path} processing path: "
                    f"sharpen={apply_sharpening}, denoise={apply_noise_reduction}, "
                    f"contrast={apply_contrast_optimization}")
        
        return strategy
    
    def _apply_enhancements(self, image: np.ndarray, 
                          strategy: EnhancementStrategy) -> tuple[np.ndarray, List[str]]:
        """
        Apply selected enhancements to image
        
        Args:
            image: Input image
            strategy: Enhancement strategy
            
        Returns:
            Tuple of (enhanced_image, list_of_applied_enhancements)
        """
        enhanced = image.copy()
        applied_enhancements = []
        
        try:
            # Apply enhancements in optimal order
            
            # 1. Noise reduction first (if needed)
            if strategy.apply_noise_reduction:
                enhanced = self.enhancer.reduce_noise(enhanced)
                applied_enhancements.append("noise_reduction")
            
            # 2. Sharpening second
            if strategy.apply_sharpening:
                target_sharpness = 0.7 * strategy.sharpening_intensity
                enhanced = self.enhancer.enhance_sharpness(enhanced, target_sharpness)
                applied_enhancements.append(f"sharpening_{strategy.sharpening_intensity}")
            
            # 3. Contrast optimization last
            if strategy.apply_contrast_optimization:
                enhanced = self.enhancer.optimize_contrast(enhanced)
                applied_enhancements.append("contrast_optimization")
            
            if not applied_enhancements:
                applied_enhancements.append("no_enhancement_needed")
            
        except Exception as e:
            logging.error(f"Enhancement application failed: {e}")
            applied_enhancements.append(f"enhancement_failed: {str(e)}")
        
        return enhanced, applied_enhancements
    
    def track_processing_history(self, attempt: ProcessingAttempt) -> None:
        """
        Track processing attempt for monitoring and analysis
        
        Args:
            attempt: Processing attempt to track
        """
        # This could be extended to write to database or log files
        logging.info(f"Tracking attempt {attempt.attempt_number}: "
                    f"Success={attempt.success}, Time={attempt.processing_time:.2f}s, "
                    f"Enhancements={attempt.enhancements_applied}")
    
    def _create_error_result(self, error_message: str) -> ProcessingResult:
        """Create a processing result for error cases"""
        # Create a minimal black image as fallback
        error_image = np.zeros((600, 600, 3), dtype=np.uint8)
        
        error_validation = ValidationResult(
            overall_score=0.0,
            grade='F',
            dimension_score=0.0,
            background_score=0.0,
            face_compliance_score=0.0,
            image_quality_score=0.0,
            recommendations=[error_message],
            is_passport_ready=False
        )
        
        return ProcessingResult(
            enhanced_image=error_image,
            validation_result=error_validation,
            processing_history=[],
            total_attempts=0,
            improvement_percentage=0.0
        )
    
    def get_processing_statistics(self) -> dict:
        """
        Get statistics from processing history
        
        Returns:
            Dictionary with processing statistics
        """
        if not self.processing_history:
            return {"total_processed": 0}
        
        total_processed = len(self.processing_history)
        successful_processing = sum(1 for result in self.processing_history 
                                  if result.validation_result.overall_score >= self.TARGET_SCORE)
        
        avg_attempts = sum(result.total_attempts for result in self.processing_history) / total_processed
        avg_improvement = sum(result.improvement_percentage for result in self.processing_history) / total_processed
        
        return {
            "total_processed": total_processed,
            "success_rate": successful_processing / total_processed,
            "average_attempts": avg_attempts,
            "average_improvement_percentage": avg_improvement,
            "target_score": self.TARGET_SCORE
        }