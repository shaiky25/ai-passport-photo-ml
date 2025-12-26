# 🔧 Fix Amplify Role Issue

## ❌ Error: "The role with name AWSAmplifyDomainRole-Z04724162EEITEIJZS1BG cannot be found."

This is a common AWS Amplify issue with IAM roles for custom domains.

## 🛠️ Solutions (Try in Order)

### Solution 1: Create Missing IAM Role (Recommended)

1. **Go to AWS IAM Console:**
   - https://console.aws.amazon.com/iam/

2. **Create Role:**
   - Click "Roles" → "Create role"
   - Select "AWS service" → "Amplify"
   - Click "Next"

3. **Attach Policies:**
   - Search and attach: `AWSAmplifyDomainRole`
   - If not found, attach: `AmazonRoute53FullAccess`
   - Click "Next"

4. **Name the Role:**
   - Role name: `AWSAmplifyDomainRole-Z04724162EEITEIJZS1BG`
   - Click "Create role"

### Solution 2: Use Different Approach (Easier)

Deploy without custom domain first, then add domain later:

1. **Deploy to Amplify without domain:**
   - Upload your `passport-photo-frontend.zip`
   - Skip domain setup for now
   - Get the default Amplify URL

2. **Test the app first:**
   - Verify everything works on default URL
   - Add API URL environment variable

3. **Add domain later:**
   - After app is working, try domain setup again
   - AWS sometimes creates roles automatically after first deployment

### Solution 3: Alternative Free Hosting

If Amplify continues to have issues, use these free alternatives:

#### Option A: Vercel (Recommended)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

#### Option B: Netlify
```bash
# Install Netlify CLI  
npm install -g netlify-cli

# Deploy
cd frontend
netlify deploy --prod --dir=build
```

#### Option C: GitHub Pages
1. Push code to GitHub
2. Enable GitHub Pages
3. Deploy from build folder

## 🎯 Quick Fix Script

Let me create a script to try the easiest solution first: