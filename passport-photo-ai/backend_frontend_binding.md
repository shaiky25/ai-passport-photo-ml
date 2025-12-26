# 🔗 Backend-Frontend Binding Configuration

## 🎯 Environment Variables for Elastic Beanstalk

### Option 1: Frontend URL (Recommended)
**Environment Variable Name**: `FRONTEND_URL`
**Value**: `https://passport-photo-ui.vercel.app`

### Option 2: Allowed Origins (CORS)
**Environment Variable Name**: `ALLOWED_ORIGINS`
**Value**: `https://passport-photo-ui.vercel.app,https://photo.faizuddinshaik.com`

### Option 3: Custom Domain
**Environment Variable Name**: `CUSTOM_DOMAIN`
**Value**: `https://photo.faizuddinshaik.com`

## 🔧 How to Set in Elastic Beanstalk

### Method 1: AWS Console
1. Go to: https://console.aws.amazon.com/elasticbeanstalk/
2. Select your environment: **passport-photo-free**
3. Go to **Configuration** → **Software**
4. Click **Edit**
5. In **Environment properties**, add:
   - **Name**: `FRONTEND_URL`
   - **Value**: `https://passport-photo-ui.vercel.app`
6. Click **Apply**

### Method 2: EB CLI
```bash
cd backend
eb setenv FRONTEND_URL=https://passport-photo-ui.vercel.app
```

### Method 3: Multiple URLs (for custom domain later)
```bash
eb setenv ALLOWED_ORIGINS="https://passport-photo-ui.vercel.app,https://photo.faizuddinshaik.com"
```

## 🔄 Update Backend Code (Optional)

If you want to use this in your Flask app, update `backend/application.py`:

```python
import os

# Get frontend URL from environment
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')

# Update CORS configuration
CORS(application, origins=ALLOWED_ORIGINS, methods=['GET', 'POST', 'OPTIONS'], allow_headers=['Content-Type'])
```

## 🎯 Current Status
Your app is already working with the current CORS setup (`origins=['*']`), so this is **optional** for security hardening.

## 💡 Recommended Setup
```bash
cd backend
eb setenv FRONTEND_URL=https://passport-photo-ui.vercel.app
eb setenv ALLOWED_ORIGINS="https://passport-photo-ui.vercel.app,https://photo.faizuddinshaik.com"
```

This prepares your backend for both the current Vercel URL and your future custom domain!