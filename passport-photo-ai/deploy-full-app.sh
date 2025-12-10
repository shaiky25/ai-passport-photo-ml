#!/bin/bash

echo "🚀 Deploying Full-Featured Passport Photo AI Application"
echo "====================================================="

# Check if SENDER_EMAIL is configured
cd backend
echo "🔍 Checking SENDER_EMAIL configuration..."

EXISTING_EMAIL=$(eb printenv 2>/dev/null | grep "SENDER_EMAIL" | cut -d'=' -f2 | tr -d ' ' || echo "")

if [ -z "$EXISTING_EMAIL" ]; then
    echo "❌ SENDER_EMAIL not configured"
    echo "📝 Please set SENDER_EMAIL environment variable first:"
    echo "   eb setenv SENDER_EMAIL=your-verified-email@example.com"
    echo "   OR use AWS Console: Configuration → Software → Environment Variables"
    exit 1
fi

echo "✅ SENDER_EMAIL configured: $EXISTING_EMAIL"

# Check if email is verified with AWS SES
echo "🔍 Checking AWS SES verification status..."
VERIFICATION_STATUS=$(aws ses get-identity-verification-attributes --identities "$EXISTING_EMAIL" --region us-east-1 --query "VerificationAttributes.\"$EXISTING_EMAIL\".VerificationStatus" --output text 2>/dev/null || echo "NotFound")

if [ "$VERIFICATION_STATUS" != "Success" ]; then
    echo "❌ Email not verified with AWS SES. Status: $VERIFICATION_STATUS"
    echo "📧 Please verify your email first:"
    echo "   aws ses verify-email-identity --email-address $EXISTING_EMAIL --region us-east-1"
    echo "   Then check your email and click the verification link"
    exit 1
fi

echo "✅ Email verified with AWS SES"

# Backup current application and deploy full version
echo "📦 Deploying full-featured application..."
cp application.py application-simple-backup.py
cp application-full.py application.py

# Deploy to Elastic Beanstalk
echo "🚀 Deploying to Elastic Beanstalk..."
echo "⏳ This may take 5-10 minutes due to additional dependencies..."

eb deploy

if [ $? -eq 0 ]; then
    echo "✅ Full application deployment successful!"
    echo ""
    echo "🎉 Features Now Available:"
    echo "• ✅ Advanced OpenCV face detection (multiple cascades)"
    echo "• ✅ AI-powered compliance analysis (Claude)"
    echo "• ✅ Background removal (rembg)"
    echo "• ✅ HEIC file support"
    echo "• ✅ Professional email OTP system (AWS SES)"
    echo "• ✅ Watermark system with email verification"
    echo "• ✅ Print sheet generation (4x6, 5x7)"
    echo "• ✅ Comprehensive face quality validation"
    echo ""
    echo "🌐 Test your full-featured app:"
    echo "eb open"
    echo ""
    echo "📊 Monitor deployment:"
    echo "eb logs"
    echo "eb health"
else
    echo "❌ Deployment failed"
    echo "📋 Checking logs..."
    eb logs --all
    
    # Restore backup
    echo "🔄 Restoring simple version..."
    cp application-simple-backup.py application.py
    exit 1
fi

cd ..