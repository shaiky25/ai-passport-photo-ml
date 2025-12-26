"""
Quality Validation System
Validates images against gold standard passport photo requirements
"""

import numpy as np
from typing import List
import logging
from .data_models import QualityMetrics, ValidationResult, FaceData


class QualityValidator:
    """Validates image quality against ICAO passport photo standards"""
    
    # Scoring weights based on design document
    DIMENSION_WEIGHT = 0.25
    BACKGROUND_WEIGHT = 0.25
    FACE_COMPLIANCE_WEIGHT = 0.30
    IMAGE_QUALITY_WEIGHT = 0.20
    
    # Quality thresholds
    MIN_SHARPNESS = 0.7
    MAX_NOISE_LEVEL = 0.01
    MIN_CONTRAST = 0.3
    MIN_BACKGROUND_UNIFORMITY = 0.9
    
    def __init__(self):
        self.validation_history = []
    
    def validate_against_gold_standard(self, image: np.ndarray, 
                                     quality_metrics: QualityMetrics,
                                     face_data: FaceData = None) -> ValidationResult:
        """
        Validate image against all gold standard criteria
        
        Args:
            image: Input image
            quality_metrics: Pre-calculated quality metrics
            face_data: Face detection results
            
        Returns:
            ValidationResult with detailed scoring
        """
        if image is None or image.size == 0:
            return self._create_error_result("Invalid input image")
        
        try:
            # Calculate individual scores
            dimension_score = self._calculate_dimension_score(image)
            background_score = self._calculate_background_score(quality_metrics)
            face_compliance_score = self._calculate_face_compliance_score(face_data, image.shape)
            image_quality_score = self._calculate_image_quality_score(quality_metrics)
            
            # Calculate overall score using weighted formula
            overall_score = (
                dimension_score * self.DIMENSION_WEIGHT +
                background_score * self.BACKGROUND_WEIGHT +
                face_compliance_score * self.FACE_COMPLIANCE_WEIGHT +
                image_quality_score * self.IMAGE_QUALITY_WEIGHT
            )
            
            # Determine grade
            grade = self._calculate_grade(overall_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                dimension_score, background_score, face_compliance_score, image_quality_score
            )
            
            # Determine if passport ready
            is_passport_ready = overall_score >= 0.8 and face_compliance_score >= 0.8
            
            result = ValidationResult(
                overall_score=overall_score,
                grade=grade,
                dimension_score=dimension_score,
                background_score=background_score,
                face_compliance_score=face_compliance_score,
                image_quality_score=image_quality_score,
                recommendations=recommendations,
                is_passport_ready=is_passport_ready
            )
            
            # Store in history for monitoring
            self.validation_history.append(result)
            
            logging.info(f"Validation completed: Overall score {overall_score:.1%} (Grade: {grade})")
            
            return result
            
        except Exception as e:
            logging.error(f"Validation failed: {e}")
            return self._create_error_result(f"Validation error: {str(e)}")
    
    def _calculate_dimension_score(self, image: np.ndarray) -> float:
        """Calculate dimension compliance score"""
        height, width = image.shape[:2]
        
        # Perfect score for 1200x1200 (passport standard)
        if width == 1200 and height == 1200:
            return 1.0
        
        # Good score for square images >= 600x600
        if width == height and width >= 600:
            return 0.9
        
        # Partial score for rectangular images with good resolution
        if min(width, height) >= 600:
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio <= 1.2:  # Close to square
                return 0.7
            else:
                return 0.5
        
        # Low score for small images
        return 0.3
    
    def _calculate_background_score(self, quality_metrics: QualityMetrics) -> float:
        """Calculate background uniformity score"""
        uniformity = quality_metrics.background_uniformity
        
        # Perfect score for very uniform backgrounds (white passport background)
        if uniformity >= self.MIN_BACKGROUND_UNIFORMITY:
            return 1.0
        
        # Scale score based on uniformity
        return max(0.0, uniformity)
    
    def _calculate_face_compliance_score(self, face_data: FaceData, image_shape: tuple) -> float:
        """Calculate face compliance score"""
        if not face_data:
            return 0.0
        
        score = 0.0
        
        # Face detection confidence (40% of face score)
        if face_data.confidence >= 0.95:
            score += 0.4
        elif face_data.confidence >= 0.8:
            score += 0.3
        elif face_data.confidence >= 0.6:
            score += 0.2
        
        # Face size compliance (40% of face score)
        if 0.70 <= face_data.face_size_ratio <= 0.80:
            score += 0.4
        elif 0.60 <= face_data.face_size_ratio <= 0.90:
            score += 0.2
        
        # Eye positioning (20% of face score)
        if face_data.eye_positions:
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_image_quality_score(self, quality_metrics: QualityMetrics) -> float:
        """Calculate image quality score"""
        score = 0.0
        
        # Sharpness (50% of quality score)
        if quality_metrics.sharpness_score >= self.MIN_SHARPNESS:
            score += 0.5
        else:
            score += (quality_metrics.sharpness_score / self.MIN_SHARPNESS) * 0.5
        
        # Noise level (25% of quality score) - lower is better
        if quality_metrics.noise_level <= self.MAX_NOISE_LEVEL:
            score += 0.25
        else:
            noise_penalty = min(1.0, quality_metrics.noise_level / 0.05)  # Penalty up to 5% noise
            score += 0.25 * (1 - noise_penalty)
        
        # Contrast (25% of quality score)
        if quality_metrics.contrast_score >= self.MIN_CONTRAST:
            score += 0.25
        else:
            score += (quality_metrics.contrast_score / self.MIN_CONTRAST) * 0.25
        
        return min(1.0, max(0.0, score))
    
    def _calculate_grade(self, overall_score: float) -> str:
        """Convert overall score to letter grade"""
        if overall_score >= 0.9:
            return 'A'
        elif overall_score >= 0.8:
            return 'B'
        elif overall_score >= 0.7:
            return 'C'
        elif overall_score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def _generate_recommendations(self, dimension_score: float, background_score: float,
                                face_compliance_score: float, image_quality_score: float) -> List[str]:
        """Generate specific improvement recommendations"""
        recommendations = []
        
        if dimension_score < 0.8:
            recommendations.append("Ensure image is square (1:1 aspect ratio) and at least 600x600 pixels")
        
        if background_score < 0.8:
            recommendations.append("Use a plain white background with uniform lighting")
        
        if face_compliance_score < 0.8:
            recommendations.append("Ensure face is clearly visible and properly positioned (70-80% of image height)")
        
        if image_quality_score < 0.8:
            recommendations.append("Improve image sharpness and reduce noise - use good lighting and stable camera")
        
        if not recommendations:
            recommendations.append("Image meets passport photo standards")
        
        return recommendations
    
    def _create_error_result(self, error_message: str) -> ValidationResult:
        """Create a validation result for error cases"""
        return ValidationResult(
            overall_score=0.0,
            grade='F',
            dimension_score=0.0,
            background_score=0.0,
            face_compliance_score=0.0,
            image_quality_score=0.0,
            recommendations=[error_message],
            is_passport_ready=False
        )
    
    def calculate_compliance_score(self, metrics: QualityMetrics) -> float:
        """
        Calculate compliance score from quality metrics
        
        Args:
            metrics: Quality metrics
            
        Returns:
            Compliance score (0.0-1.0)
        """
        # This is a simplified version for quick assessment
        scores = []
        
        # Dimension compliance
        scores.append(1.0 if metrics.dimension_compliance else 0.5)
        
        # Background uniformity
        scores.append(metrics.background_uniformity)
        
        # Image quality (average of sharpness and contrast, penalized by noise)
        quality_score = (metrics.sharpness_score + metrics.contrast_score) / 2
        noise_penalty = min(1.0, metrics.noise_level / self.MAX_NOISE_LEVEL)
        quality_score *= (1 - noise_penalty * 0.5)
        scores.append(quality_score)
        
        # Face compliance (if available)
        if metrics.face_compliance_score > 0:
            scores.append(metrics.face_compliance_score)
        
        return sum(scores) / len(scores)
    
    def generate_improvement_recommendations(self, result: ValidationResult) -> List[str]:
        """
        Generate specific improvement recommendations based on validation result
        
        Args:
            result: Validation result
            
        Returns:
            List of specific recommendations
        """
        recommendations = []
        
        if result.dimension_score < 0.8:
            recommendations.append("Crop image to square format (1:1 ratio)")
            recommendations.append("Ensure minimum resolution of 600x600 pixels")
        
        if result.background_score < 0.8:
            recommendations.append("Use plain white background")
            recommendations.append("Ensure even lighting without shadows")
        
        if result.face_compliance_score < 0.8:
            recommendations.append("Position face to occupy 70-80% of image height")
            recommendations.append("Ensure face is centered horizontally")
            recommendations.append("Make sure eyes are clearly visible and properly positioned")
        
        if result.image_quality_score < 0.8:
            recommendations.append("Improve image sharpness - use better lighting or camera settings")
            recommendations.append("Reduce image noise - avoid high ISO settings")
            recommendations.append("Optimize contrast for better facial feature visibility")
        
        return recommendations
    
    def compare_with_original(self, original_metrics: QualityMetrics, 
                            enhanced_metrics: QualityMetrics) -> dict:
        """
        Compare enhanced image metrics with original
        
        Args:
            original_metrics: Metrics from original image
            enhanced_metrics: Metrics from enhanced image
            
        Returns:
            Dictionary with improvement analysis
        """
        improvements = {}
        
        # Calculate improvements
        sharpness_improvement = enhanced_metrics.sharpness_score - original_metrics.sharpness_score
        noise_improvement = original_metrics.noise_level - enhanced_metrics.noise_level  # Lower is better
        contrast_improvement = enhanced_metrics.contrast_score - original_metrics.contrast_score
        
        improvements['sharpness_improved'] = sharpness_improvement > 0.05
        improvements['noise_reduced'] = noise_improvement > 0.005
        improvements['contrast_improved'] = contrast_improvement > 0.05
        
        improvements['sharpness_change'] = sharpness_improvement
        improvements['noise_change'] = -noise_improvement  # Negative because reduction is good
        improvements['contrast_change'] = contrast_improvement
        
        # Overall improvement
        total_improvements = sum([
            improvements['sharpness_improved'],
            improvements['noise_reduced'],
            improvements['contrast_improved']
        ])
        
        improvements['overall_improved'] = total_improvements >= 2
        improvements['improvement_count'] = total_improvements
        
        return improvements