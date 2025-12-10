#!/bin/bash

echo "🚀 Deploying Passport Photo AI Backend to AWS Elastic Beanstalk (Free Tier)"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   brew install awscli  # macOS"
    echo "   pip install awscli   # Python"
    exit 1
fi

# Check if EB CLI is installed
if ! command -v eb &> /dev/null; then
    echo "❌ EB CLI not found. Installing..."
    pip install awsebcli
fi

cd backend

# Initialize EB application (only run once)
if [ ! -f .elasticbeanstalk/config.yml ]; then
    echo "📝 Initializing Elastic Beanstalk application..."
    eb init passport-photo-ai-backend \
        --platform python-3.9 \
        --region us-east-1
fi

# Create environment (only run once)
echo "🏗️  Creating Elastic Beanstalk environment..."
eb create passport-photo-ai-env \
    --instance-type t3.micro \
    --platform-version "3.4.24" \
    --envvars FLASK_ENV=production \
    --single-instance

echo "✅ Backend deployment initiated!"
echo "📊 Monitor deployment: eb status"
echo "🌐 Open app: eb open"
echo "📋 View logs: eb logs"

cd ..