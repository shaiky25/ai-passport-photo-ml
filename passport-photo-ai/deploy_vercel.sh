#!/bin/bash

echo "🚀 Deploying Passport Photo AI to Vercel"
echo "========================================"
echo "✅ Free hosting with custom domain support"
echo "✅ Automatic HTTPS and CDN"
echo "✅ No AWS Amplify issues"
echo ""

# Navigate to frontend
cd frontend

echo "📦 Installing Vercel CLI..."
npm install -g vercel

echo ""
echo "🔧 Setting up environment variables..."

# Create vercel environment file
cat > .env.production << EOF
REACT_APP_API_URL=http://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api
EOF

echo "✅ Environment variables configured"

echo ""
echo "🌐 Deploying to Vercel..."
echo "📋 You'll be prompted to:"
echo "1. Set up and deploy? → Y"
echo "2. Which scope? → Your account"
echo "3. Link to existing project? → N"
echo "4. Project name? → passport-photo-ai"
echo "5. Directory? → ./ (current directory)"
echo "6. Override settings? → N"

echo ""
echo "🚀 Starting deployment..."
vercel --prod

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 What you get:"
echo "✅ Live URL (e.g., https://passport-photo-ai.vercel.app)"
echo "✅ Automatic HTTPS"
echo "✅ Global CDN"
echo "✅ Custom domain support"
echo "✅ $0 cost"

echo ""
echo "🌐 To add custom domain later:"
echo "1. Go to: https://vercel.com/dashboard"
echo "2. Select your project: passport-photo-ai"
echo "3. Go to Settings → Domains"
echo "4. Add: photo.faizuddinshaik.com"
echo "5. Follow DNS instructions"

echo ""
echo "🧪 Test your app:"
echo "python ../tests/test_deployed_app.py"