#!/bin/bash

echo "💰 Budget-Friendly Frontend Deployment (AWS Amplify Free Tier)"
echo "=============================================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Navigate to frontend directory
cd frontend

echo "📦 Installing dependencies..."
npm install

echo "🔨 Building frontend..."
npm run build

echo "📋 Frontend build completed!"
echo "📁 Build artifacts are in: frontend/build/"

# Create a zip file for manual upload
echo "📦 Creating deployment zip..."
zip -r passport-photo-frontend.zip build/

echo "✅ Created passport-photo-frontend.zip for manual upload to Amplify"
echo "📁 Location: frontend/passport-photo-frontend.zip"

echo ""
echo "💰 AMPLIFY FREE TIER LIMITS:"
echo "- ✅ 1000 build minutes/month (plenty for our app)"
echo "- ✅ 15GB storage (our app is ~1MB)"
echo "- ✅ 100GB data transfer/month"
echo "- ✅ Custom domain included"
echo "- ✅ HTTPS certificate included"
echo ""
echo "📊 Expected cost: $0/month (within free tier)"

echo ""
echo "🌐 AMPLIFY DEPLOYMENT STEPS:"
echo "1. Go to: https://console.aws.amazon.com/amplify/"
echo "2. Click 'New app' > 'Host web app'"
echo "3. Choose 'Deploy without Git provider'"
echo "4. Upload: passport-photo-frontend.zip"
echo "5. Set environment variable:"
echo "   REACT_APP_API_URL = http://your-backend-url/api"
echo "6. Deploy!"

echo ""
echo "🔍 After deployment, verify:"
echo "- Frontend loads without errors"
echo "- API calls work (check browser console)"
echo "- Image upload and processing works"
echo "- Watermark is 3x larger and clean white"