#!/bin/bash

echo "🌐 Setting up Custom Domain for Passport Photo AI"
echo "================================================"
echo "Domain: faizuddinshaik.com"
echo ""

# First, let's deploy the frontend to Amplify
echo "🚀 Step 1: Deploying Frontend to Amplify..."
./deploy_amplify_frontend.sh

echo ""
echo "🌐 Step 2: Custom Domain Setup Instructions"
echo "==========================================="

echo ""
echo "📋 RECOMMENDED SUBDOMAIN OPTIONS:"
echo "1. passport.faizuddinshaik.com ✨ (Recommended)"
echo "2. photo.faizuddinshaik.com"
echo "3. ai.faizuddinshaik.com"
echo "4. app.faizuddinshaik.com"

echo ""
read -p "Which subdomain would you like to use? (e.g., passport): " SUBDOMAIN

if [ -z "$SUBDOMAIN" ]; then
    SUBDOMAIN="passport"
fi

FULL_DOMAIN="${SUBDOMAIN}.faizuddinshaik.com"

echo ""
echo "✅ Selected domain: $FULL_DOMAIN"

echo ""
echo "🔧 AMPLIFY DOMAIN SETUP STEPS:"
echo "1. Go to: https://console.aws.amazon.com/amplify/"
echo "2. Select your app: passport-photo-frontend"
echo "3. Click 'Domain management' in left sidebar"
echo "4. Click 'Add domain'"
echo "5. Enter: $FULL_DOMAIN"
echo "6. Click 'Configure domain'"

echo ""
echo "📝 DNS RECORDS TO ADD:"
echo "After adding domain in Amplify, you'll get DNS records like:"
echo ""
echo "Type: CNAME"
echo "Name: $SUBDOMAIN"
echo "Value: [Amplify will provide this - something like d1234567890.cloudfront.net]"
echo ""
echo "⚠️  Add this CNAME record to your domain registrar's DNS settings"

echo ""
echo "🔍 WHERE TO ADD DNS RECORDS:"
echo "- If domain is with GoDaddy: Go to DNS Management"
echo "- If domain is with Namecheap: Go to Advanced DNS"
echo "- If domain is with Cloudflare: Go to DNS settings"
echo "- If domain is with Route 53: Already in AWS!"

echo ""
echo "⏱️  TIMING:"
echo "- DNS propagation: 5-48 hours (usually within 1 hour)"
echo "- SSL certificate: Automatic (5-10 minutes after DNS)"
echo "- Your app will be live at: https://$FULL_DOMAIN"

echo ""
echo "🎉 FINAL RESULT:"
echo "Your Passport Photo AI will be available at:"
echo "🌐 https://$FULL_DOMAIN"
echo "🔒 Automatic HTTPS (SSL certificate included)"
echo "⚡ CDN-powered (fast worldwide)"
echo "💰 FREE (included in Amplify free tier)"

echo ""
echo "📞 NEED HELP?"
echo "1. Check DNS propagation: https://dnschecker.org/"
echo "2. Verify SSL: https://www.ssllabs.com/ssltest/"
echo "3. AWS Amplify docs: https://docs.aws.amazon.com/amplify/"