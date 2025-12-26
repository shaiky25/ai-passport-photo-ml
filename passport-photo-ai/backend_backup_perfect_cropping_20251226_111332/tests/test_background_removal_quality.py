"""
Tests for comprehensive background removal with quality evaluation
"""

import pytest
import numpy as np
import cv2
from PIL import Image, ImageDraw
import os
from enhancement.background_removal import ComprehensiveBackgroundRemover, BackgroundRemovalQualityMetrics
from enhancement.data_models import FaceData


class TestBackgroundRemovalQuality:
    """Test background removal quality evaluation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.remover = ComprehensiveBackgroundRemover()
        self.metrics = BackgroundRemovalQualityMetrics()
    
    def create_test_image_with_person(self, size=(400, 400), background_color='lightblue', person_color='brown'):
        """Create a test image with a simple person shape"""
        image = Image.new('RGB', size, background_color)
        draw = ImageDraw.Draw(image)
        
        # Draw simple person shape
        center_x, center_y = size[0] // 2, size[1] // 2
        
        # Body (rectangle)
        body_width, body_height = 80, 200
        body_left = center_x - body_width // 2
        body_top = center_y - body_height // 2
        draw.rectangle([body_left, body_top, body_left + body_width, body_top + body_height], fill=person_color)
        
        # Head (circle)
        head_radius = 40
        head_top = body_top - head_radius * 2
        draw.ellipse([center_x - head_radius, head_top, center_x + head_radius, head_top + head_radius * 2], fill=(255, 218, 185))  # Peach color
        
        # Create corresponding face data
        face_data = FaceData(
            bounding_box=(center_x - head_radius, head_top, head_radius * 2, head_radius * 2),
            confidence=0.9,
            landmarks={},
            eye_positions=None,
            face_size_ratio=(head_radius * 2) / size[1]
        )
        
        return image, face_data
    
    def create_perfect_removal_result(self, size=(400, 400)):
        """Create a perfect background removal result (person on white background)"""
        image = Image.new('RGB', size, 'white')
        draw = ImageDraw.Draw(image)
        
        # Draw person on white background
        center_x, center_y = size[0] // 2, size[1] // 2
        
        # Body
        body_width, body_height = 80, 200
        body_left = center_x - body_width // 2
        body_top = center_y - body_height // 2
        draw.rectangle([body_left, body_top, body_left + body_width, body_top + body_height], fill='brown')
        
        # Head
        head_radius = 40
        head_top = body_top - head_radius * 2
        draw.ellipse([center_x - head_radius, head_top, center_x + head_radius, head_top + head_radius * 2], fill=(255, 218, 185))  # Peach color
        
        return image
    
    def test_background_uniformity_evaluation(self):
        """Test background uniformity evaluation"""
        # Test perfect white background
        perfect_image = Image.new('RGB', (400, 400), 'white')
        perfect_array = np.array(perfect_image)
        uniformity_score = self.metrics.evaluate_background_uniformity(perfect_array)
        
        assert uniformity_score > 0.9, f"Perfect white background should score high: {uniformity_score}"
        
        # Test non-uniform background
        noisy_image = Image.new('RGB', (400, 400), 'white')
        noisy_array = np.array(noisy_image)
        # Add noise
        noise = np.random.randint(-50, 50, noisy_array.shape, dtype=np.int16)
        noisy_array = np.clip(noisy_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        noisy_uniformity = self.metrics.evaluate_background_uniformity(noisy_array)
        assert noisy_uniformity < uniformity_score, "Noisy background should score lower than perfect background"
    
    def test_edge_quality_evaluation(self):
        """Test edge quality evaluation"""
        # Create image with clean edges
        clean_image, face_data = self.create_test_image_with_person()
        clean_array = np.array(clean_image)
        
        edge_score = self.metrics.evaluate_edge_quality(clean_array, face_data)
        assert 0 <= edge_score <= 1, f"Edge score should be between 0 and 1: {edge_score}"
        
        # Test should return reasonable score for clean synthetic image
        assert edge_score > 0.3, f"Clean synthetic image should have reasonable edge score: {edge_score}"
    
    def test_person_preservation_evaluation(self):
        """Test person preservation evaluation"""
        original_image, face_data = self.create_test_image_with_person()
        
        # Test perfect preservation (same image)
        perfect_score = self.metrics.evaluate_person_preservation(
            np.array(original_image), np.array(original_image), face_data
        )
        assert perfect_score > 0.8, f"Identical images should have high preservation score: {perfect_score}"
        
        # Test with background removed but person preserved
        processed_image = self.create_perfect_removal_result()
        preservation_score = self.metrics.evaluate_person_preservation(
            np.array(original_image), np.array(processed_image), face_data
        )
        assert preservation_score > 0.5, f"Person should be reasonably preserved: {preservation_score}"
    
    def test_comprehensive_quality_evaluation(self):
        """Test comprehensive quality evaluation"""
        original_image, face_data = self.create_test_image_with_person()
        processed_image = self.create_perfect_removal_result()
        
        quality_metrics = self.remover.evaluate_removal_quality(original_image, processed_image, face_data)
        
        # Check all required metrics are present
        required_keys = ['background_uniformity', 'edge_quality', 'person_preservation', 'overall_quality', 'quality_grade']
        for key in required_keys:
            assert key in quality_metrics, f"Missing quality metric: {key}"
            if key != 'quality_grade':
                assert 0 <= quality_metrics[key] <= 1, f"Quality metric {key} should be 0-1: {quality_metrics[key]}"
        
        # Check quality grade is valid
        assert quality_metrics['quality_grade'] in ['A', 'B', 'C', 'D', 'F'], f"Invalid quality grade: {quality_metrics['quality_grade']}"
        
        print(f"Quality metrics: {quality_metrics}")
    
    def test_adaptive_background_removal(self):
        """Test adaptive background removal with quality evaluation"""
        original_image, face_data = self.create_test_image_with_person()
        
        # Test adaptive removal
        result_image, quality_metrics = self.remover.remove_background_adaptive(original_image, face_data)
        
        # Check result is valid
        assert isinstance(result_image, Image.Image), "Result should be PIL Image"
        assert result_image.mode == 'RGB', "Result should be RGB mode"
        assert result_image.size == original_image.size, "Result should maintain original size"
        
        # Check quality metrics
        assert isinstance(quality_metrics, dict), "Quality metrics should be dict"
        assert 'overall_quality' in quality_metrics, "Should include overall quality"
        assert 0 <= quality_metrics['overall_quality'] <= 1, "Overall quality should be 0-1"
        
        print(f"Adaptive removal quality: {quality_metrics['overall_quality']:.3f} ({quality_metrics['quality_grade']})")
        
        # Save result for visual inspection
        result_image.save('test_adaptive_bg_removal.jpg', quality=95)
        print("Saved test result: test_adaptive_bg_removal.jpg")
    
    def test_quality_grade_assignment(self):
        """Test quality grade assignment"""
        test_scores = [0.95, 0.85, 0.75, 0.65, 0.45]
        expected_grades = ['A', 'B', 'C', 'D', 'F']
        
        for score, expected_grade in zip(test_scores, expected_grades):
            grade = self.remover._get_quality_grade(score)
            assert grade == expected_grade, f"Score {score} should get grade {expected_grade}, got {grade}"
    
    @pytest.mark.skipif(not os.path.exists("backend/test_images"), reason="Test images directory not found")
    def test_real_image_background_removal(self):
        """Test background removal on real images if available"""
        test_dir = "backend/test_images"
        test_images = ["faiz.png", "sample_image_1.jpg", "sample_image_2.jpg"]
        
        for img_name in test_images:
            img_path = os.path.join(test_dir, img_name)
            if os.path.exists(img_path):
                print(f"\nTesting background removal on {img_name}")
                
                # Load image
                original_image = Image.open(img_path).convert('RGB')
                
                # Test adaptive removal (without face data for now)
                result_image, quality_metrics = self.remover.remove_background_adaptive(original_image)
                
                print(f"Quality: {quality_metrics['overall_quality']:.3f} ({quality_metrics['quality_grade']})")
                print(f"  Background uniformity: {quality_metrics['background_uniformity']:.3f}")
                print(f"  Edge quality: {quality_metrics['edge_quality']:.3f}")
                print(f"  Person preservation: {quality_metrics['person_preservation']:.3f}")
                
                # Save result
                output_name = f"test_bg_removal_{img_name}"
                result_image.save(output_name, quality=95)
                print(f"  Saved: {output_name}")
                
                # Basic quality check
                assert quality_metrics['overall_quality'] > 0.2, f"Quality too low for {img_name}: {quality_metrics['overall_quality']}"


class TestBackgroundRemovalIntegration:
    """Test integration with face detection"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.remover = ComprehensiveBackgroundRemover()
    
    def test_background_removal_with_face_detection(self):
        """Test background removal integrated with face detection results"""
        # This would be tested with actual face detection results
        # For now, test with synthetic face data
        
        original_image, face_data = TestBackgroundRemovalQuality().create_test_image_with_person()
        
        # Test removal with face data
        result_image, quality_metrics = self.remover.remove_background_adaptive(original_image, face_data)
        
        # Quality should be reasonable with face data
        assert quality_metrics['overall_quality'] > 0.3, f"Quality with face data should be reasonable: {quality_metrics['overall_quality']}"
        
        # Test removal without face data
        result_no_face, quality_no_face = self.remover.remove_background_adaptive(original_image, None)
        
        # Both should work, but face data might help with quality
        assert quality_no_face['overall_quality'] > 0.2, f"Quality without face data should still be reasonable: {quality_no_face['overall_quality']}"
        
        print(f"Quality with face data: {quality_metrics['overall_quality']:.3f}")
        print(f"Quality without face data: {quality_no_face['overall_quality']:.3f}")


if __name__ == "__main__":
    # Run basic tests
    test_class = TestBackgroundRemovalQuality()
    test_class.setup_method()
    
    print("Testing background removal quality evaluation...")
    test_class.test_comprehensive_quality_evaluation()
    test_class.test_adaptive_background_removal()
    
    print("\n✅ Background removal quality tests completed!")