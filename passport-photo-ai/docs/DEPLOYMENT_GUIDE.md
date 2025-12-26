# 🚀 Complete Deployment Guide - Passport Photo AI

## ✅ Prerequisites Completed
- [x] All local tests passed (5/5)
- [x] Backend functionality verified
- [x] Frontend build ready
- [x] No S3 dependencies

## 🎯 Deployment Strategy

### Backend: AWS Elastic Beanstalk
### Frontend: AWS Amplify

---

## 📋 Step 1: Deploy Backend (Elastic Beanstalk)

### Option A: Using our script
```bash
./deploy_without_s3.sh
```

### Option B: Manual deployment
```bash
cd backend
eb init --platform python-3.12 --region us-east-1 passport-photo-ai-backend
eb create passport-photo-app --single-instance
```

### Verify Backend Deployment
```bash
eb status
eb open  # Opens the backend URL
```

**Expected Backend URL format:** `http://passport-photo-app.eba-xxxxx.us-east-1.elasticbeanstalk.com`

---

## 🌐 Step 2: Deploy Frontend (AWS Amplify)

### Option A: Using our script
```bash
./deploy_amplify_frontend.sh
```

This will:
- Build the frontend
- Create `passport-photo-frontend.zip`
- Provide deployment instructions

### Option B: Manual Amplify Deployment

1. **Build the frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Go to AWS Amplify Console:**
   - Visit: https://console.aws.amazon.com/amplify/
   - Click "New app" > "Host web app"
   - Choose "Deploy without Git provider"

3. **Upload build folder:**
   - Zip the `frontend/build` folder
   - Upload to Amplify

4. **Set Environment Variables:**
   - In Amplify console, go to "Environment variables"
   - Add: `REACT_APP_API_URL` = `http://your-backend-url.elasticbeanstalk.com/api`

5. **Deploy:**
   - Click "Save and deploy"

---

## 🔧 Step 3: Configure API Connection

### Update Frontend Environment Variable

Once your backend is deployed, update the frontend's API URL:

1. **Get Backend URL:**
   ```bash
   cd backend
   eb status
   ```
   Copy the CNAME URL (e.g., `passport-photo-app.eba-xxxxx.us-east-1.elasticbeanstalk.com`)

2. **Set in Amplify:**
   - Go to Amplify Console
   - Select your app
   - Go to "Environment variables"
   - Set: `REACT_APP_API_URL` = `http://your-backend-url/api`
   - Redeploy the app

---

## 🧪 Step 4: Test Deployed Application

### Backend Health Check
```bash
curl http://your-backend-url/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Passport Photo AI (Fixed) is running",
  "python_version": "3.12",
  "heic_support": true,
  "opencv_available": true
}
```

### Frontend Test
1. Visit your Amplify URL
2. Upload a test image
3. Verify:
   - ✅ Face detection works
   - ✅ Watermark is 3x larger and clean white
   - ✅ Background removal works
   - ✅ Email verification works

---

## 📊 Deployment Architecture

```
┌─────────────────┐    HTTP/HTTPS    ┌──────────────────┐
│   AWS Amplify   │ ──────────────► │ Elastic Beanstalk│
│   (Frontend)    │                 │    (Backend)     │
│                 │                 │                  │
│ - React App     │                 │ - Flask API      │
│ - Static Files  │                 │ - Face Detection │
│ - Auto HTTPS    │                 │ - Image Process  │
│ - CDN           │                 │ - Email (SES)    │
└─────────────────┘                 └──────────────────┘
```

---

## 💰 Cost Estimation (AWS Free Tier)

### Elastic Beanstalk (Backend)
- **Free Tier:** 750 hours/month of t3.micro
- **Cost:** $0 for first 12 months

### Amplify (Frontend)
- **Free Tier:** 1000 build minutes/month, 15GB storage
- **Cost:** $0 for typical usage

### SES (Email)
- **Free Tier:** 200 emails/day
- **Cost:** $0 for typical usage

**Total Monthly Cost:** ~$0 (within free tier limits)

---

## 🔍 Monitoring & Logs

### Backend Logs
```bash
cd backend
eb logs
```

### Frontend Logs
- Available in Amplify Console
- Real-time monitoring dashboard

### Health Monitoring
- Backend: `/api/health` endpoint
- Frontend: Amplify provides uptime monitoring

---

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors:**
   - Backend already configured for `*` origins
   - Should work out of the box

2. **API Connection Failed:**
   - Check `REACT_APP_API_URL` environment variable
   - Ensure backend URL is correct (with `/api` suffix)

3. **Backend Not Starting:**
   - Check `eb logs` for Python errors
   - Verify all dependencies in requirements.txt

4. **Frontend Build Fails:**
   - Run `npm install` in frontend directory
   - Check for any missing dependencies

---

## ✅ Success Checklist

- [ ] Backend deployed to Elastic Beanstalk
- [ ] Backend health check returns 200
- [ ] Frontend deployed to Amplify  
- [ ] Frontend loads without errors
- [ ] API connection working (no CORS errors)
- [ ] Image upload and processing works
- [ ] Watermark is 3x larger and clean white
- [ ] Background removal works
- [ ] Email verification works

---

## 🎉 Final URLs

After successful deployment, you'll have:

- **Frontend:** `https://your-app-id.amplifyapp.com`
- **Backend:** `http://your-app.elasticbeanstalk.com`

Both services are now running without any S3 dependencies from your side!

---

## 📞 Support

If you encounter any issues:
1. Check the logs (`eb logs` for backend)
2. Verify environment variables in Amplify
3. Test backend endpoints directly with curl
4. Check browser console for frontend errors