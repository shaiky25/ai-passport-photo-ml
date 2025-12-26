# Deployment Pipeline Configuration

## Overview
This deployment pipeline ensures that all critical tests pass before deploying the government-compliant passport photo application to AWS Elastic Beanstalk.

## Pipeline Components

### 1. Pre-deployment Tests (`deployment_test_suite.py`)
- **Server Health**: Verifies Flask application is running and healthy
- **System Dependencies**: Checks OpenCV, REMBG, and HEIC support
- **Pipeline Configuration**: Validates all feature flags are correctly set
- **Government Compliance**: Tests passport photo compliance with sample images
- **Performance**: Validates response times are acceptable

### 2. Deployment Script (`deploy_with_tests.sh`)
- Runs comprehensive test suite
- Creates automatic backup before deployment
- Deploys to AWS Elastic Beanstalk with version labeling
- Performs post-deployment validation
- Provides rollback information if deployment fails

### 3. Rollback Script (`rollback_deployment.sh`)
- Emergency rollback to previous working version
- Lists available deployment versions
- Tests rolled-back deployment health

## Critical Test Requirements

### Must Pass (Deployment Blockers):
- ✅ Server health check
- ✅ OpenCV availability
- ✅ REMBG availability  
- ✅ Enhanced face detection enabled
- ✅ Intelligent cropping enabled
- ✅ Image enhancement enabled
- ✅ Government compliance (100% for single-face images)
- ✅ Face height ratio exactly 75% (within 70-80% requirement)

### Should Pass (Warnings Only):
- ✅ HEIC support
- ✅ Background removal disabled (for stability)
- ✅ Watermark enabled
- ✅ Learned profile enabled
- ✅ Response time < 1 second
- ✅ Image processing < 5 seconds

## Usage

### Deploy with Tests
```bash
./deploy_with_tests.sh
```

### Run Tests Only
```bash
python deployment_test_suite.py
```

### Emergency Rollback
```bash
./rollback_deployment.sh
```

### Test Remote Deployment
```bash
python deployment_test_suite.py https://your-app-url.elasticbeanstalk.com
```

## Test Images Required
The pipeline requires these test images in `backend/test_images/`:
- `faiz.png` - Basic face test
- `sample_image_1.jpg` - Standard portrait
- `faiz_with_glasses.png` - Edge case (glasses)

## Deployment Checklist

Before running deployment:
- [ ] All local tests pass
- [ ] Code changes committed to git (recommended)
- [ ] Test images available
- [ ] AWS credentials configured
- [ ] EB CLI installed and configured

## Pipeline Flow

1. **Pre-deployment Checks**
   - Verify environment setup
   - Check git status (optional)
   - Validate required files

2. **Local Testing**
   - Start Flask test server
   - Run comprehensive test suite
   - Validate all critical requirements

3. **Backup Creation**
   - Create timestamped backup
   - Store in `deployment_backup_YYYYMMDD_HHMMSS/`

4. **Deployment**
   - Deploy to Elastic Beanstalk with version label
   - Monitor deployment progress

5. **Post-deployment Validation**
   - Test deployed application health
   - Validate government compliance on live server
   - Confirm all endpoints working

6. **Cleanup**
   - Remove temporary test files
   - Report deployment success/failure

## Monitoring

After deployment, monitor:
- Application health via `/api/health`
- Government compliance via test suite
- Performance metrics
- Error rates in EB logs

## Troubleshooting

### Common Issues:
1. **Test failures**: Check server logs and fix issues before retrying
2. **Deployment timeout**: Increase timeout or check EB environment health
3. **Post-deployment failures**: Use rollback script immediately

### Emergency Procedures:
1. If deployment fails: Automatic rollback information provided
2. If tests fail post-deployment: Run `./rollback_deployment.sh`
3. If application is unhealthy: Check EB logs and consider rollback

## Version Management

Deployments use timestamp-based version labels:
- Format: `app-YYMMDD_HHMMSS`
- Example: `app-251226_143022`

Backups use similar naming:
- Format: `deployment_backup_YYYYMMDD_HHMMSS`
- Example: `deployment_backup_20251226_143022`