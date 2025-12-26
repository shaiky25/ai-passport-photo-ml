#!/bin/bash

echo "🔒 Fixing HTTPS Mixed Content Error"
echo "=================================="
echo "Issue: Frontend (HTTPS) → Backend (HTTP) blocked by browser"
echo "Solution: Enable HTTPS on Elastic Beanstalk"
echo ""

cd backend

echo "🔧 Step 1: Configure HTTPS on Elastic Beanstalk..."

# Create HTTPS configuration
mkdir -p .ebextensions

cat > .ebextensions/https-redirect.config << 'EOF'
option_settings:
  aws:elbv2:listener:443:
    Protocol: HTTPS
    SSLCertificateArns: arn:aws:acm:us-east-1:677276111739:certificate/YOUR_CERT_ARN
  aws:elbv2:listener:80:
    Protocol: HTTP
  aws:elasticbeanstalk:environment:
    LoadBalancerType: application
Resources:
  AWSEBV2LoadBalancerListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: redirect
          RedirectConfig:
            Protocol: HTTPS
            Port: 443
            StatusCode: HTTP_301
      LoadBalancerArn:
        Ref: AWSEBV2LoadBalancer
      Port: 80
      Protocol: HTTP
EOF

echo "✅ HTTPS configuration created"

echo ""
echo "🔧 Step 2: Request SSL Certificate..."

# Request SSL certificate for the EB domain
DOMAIN="passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com"

echo "Requesting SSL certificate for: $DOMAIN"

aws acm request-certificate \
    --domain-name "$DOMAIN" \
    --validation-method DNS \
    --region us-east-1

echo ""
echo "⚠️  IMPORTANT: You need to:"
echo "1. Go to AWS Certificate Manager console"
echo "2. Find your certificate request"
echo "3. Add the DNS validation record to Route 53"
echo "4. Wait for certificate to be issued"
echo "5. Update the certificate ARN in .ebextensions/https-redirect.config"
echo "6. Deploy with: eb deploy"

echo ""
echo "🚀 Alternative Quick Fix (Temporary):"
echo "Update Vercel environment variable to use HTTPS:"
echo "REACT_APP_API_URL=https://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api"