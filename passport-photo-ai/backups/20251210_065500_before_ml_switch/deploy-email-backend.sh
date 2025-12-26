#!/bin/bash

echo "📧 Deploying Backend with Email Support"
echo "======================================"

# Check if email is verified
if [ ! -f .verified-email ]; then
    echo "❌ No verified email found. Please run ./setup-email.sh first"
    exit 1
fi

VERIFIED_EMAIL=$(cat .verified-email)

echo "📝 Using verified email: $VERIFIED_EMAIL"

# Check email verification status
echo "🔍 Checking email verification status..."
VERIFICATION_STATUS=$(aws ses get-identity-verification-attributes --identities "$VERIFIED_EMAIL" --region us-east-1 --query "VerificationAttributes.\"$VERIFIED_EMAIL\".VerificationStatus" --output text)

if [ "$VERIFICATION_STATUS" != "Success" ]; then
    echo "❌ Email not verified yet. Status: $VERIFICATION_STATUS"
    echo "📬 Please check your email and click the verification link from AWS."
    echo "💡 You can check status with:"
    echo "   aws ses get-identity-verification-attributes --identities $VERIFIED_EMAIL --region us-east-1"
    exit 1
fi

echo "✅ Email verified successfully!"

cd backend

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
    echo "🔧 Setting environment variables..."
    
    # Set the sender email environment variable
    eb setenv SENDER_EMAIL="$VERIFIED_EMAIL"
    
    echo "✅ Email setup complete!"
    echo ""
    echo "📊 Your app now supports real email sending:"
    echo "   • OTPs will be sent to users' email addresses"
    echo "   • No more checking backend logs for OTPs"
    echo "   • Professional email templates included"
    echo ""
    echo "🌐 Test your app: eb open"
else
    echo "❌ Deployment failed"
    # Restore backup
    cp application-simple-backup.py application.py
    exit 1
fi

cd ..