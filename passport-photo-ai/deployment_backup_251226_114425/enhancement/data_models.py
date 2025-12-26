"""
Data models for the photo quality enhancement system
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Dict, List, Any
import numpy as np


@dataclass
class FaceData:
    """Data structure for face detection results"""
    bounding_box: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    landmarks: Optional[Dict[str, Tuple[int, int]]] = None
    eye_positions: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    face_size_ratio: float = 0.0  # Percentage of image height


@dataclass
class QualityMetrics:
    """Quality metrics for image assessment"""
    sharpness_score: float = 0.0
    noise_level: float = 0.0
    contrast_score: float = 0.0
    brightness_level: float = 0.0
    face_compliance_score: float = 0.0
    dimension_compliance: bool = False
    background_uniformity: float = 0.0


@dataclass
class ValidationResult:
    """Results from quality validation"""
    overall_score: float
    grade: str  # A, B, C, D, F
    dimension_score: float
    background_score: float
    face_compliance_score: float
    image_quality_score: float
    recommendations: List[str]
    is_passport_ready: bool


@dataclass
class ProcessingAttempt:
    """Record of a single processing attempt"""
    attempt_number: int
    initial_metrics: QualityMetrics
    final_metrics: QualityMetrics
    enhancements_applied: List[str]
    processing_time: float
    success: bool


@dataclass
class ProcessingResult:
    """Final result from the enhancement pipeline"""
    enhanced_image: np.ndarray
    validation_result: ValidationResult
    processing_history: List[ProcessingAttempt]
    total_attempts: int
    improvement_percentage: float


@dataclass
class FaceDetectionResult:
    """Result from face detection pipeline"""
    faces: List[FaceData]
    primary_face: Optional[FaceData]
    confidence: float
    multiple_faces_detected: bool
    requires_manual_review: bool
    error_message: Optional[str] = None


@dataclass
class ComplianceResult:
    """Result from face compliance validation"""
    is_compliant: bool
    face_size_valid: bool
    eye_positioning_valid: bool
    centering_valid: bool
    issues: List[str]
    # Enhanced eye validation fields
    eyes_detected: bool = False
    eye_level_valid: bool = False
    eye_distance_valid: bool = False
    eye_visibility_valid: bool = False
    eye_symmetry_valid: bool = False
    icao_eye_compliance: bool = False
    eye_validation_details: Optional[Dict[str, float]] = None
    # Glasses detection fields
    glasses_detected: bool = False
    sunglasses_detected: bool = False
    glasses_info: Optional[Dict[str, Any]] = None


@dataclass
class EnhancementStrategy:
    """Strategy for image enhancement"""
    apply_sharpening: bool
    apply_noise_reduction: bool
    apply_contrast_optimization: bool
    sharpening_intensity: float
    processing_path: str  # 'fast', 'standard', 'heavy'