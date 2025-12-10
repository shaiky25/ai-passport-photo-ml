# Requirements Document

## Introduction

The Passport Photo Processor is an AI-driven web application that converts user-uploaded photos into compliant U.S. passport and visa photos. The system combines computer vision for geometric analysis, deep learning for background removal, and large language models for qualitative compliance checking. The application provides real-time feedback on photo compliance, automatically processes images to meet official specifications, and generates print-ready sheets for physical submission.

## Glossary

- **System**: The Passport Photo Processor application (frontend and backend combined)
- **User**: An individual who uploads a photo to be processed into a passport photo
- **Passport Photo**: A 2x2 inch photo (600x600 pixels at 300 DPI) meeting U.S. passport/visa requirements
- **Face Detection**: Computer vision process to identify and locate human faces in images
- **Background Removal**: Deep learning process to isolate the subject and replace the background
- **Compliance Analysis**: Automated checking of photo against official passport photo requirements
- **AI Analysis**: Large language model evaluation of qualitative photo characteristics
- **Learned Profile**: Statistical model derived from sample photos to optimize cropping
- **Print Sheet**: A formatted page (4x6 or 5x7 inches) containing multiple passport photos with cutting guides
- **Head Height Ratio**: The proportion of the image height occupied by the head (must be 50-69%)
- **HEIC Format**: High Efficiency Image Container format used by Apple devices

## Requirements

### Requirement 1

**User Story:** As a user, I want to upload a photo in common formats, so that I can process it into a passport photo regardless of my device or camera.

#### Acceptance Criteria

1. WHEN a user uploads an image file THEN the System SHALL accept JPEG, PNG, and HEIC formats
2. WHEN a user uploads a HEIC file THEN the System SHALL convert it to JPEG format before processing
3. WHEN a user uploads a file larger than 16MB THEN the System SHALL reject the upload and notify the user
4. WHEN a user uploads an image with resolution below 600x600 pixels THEN the System SHALL reject the image and inform the user that resolution is too low
5. WHEN a user selects a file THEN the System SHALL display a preview of the original image

### Requirement 2

**User Story:** As a user, I want the system to detect faces in my photo, so that I can verify my photo is suitable for processing.

#### Acceptance Criteria

1. WHEN the System processes an uploaded image THEN the System SHALL detect faces using OpenCV Haar Cascade face detection
2. WHEN the System detects zero faces THEN the System SHALL report "No face detected" and prevent further processing
3. WHEN the System detects multiple faces THEN the System SHALL report "Multiple faces detected" and prevent further processing
4. WHEN the System detects exactly one face THEN the System SHALL extract the face bounding box coordinates
5. WHEN the System processes large images THEN the System SHALL resize images exceeding 1024 pixels in the largest dimension before face detection to improve performance
6. WHEN the System detects a face THEN the System SHALL calculate the head height ratio as the face height divided by image height
7. WHEN the head height ratio is between 0.50 and 0.69 THEN the System SHALL mark head height as valid
8. WHEN the face center is within 30% of the horizontal image center THEN the System SHALL mark the face as horizontally centered

### Requirement 3

**User Story:** As a user, I want AI-powered compliance analysis, so that I can understand if my photo meets qualitative passport requirements.

#### Acceptance Criteria

1. WHEN the System performs AI analysis THEN the System SHALL use the Anthropic Claude API to evaluate the photo
2. WHEN the System sends an image to the AI THEN the System SHALL encode the image as base64 and specify the correct media type
3. WHEN the System requests AI analysis THEN the System SHALL provide a structured prompt listing all U.S. visa photo compliance rules
4. WHEN the AI returns a response THEN the System SHALL parse the JSON response containing compliance status and specific issues
5. WHEN the AI identifies non-compliance THEN the System SHALL extract and display the list of specific issues found
6. WHEN the AI analysis evaluates the photo THEN the System SHALL check for plain white background, neutral expression, open eyes, no eyeglasses, no head coverings (except religious), proper lighting, and no shadows
7. WHEN the AI analysis fails due to an error THEN the System SHALL return an error status without blocking the rest of the processing workflow

### Requirement 4

**User Story:** As a user, I want automatic background removal, so that I can ensure my photo has a compliant plain white background.

#### Acceptance Criteria

1. WHEN a user enables background removal THEN the System SHALL use the rembg deep learning model to remove the background
2. WHEN the System removes a background THEN the System SHALL replace it with a solid white background (RGB 255, 255, 255)
3. WHEN background removal is enabled THEN the System SHALL preserve the foreground subject with transparency information
4. WHEN background removal fails THEN the System SHALL return the original image without modification
5. WHEN a user disables background removal THEN the System SHALL process the photo with the original background intact

### Requirement 5

**User Story:** As a user, I want my photo automatically cropped and sized to passport specifications, so that I don't need to manually adjust dimensions.

#### Acceptance Criteria

1. WHEN the System processes a photo THEN the System SHALL produce a final image of exactly 600x600 pixels at 300 DPI
2. WHEN a valid face is detected THEN the System SHALL crop the image to center the face and achieve proper head positioning
3. WHEN a learned profile exists THEN the System SHALL use the learned geometric ratios to determine crop position and size
4. WHEN no learned profile exists THEN the System SHALL use default cropping rules with a target head height ratio of 0.60
5. WHEN calculating crop dimensions THEN the System SHALL ensure the crop area remains within image boundaries
6. WHEN no face is detected THEN the System SHALL perform a center crop using the minimum dimension of the image
7. WHEN the System produces the final image THEN the System SHALL apply brightness enhancement of 1.05 and contrast enhancement of 1.1
8. WHEN the System saves the processed image THEN the System SHALL use JPEG format with 95% quality, 300 DPI resolution, and 4:4:4 chroma subsampling to ensure maximum quality for government submission

### Requirement 6

**User Story:** As a user, I want to learn optimal cropping parameters from sample photos, so that the system can improve its accuracy over time.

#### Acceptance Criteria

1. WHEN the learning script runs THEN the System SHALL analyze all JPEG and PNG images in the training_data directory
2. WHEN the learning script analyzes an image THEN the System SHALL detect exactly one face using Haar Cascade classifier
3. WHEN the learning script detects a face THEN the System SHALL calculate head height ratio, face center x ratio, and head top y ratio
4. WHEN the learning script processes all images THEN the System SHALL compute mean and standard deviation for all geometric ratios
5. WHEN the learning script completes THEN the System SHALL save the statistical profile to learned_profile.json
6. WHEN the main application starts THEN the System SHALL load the learned profile if it exists
7. WHEN an image has zero or multiple faces THEN the learning script SHALL skip that image and log a warning

### Requirement 7

**User Story:** As a user, I want to see a detailed compliance checklist, so that I can understand what aspects of my photo meet or fail requirements.

#### Acceptance Criteria

1. WHEN the System completes analysis THEN the System SHALL display compliance status for high resolution, head centered, correct head size, plain background, neutral expression, eyes open, no shadows, and no obstructions
2. WHEN a compliance check passes THEN the System SHALL display a green checkmark icon
3. WHEN a compliance check fails THEN the System SHALL display a red X icon
4. WHEN a compliance check is not yet evaluated THEN the System SHALL display a gray dot icon
5. WHEN face detection fails THEN the System SHALL mark all face-dependent checks as failed
6. WHEN background removal is enabled and background check fails THEN the System SHALL display "Will be replaced" instead of a failure indicator
7. WHEN AI analysis identifies issues THEN the System SHALL display a list of specific issues to fix

### Requirement 8

**User Story:** As a user, I want to download my processed passport photo, so that I can submit it for my passport or visa application.

#### Acceptance Criteria

1. WHEN the System successfully processes a photo THEN the System SHALL provide a download button for the single processed photo
2. WHEN a user clicks download THEN the System SHALL download the image as a JPEG file named "passport_photo_2x2.jpg"
3. WHEN the photo is fully compliant THEN the System SHALL enable print sheet download options
4. WHEN a user requests a 4x6 print sheet THEN the System SHALL generate a 1800x1200 pixel image at 300 DPI with 2 passport photos arranged horizontally
5. WHEN a user requests a 5x7 print sheet THEN the System SHALL generate a 2100x1500 pixel image at 300 DPI with 4 passport photos in a 2x2 grid
6. WHEN the System generates a print sheet THEN the System SHALL include dashed cutting guide lines around each photo
7. WHEN the System generates a print sheet THEN the System SHALL center the photos with equal margins between them

### Requirement 9

**User Story:** As a user, I want to restart the process with a new photo, so that I can process multiple photos in one session.

#### Acceptance Criteria

1. WHEN a user clicks "Start Over" THEN the System SHALL clear the uploaded file, preview, analysis results, and processed image
2. WHEN a user clicks "Start Over" THEN the System SHALL reset the file input element
3. WHEN the state is reset THEN the System SHALL return to the initial upload screen
4. WHEN a user uploads a new file after starting over THEN the System SHALL process it as if it were the first upload

### Requirement 10

**User Story:** As a system administrator, I want to collect analytics on user interactions, so that I can understand usage patterns and improve the application.

#### Acceptance Criteria

1. WHEN a user completes photo processing THEN the System SHALL log an analytics event with processing status
2. WHEN processing succeeds THEN the System SHALL log whether the photo is fully compliant or partially compliant
3. WHEN processing fails THEN the System SHALL log the error message and failure reason
4. WHEN a user downloads a photo THEN the System SHALL log a download event with the download type
5. WHEN the System logs an event THEN the System SHALL include a server-side UTC timestamp
6. WHEN the System logs an event THEN the System SHALL write it as a single JSON line to the analytics.log file
7. WHEN the analytics log directory does not exist THEN the System SHALL create it automatically

### Requirement 11

**User Story:** As a user, I want to toggle background removal on and off, so that I can choose whether to keep my original background.

#### Acceptance Criteria

1. WHEN the user interface loads THEN the System SHALL display a background removal toggle switch
2. WHEN the toggle is enabled THEN the System SHALL set background removal to true
3. WHEN the toggle is disabled THEN the System SHALL set background removal to false
4. WHEN a user changes the toggle state THEN the System SHALL reprocess the current image with the new setting
5. WHEN processing is in progress THEN the System SHALL disable the toggle to prevent state changes during processing

### Requirement 12

**User Story:** As a user, I want visual feedback during processing, so that I know the system is working on my photo.

#### Acceptance Criteria

1. WHEN the System begins processing THEN the System SHALL display a loading spinner animation
2. WHEN the System is processing THEN the System SHALL show the original image with reduced opacity
3. WHEN the System is processing THEN the System SHALL display "Processing..." text
4. WHEN the System is processing THEN the System SHALL show a scanning line animation overlay
5. WHEN processing completes successfully THEN the System SHALL remove all loading indicators and display the processed image
6. WHEN processing fails THEN the System SHALL display an error icon and error message
