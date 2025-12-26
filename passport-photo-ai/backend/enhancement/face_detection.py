"""
Enhanced Face Detection Pipeline
Uses MediaPipe as primary detector with OpenCV fallback
"""

import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict, Any
import logging
from .data_models import FaceData, FaceDetectionResult, ComplianceResult

# Try to import MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logging.warning("MediaPipe not available, using OpenCV only")


class FaceDetectionPipeline:
    """Enhanced face detection using MediaPipe with OpenCV fallback"""
    
    def __init__(self):
        self.mediapipe_detector = None
        self.opencv_detector = None
        self._initialize_detectors()
    
    def _initialize_detectors(self):
        """Initialize face detection models"""
        # Initialize MediaPipe face detection
        if MEDIAPIPE_AVAILABLE:
            try:
                mp_face_detection = mp.solutions.face_detection
                # Use more sensitive detection settings
                self.mediapipe_detector = mp_face_detection.FaceDetection(
                    model_selection=0,  # 0 for short-range (< 2 meters)
                    min_detection_confidence=0.3  # Lower threshold for better detection
                )
                logging.info("MediaPipe face detector initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize MediaPipe: {e}")
                self.mediapipe_detector = None
        
        # Initialize OpenCV Haar cascade as fallback
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.opencv_detector = cv2.CascadeClassifier(cascade_path)
            if self.opencv_detector.empty():
                self.opencv_detector = None
                logging.error("Failed to load OpenCV face cascade")
            else:
                logging.info("OpenCV face detector initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize OpenCV detector: {e}")
            self.opencv_detector = None
    
    def detect_faces(self, image: np.ndarray) -> FaceDetectionResult:
        """
        Detect faces in image using MediaPipe with OpenCV fallback
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            FaceDetectionResult with detected faces and metadata
        """
        if image is None or image.size == 0:
            return FaceDetectionResult(
                faces=[],
                primary_face=None,
                confidence=0.0,
                multiple_faces_detected=False,
                requires_manual_review=False,
                error_message="Invalid input image"
            )
        
        # Validate image dimensions
        if len(image.shape) < 2:
            return FaceDetectionResult(
                faces=[],
                primary_face=None,
                confidence=0.0,
                multiple_faces_detected=False,
                requires_manual_review=False,
                error_message="Invalid image dimensions - image must be 2D or 3D array"
            )
        
        height, width = image.shape[:2]
        
        # Try MediaPipe first
        faces = self._detect_with_mediapipe(image)
        detection_method = "MediaPipe"
        
        # Fallback to OpenCV if MediaPipe fails or has low confidence
        if not faces or (faces and max(face.confidence for face in faces) < 0.5):
            opencv_faces = self._detect_with_opencv(image)
            if opencv_faces:
                # Use OpenCV results if they're better or MediaPipe found nothing
                if not faces or len(opencv_faces) > len(faces):
                    faces = opencv_faces
                    detection_method = "OpenCV"
                # Or if OpenCV found faces with better positioning
                elif opencv_faces:
                    # Prefer faces that are better sized for passport photos
                    best_opencv = max(opencv_faces, key=lambda f: f.face_size_ratio if 0.6 <= f.face_size_ratio <= 0.9 else 0)
                    best_mediapipe = max(faces, key=lambda f: f.confidence)
                    
                    if (0.6 <= best_opencv.face_size_ratio <= 0.9 and 
                        best_mediapipe.face_size_ratio < 0.6):
                        faces = opencv_faces
                        detection_method = "OpenCV (better sizing)"
        
        # Determine primary face and review requirements
        primary_face = self.get_primary_face(faces) if faces else None
        multiple_faces = len(faces) > 1
        requires_review = multiple_faces or (primary_face and primary_face.confidence < 0.9)
        
        overall_confidence = primary_face.confidence if primary_face else 0.0
        
        # Generate appropriate error message
        error_message = None
        if not faces:
            error_message = "No faces detected"
        elif multiple_faces:
            # Check if multiple faces are detected with high accuracy
            high_confidence_faces = [f for f in faces if f.confidence > 0.7]
            if len(high_confidence_faces) > 1:
                error_message = "Image must contain only 1 person. Multiple faces detected with high confidence."
            else:
                error_message = "Multiple faces detected. Please ensure image contains only one person."
        
        logging.info(f"Face detection completed using {detection_method}: "
                    f"{len(faces)} faces detected, confidence: {overall_confidence:.2f}")
        
        return FaceDetectionResult(
            faces=faces,
            primary_face=primary_face,
            confidence=overall_confidence,
            multiple_faces_detected=multiple_faces,
            requires_manual_review=requires_review,
            error_message=error_message
        )
    
    def _detect_with_mediapipe(self, image: np.ndarray) -> List[FaceData]:
        """Detect faces using MediaPipe"""
        if not self.mediapipe_detector:
            return []
        
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            height, width = image.shape[:2]
            
            results = self.mediapipe_detector.process(rgb_image)
            
            faces = []
            if results.detections:
                for detection in results.detections:
                    # Get bounding box
                    bbox = detection.location_data.relative_bounding_box
                    x = int(bbox.xmin * width)
                    y = int(bbox.ymin * height)
                    w = int(bbox.width * width)
                    h = int(bbox.height * height)
                    
                    # Ensure bounding box is within image bounds
                    x = max(0, min(x, width - 1))
                    y = max(0, min(y, height - 1))
                    w = min(w, width - x)
                    h = min(h, height - y)
                    
                    # Calculate face size ratio
                    face_size_ratio = h / height if height > 0 else 0
                    
                    # Extract eye positions and landmarks if available
                    eye_positions = None
                    landmarks = {}
                    
                    # MediaPipe face detection provides 6 key points
                    if hasattr(detection.location_data, 'relative_keypoints') and detection.location_data.relative_keypoints:
                        keypoints = detection.location_data.relative_keypoints
                        if len(keypoints) >= 6:
                            # MediaPipe keypoints: right_eye, left_eye, nose_tip, mouth_center, right_ear_tragion, left_ear_tragion
                            right_eye = (int(keypoints[0].x * width), int(keypoints[0].y * height))
                            left_eye = (int(keypoints[1].x * width), int(keypoints[1].y * height))
                            nose_tip = (int(keypoints[2].x * width), int(keypoints[2].y * height))
                            mouth_center = (int(keypoints[3].x * width), int(keypoints[3].y * height))
                            
                            eye_positions = (left_eye, right_eye)  # (left, right) order
                            landmarks = {
                                'left_eye': left_eye,
                                'right_eye': right_eye,
                                'nose_tip': nose_tip,
                                'mouth_center': mouth_center
                            }
                    
                    face_data = FaceData(
                        bounding_box=(x, y, w, h),
                        confidence=detection.score[0] if detection.score else 0.0,
                        landmarks=landmarks,
                        eye_positions=eye_positions,
                        face_size_ratio=face_size_ratio
                    )
                    faces.append(face_data)
            
            return faces
            
        except Exception as e:
            logging.error(f"MediaPipe face detection failed: {e}")
            return []
    
    def _detect_with_opencv(self, image: np.ndarray) -> List[FaceData]:
        """Detect faces using OpenCV Haar cascades"""
        if not self.opencv_detector:
            return []
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            height, width = image.shape[:2]
            
            # Detect faces with multiple scale factors for better detection
            faces_rect = []
            
            # Try different parameters for better detection
            for scale_factor in [1.1, 1.2, 1.3]:
                for min_neighbors in [3, 5, 7]:
                    detected = self.opencv_detector.detectMultiScale(
                        gray,
                        scaleFactor=scale_factor,
                        minNeighbors=min_neighbors,
                        minSize=(50, 50),
                        maxSize=(int(width*0.8), int(height*0.8)),
                        flags=cv2.CASCADE_SCALE_IMAGE
                    )
                    if len(detected) > 0:
                        faces_rect = detected
                        break
                if len(faces_rect) > 0:
                    break
            
            faces = []
            for (x, y, w, h) in faces_rect:
                # Calculate face size ratio
                face_size_ratio = h / height if height > 0 else 0
                
                # Estimate confidence based on face size and position
                # Faces closer to passport photo standards get higher confidence
                size_score = 1.0 - abs(face_size_ratio - 0.75)  # Target 75% of image height
                center_x = x + w/2
                center_score = 1.0 - abs(center_x - width/2) / (width/2)
                confidence = min(0.95, max(0.6, (size_score + center_score) / 2))
                
                face_data = FaceData(
                    bounding_box=(x, y, w, h),
                    confidence=confidence,
                    landmarks=None,
                    eye_positions=None,
                    face_size_ratio=face_size_ratio
                )
                faces.append(face_data)
            
            return faces
            
        except Exception as e:
            logging.error(f"OpenCV face detection failed: {e}")
            return []
    
    def get_primary_face(self, faces: List[FaceData]) -> Optional[FaceData]:
        """
        Select the primary face from detected faces
        
        Args:
            faces: List of detected faces
            
        Returns:
            Primary face or None if no faces
        """
        if not faces:
            return None
        
        if len(faces) == 1:
            return faces[0]
        
        # For multiple faces, select based on:
        # 1. Highest confidence (40%)
        # 2. Best face size for passport photos (30%)
        # 3. Most centered position (30%)
        
        def face_score(face: FaceData, image_width: int = 1200, image_height: int = 1200) -> float:
            x, y, w, h = face.bounding_box
            
            # Confidence weight (40%)
            confidence_score = face.confidence * 0.4
            
            # Size weight (30%) - prefer faces that are 70-80% of image height
            target_ratio = 0.75
            size_deviation = abs(face.face_size_ratio - target_ratio)
            size_score = max(0, (1 - size_deviation * 2)) * 0.3  # Penalize deviation from target
            
            # Centering weight (30%) - prefer faces closer to center
            face_center_x = x + w / 2
            face_center_y = y + h / 2
            image_center_x = image_width / 2
            image_center_y = image_height / 2
            
            # Calculate distance from center as percentage of image diagonal
            distance_from_center = ((face_center_x - image_center_x) ** 2 + 
                                  (face_center_y - image_center_y) ** 2) ** 0.5
            max_distance = (image_width ** 2 + image_height ** 2) ** 0.5 / 2
            center_score = max(0, (1 - distance_from_center / max_distance)) * 0.3
            
            return confidence_score + size_score + center_score
        
        # Return face with highest score
        return max(faces, key=lambda face: face_score(face))
    
    def validate_face_compliance(self, face_data: FaceData, image_shape: Tuple[int, int]) -> ComplianceResult:
        """
        Validate face compliance with passport photo standards
        
        Args:
            face_data: Detected face data
            image_shape: (height, width) of the image
            
        Returns:
            ComplianceResult with validation details
        """
        height, width = image_shape
        x, y, w, h = face_data.bounding_box
        
        issues = []
        
        # Face size validation (70-80% of image height)
        face_size_valid = 0.70 <= face_data.face_size_ratio <= 0.80
        if not face_size_valid:
            if face_data.face_size_ratio < 0.70:
                issues.append("Face is too small - should be 70-80% of image height")
            else:
                issues.append("Face is too large - should be 70-80% of image height")
        
        # Eye positioning validation (29-35mm from bottom in passport photos)
        # For digital images, we approximate this as eye level being in upper 1/3 of face
        eye_positioning_valid = True
        if face_data.eye_positions:
            left_eye, right_eye = face_data.eye_positions
            avg_eye_y = (left_eye[1] + right_eye[1]) / 2
            face_top = y
            eye_position_in_face = (avg_eye_y - face_top) / h
            
            # Eyes should be in upper 1/3 of face region
            if not (0.2 <= eye_position_in_face <= 0.4):
                eye_positioning_valid = False
                issues.append("Eye positioning may not meet passport standards")
        else:
            # If no eye landmarks detected, we can't validate positioning
            eye_positioning_valid = False
            issues.append("Could not detect eye positions for validation")
        
        # Face centering validation
        face_center_x = x + w / 2
        face_center_y = y + h / 2
        image_center_x = width / 2
        image_center_y = height / 2
        
        # Calculate horizontal and vertical offset from center
        horizontal_offset = abs(face_center_x - image_center_x) / width
        vertical_offset = abs(face_center_y - image_center_y) / height
        
        # Face should be centered within 10% horizontally and 15% vertically
        centering_valid = horizontal_offset < 0.1 and vertical_offset < 0.15
        if not centering_valid:
            if horizontal_offset >= 0.1:
                issues.append("Face is not properly centered horizontally")
            if vertical_offset >= 0.15:
                issues.append("Face is not properly centered vertically")
        
        # Overall compliance
        is_compliant = face_size_valid and eye_positioning_valid and centering_valid
        
        return ComplianceResult(
            is_compliant=is_compliant,
            face_size_valid=face_size_valid,
            eye_positioning_valid=eye_positioning_valid,
            centering_valid=centering_valid,
            issues=issues
        )
    
    def validate_eye_compliance_icao(self, face_data: FaceData, image_shape: Tuple[int, int], image: Optional[np.ndarray] = None) -> ComplianceResult:
        """
        Comprehensive eye validation according to ICAO standards for passport photos
        
        ICAO Requirements:
        - Eyes must be clearly visible and open
        - Eye level should be between 29-35mm from bottom of photo (for 35x45mm photo)
        - Eyes should be horizontally aligned
        - Pupil-to-pupil distance should be appropriate for face size
        - No red-eye, shadows, or reflections on eyes
        
        Args:
            face_data: Detected face data with eye positions
            image_shape: (height, width) of the image
            
        Returns:
            ComplianceResult with detailed eye validation
        """
        height, width = image_shape
        x, y, w, h = face_data.bounding_box
        
        issues = []
        eye_validation_details = {}
        
        # Initialize validation flags
        eyes_detected = face_data.eye_positions is not None
        eye_level_valid = False
        eye_distance_valid = False
        eye_visibility_valid = False
        eye_symmetry_valid = False
        
        if not eyes_detected:
            issues.append("Eyes could not be detected - ensure eyes are clearly visible and open")
            eye_validation_details['detection_confidence'] = 0.0
        else:
            left_eye, right_eye = face_data.eye_positions
            
            # 1. Eye Level Validation (ICAO: 29-35mm from bottom for 35x45mm photo)
            # For digital images, we calculate this as a ratio of image height
            avg_eye_y = (left_eye[1] + right_eye[1]) / 2
            
            # Eye level should be approximately 25-70% from top of image (relaxed by ~15%)
            # (equivalent to having eyes in upper-middle portion of face)
            # This allows for forehead space above and mouth/chin space below
            eye_level_ratio = avg_eye_y / height
            eye_level_valid = 0.25 <= eye_level_ratio <= 0.70
            
            if not eye_level_valid:
                if eye_level_ratio < 0.30:
                    issues.append("Eyes are positioned too high in the image")
                else:
                    issues.append("Eyes are positioned too low in the image")
            
            eye_validation_details['eye_level_ratio'] = eye_level_ratio
            eye_validation_details['eye_level_target_range'] = (0.25, 0.70)
            
            # 2. Eye Distance Validation
            # Pupil-to-pupil distance should be proportional to face width
            eye_distance_pixels = abs(right_eye[0] - left_eye[0])
            eye_distance_ratio = eye_distance_pixels / w if w > 0 else 0
            
            # Typical eye distance is 15-60% of face width (relaxed by ~10-15%)
            eye_distance_valid = 0.15 <= eye_distance_ratio <= 0.60
            
            if not eye_distance_valid:
                if eye_distance_ratio < 0.15:
                    issues.append("Eyes appear too close together - check face angle")
                else:
                    issues.append("Eyes appear too far apart - check face angle or detection accuracy")
            
            eye_validation_details['eye_distance_ratio'] = eye_distance_ratio
            eye_validation_details['eye_distance_target_range'] = (0.15, 0.60)
            eye_validation_details['eye_distance_pixels'] = eye_distance_pixels
            
            # 3. Eye Symmetry Validation (relaxed tolerance)
            # Eyes should be horizontally aligned (same Y coordinate within tolerance)
            eye_y_difference = abs(left_eye[1] - right_eye[1])
            eye_y_tolerance = h * 0.08  # 8% of face height tolerance (relaxed from 5%)
            eye_symmetry_valid = eye_y_difference <= eye_y_tolerance
            
            if not eye_symmetry_valid:
                issues.append("Eyes are not horizontally aligned - check head tilt")
            
            eye_validation_details['eye_y_difference'] = eye_y_difference
            eye_validation_details['eye_y_tolerance'] = eye_y_tolerance
            eye_validation_details['eye_symmetry_score'] = max(0, 1 - (eye_y_difference / eye_y_tolerance))
            
            # 4. Eye Visibility Assessment (basic check based on positioning)
            # Eyes should be within the face bounding box and not at edges
            left_eye_in_bounds = (x + w * 0.05) <= left_eye[0] <= (x + w * 0.95)
            right_eye_in_bounds = (x + w * 0.05) <= right_eye[0] <= (x + w * 0.95)
            eyes_y_in_bounds = (y + h * 0.05) <= avg_eye_y <= (y + h * 0.7)
            
            eye_visibility_valid = left_eye_in_bounds and right_eye_in_bounds and eyes_y_in_bounds
            
            if not eye_visibility_valid:
                issues.append("Eyes may be partially obscured or at image edges")
            
            eye_validation_details['left_eye_in_bounds'] = left_eye_in_bounds
            eye_validation_details['right_eye_in_bounds'] = right_eye_in_bounds
            eye_validation_details['eyes_y_in_bounds'] = eyes_y_in_bounds
            
            # 5. Overall Eye Detection Confidence
            eye_validation_details['detection_confidence'] = face_data.confidence
        
        # Check for glasses/sunglasses (not allowed in passport photos)
        glasses_info = {'glasses_detected': False, 'sunglasses_detected': False}
        glasses_detected = False
        
        if image is not None:
            glasses_info = self.detect_glasses_or_sunglasses(image, face_data)
            glasses_detected = glasses_info['glasses_detected'] or glasses_info['sunglasses_detected']
            
            if glasses_detected:
                issues.append("Glasses or sunglasses detected - not allowed in passport photos")
                if glasses_info['sunglasses_detected']:
                    issues.append("Sunglasses must be removed for passport photos")
                if glasses_info['glasses_detected']:
                    issues.append("Regular glasses must be removed for passport photos")
        
        # ICAO Overall Eye Compliance (now includes glasses check)
        icao_eye_compliance = (eyes_detected and eye_level_valid and 
                              eye_distance_valid and eye_visibility_valid and 
                              eye_symmetry_valid and not glasses_detected)
        
        if not icao_eye_compliance and eyes_detected:
            issues.append("Eyes do not meet ICAO passport photo standards")
        
        # Face size validation (reuse from original method)
        face_size_valid = 0.70 <= face_data.face_size_ratio <= 0.80
        if not face_size_valid:
            if face_data.face_size_ratio < 0.70:
                issues.append("Face is too small - should be 70-80% of image height")
            else:
                issues.append("Face is too large - should be 70-80% of image height")
        
        # Face centering validation (reuse from original method)
        face_center_x = x + w / 2
        face_center_y = y + h / 2
        image_center_x = width / 2
        image_center_y = height / 2
        
        horizontal_offset = abs(face_center_x - image_center_x) / width
        vertical_offset = abs(face_center_y - image_center_y) / height
        
        centering_valid = horizontal_offset < 0.1 and vertical_offset < 0.15
        if not centering_valid:
            if horizontal_offset >= 0.1:
                issues.append("Face is not properly centered horizontally")
            if vertical_offset >= 0.15:
                issues.append("Face is not properly centered vertically")
        
        # Overall compliance requires all validations to pass
        is_compliant = (face_size_valid and icao_eye_compliance and centering_valid)
        
        return ComplianceResult(
            is_compliant=is_compliant,
            face_size_valid=face_size_valid,
            eye_positioning_valid=eye_level_valid,
            centering_valid=centering_valid,
            issues=issues,
            eyes_detected=eyes_detected,
            eye_level_valid=eye_level_valid,
            eye_distance_valid=eye_distance_valid,
            eye_visibility_valid=eye_visibility_valid,
            eye_symmetry_valid=eye_symmetry_valid,
            icao_eye_compliance=icao_eye_compliance,
            eye_validation_details=eye_validation_details,
            glasses_detected=glasses_info.get('glasses_detected', False),
            sunglasses_detected=glasses_info.get('sunglasses_detected', False),
            glasses_info=glasses_info
        )
    
    def detect_glasses_or_sunglasses(self, image: np.ndarray, face_data: FaceData) -> Dict[str, Any]:
        """
        Detect if person is wearing glasses or sunglasses (not allowed in passport photos)
        
        Args:
            image: Input image as numpy array
            face_data: Detected face data with eye positions
            
        Returns:
            Dict with glasses detection results
        """
        glasses_info = {
            'glasses_detected': False,
            'sunglasses_detected': False,
            'confidence': 0.0,
            'detection_method': 'none',
            'reasons': []
        }
        
        if not face_data.eye_positions:
            glasses_info['reasons'].append('No eye positions available for glasses detection')
            return glasses_info
        
        try:
            left_eye, right_eye = face_data.eye_positions
            x, y, w, h = face_data.bounding_box
            
            # Convert to grayscale for edge detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Define region around eyes for glasses detection
            eye_region_expansion = 0.3  # Expand 30% around eyes
            
            # Calculate eye region bounds
            min_x = max(0, int(min(left_eye[0], right_eye[0]) - w * eye_region_expansion))
            max_x = min(image.shape[1], int(max(left_eye[0], right_eye[0]) + w * eye_region_expansion))
            min_y = max(0, int(min(left_eye[1], right_eye[1]) - h * eye_region_expansion))
            max_y = min(image.shape[0], int(max(left_eye[1], right_eye[1]) + h * eye_region_expansion))
            
            eye_region = gray[min_y:max_y, min_x:max_x]
            
            if eye_region.size == 0:
                glasses_info['reasons'].append('Invalid eye region for glasses detection')
                return glasses_info
            
            # Method 1: Edge detection for glasses frames
            edges = cv2.Canny(eye_region, 50, 150)
            
            # Look for horizontal and vertical lines (typical of glasses frames)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
            
            horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
            vertical_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)
            
            # Count significant line pixels
            horizontal_pixels = np.sum(horizontal_lines > 0)
            vertical_pixels = np.sum(vertical_lines > 0)
            total_pixels = eye_region.shape[0] * eye_region.shape[1]
            
            line_density = (horizontal_pixels + vertical_pixels) / total_pixels
            
            # Method 2: Brightness analysis for sunglasses
            eye_brightness = np.mean(eye_region)
            face_brightness = np.mean(gray[y:y+h, x:x+w])
            brightness_ratio = eye_brightness / face_brightness if face_brightness > 0 else 1.0
            
            # Method 3: Contrast analysis around eyes
            eye_std = np.std(eye_region.astype(float))
            
            # Detection thresholds
            glasses_line_threshold = 0.02  # 2% of pixels should be frame lines
            sunglasses_brightness_threshold = 0.7  # Eyes should be at least 70% as bright as face
            low_contrast_threshold = 15  # Low standard deviation indicates uniform dark area (sunglasses)
            
            # Glasses detection logic
            if line_density > glasses_line_threshold:
                glasses_info['glasses_detected'] = True
                glasses_info['confidence'] = min(1.0, line_density / glasses_line_threshold)
                glasses_info['detection_method'] = 'edge_detection'
                glasses_info['reasons'].append(f'Detected glasses frames (line density: {line_density:.3f})')
            
            # Sunglasses detection logic
            if brightness_ratio < sunglasses_brightness_threshold and eye_std < low_contrast_threshold:
                glasses_info['sunglasses_detected'] = True
                glasses_info['confidence'] = max(glasses_info['confidence'], 
                                               1.0 - brightness_ratio + (low_contrast_threshold - eye_std) / low_contrast_threshold)
                glasses_info['detection_method'] = 'brightness_analysis'
                glasses_info['reasons'].append(f'Detected sunglasses (brightness ratio: {brightness_ratio:.3f}, contrast: {eye_std:.1f})')
            
            # Additional heuristics for glasses detection
            if eye_std > 30 and line_density > 0.01:  # High contrast with some lines
                glasses_info['glasses_detected'] = True
                glasses_info['confidence'] = max(glasses_info['confidence'], 0.6)
                glasses_info['reasons'].append('High contrast pattern suggests glasses frames')
            
            # Store analysis details
            glasses_info['analysis_details'] = {
                'line_density': line_density,
                'brightness_ratio': brightness_ratio,
                'eye_contrast': eye_std,
                'horizontal_lines': horizontal_pixels,
                'vertical_lines': vertical_pixels,
                'eye_brightness': eye_brightness,
                'face_brightness': face_brightness
            }
            
        except Exception as e:
            logging.error(f"Glasses detection failed: {e}")
            glasses_info['reasons'].append(f'Detection error: {str(e)}')
        
        return glasses_info
    
    def enhance_eye_detection_with_landmarks(self, image: np.ndarray, face_data: FaceData) -> FaceData:
        """
        Enhance eye detection using MediaPipe Face Mesh for more precise landmarks
        
        Args:
            image: Input image as numpy array
            face_data: Existing face data to enhance
            
        Returns:
            Enhanced FaceData with improved eye positions and landmarks
        """
        if not MEDIAPIPE_AVAILABLE:
            return face_data
        
        try:
            # Initialize MediaPipe Face Mesh for detailed landmarks
            mp_face_mesh = mp.solutions.face_mesh
            
            with mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.3
            ) as face_mesh:
                
                # Convert BGR to RGB
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                height, width = image.shape[:2]
                
                results = face_mesh.process(rgb_image)
                
                if results.multi_face_landmarks:
                    face_landmarks = results.multi_face_landmarks[0]
                    
                    # Extract key eye landmarks (MediaPipe Face Mesh indices)
                    # Left eye landmarks: 33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246
                    # Right eye landmarks: 362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398
                    
                    left_eye_indices = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
                    right_eye_indices = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
                    
                    # Calculate eye centers
                    left_eye_points = [(int(face_landmarks.landmark[i].x * width), 
                                      int(face_landmarks.landmark[i].y * height)) for i in left_eye_indices]
                    right_eye_points = [(int(face_landmarks.landmark[i].x * width), 
                                       int(face_landmarks.landmark[i].y * height)) for i in right_eye_indices]
                    
                    # Calculate eye centers as average of eye corner points
                    left_eye_center = (
                        sum(p[0] for p in left_eye_points) // len(left_eye_points),
                        sum(p[1] for p in left_eye_points) // len(left_eye_points)
                    )
                    right_eye_center = (
                        sum(p[0] for p in right_eye_points) // len(right_eye_points),
                        sum(p[1] for p in right_eye_points) // len(right_eye_points)
                    )
                    
                    # Extract additional landmarks
                    nose_tip = (int(face_landmarks.landmark[1].x * width), 
                               int(face_landmarks.landmark[1].y * height))
                    mouth_center = (int(face_landmarks.landmark[13].x * width), 
                                   int(face_landmarks.landmark[13].y * height))
                    
                    # Create enhanced landmarks dictionary
                    enhanced_landmarks = {
                        'left_eye': left_eye_center,
                        'right_eye': right_eye_center,
                        'nose_tip': nose_tip,
                        'mouth_center': mouth_center,
                        'left_eye_points': left_eye_points,
                        'right_eye_points': right_eye_points
                    }
                    
                    # Create enhanced face data
                    enhanced_face_data = FaceData(
                        bounding_box=face_data.bounding_box,
                        confidence=min(face_data.confidence + 0.1, 1.0),  # Boost confidence slightly
                        landmarks=enhanced_landmarks,
                        eye_positions=(left_eye_center, right_eye_center),
                        face_size_ratio=face_data.face_size_ratio
                    )
                    
                    return enhanced_face_data
        
        except Exception as e:
            logging.error(f"Face mesh enhancement failed: {e}")
        
        # Return original face data if enhancement fails
        return face_data