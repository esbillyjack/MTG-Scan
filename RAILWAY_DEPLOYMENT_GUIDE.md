# Railway Deployment Guide
**Magic Card Scanner - Phase 1 Cloud Deployment**

## 🚀 **Prerequisites**

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **OpenAI API Key**: Required for card identification functionality

## 📋 **Step-by-Step Deployment**

### **1. Create Railway Project**

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your Magic Card Scanner repository
5. Railway will automatically detect it's a Python project

### **2. Add PostgreSQL Database**

1. In your Railway project dashboard, click "New Service"
2. Select "Database" → "PostgreSQL" 
3. Railway will automatically provision a PostgreSQL database
4. The `DATABASE_URL` environment variable will be automatically set

### **3. Configure Environment Variables**

In your Railway project settings, add these environment variables:

**Required Variables:**
```
ENV_MODE=production
PORT=8000
OPENAI_API_KEY=your-actual-openai-api-key-here
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
```

**Optional Variables:**
```
DEBUG=false
```

### **4. Deploy Application**

1. Railway will automatically trigger a deployment when you push to your GitHub repository
2. Monitor the deployment logs in the Railway dashboard
3. Once deployed, you'll get a public URL (e.g., `https://your-app.railway.app`)

### **5. Data Migration (If Needed)**

If you have existing data in SQLite, run the migration script:

```bash
# Set your Railway DATABASE_URL as environment variable
export DATABASE_URL="postgresql://user:password@host:port/database"

# Run migration script
python migrate_to_postgresql.py
```

### **6. Verify Deployment**

1. Visit your Railway URL
2. Check that the app loads correctly
3. Test card scanning functionality
4. Verify data persistence

## 🔧 **Configuration Details**

### **Environment Variables Explained**

- **ENV_MODE**: Set to `production` for Railway deployment
- **PORT**: Railway will set this automatically, but default is `8000`
- **OPENAI_API_KEY**: Your OpenAI API key for card identification
- **JWT_SECRET_KEY**: Secret key for JWT tokens (Phase 2)
- **DATABASE_URL**: Automatically set by Railway PostgreSQL service

### **Database Configuration**

- Railway automatically provides PostgreSQL database
- `DATABASE_URL` is set automatically by Railway
- Your app will automatically use PostgreSQL when `DATABASE_URL` is present
- Tables are created automatically on first run

### **File Storage**

- Phase 1: Uses Railway's ephemeral file system
- Files are stored in `/uploads` directory
- **Note**: Files may be lost on deployments/restarts
- Phase 2+: Will implement persistent file storage

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **App won't start**: Check logs for missing environment variables
2. **Database connection error**: Verify PostgreSQL service is running
3. **OpenAI API errors**: Check API key is valid and has credits
4. **File upload issues**: Ensure uploads directory permissions

### **Debugging Steps**

1. **Check Railway logs**: View real-time logs in Railway dashboard
2. **Test API endpoints**: Use `/api/environment` to verify configuration
3. **Database connectivity**: Check if tables are created properly
4. **Environment variables**: Verify all required variables are set

## 📊 **Expected Results**

After successful deployment:

✅ **App accessible** via Railway URL  
✅ **Database working** with PostgreSQL  
✅ **Card scanning** functional with OpenAI API  
✅ **File uploads** working (ephemeral)  
✅ **All features** from local version working  

## 🔄 **Continuous Deployment**

Railway automatically deploys when you push to your GitHub repository:

1. Push code changes to GitHub
2. Railway detects changes and triggers build
3. App is automatically deployed with zero downtime
4. Monitor deployment in Railway dashboard

## 💰 **Cost Considerations**

- **Free Tier**: Railway provides free tier for small projects
- **PostgreSQL**: Included in Railway pricing
- **Usage-based**: Pay only for what you use
- **Scaling**: Automatically scales based on demand

## 🔐 **Security Notes**

- Never commit real API keys to GitHub
- Use Railway's environment variables for secrets
- JWT_SECRET_KEY should be long and random
- Database credentials are managed by Railway

## 🎯 **Next Steps (Phase 2)**

After successful Phase 1 deployment:

1. **Authentication**: Add user registration/login
2. **Multi-user**: Implement per-user data isolation
3. **Persistent Storage**: Move files to cloud storage
4. **Custom Domain**: Set up custom domain
5. **Monitoring**: Add logging and monitoring

---

**Need Help?** 
- Railway docs: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Check THE_PLAN.md for overall strategy 