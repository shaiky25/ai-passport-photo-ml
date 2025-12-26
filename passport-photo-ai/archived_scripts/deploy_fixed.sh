#!/bin/bash
set -e

echo "🚀 Starting comprehensive deployment..."

# 1. Clean up any existing deployment
echo "🧹 Cleaning up..."
cd backend
eb terminate --force || true

# 2. Create new environment with correct platform
echo "🏗️  Creating new environment..."
eb create passport-photo-backend-v2 \
    --platform "Python 3.12 running on 64bit Amazon Linux 2023" \
    --instance-type t3.medium \
    --timeout 20

# 3. Deploy application
echo "📦 Deploying application..."
eb deploy --timeout 20

# 4. Test deployment
echo "🧪 Testing deployment..."
python ../test_python312_deployment.py

echo "✅ Deployment complete!"
