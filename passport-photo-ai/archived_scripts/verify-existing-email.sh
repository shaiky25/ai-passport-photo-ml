#!/bin/bash

echo "📧 Verifying Existing Email Configuration"
echo "========================================"

cd backend

# Get current environment variables from EB
echo "🔍 Checking current environment variables..."
EXISTING_EMAIL=$(eb printenv 2>/dev/null | grep "SENDER_EMAIL" | cut -d'=' -f2 | tr -d ' ' || echo "")

if [ -z "$EXISTING_EMAIL" ]; then
    echo "❌ No SENDER_EMAIL found in environment variables"
    echo ""
    echo "📝 Please set SENDER_EMAIL first:"
    echo "Option 1 - AWS Console:"
    echo "• Go to Elastic Beanstalk → passport-photo-ai-backend → passport-photo-backend"
    echo "• Configuration → Software → Environment Variables"
    echo "• Add: SENDER_EMAIL = your-email@example.com"
    echo ""
    echo "Option 2 - Command Line:"
    echo "eb setenv SENDER_EMAIL=your-email@example.com"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Found SENDER_EMAIL: $EXISTING_EMAIL"

# Check if email is verified with AWS SES
echo "🔍 Checking AWS SES verification status..."
VERIFICATION_STATUS=$(aws ses get-identity-verification-attributes --identities "$EXISTING_EMAIL" --region us-east-1 --query "VerificationAttributes.\"$EXISTING_EMAIL\".VerificationStatus" --output text 2>/dev/null || echo "NotFound")

if [ "$VERIFICATION_STATUS" = "Success" ]; then
    echo "✅ Email is verified with AWS SES!"
    echo ""
    echo "🚀 Ready to deploy email-enabled backend:"
    echo "./deploy-email-simple.sh"
elif [ "$VERIFICATION_STATUS" = "Pending" ]; then
    echo "⏳ Email verification is pending"
    echo "📬 Please check your email inbox and click the verification link from AWS"
    echo ""
    echo "💡 After verification, run: ./deploy-email-simple.sh"
elif [ "$VERIFICATION_STATUS" = "NotFound" ]; then
    echo "❌ Email not found in AWS SES"
    echo "📝 Verifying email with AWS SES..."
    
    # Verify the email address
    aws ses verify-email-identity --email-address "$EXISTING_EMAIL" --region us-east-1
    
    if [ $? -eq 0 ]; then
        echo "✅ Verification email sent to: $EXISTING_EMAIL"
        echo "📬 Please check your email and click the verification link"
        echo ""
        echo "💡 After verification, run: ./deploy-email-simple.sh"
    else
        echo "❌ Failed to send verification email"
        exit 1
    fi
else
    echo "❌ Email verification failed. Status: $VERIFICATION_STATUS"
    echo "📝 Re-sending verification email..."
    
    aws ses verify-email-identity --email-address "$EXISTING_EMAIL" --region us-east-1
    
    if [ $? -eq 0 ]; then
        echo "✅ Verification email sent to: $EXISTING_EMAIL"
        echo "📬 Please check your email and click the verification link"
    else
        echo "❌ Failed to send verification email"
        exit 1
    fi
fi

cd ..