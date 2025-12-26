#!/bin/bash

echo "🚀 Deploying Passport Photo AI Frontend to AWS S3 + CloudFront (Free Tier)"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   brew install awscli  # macOS"
    echo "   pip install awscli   # Python"
    exit 1
fi

# Get backend URL from user
read -p "Enter your backend URL (from EB deployment): " BACKEND_URL

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Backend URL is required"
    exit 1
fi

# Generate unique bucket name
BUCKET_NAME="passport-photo-ai-$(date +%s)"
REGION="us-east-1"

echo "📦 Building frontend with backend URL: $BACKEND_URL"

cd frontend

# Set environment variable for build
export REACT_APP_API_URL="$BACKEND_URL/api"

# Install dependencies and build
npm install
npm run build

echo "☁️  Creating S3 bucket: $BUCKET_NAME"

# Create S3 bucket
aws s3 mb s3://$BUCKET_NAME --region $REGION

# Configure bucket for static website hosting
aws s3 website s3://$BUCKET_NAME \
    --index-document index.html \
    --error-document index.html

# Set bucket policy for public read access
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

aws s3api put-bucket-policy \
    --bucket $BUCKET_NAME \
    --policy file://bucket-policy.json

# Upload build files
echo "📤 Uploading files to S3..."
aws s3 sync build/ s3://$BUCKET_NAME --delete

# Create CloudFront distribution
echo "🌐 Creating CloudFront distribution..."
cat > cloudfront-config.json << EOF
{
    "CallerReference": "passport-photo-ai-$(date +%s)",
    "Comment": "Passport Photo AI Frontend",
    "DefaultCacheBehavior": {
        "TargetOriginId": "$BUCKET_NAME",
        "ViewerProtocolPolicy": "redirect-to-https",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        },
        "MinTTL": 0,
        "Compress": true
    },
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "$BUCKET_NAME",
                "DomainName": "$BUCKET_NAME.s3-website-$REGION.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only"
                }
            }
        ]
    },
    "Enabled": true,
    "DefaultRootObject": "index.html",
    "CustomErrorResponses": {
        "Quantity": 1,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "PriceClass": "PriceClass_100"
}
EOF

DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json \
    --query 'Distribution.Id' \
    --output text)

echo "✅ Frontend deployment complete!"
echo ""
echo "📊 Deployment Summary:"
echo "   S3 Bucket: $BUCKET_NAME"
echo "   Website URL: http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"
echo "   CloudFront Distribution ID: $DISTRIBUTION_ID"
echo ""
echo "⏳ CloudFront distribution is being created (takes 10-15 minutes)"
echo "🌐 Your app will be available at the CloudFront URL once ready"

# Clean up temporary files
rm bucket-policy.json cloudfront-config.json

cd ..