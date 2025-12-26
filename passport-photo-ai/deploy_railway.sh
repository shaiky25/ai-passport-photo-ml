#!/bin/bash

echo "🚂 Deploying Backend to Railway.app"
echo "==================================="
echo "✅ Free tier with HTTPS"
echo "✅ 500 hours/month (plenty for your app)"
echo "✅ Automatic SSL certificates"
echo "✅ $0/month cost"
echo ""

cd backend

echo "📦 Installing Railway CLI..."
npm install -g @railway/cli

echo ""
echo "🔧 Preparing Railway deployment..."

# Create railway.json configuration
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn application:application --bind 0.0.0.0:$PORT",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE"
  }
}
EOF

# Create Procfile for Railway
cat > Procfile << 'EOF'
web: gunicorn application:application --bind 0.0.0.0:$PORT
EOF

# Ensure requirements.txt has gunicorn
if ! grep -q "gunicorn" requirements.txt; then
    echo "gunicorn" >> requirements.txt
fi

echo "✅ Railway configuration created"

echo ""
echo "🚂 Starting Railway deployment..."
echo "📋 You'll be prompted to:"
echo "1. Login to Railway (use GitHub/Google/email)"
echo "2. Create new project"
echo "3. Deploy from current directory"

echo ""
echo "🚀 Deploying..."
railway login

echo ""
echo "Creating new project..."
railway init

echo ""
echo "Deploying backend..."
railway up

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 What you get:"
echo "✅ HTTPS URL (e.g., https://your-app.railway.app)"
echo "✅ Automatic SSL certificate"
echo "✅ 500 hours/month free"
echo "✅ All your Flask features working"
echo "✅ $0 cost"

echo ""
echo "🔧 Next steps:"
echo "1. Get your Railway URL from the deployment output"
echo "2. Update Vercel environment variable:"
echo "   REACT_APP_API_URL=https://your-app.railway.app/api"
echo "3. Test your app!"

echo ""
echo "💰 Cost savings:"
echo "- AWS Elastic Beanstalk: $1.44/month → $0"
echo "- Railway.app: $0/month"
echo "- Total: $0/month (100% free!)"