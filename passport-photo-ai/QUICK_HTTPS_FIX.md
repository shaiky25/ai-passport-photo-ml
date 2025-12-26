# 🔒 Quick HTTPS Mixed Content Fix

## ❌ **Problem**: 
Your frontend (HTTPS) can't call your backend (HTTP) - browser blocks mixed content.

## ✅ **Quick Solution Options**:

### Option 1: Enable HTTPS on Elastic Beanstalk (Recommended)

#### Step 1: Configure Load Balancer for HTTPS
```bash
cd backend
eb config
```

In the editor, find and update:
```yaml
aws:ec2:vpc:
  ELBScheme: internet-facing
aws:elasticbeanstalk:environment:
  LoadBalancerType: application
aws:elbv2:listener:443:
  Protocol: HTTPS
  SSLCertificateArns: arn:aws:acm:us-east-1:677276111739:certificate/[CERT-ID]
```

#### Step 2: Request SSL Certificate
1. Go to: https://console.aws.amazon.com/acm/
2. Click "Request a certificate"
3. Domain: `passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com`
4. Validation: DNS
5. Add DNS record to validate
6. Wait for "Issued" status

#### Step 3: Update Environment Variable
In Vercel dashboard:
- Change `REACT_APP_API_URL` to: `https://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api`

### Option 2: Use CloudFront (Alternative)
Create CloudFront distribution for your backend to get HTTPS.

### Option 3: Temporary Workaround (Not Recommended)
Some browsers allow mixed content in development mode, but this won't work for production users.

## 🚀 **Simplest Approach**:

1. **Request SSL Certificate** in AWS Certificate Manager
2. **Enable HTTPS** on your Elastic Beanstalk load balancer  
3. **Update Vercel env var** to use `https://` instead of `http://`

## 💰 **Cost Impact**:
- SSL Certificate: **FREE** (AWS ACM)
- Application Load Balancer: **~$16/month** (⚠️ This exceeds your budget!)

## 🎯 **Budget-Friendly Alternative**:
Since ALB costs $16/month, consider:
1. **Move backend to Vercel** (free, supports HTTPS)
2. **Use Railway.app** (free tier with HTTPS)
3. **Use Render.com** (free tier with HTTPS)

Would you like me to help you migrate the backend to a free HTTPS platform instead?