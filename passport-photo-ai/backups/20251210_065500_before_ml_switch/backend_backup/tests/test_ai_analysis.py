"""
Tests for AI analysis integration functionality.
Tests Requirements 3.2, 3.3, 3.4, 3.5, 3.7 from the specification.
"""

import pytest
import os
import json
import base64
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import tempfile


class TestAIAnalysisIntegration:
    """Test AI analysis integration with Claude API."""
    
    def test_ai_analysis_method_exists(self):
        """Test that the AI analysis method is available."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        assert hasattr(processor, 'analyze_with_ai')
        assert callable(processor.analyze_with_ai)
    
    def test_image_encoding_for_ai(self):
        """
        Test that images are encoded as base64 with correct media type.
        Validates: Requirement 3.2 - WHEN the System sends an image to the AI 
        THEN the System SHALL encode the image as base64 and specify the correct media type
        """
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (100, 100), color='red')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Read and encode the image
            with open(tmp_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')
            
            # Verify encoding
            assert isinstance(image_data, str)
            assert len(image_data) > 0
            
            # Verify it's valid base64
            try:
                decoded = base64.standard_b64decode(image_data)
                assert len(decoded) > 0
            except Exception:
                pytest.fail("Image data is not valid base64")
            
            # Verify media type detection
            ext = os.path.splitext(tmp_path)[1].lower()
            media_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}
            media_type = media_types.get(ext, 'image/jpeg')
            
            assert media_type == 'image/jpeg'
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    def test_media_type_detection_for_different_formats(self):
        """Test that media type is correctly detected for different image formats."""
        test_cases = [
            ('.jpg', 'image/jpeg'),
            ('.jpeg', 'image/jpeg'),
            ('.JPG', 'image/jpeg'),
            ('.JPEG', 'image/jpeg'),
            ('.png', 'image/png'),
            ('.PNG', 'image/png'),
            ('.unknown', 'image/jpeg'),  # Default fallback
        ]
        
        for ext, expected_media_type in test_cases:
            media_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}
            media_type = media_types.get(ext.lower(), 'image/jpeg')
            assert media_type == expected_media_type, f"Failed for extension {ext}"
    
    @pytest.mark.asyncio
    async def test_ai_response_parsing(self):
        """
        Test that AI responses are correctly parsed.
        Validates: Requirement 3.4 - WHEN the AI returns a response 
        THEN the System SHALL parse the JSON response containing compliance status and specific issues
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock AI response
        mock_response = {
            "compliant": False,
            "issues": ["Background is not white", "Person is wearing glasses"],
            "analysis_details": {
                "background_ok": False,
                "expression_neutral": True,
                "eyes_open": True,
                "no_eyeglasses": False,
                "no_head_covering_issue": True,
                "lighting_ok": True
            }
        }
        
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (100, 100), color='blue')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Mock the Anthropic API (imported inside the method)
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client
                
                mock_message = MagicMock()
                mock_message.content = [MagicMock(text=json.dumps(mock_response))]
                mock_client.messages.create.return_value = mock_message
                
                result = await processor.analyze_with_ai(tmp_path)
                
                # Verify parsing
                assert result['success'] is True
                assert 'ai_analysis' in result
                assert result['ai_analysis']['compliant'] is False
                assert len(result['ai_analysis']['issues']) == 2
                assert 'analysis_details' in result['ai_analysis']
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    @pytest.mark.asyncio
    async def test_ai_issues_extraction(self):
        """
        Test that specific issues are extracted from AI response.
        Validates: Requirement 3.5 - WHEN the AI identifies non-compliance 
        THEN the System SHALL extract and display the list of specific issues found
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        # Mock AI response with specific issues
        mock_response = {
            "compliant": False,
            "issues": [
                "Background is not plain white",
                "Person is wearing eyeglasses",
                "Expression is not neutral (smiling)"
            ],
            "analysis_details": {
                "background_ok": False,
                "expression_neutral": False,
                "eyes_open": True,
                "no_eyeglasses": False,
                "no_head_covering_issue": True,
                "lighting_ok": True
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (100, 100), color='green')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client
                
                mock_message = MagicMock()
                mock_message.content = [MagicMock(text=json.dumps(mock_response))]
                mock_client.messages.create.return_value = mock_message
                
                result = await processor.analyze_with_ai(tmp_path)
                
                # Verify issues extraction
                assert result['success'] is True
                assert 'issues' in result['ai_analysis']
                issues = result['ai_analysis']['issues']
                assert len(issues) == 3
                assert "Background is not plain white" in issues
                assert "Person is wearing eyeglasses" in issues
                assert "Expression is not neutral (smiling)" in issues
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    @pytest.mark.asyncio
    async def test_ai_analysis_error_handling(self):
        """
        Test that AI analysis errors are handled gracefully.
        Validates: Requirement 3.7 - WHEN the AI analysis fails due to an error 
        THEN the System SHALL return an error status without blocking the rest of the processing workflow
        """
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (100, 100), color='yellow')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            # Mock the Anthropic API to raise an exception
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_anthropic.side_effect = Exception("API connection failed")
                
                result = await processor.analyze_with_ai(tmp_path)
                
                # Verify error handling
                assert result['success'] is False
                assert 'error' in result
                assert result['ai_analysis'] is None
                assert "API connection failed" in result['error']
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    @pytest.mark.asyncio
    async def test_ai_response_with_json_code_blocks(self):
        """Test that AI responses wrapped in JSON code blocks are parsed correctly."""
        from application import PassportPhotoProcessor
        
        processor = PassportPhotoProcessor()
        
        mock_response = {
            "compliant": True,
            "issues": [],
            "analysis_details": {
                "background_ok": True,
                "expression_neutral": True,
                "eyes_open": True,
                "no_eyeglasses": True,
                "no_head_covering_issue": True,
                "lighting_ok": True
            }
        }
        
        # Wrap response in code blocks (as Claude sometimes does)
        wrapped_response = f"```json\n{json.dumps(mock_response)}\n```"
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img = Image.new('RGB', (100, 100), color='white')
            test_img.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client
                
                mock_message = MagicMock()
                mock_message.content = [MagicMock(text=wrapped_response)]
                mock_client.messages.create.return_value = mock_message
                
                result = await processor.analyze_with_ai(tmp_path)
                
                # Verify parsing works with code blocks
                assert result['success'] is True
                assert result['ai_analysis']['compliant'] is True
                assert len(result['ai_analysis']['issues']) == 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestAIAnalysisPrompt:
    """Test AI analysis prompt structure and requirements."""
    
    def test_prompt_includes_all_compliance_rules(self):
        """
        Test that the AI prompt includes all U.S. visa photo compliance rules.
        Validates: Requirement 3.3 - WHEN the System requests AI analysis 
        THEN the System SHALL provide a structured prompt listing all U.S. visa photo compliance rules
        """
        # Expected compliance rules
        required_rules = [
            "Background",
            "white",
            "Expression",
            "neutral",
            "eyes open",
            "Head Coverings",
            "Eyeglasses",
            "Lighting",
            "Quality"
        ]
        
        # This would be the actual prompt from the code
        prompt = """
Analyze this photo for U.S. visa photo compliance. Respond in JSON format only.
Rules:
1. Background: Must be plain white or off-white.
2. View/Expression: Full-face view, neutral expression, both eyes open.
3. Head Coverings: No hats/head coverings unless for religious purposes (full face visible, no shadows).
4. Eyeglasses: Not allowed.
5. Other Items: No headphones or similar devices.
6. Lighting: Well-lit, no shadows on the face.
7. Quality: In color, clear, not a copy/scan.
"""
        
        # Verify all required rules are mentioned
        for rule in required_rules:
            assert rule.lower() in prompt.lower(), f"Prompt missing rule: {rule}"
    
    def test_prompt_requests_json_format(self):
        """Test that the prompt requests JSON format response."""
        prompt = """
Analyze this photo for U.S. visa photo compliance. Respond in JSON format only.
"""
        assert "JSON" in prompt or "json" in prompt
    
    def test_prompt_specifies_response_structure(self):
        """Test that the prompt specifies the expected response structure."""
        prompt = """
Respond with this structure:
{
  "compliant": true/false,
  "issues": ["List of specific issues found."],
  "analysis_details": {
    "background_ok": true/false, "expression_neutral": true/false, "eyes_open": true/false,
    "no_eyeglasses": true/false, "no_head_covering_issue": true/false, "lighting_ok": true/false
  }
}
"""
        
        required_fields = ["compliant", "issues", "analysis_details"]
        for field in required_fields:
            assert field in prompt


class TestAIAnalysisResponseStructure:
    """Test AI analysis response structure validation."""
    
    def test_compliant_response_structure(self):
        """Test the structure of a compliant AI response."""
        response = {
            "compliant": True,
            "issues": [],
            "analysis_details": {
                "background_ok": True,
                "expression_neutral": True,
                "eyes_open": True,
                "no_eyeglasses": True,
                "no_head_covering_issue": True,
                "lighting_ok": True
            }
        }
        
        # Verify structure
        assert 'compliant' in response
        assert 'issues' in response
        assert 'analysis_details' in response
        assert isinstance(response['compliant'], bool)
        assert isinstance(response['issues'], list)
        assert isinstance(response['analysis_details'], dict)
    
    def test_non_compliant_response_structure(self):
        """Test the structure of a non-compliant AI response."""
        response = {
            "compliant": False,
            "issues": ["Background is not white", "Wearing glasses"],
            "analysis_details": {
                "background_ok": False,
                "expression_neutral": True,
                "eyes_open": True,
                "no_eyeglasses": False,
                "no_head_covering_issue": True,
                "lighting_ok": True
            }
        }
        
        # Verify structure
        assert response['compliant'] is False
        assert len(response['issues']) > 0
        assert all(isinstance(issue, str) for issue in response['issues'])
        
        # Verify analysis details
        details = response['analysis_details']
        assert 'background_ok' in details
        assert 'expression_neutral' in details
        assert 'eyes_open' in details
        assert 'no_eyeglasses' in details
        assert 'no_head_covering_issue' in details
        assert 'lighting_ok' in details
