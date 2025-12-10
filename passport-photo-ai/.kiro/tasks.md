# Implementation Plan

- [x] 1. Set up testing infrastructure
  - Install pytest, Hypothesis, pytest-mock for backend testing
  - Install Jest, React Testing Library, fast-check for frontend testing
  - Create test directory structure (backend/tests/, frontend/src/__tests__/)
  - Configure pytest.ini and jest.config.js with coverage settings
  - Create test fixtures directory with sample images (various sizes, face counts)
  - _Requirements: All testing requirements_

- [ ]* 1.1 Write property test for format acceptance
  - **Property 1: Format acceptance**
  - **Validates: Requirements 1.1**

- [ ]* 1.2 Write property test for resolution validation
  - **Property 3: Resolution validation**
  - **Validates: Requirements 1.4**

- [x] 2. Implement and test face detection validation
  - Create test images with 0, 1, and multiple faces
  - Verify face detection returns correct face count
  - Verify bounding box extraction for single face images
  - _Requirements: 2.2, 2.3, 2.4_

- [ ]* 2.1 Write property test for single face bounding box extraction
  - **Property 4: Single face bounding box extraction**
  - **Validates: Requirements 2.4**

- [ ]* 2.2 Write property test for head height ratio calculation
  - **Property 5: Head height ratio calculation**
  - **Validates: Requirements 2.6**

- [ ]* 2.3 Write property test for head height validation
  - **Property 6: Head height validation**
  - **Validates: Requirements 2.7**

- [ ]* 2.4 Write property test for horizontal centering validation
  - **Property 7: Horizontal centering validation**
  - **Validates: Requirements 2.8**

- [x] 3. Test HEIC conversion functionality
  - Create test HEIC files or use sample HEIC images
  - Verify HEIC files are converted to JPEG before processing
  - Verify converted images are valid JPEG format
  - _Requirements: 1.2_

- [ ]* 3.1 Write property test for HEIC conversion round-trip
  - **Property 2: HEIC conversion round-trip**
  - **Validates: Requirements 1.2**

- [x] 4. Test AI analysis integration
  - Create mock AI responses for testing
  - Verify AI request includes base64 encoded image with correct media type
  - Verify AI response parsing extracts compliance status and issues
  - Test error handling when AI analysis fails
  - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.7_

- [ ]* 4.1 Write property test for image encoding for AI
  - **Property 8: Image encoding for AI**
  - **Validates: Requirements 3.2**

- [ ]* 4.2 Write property test for AI response parsing
  - **Property 9: AI response parsing**
  - **Validates: Requirements 3.4**

- [ ]* 4.3 Write property test for AI issues extraction
  - **Property 10: AI issues extraction**
  - **Validates: Requirements 3.5**

- [x] 5. Test background removal functionality
  - Verify background pixels are white (255, 255, 255) after removal
  - Verify foreground subject is preserved
  - Test fallback behavior when background removal fails
  - Test toggle on/off functionality
  - _Requirements: 4.2, 4.3, 4.4, 4.5_

- [ ]* 5.1 Write property test for background color replacement
  - **Property 11: Background color replacement**
  - **Validates: Requirements 4.2**

- [ ]* 5.2 Write property test for foreground preservation
  - **Property 12: Foreground preservation**
  - **Validates: Requirements 4.3**

- [x] 6. Test image processing and cropping
  - Verify output dimensions are exactly 600x600 at 300 DPI
  - Verify face centering in processed photos
  - Verify crop boundaries remain within image bounds
  - Test processing with and without learned profile
  - Test center crop fallback when no face detected
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ]* 6.1 Write property test for output dimensions invariant
  - **Property 13: Output dimensions invariant**
  - **Validates: Requirements 5.1**

- [ ]* 6.2 Write property test for face centering after crop
  - **Property 14: Face centering after crop**
  - **Validates: Requirements 5.2**

- [ ]* 6.3 Write property test for crop boundary constraints
  - **Property 15: Crop boundary constraints**
  - **Validates: Requirements 5.5**

- [x] 7. Test image enhancement and output format
  - Verify brightness enhancement factor is 1.05
  - Verify contrast enhancement factor is 1.1
  - Verify output format is JPEG with 95% quality and 300 DPI
  - _Requirements: 5.7, 5.8_

- [ ]* 7.1 Write property test for brightness and contrast enhancement
  - **Property 16: Brightness and contrast enhancement**
  - **Validates: Requirements 5.7**

- [ ]* 7.2 Write property test for output format specifications
  - **Property 17: Output format specifications**
  - **Validates: Requirements 5.8**

- [x] 8. Test learning script functionality
  - Verify script processes all JPEG and PNG files in training_data
  - Verify geometric ratios are calculated for detected faces
  - Verify mean and standard deviation are computed correctly
  - Verify learned_profile.json is created with valid structure
  - Test error handling for images with 0 or multiple faces
  - _Requirements: 6.1, 6.3, 6.4, 6.5, 6.7_

- [ ]* 8.1 Write property test for training data processing
  - **Property 18: Training data processing**
  - **Validates: Requirements 6.1**

- [ ]* 8.2 Write property test for geometric ratio calculation
  - **Property 19: Geometric ratio calculation**
  - **Validates: Requirements 6.3**

- [ ]* 8.3 Write property test for statistical profile computation
  - **Property 20: Statistical profile computation**
  - **Validates: Requirements 6.4**

- [ ]* 8.4 Write property test for profile persistence
  - **Property 21: Profile persistence**
  - **Validates: Requirements 6.5**

- [x] 9. Test compliance checklist UI
  - Verify all 8 compliance checks are displayed
  - Verify correct icons for pass/fail/pending states
  - Verify face detection failure cascades to dependent checks
  - Verify "Will be replaced" message when background removal enabled
  - Verify issues list is displayed when AI identifies problems
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ]* 9.1 Write property test for face detection failure cascade
  - **Property 22: Face detection failure cascade**
  - **Validates: Requirements 7.5**

- [x] 10. Test download functionality
  - Verify single photo download with correct filename
  - Verify download button appears after successful processing
  - Verify print sheet options enabled only when fully compliant
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 11. Test print sheet generation
  - Verify 4x6 print sheet dimensions (1800x1200 at 300 DPI) with 2 photos
  - Verify 5x7 print sheet dimensions (2100x1500 at 300 DPI) with 4 photos
  - Verify cutting guide lines are present
  - Verify equal margins between photos
  - _Requirements: 8.4, 8.5, 8.6, 8.7_

- [ ]* 11.1 Write property test for 4x6 print sheet specifications
  - **Property 23: 4x6 print sheet specifications**
  - **Validates: Requirements 8.4**

- [ ]* 11.2 Write property test for 5x7 print sheet specifications
  - **Property 24: 5x7 print sheet specifications**
  - **Validates: Requirements 8.5**

- [ ]* 11.3 Write property test for print sheet cutting guides
  - **Property 25: Print sheet cutting guides**
  - **Validates: Requirements 8.6**

- [ ]* 11.4 Write property test for print sheet margin equality
  - **Property 26: Print sheet margin equality**
  - **Validates: Requirements 8.7**

- [x] 12. Test state management and reset functionality
  - Verify "Start Over" clears all state (file, preview, analysis, processed image)
  - Verify file input is reset
  - Verify UI returns to initial upload screen
  - Verify new upload works correctly after reset
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 13. Test analytics logging
  - Verify processing events are logged with status
  - Verify compliance status is included in logs
  - Verify download events are logged with type
  - Verify all log entries include UTC timestamp
  - Verify log format is valid JSON on single lines
  - Verify log directory is created if not exists
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ]* 13.1 Write property test for processing event logging
  - **Property 27: Processing event logging**
  - **Validates: Requirements 10.1**

- [ ]* 13.2 Write property test for compliance status logging
  - **Property 28: Compliance status logging**
  - **Validates: Requirements 10.2**

- [ ]* 13.3 Write property test for download event logging
  - **Property 29: Download event logging**
  - **Validates: Requirements 10.4**

- [ ]* 13.4 Write property test for log timestamp inclusion
  - **Property 30: Log timestamp inclusion**
  - **Validates: Requirements 10.5**

- [ ]* 13.5 Write property test for log format consistency
  - **Property 31: Log format consistency**
  - **Validates: Requirements 10.6**

- [x] 14. Test background removal toggle
  - Verify toggle is displayed in UI
  - Verify toggle state changes background removal setting
  - Verify changing toggle triggers reprocessing
  - Verify toggle is disabled during processing
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 15. Test loading and error UI states
  - Verify loading spinner displays during processing
  - Verify original image shows with reduced opacity during processing
  - Verify "Processing..." text displays
  - Verify scanning line animation displays
  - Verify loading indicators removed after completion
  - Verify error icon and message display on failure
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 17. Integration testing
  - Test full end-to-end workflow: upload → detect → analyze → process → download
  - Test workflow without AI analysis
  - Test workflow with background removal
  - Test error scenarios (invalid files, network errors, API failures)
  - _Requirements: All requirements_

- [ ]* 18. Performance testing
  - Benchmark face detection performance with various image sizes
  - Benchmark background removal performance
  - Benchmark full workflow processing time
  - Verify performance meets expected targets (<10 seconds total)
  - _Requirements: Performance considerations_

- [ ]* 19. Security testing
  - Test file size limits (16MB)
  - Test file type validation
  - Verify temporary files are cleaned up
  - Verify no sensitive data in logs
  - Test CORS configuration
  - _Requirements: Security considerations_

- [x] 20. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
