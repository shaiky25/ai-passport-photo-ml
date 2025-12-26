#!/bin/bash

echo "📧 Setting up AWS SES with Environment Variables"
echo "=============================================="

# Check if SENDER_EMAIL is already configured in EB environment
cd backend
echo "🔍 Checking for existing SENDER_EMAIL configuration..."

# Get current environment variables from EB
EXISTING_EMAIL=$(eb printenv 2>/dev/null | grep "SENDER_EMAIL" | cut -d'=' -f2 | tr -d ' ' || echo "")

if [ ! -z "$EXISTING_EMAIL" ]; then
    echo "✅ Found existing SENDER_EMAIL: $EXISTING_EMAIL"
    read -p "Use existing email ($EXISTING_EMAIL)? [Y/n]: " USE_EXISTING
    
    if [[ "$USE_EXISTING" =~ ^[Nn]$ ]]; then
        read -p "Enter new email address for sending OTPs: " EMAIL
    else
        EMAIL="$EXISTING_EMAIL"
        echo "📧 Using existing email: $EMAIL"
    fi
else
    echo "📝 No SENDER_EMAIL found in environment variables"
    read -p "Enter your email address for sending OTPs: " EMAIL
fi

if [ -z "$EMAIL" ]; then
    echo "❌ Email address is required"
    exit 1
fi

cd ..

echo "📝 Verifying email address with AWS SES..."

# Verify the email address
aws ses verify-email-identity --email-address "$EMAIL" --region us-east-1

if [ $? -eq 0 ]; then
    echo "✅ Email verification request sent!"
    echo ""
    echo "📬 IMPORTANT STEPS:"
    echo "1. Check your email inbox for a verification email from AWS"
    echo "2. Click the verification link to activate email sending"
    echo "3. Set environment variable in Elastic Beanstalk:"
    echo ""
    echo "   🔧 Via AWS Console:"
    echo "   • Go to Elastic Beanstalk → passport-photo-ai-backend → passport-photo-backend"
    echo "   • Configuration → Software → Environment Variables"
    echo "   • Add: SENDER_EMAIL = $EMAIL"
    echo ""
    echo "   🔧 Via Command Line (after verification):"
    echo "   cd backend && eb setenv SENDER_EMAIL=$EMAIL"
    echo ""
    echo "4. Deploy the email-enabled backend:"
    echo "   ./deploy-email-simple.sh"
    echo ""
    echo "💡 Check verification status:"
    echo "   aws ses get-identity-verification-attributes --identities $EMAIL --region us-east-1"
else
    echo "❌ Failed to verify email address"
    exit 1
fi