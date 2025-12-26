# 💰 Budget Summary - Passport Photo AI

## 🎯 Target: Under $10/month

## ✅ Recommended Deployment (FREE)

### AWS Free Tier Deployment
```
Backend:  Elastic Beanstalk (t3.micro, single instance)
Frontend: AWS Amplify (static hosting)
Email:    SES (under 200 emails/day)
Total:    $0/month (within free tier limits)
```

### Free Tier Limits:
- **EC2**: 750 hours/month of t3.micro (enough for 24/7 operation)
- **Amplify**: 1000 build minutes + 15GB storage + 100GB transfer
- **SES**: 200 emails/day when sending from EC2
- **Data Transfer**: 100GB/month outbound

## 📊 Cost Monitoring Tools

### Scripts Created:
1. `check_aws_costs.py` - Monitor current spending
2. `deploy_budget_friendly.sh` - Deploy with cost controls
3. Billing alerts at $5 and $8

### Usage:
```bash
# Check current costs
python check_aws_costs.py

# Deploy with budget controls
./deploy_budget_friendly.sh
```

## 🚨 Cost Control Measures

### Automatic Safeguards:
- ✅ Single t3.micro instance only
- ✅ No auto-scaling (prevents extra instances)
- ✅ No load balancer (single instance mode)
- ✅ Basic monitoring only
- ✅ us-east-1 region (cheapest)

### Manual Monitoring:
- ✅ Weekly billing dashboard checks
- ✅ Billing alerts at $5 and $8
- ✅ Free tier usage monitoring

## 🔄 Alternative Free Options

If you want to avoid AWS costs entirely:

### Option 1: Railway + Vercel
```
Backend:  Railway.app (free tier: 500 hours/month)
Frontend: Vercel (free tier: unlimited static hosting)
Email:    EmailJS (free tier: 200 emails/month)
Total:    $0/month
```

### Option 2: Render + Netlify
```
Backend:  Render.com (free tier: 750 hours/month)
Frontend: Netlify (free tier: 100GB bandwidth)
Email:    EmailJS or Formspree
Total:    $0/month
```

## 📈 Expected Usage vs Limits

### Conservative Estimates:
- **Compute**: 1 instance × 24/7 = 744 hours/month (under 750 limit)
- **Storage**: ~50MB for app (under 15GB limit)
- **Transfer**: ~10GB/month typical usage (under 100GB limit)
- **Emails**: ~50/month typical (under 200/day limit)

### Result: $0/month (well within all free tier limits)

## 🎯 Deployment Decision

**Recommended**: AWS Free Tier deployment
- Stays within your $10 budget (actually $0)
- Professional AWS infrastructure
- Easy to scale later if needed
- All monitoring tools included

**Commands to deploy:**
```bash
# 1. Deploy backend (free tier optimized)
./deploy_budget_friendly.sh

# 2. Deploy frontend (free tier)
./deploy_amplify_frontend.sh

# 3. Monitor costs
python check_aws_costs.py
```

## 🔒 Budget Safety Net

Even if something goes wrong:
- Billing alerts at $5 and $8
- Single instance limit prevents runaway costs
- Easy to shut down if needed
- Maximum possible cost: ~$15/month (if everything goes wrong)

**You're safe with this deployment strategy!** 🛡️