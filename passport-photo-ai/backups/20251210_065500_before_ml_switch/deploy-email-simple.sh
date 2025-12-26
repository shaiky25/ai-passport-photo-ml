#!/bin/bash

echo "📧 Deploying Backend with Email Support (Environment Variable)"
echo "==========================================================="

cd backend

# Check if SENDER_EMAIL is set in EB environment
echo "🔍 Checking if SENDER_EMAIL is configured..."

# Get current environment variables
ENV_VARS=$(eb printenv 2>/dev/null | grep SENDER_EMAIL || echo "")

if [ -z "$ENV_VARS" ]; then
    echo "⚠️  SENDER_EMAIL not found in environment variables"
    echo ""
    echo "📝 Please set SENDER_EMAIL environment variable:"
    echo ""
    echo "Option 1 - AWS Console:"
    echo "• Go to Elastic Beanstalk → passport-photo-ai-backend → passport-photo-backend"
    echo "• Configuration → Software → Environment Variables"
    echo "• Add: SENDER_EMAIL = your-verified-email@example.com"
    echo ""
    echo "Option 2 - Command Line:"
    read -p "Enter your verified email address: " EMAIL
    if [ ! -z "$EMAIL" ]; then
        echo "Setting SENDER_EMAIL environment variable..."
        eb setenv SENDER_EMAIL="$EMAIL"
        if [ $? -ne 0 ]; then
            echo "❌ Failed to set environment variable. Try using AWS Console instead."
            exit 1
        fi
    else
        echo "❌ Email required. Please set manually via AWS Console."
        exit 1
    fi
else
    echo "✅ SENDER_EMAIL is configured"
fi

# Backup current application and use email version
echo "📦 Updating application with email support..."
cp application.py application-simple-backup.py
cp application-with-email.py application.py

# Deploy to Elastic Beanstalk
echo "🚀 Deploying to Elastic Beanstalk..."
eb deploy

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo ""
    echo "📧 Email Features Enabled:"
    echo "• Real OTP emails sent to users"
    echo "• Professional HTML email templates"
    echo "• No more checking backend logs"
    echo "• Uses AWS SES (62,000 free emails/month)"
    echo ""
    echo "🌐 Test your app:"
    echo "eb open"
    echo ""
    echo "📊 Monitor:"
    echo "eb logs"
else
    echo "❌ Deployment failed"
    # Restore backup
    cp application-simple-backup.py application.py
    exit 1
fi

cd ..