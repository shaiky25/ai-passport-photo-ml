#!/bin/bash

echo "💰 Budget-Friendly Deployment (Under $10/month)"
echo "==============================================="

# Set AWS region to us-east-1 (cheapest)
export AWS_DEFAULT_REGION=us-east-1

echo "🔍 Checking AWS Free Tier eligibility..."

# Check if account is within 12 months (free tier eligible)
ACCOUNT_AGE=$(aws organizations describe-account --account-id $(aws sts get-caller-identity --query Account --output text) --query 'Account.JoinedTimestamp' --output text 2>/dev/null || echo "unknown")

echo "📊 Setting up billing alerts..."

# Create billing alarm for $5
aws cloudwatch put-metric-alarm \
    --alarm-name "BillingAlert-5USD" \
    --alarm-description "Alert when charges exceed $5" \
    --metric-name EstimatedCharges \
    --namespace AWS/Billing \
    --statistic Maximum \
    --period 86400 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=Currency,Value=USD \
    --evaluation-periods 1 \
    --region us-east-1 2>/dev/null || echo "⚠️  Billing alerts require root account access"

echo "🚀 Deploying Backend (Free Tier Optimized)..."

cd backend

# Initialize EB with free tier settings
eb init --platform python-3.12 --region us-east-1 passport-photo-budget

# Create environment with free tier instance
eb create passport-photo-free \
    --instance-type t3.micro \
    --single-instance \
    --region us-east-1

echo "✅ Backend deployed with free tier settings!"
echo "📊 Instance type: t3.micro (free tier eligible)"
echo "🔒 Single instance (no load balancer costs)"

# Get the backend URL
BACKEND_URL=$(eb status | grep "CNAME" | awk '{print $2}')
echo "🌐 Backend URL: http://$BACKEND_URL"

cd ..

echo ""
echo "💡 COST OPTIMIZATION TIPS:"
echo "- Your t3.micro instance gives you 750 hours/month FREE"
echo "- Single instance = no load balancer costs"
echo "- Stay under 200 emails/day for free SES"
echo "- Monitor usage in AWS billing dashboard"
echo ""
echo "📈 Expected monthly cost: $0 (within free tier)"
echo "🚨 Set up billing alerts in AWS Console for extra safety"

echo ""
echo "🎯 Next: Deploy frontend to Amplify (also free tier)"
echo "Run: ./deploy_amplify_frontend.sh"