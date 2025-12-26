# 🌐 Custom Domain Setup - faizuddinshaik.com

## 🎯 Goal: Use faizuddinshaik.com for your Passport Photo AI frontend

## 📋 Prerequisites
- ✅ Domain: faizuddinshaik.com (you own this)
- ✅ AWS Amplify app deployed
- ✅ Access to domain registrar (where you bought the domain)

## 🚀 Setup Options

### Option 1: Subdomain (Recommended)
Use: `passport.faizuddinshaik.com` or `photo.faizuddinshaik.com`

**Pros:**
- Keeps main domain available for other uses
- Easy to set up
- Professional looking
- Can have multiple apps on subdomains

### Option 2: Root Domain
Use: `faizuddinshaik.com` directly

**Pros:**
- Shorter URL
- Main domain usage

**Cons:**
- Uses entire domain for this app

## 🔧 Step-by-Step Setup

### Step 1: Deploy Frontend to Amplify First
```bash
./deploy_amplify_frontend.sh
```

### Step 2: Add Custom Domain in Amplify Console

1. **Go to AWS Amplify Console:**
   - https://console.aws.amazon.com/amplify/

2. **Select your app** (passport-photo-frontend)

3. **Go to "Domain management"** (left sidebar)

4. **Click "Add domain"**

5. **Enter your domain:**
   - For subdomain: `passport.faizuddinshaik.com`
   - For root domain: `faizuddinshaik.com`

6. **AWS will provide DNS records** to add to your domain

### Step 3: Configure DNS Records

You'll need to add these records to your domain registrar:

#### For Subdomain (passport.faizuddinshaik.com):
```
Type: CNAME
Name: passport
Value: [AWS Amplify URL provided]
```

#### For Root Domain (faizuddinshaik.com):
```
Type: A
Name: @
Value: [AWS Amplify IP addresses provided]

Type: AAAA  
Name: @
Value: [AWS Amplify IPv6 addresses provided]
```

### Step 4: SSL Certificate
- AWS Amplify automatically provides FREE SSL certificate
- HTTPS will work automatically
- Certificate auto-renews

## 🎨 Recommended Subdomain Options

1. **passport.faizuddinshaik.com** ✨ (Recommended)
2. **photo.faizuddinshaik.com**
3. **ai.faizuddinshaik.com**
4. **app.faizuddinshaik.com**

## 📱 Complete Setup Script

Let me create a script to help with the domain setup: