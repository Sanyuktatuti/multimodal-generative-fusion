# 🚀 Cloud Deployment Guide

This guide walks through deploying the Multimodal Fusion system to **Railway (API)**, **Vercel (Viewer)**, and **Upstash (Redis)**.

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Vercel    │────│   Railway   │────│   Upstash   │
│  (Viewer)   │    │    (API)    │    │   (Redis)   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │                   │                   │
   Next.js              FastAPI            Redis Cloud
   Three.js             + SageMaker        (job status)
```

## 📋 Prerequisites

- GitHub account (free)
- Railway account (free tier)
- Vercel account (free tier)
- Upstash account (free tier)
- AWS account (SageMaker usage)

## 🚂 Step 1: Deploy API to Railway

### 1.1 Connect GitHub Repository

1. Go to [Railway.app](https://railway.app)
2. Sign in with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select `multimodal-generative-fusion`
5. Railway auto-detects the Dockerfile ✅

### 1.2 Configure Environment Variables

Add these in Railway dashboard → Variables:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
SAGEMAKER_ROLE_ARN=arn:aws:iam::your-account:role/SageMakerProcessingRole
ECR_IMAGE_URI=your-account.dkr.ecr.us-east-1.amazonaws.com/multimodal-fusion:sprint3
S3_BUCKET=s3://your-bucket-name

# SageMaker Configuration
SM_INSTANCE_TYPE=ml.m5.xlarge
SM_VOL_GB=50
SM_MAX_SEC=1800

# API Configuration
CORS_ALLOW_ORIGINS=https://your-viewer.vercel.app,http://localhost:3000
OPENAI_API_KEY=your_openai_key

# Redis (will add Upstash URL later)
REDIS_URL=redis://default:password@host:port
```

### 1.3 Deploy

Railway automatically deploys on git push. Get your Railway URL: `https://your-app.railway.app`

## ▲ Step 2: Deploy Viewer to Vercel

### 2.1 Install Vercel CLI (optional)

```bash
npm i -g vercel
```

### 2.2 Deploy from Dashboard

1. Go to [Vercel.com](https://vercel.com)
2. **"Add New Project"** → Import from GitHub
3. Select `multimodal-generative-fusion`
4. **Root Directory**: `apps/viewer`
5. **Framework**: Next.js ✅

### 2.3 Environment Variables

Add in Vercel dashboard → Settings → Environment Variables:

```bash
API_BASE=https://your-app.railway.app
```

### 2.4 Deploy

Vercel auto-deploys on push. Get your URL: `https://your-viewer.vercel.app`

## 🔴 Step 3: Setup Upstash Redis

### 3.1 Create Database

1. Go to [Upstash Console](https://console.upstash.com)
2. **"Create Database"**
3. **Name**: `multimodal-fusion`
4. **Region**: Same as Railway (for latency)
5. **Type**: Pay as You Go (free tier)

### 3.2 Get Connection URL

Copy the **Redis URL** from Upstash dashboard.

### 3.3 Update Railway

Add to Railway environment variables:

```bash
REDIS_URL=redis://default:your_password@your_host.upstash.io:your_port
```

## 🧪 Step 4: Test End-to-End

### 4.1 Test API Health

```bash
curl https://your-app.railway.app/
# Should return: {"message": "Multimodal Fusion API", "version": "0.1.0"}
```

### 4.2 Submit Job

```bash
curl -X POST https://your-app.railway.app/v1/generations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "cyberpunk alley, neon signs, misty night"}'
# Returns: {"task_id": "envgen-...", "job_id": "envgen-...", "status": "submitted"}
```

### 4.3 Check Status

```bash
curl https://your-app.railway.app/v1/generations/{job_id}/status
# Returns: {"state": "PENDING|SUCCESS|FAILURE", "job_id": "...", "sagemaker_status": "..."}
```

### 4.4 View Result

1. Go to `https://your-viewer.vercel.app/viewer?job_id={job_id}`
2. Should load the 3D scene with overlay ✅

## 🛠️ Troubleshooting

### Railway Issues

- **503 Service Unavailable**: Check Railway logs, ensure PORT variable works
- **Environment Variables**: Make sure all AWS keys are set correctly
- **Build Failures**: Check Dockerfile.railway for dependency issues

### Vercel Issues

- **404 on /api routes**: Ensure `next.config.js` rewrites are correct
- **CORS Errors**: Add Vercel URL to Railway's `CORS_ALLOW_ORIGINS`
- **Build Failures**: Check `package.json` dependencies

### SageMaker Issues

- **ResourceLimitExceeded**: Request quota increases for ml.m5.xlarge
- **Access Denied**: Verify IAM role and ECR permissions
- **Image Not Found**: Ensure ECR image URI is correct

## 💰 Cost Monitoring

### Free Tier Limits

- **Railway**: 500 hours/month, $5 credit
- **Vercel**: 100GB bandwidth, unlimited deploys
- **Upstash**: 10K commands/day
- **SageMaker**: Pay-per-use (expect ~$0.20/job on ml.m5.xlarge)

### Set Budgets

1. **AWS Budgets**: Set $10/month limit with alerts
2. **Railway**: Monitor usage in dashboard
3. **SageMaker**: Set CloudWatch billing alarms

## 🔄 CI/CD Pipeline

The system auto-deploys on git push:

1. **Push to main** → Railway redeploys API
2. **Push to main** → Vercel redeploys viewer
3. **ECR image updates** → Update Railway `ECR_IMAGE_URI` env var

## 🎯 Next Steps

- [ ] Set up monitoring (Railway logs, Vercel analytics)
- [ ] Add authentication (Clerk/Auth0)
- [ ] Implement caching strategies
- [ ] Set up alerting for failures
- [ ] Scale SageMaker quotas for production

---

**🚀 You now have a fully cloud-deployed multimodal AI system!**
