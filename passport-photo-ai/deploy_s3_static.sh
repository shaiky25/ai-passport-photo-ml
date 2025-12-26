#!/bin/bash

echo "🪣 Deploying Frontend to AWS S3 Static Website"
echo "=============================================="
echo "✅ HTTP frontend → HTTP backend (no mixed content)"
echo "✅ ~$0.50/month cost"
echo "✅ Full AWS ecosystem"
echo "✅ Custom domain support"
echo ""

# Configuration
BUCKET_NAME="passport-photo-ui-faiz"
REGION="us-east-1"
BACKEND_URL="http://passport-photo-fixed.eba-mvpmm2ar.us-east-1.elasticbeanstalk.com"

echo "📦 Step 1: Creating S3 bucket..."
aws s3 mb s3://$BUCKET_NAME --region $REGION

echo ""
echo "🌐 Step 2: Configuring bucket for static website hosting..."
aws s3 website s3://$BUCKET_NAME --index-document index.html --error-document index.html

echo ""
echo "🔓 Step 3: Setting bucket policy for public access..."
cat > bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json

echo ""
echo "🔧 Step 4: Updating frontend configuration..."
# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Frontend directory not found. Please ensure you have the frontend code."
    exit 1
fi

cd frontend

# Update the API URL in the frontend to use HTTP backend
echo "Updating API URL to: $BACKEND_URL/api"

# Create or update .env file for React
cat > .env << EOF
REACT_APP_API_URL=$BACKEND_URL/api
GENERATE_SOURCEMAP=false
EOF

echo ""
echo "🏗️ Step 5: Building React app..."
npm install
npm run build

echo ""
echo "📤 Step 6: Uploading to S3..."
aws s3 sync build/ s3://$BUCKET_NAME --acl public-read --delete

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 Your app is now available at:"
echo "🌐 Frontend URL: http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
echo "🔗 Backend URL: $BACKEND_URL/api"
echo ""
echo "✅ Benefits:"
echo "- HTTP frontend → HTTP backend (no mixed content issues)"
echo "- ~$0.50/month cost"
echo "- Full AWS ecosystem"
echo "- Easy to update with: aws s3 sync build/ s3://$BUCKET_NAME --acl public-read"
echo ""
echo "💰 Cost breakdown:"
echo "- S3 storage: ~$0.023/GB (~$0.50/month for typical usage)"
echo "- S3 requests: ~$0.0004/1000 requests"
echo "- Data transfer: First 1GB free, then $0.09/GB"
echo ""
echo "🔧 To update your app in the future:"
echo "1. Make changes to your React code"
echo "2. Run: npm run build"
echo "3. Run: aws s3 sync build/ s3://$BUCKET_NAME --acl public-read"

# Clean up
rm -f bucket-policy.json

cd ..