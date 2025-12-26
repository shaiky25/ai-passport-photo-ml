# 🎯 ESSENTIAL DEPLOYMENT GUIDE - VERCEL VERSION

## 💰 COST BREAKDOWN (Current Status)

### ✅ Current Monthly Costs: $1.44 / $10.00 Budget
- **EC2 (Backend)**: $0.00 (Free Tier - t3.micro)
- **Route 53**: $0.50 (DNS queries)
- **VPC**: $0.93 (Network usage)
- **Vercel (Frontend)**: $0.00 (Free - unlimited)
- **Remaining Budget**: $8.56

### 📊 Free Tier Usage:
- **EC2 Hours**: 576/750 used (174 hours remaining)
- **Vercel**: Unlimited free hosting
- **Custom Domain**: Free on Vercel

## 🚀 COMPLETE DEPLOYMENT COMMANDS

### Step 1: Check Backend Status
```bash
# Verify backend is working
curl http://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api/health

# Check current AWS costs
python scripts/check_aws_costs.py
```

### Step 2: Deploy Frontend to Vercel
```bash
# Navigate to frontend
cd frontend

# Login to Vercel (one-time setup)
vercel login
# Visit the URL shown and login with GitHub/Google/email

# Deploy to production
vercel --prod
```

**Answer the prompts:**
- Set up and deploy? → **Y**
- Which scope? → **Your account**
- Link to existing project? → **N**
- Project name? → **passport-photo-ai**
- Directory? → **./** (press ENTER)
- Override settings? → **N**

### Step 3: Set Environment Variable
1. Go to: https://vercel.com/dashboard
2. Select: **passport-photo-ai**
3. Go to **Settings** → **Environment Variables**
4. Add:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `http://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api`
   - **Environment**: Production
5. **Save** and **Redeploy**

### Step 4: Test Deployed Application
```bash
# Test your deployed app (enter Vercel URL when prompted)
python tests/test_deployed_app.py
```

### Step 5: Add Custom Domain (Optional)
```bash
# In Vercel dashboard:
# Settings → Domains → Add: photo.faizuddinshaik.com
# Add CNAME record: photo → cname.vercel-dns.com
```

## 📋 Expected Results

### ✅ After Successful Deployment:
- **Frontend URL**: `https://passport-photo-ai-[random].vercel.app`
- **Backend URL**: `http://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api`
- **Total Cost**: $1.44/month (no change - Vercel is free)
- **Custom Domain**: `https://photo.faizuddinshaik.com` (free)

### 🧪 Test Checklist:
- [ ] Frontend loads without errors
- [ ] Can upload an image
- [ ] Image processing completes
- [ ] Watermark appears (3x larger, clean white)
- [ ] Background removal works
- [ ] No CORS errors in browser console

## 🚨 Troubleshooting Commands

### If Frontend Has Issues:
```bash
# Check environment variables in Vercel dashboard
# Settings → Environment Variables

# Test backend directly
curl http://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api/health

# Redeploy in Vercel dashboard
# Deployments → Redeploy latest
```

### If Costs Spike:
```bash
# Check AWS costs (Vercel is always free)
python scripts/check_aws_costs.py
```

## 🎯 SUCCESS CRITERIA
- ✅ App loads at Vercel URL
- ✅ Image processing works end-to-end
- ✅ Costs remain at $1.44/month
- ✅ Custom domain working (optional)

## ✅ Why Vercel is Better:
- **No domain verification issues** (unlike Amplify)
- **Easier custom domain setup**
- **Better performance and CDN**
- **Completely free forever**
- **No AWS complexity**

## 📁 File Locations
- **Frontend Code**: `frontend/` (deploy from here)
- **Test Script**: `tests/test_deployed_app.py`
- **Cost Monitor**: `scripts/check_aws_costs.py`
- **Backend Code**: `backend/application.py`

Follow the Vercel steps above - much simpler than Amplify! 🎉