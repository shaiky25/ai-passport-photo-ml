#!/bin/bash

echo "🚀 Deploying Passport Photo AI Backend (No S3 Required)"
echo "=================================================="

# Navigate to backend directory
cd backend

# Initialize Elastic Beanstalk application (if not already done)
echo "📋 Initializing Elastic Beanstalk application..."
eb init --platform python-3.12 --region us-east-1 passport-photo-ai-backend

# Create environment
echo "🏗️  Creating Elastic Beanstalk environment..."
eb create passport-photo-app --single-instance

echo "✅ Deployment completed!"
echo "📊 Check status: eb status"
echo "🌐 Open app: eb open"
echo "📋 View logs: eb logs"