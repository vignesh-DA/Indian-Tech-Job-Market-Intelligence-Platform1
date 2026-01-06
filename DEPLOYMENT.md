# Render Deployment Checklist

## ✅ Files Ready for Deployment

### Core Files
- ✅ `server.py` - Flask app configured for production (host 0.0.0.0)
- ✅ `Procfile` - Gunicorn startup command
- ✅ `requirements.txt` - All dependencies with gunicorn
- ✅ `src/oauth_handler.py` - Auto-detects environment

### Frontend
- ✅ `frontend/` - All HTML/CSS/JS files
- ✅ `frontend/assets/` - All static assets

### Data
- ✅ `data/jobs_*.csv` - Job data
- ✅ `data/profile_pics/` - User profile pictures

---

## 🚀 Render Deployment Steps

### 1. Connect GitHub Repository
```
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Select branch (main/master)
```

### 2. Configure Render Service

**Service Settings:**
- **Name:** gravito
- **Environment:** Python 3.10+
- **Region:** Choose closest to your users

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn --workers 2 --threads 2 --worker-class gthread --bind 0.0.0.0:$PORT server:app
```

### 3. Add Environment Variables

In Render Dashboard → Settings → Environment:

```
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_OAUTH_CLIENT_ID=your_google_oauth_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_OAUTH_REDIRECT_URI=https://indian-tech-job-market-intelligence.onrender.com/api/auth/callback
FLASK_SECRET_KEY=generate_a_secure_random_string_here
FLASK_ENV=production
DEBUG=False
RENDER=true
```

⚠️ **Security Notes:**
- Change `FLASK_SECRET_KEY` to a unique secure string
- Never commit `.env` with real secrets
- Use Render's secrets manager for sensitive data

### 4. Verify OAuth Configuration

Google Cloud Console must have:
- **JavaScript Origin:** `https://indian-tech-job-market-intelligence.onrender.com`
- **Redirect URI:** `https://indian-tech-job-market-intelligence.onrender.com/api/auth/callback`

✅ **Already configured!**

### 5. Deploy

1. Click "Deploy" button in Render dashboard
2. Watch deployment logs
3. Once live, visit your app URL
4. Test OAuth login with Google

---

## 📋 Current .env Status

### Enabled Variables
- ✅ `ADZUNA_APP_ID` - Job data API
- ✅ `ADZUNA_APP_KEY` - Job data API
- ✅ `GEMINI_API_KEY` - AI/Chatbot
- ✅ `GOOGLE_OAUTH_CLIENT_ID` - OAuth
- ✅ `GOOGLE_OAUTH_CLIENT_SECRET` - OAuth
- ✅ `GOOGLE_OAUTH_REDIRECT_URI` - OAuth (auto-detected)
- ✅ `FLASK_SECRET_KEY` - Session encryption
- ✅ `FLASK_ENV` - Environment mode
- ✅ `DEBUG` - Debug mode

### Notes
- Local `.env` uses `http://localhost:5000` redirects
- Code auto-detects production environment from Render
- All API keys are configured and active

---

## 🧪 Testing Checklist

After deployment:
- [ ] Homepage loads
- [ ] Google OAuth login works
- [ ] Profile page displays user info
- [ ] Dashboard shows job statistics
- [ ] Recommendations generate correctly
- [ ] Chat with AI works

---

## 📞 Troubleshooting

### OAuth Error: "redirect_uri_mismatch"
- Verify Google Cloud Console has exact redirect URI
- Check Render environment variables are set
- Wait 5-10 minutes for propagation

### App crashes on startup
- Check `Procfile` syntax
- Verify all environment variables in Render
- Review deployment logs in Render dashboard

### 500 Errors
- Check API keys (Gemini, Adzuna)
- Verify database connection
- Review logs: Render → Logs tab

---

Generated: January 6, 2026
Status: Ready for production deployment ✅
