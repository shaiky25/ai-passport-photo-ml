#!/bin/bash

echo "🚀 Simple Amplify Deployment (No Custom Domain)"
echo "==============================================="

# Navigate to frontend
cd frontend

echo "📦 Frontend is already built!"
echo "📁 Using existing: passport-photo-frontend.zip"

echo ""
echo "🌐 AMPLIFY DEPLOYMENT STEPS:"
echo "1. Go to: https://console.aws.amazon.com/amplify/"
echo "2. Click 'New app' > 'Host web app'"
echo "3. Choose 'Deploy without Git provider'"
echo "4. Upload: passport-photo-frontend.zip"
echo "5. App name: passport-photo-ai"
echo "6. Environment name: production"
echo "7. Click 'Save and deploy'"

echo ""
echo "⚙️  ENVIRONMENT VARIABLES TO SET:"
echo "After deployment, go to 'Environment variables' and add:"
echo ""
echo "Key: REACT_APP_API_URL"
echo "Value: http://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api"
echo ""

echo "🎯 RESULT:"
echo "You'll get a URL like: https://main.d1234567890.amplifyapp.com"
echo "This will be your working app URL!"

echo ""
echo "🌐 CUSTOM DOMAIN (OPTIONAL):"
echo "After the app is working, you can add photo.faizuddinshaik.com"
echo "The IAM role issue should now be fixed!"

echo ""
echo "💰 COST: $0 (Free tier)"
echo "📊 Features: HTTPS, CDN, Auto-scaling"