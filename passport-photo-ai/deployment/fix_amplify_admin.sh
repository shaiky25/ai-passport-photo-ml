#!/bin/bash

echo "🔧 Fixing Amplify IAM Role Issue for Admin User"
echo "=============================================="
echo "User: adminfaiz (admin access)"
echo ""

# Check current AWS identity
echo "🔍 Checking current AWS identity..."
aws sts get-caller-identity

echo ""
echo "🛠️  Creating missing Amplify IAM role..."

# Create the trust policy for Amplify
cat > amplify-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "amplify.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
ROLE_NAME="AWSAmplifyDomainRole-Z04724162EEITEIJZS1BG"

echo "📋 Creating IAM role: $ROLE_NAME"

aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document file://amplify-trust-policy.json \
    --description "Amplify domain management role"

if [ $? -eq 0 ]; then
    echo "✅ Role created successfully!"
else
    echo "⚠️  Role might already exist or there's a permission issue"
fi

echo ""
echo "🔗 Attaching required policies..."

# Attach the necessary policies
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AmplifyBackendDeployFullAccess"

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/AmazonRoute53FullAccess"

# Create custom policy for domain management
cat > amplify-domain-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "acm:ListCertificates",
                "acm:RequestCertificate",
                "acm:DescribeCertificate",
                "acm:GetCertificate",
                "route53:ListHostedZones",
                "route53:ChangeResourceRecordSets",
                "route53:GetChange",
                "route53:ListResourceRecordSets"
            ],
            "Resource": "*"
        }
    ]
}
EOF

# Create and attach custom policy
aws iam create-policy \
    --policy-name "AmplifyDomainManagement" \
    --policy-document file://amplify-domain-policy.json \
    --description "Custom policy for Amplify domain management" 2>/dev/null

# Get account ID for policy ARN
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/AmplifyDomainManagement"

echo ""
echo "✅ IAM role setup completed!"
echo ""
echo "🧹 Cleaning up temporary files..."
rm -f amplify-trust-policy.json amplify-domain-policy.json

echo ""
echo "🎯 Next Steps:"
echo "1. Go back to Amplify Console"
echo "2. Try adding your custom domain again"
echo "3. The role should now be available"
echo ""
echo "🌐 If it still fails, try these alternatives:"
echo "- Deploy without custom domain first"
echo "- Use Vercel or Netlify instead (also free)"
echo "- Wait 5-10 minutes for IAM changes to propagate"