#!/bin/bash

echo "📧 Setting up AWS SES for Email Verification"
echo "============================================"

# Get email from user
read -p "Enter your email address (this will be used to send OTPs): " EMAIL

if [ -z "$EMAIL" ]; then
    exit 1
fi

echo "📝 Verifying email address with AWS SES..."

# Verify the email address
aws ses verify-email-identity --email-address "$EMAIL" --region us-east-1

if [ $? -eq 0 ]; then
    echo "✅ Email verification request sent!"
    echo ""
    echo "📬 IMPORTANT: Check your email inbox for a verification email from AWS."
    echo "   Click the verification link to activate email sending."
    echo ""
    echo "⏳ After verifying your email, run: ./deploy-email-backend.sh"
    echo ""
    echo "💡 Note: You can check verification status with:"
    echo "   aws ses get-identity-verification-attributes --identities $EMAIL --region us-east-1"
else
    echo "❌ Failed to verify email address"
    exit 1
fi

# Save email for later use
echo "$EMAIL" > .verified-email