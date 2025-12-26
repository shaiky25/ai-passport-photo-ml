# 🚀 Vercel Deployment Guide

## ✅ Why Vercel is Better Than Amplify:
- No domain verification issues
- Easier custom domain setup
- Better performance
- Completely free
- No AWS complexity

## 📋 Step-by-Step Deployment

### Step 1: Login to Vercel
```bash
cd frontend
vercel login
```
- Visit the URL shown (https://vercel.com/oauth/device?user_code=XXXX)
- Login with GitHub, Google, or email
- Press ENTER in terminal

### Step 2: Deploy Your App
```bash
vercel --prod
```
Answer the prompts:
- Set up and deploy? → **Y**
- Which scope? → **Your account**
- Link to existing project? → **N**
- Project name? → **passport-photo-ai**
- Directory? → **./** (just press ENTER)
- Override settings? → **N**

### Step 3: Set Environment Variable
After deployment:
1. Go to: https://vercel.com/dashboard
2. Select your project: **passport-photo-ai**
3. Go to **Settings** → **Environment Variables**
4. Add:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `http://passport-photo-free.eba-teefmmhg.us-east-1.elasticbeanstalk.com/api`
   - **Environment**: Production
5. Click **Save**
6. Go to **Deployments** → **Redeploy** latest deployment

## 🎯 Expected Result
- **Your URL**: `https://passport-photo-ai-[random].vercel.app`
- **Features**: All working (watermark, background removal, face detection)
- **Cost**: $0 (completely free)
- **Performance**: Faster than Amplify

## 🌐 Add Custom Domain (Optional)
1. In Vercel dashboard → **Settings** → **Domains**
2. Add: `photo.faizuddinshaik.com`
3. Add DNS record to your domain registrar:
   - Type: **CNAME**
   - Name: **photo**
   - Value: **cname.vercel-dns.com**

## 🧪 Test Your App
```bash
python tests/test_deployed_app.py
```

## 💰 Cost Comparison
- **Vercel**: $0/month (unlimited)
- **Current AWS**: $1.44/month
- **Total**: $1.44/month (same as before)

Much simpler than Amplify! 🎉