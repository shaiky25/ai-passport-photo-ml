# AWS Free Tier Deployment Guide
## Passport Photo AI Application

This guide will help you deploy your Passport Photo AI app to AWS using **free tier resources only**.

## 📋 Prerequisites

1. **AWS Account** with free tier available
2. **AWS CLI** installed and configured
3. **Node.js** and **npm** installed
4. **Python 3.9+** installed

### Install AWS CLI (if not installed)
```bash
# macOS
brew install awscli

# Or using pip
pip install awscli
```

### Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Default region: us-east-1
# Default output format: json
```

## 🚀 Deployment Steps

### Step 1: Deploy Backend (Elastic Beanstalk)

```bash
./deploy-backend.sh
```

This will:
- Create an Elastic Beanstalk application
- Deploy on **t3.micro** instance (free tier)
- Set up all required dependencies
- Download the AI model automatically

**Expected time:** 5-10 minutes

### Step 2: Deploy Frontend (S3 + CloudFront)

After backend deployment completes:

1. Get your backend URL from the EB deployment
2. Run the frontend deployment:

```bash
./deploy-frontend.sh
```

3. Enter your backend URL when prompted

This will:
- Build the React app with your backend URL
- Create an S3 bucket for static hosting
- Set up CloudFront CDN distribution
- Upload all files

**Expected time:** 10-15 minutes (CloudFront takes time to propagate)

## 💰 Free Tier Usage

### Elastic Beanstalk (Backend)
- **Instance:** t3.micro (750 hours/month free)
- **Load Balancer:** Application LB (750 hours/month free)
- **Storage:** 5 GB (free)

### S3 + CloudFront (Frontend)
- **S3 Storage:** 5 GB (free)
- **S3 Requests:** 20,000 GET, 2,000 PUT (free)
- **CloudFront:** 1 TB data transfer (free)

**Total monthly cost:** $0 (within free tier limits)

## 🔧 Environment Variables

The backend needs these environment variables (automatically set):
- `FLASK_ENV=production`
- `U2NET_HOME=/var/app/current/models`
- `ANTHROPIC_API_KEY` (add this manually in EB console)

### Adding API Keys

1. Go to AWS Elastic Beanstalk console
2. Select your application → Environment
3. Go to Configuration → Software
4. Add environment variables:
   - `ANTHROPIC_API_KEY`: Your Claude API key

## 📊 Monitoring & Management

### Backend (Elastic Beanstalk)
```bash
cd backend
eb status          # Check deployment status
eb health          # Check application health
eb logs            # View application logs
eb open            # Open app in browser
```

### Frontend (S3)
- Monitor via AWS S3 Console
- CloudFront metrics in AWS Console
- Access logs available in S3

## 🔄 Updates & Redeployment

### Update Backend
```bash
cd backend
eb deploy
```

### Update Frontend
```bash
cd frontend
npm run build
aws s3 sync build/ s3://your-bucket-name --delete
```

## 🛡️ Security Considerations

1. **API Keys:** Store in EB environment variables, not in code
2. **CORS:** Backend is configured for your frontend domain
3. **HTTPS:** CloudFront provides free SSL certificates
4. **S3:** Bucket policy allows public read access (required for website)

## 🚨 Troubleshooting

### Backend Issues
- Check EB logs: `eb logs`
- Verify environment variables in EB console
- Ensure all dependencies in requirements.txt

### Frontend Issues
- Check S3 bucket policy allows public access
- Verify REACT_APP_API_URL points to correct backend
- CloudFront may take 15 minutes to propagate changes

### Common Errors
1. **502 Bad Gateway:** Backend not responding (check EB health)
2. **CORS Error:** Backend URL incorrect in frontend
3. **404 on refresh:** CloudFront custom error pages not set

## 📞 Support

If you encounter issues:
1. Check AWS CloudWatch logs
2. Verify free tier limits not exceeded
3. Ensure all prerequisites are installed
4. Check AWS service status page

## 🎯 Next Steps

After successful deployment:
1. Test all functionality (upload, processing, download)
2. Monitor usage in AWS billing dashboard
3. Set up CloudWatch alarms for usage monitoring
4. Consider setting up a custom domain (Route 53)

---

**Estimated Total Deployment Time:** 15-25 minutes
**Monthly Cost:** $0 (within AWS free tier)