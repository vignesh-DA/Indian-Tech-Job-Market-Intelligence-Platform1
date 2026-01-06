# 🚀 TechScope India - AI-Powered Career Assistant

**Discover smarter job matches and career insights tailored just for you**

An intelligent job recommendation platform for India's tech job market. Uses AI/ML to match your skills with the best job opportunities and provides real-time market insights.

**Live Stats:**
- 📊 **12,550+ jobs** from top Indian companies
- 🎯 **150+ job roles** categorized intelligently  
- 🗺️ **100+ locations** across India
- ⚡ **Parallel scraping** - Fetches jobs in ~3 minutes
- 🤖 **ML-powered matching** - 70% accuracy on skill recommendations

---

## ✨ Key Features

### 🎯 **Smart Job Recommendations**
- Enter your skills, experience, and location
- Get 10 personalized job matches instantly
- See skill gaps and learning recommendations
- Match score with confidence percentage
- Save favorite jobs for later

### 📊 **Market Intelligence Dashboard**
- Real-time salary trends by role & location
- Top 15 in-demand skills
- Hiring trends over 30 days
- Experience distribution analysis
- Location-based filtering
- Experience level breakdown

### 💾 **Job Management**
- Bookmark and organize saved jobs
- Track application status
- Filter by role, location, experience
- Search across all saved jobs
- Export data

### 🔐 **Secure Authentication**
- Google OAuth 2.0 login
- Persistent 2-day sessions
- Secure user profiles
- No password management

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.8+ 
- pip (Python package manager)
- Git
- Internet connection
- Google account (for OAuth login)

### **Step 1: Clone the Repository**
```bash
git clone "https://github.com/vignesh-DA/Indian-Tech-Job-Market-Intelligence-Platform"
cd gravito
```

### **Step 2: Create Virtual Environment (Recommended)**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Required packages:**
- Flask 1.1+ - Web framework
- pandas - Data processing
- numpy - Numerical computing
- scikit-learn - ML & TF-IDF
- requests - API calls
- python-dotenv - Environment variables

---

## 🔑 Get API Keys & Credentials

### **A. Adzuna API (Job Data Source)**

1. **Sign up** at [Adzuna Developer](https://developer.adzuna.com/)
2. **Create an account** (free)
3. **Get credentials:**
   - Go to "My Applications"
   - Create New Application → Get **App ID** and **App Key**
4. **Example format (use your own keys):**
   ```
   App ID: your_adzuna_app_id_here
   App Key: your_adzuna_app_key_here
   ```

### **B. Google OAuth 2.0 (User Login)**

1. **Go to** [Google Cloud Console](https://console.cloud.google.com/)
2. **Create new project:**
   - Click "Select a Project"
   - Click "New Project"
   - Name: "TechScope India"
   - Click "Create"

3. **Enable OAuth:**
   - Search for "OAuth consent screen"
   - Select "External"
   - Fill in:
     - App name: "TechScope India"
     - User support email: your-email@gmail.com
     - Developer contact: your-email@gmail.com
   - Click "Save and Continue"
   - Click "Save and Continue" again (skip scopes)
   - Click "Save and Continue" (skip test users)
   - Click "Back to Dashboard"

4. **Create OAuth Client:**
   - Click "Credentials" in left menu
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Web application"
   - Name: "TechScope India Web"
   - **Authorized JavaScript origins:** Add `http://localhost:5000`
   - **Authorized redirect URIs:** Add `http://localhost:5000/api/auth/callback`
   - Click "Create"
   - Copy **Client ID** and **Client Secret**

5. **Example format (use your own keys):**
   ```
   Client ID: your_google_client_id_here
   Client Secret: your_google_client_secret_here
   ```

### **C. Optional: Gemini API (AI Chatbot)**

1. Go to [Google AI Studio](https://ai.google.dev/)
2. Click "Get API Key"
3. Create new API key
4. Copy the key

---

## 🔧 Configure Environment Variables

**Create `.env` file** in project root:

```bash
# Adzuna API (Job Data)
ADZUNA_APP_ID=your_adzuna_app_id_here
ADZUNA_APP_KEY=your_adzuna_app_key_here

# Google OAuth 2.0 (User Login)
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5000/api/auth/callback

# Flask Configuration
FLASK_SECRET_KEY=change-this-to-random-secret-key-in-production

# Optional: Google Gemini API (Chatbot)
GEMINI_API_KEY=your_gemini_api_key_here
```

**⚠️ Important Security Notes:**
- Never commit `.env` to git
- Use strong, random `FLASK_SECRET_KEY` in production
- Change all credentials in production deployment
- Never share API keys publicly

---

## ▶️ Run the Application

### **Start the Server**
```bash
python server.py
```

**Expected output:**
```
Running on http://127.0.0.1:5000
Running on http://10.239.158.146:5000
Press CTRL+C to quit
```

### **Access the Application**
Open browser and go to: **http://localhost:5000**

---

## 📊 Fetch Job Data

### **First Time Setup**
When you start, you'll see ~12,550 pre-loaded jobs. To refresh:

1. **Click** "Fetch Job Data" button on home page
2. **Wait** for 2-3 minutes (parallel scraping in progress)
3. **Status message** shows when complete
4. **ML model retrains** automatically
5. **Recommendations updated** with latest jobs

**What happens during fetch:**
- ⚡ **Parallel scraping** with 3 workers
- Fetches from: 15 roles × 10 locations
- ~300 API requests total
- Saves to `data/jobs_YYYY_MM_DD.csv`
- Trains new ML model (~20MB)
- Ready for new recommendations

---

## 📁 Project Structure

```
gravito/
├── server.py                    # Flask backend server
├── requirements.txt             # Python dependencies
├── .env                         # API keys (not in git)
├── README.md                    # This file
│
├── src/                         # Core Python modules
│   ├── scrapers.py             # Adzuna API parallel scraping
│   ├── analytics.py            # Market statistics & analysis
│   ├── recommendation_engine.py # ML job matching (TF-IDF + Cosine)
│   ├── chatbot_engine.py       # AI chatbot responses
│   ├── oauth_handler.py        # Google OAuth authentication
│   ├── user_db.py              # SQLite user management
│   ├── data_loader.py          # CSV data processing
│   ├── logger.py               # Logging setup
│   ├── exception.py            # Custom exceptions
│   └── utils.py                # Helper functions
│
├── frontend/                    # Web UI (HTML/CSS/JS)
│   ├── index.html              # Home page
│   ├── login.html              # OAuth login
│   ├── recommendations.html    # Job recommendations
│   ├── market-dashboard.html   # Market insights
│   ├── saved-jobs.html         # Saved jobs
│   └── assets/
│       ├── css/                # Styles
│       │   ├── variables.css
│       │   ├── styles.css
│       │   ├── components.css
│       │   └── responsive.css
│       └── js/                 # Frontend logic
│           ├── api.js          # API calls
│           ├── config.js       # Configuration
│           ├── main.js         # Home page logic
│           ├── recommendations.js
│           ├── dashboard.js    # Analytics logic
│           ├── profile.js      # Saved jobs logic
│           ├── chatbot.js      # Chat UI
│           └── utils.js        # Helpers
│
├── data/                        # Job data CSVs
│   └── jobs_2026_01_06.csv     # Latest job data
│
├── models/                      # Trained ML models
│   └── recommendation_model.pkl # ML model (20MB+)
│
├── logs/                        # Application logs
│   └── *.log                   # Daily log files
│
└── .gitignore                   # Git ignore rules
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML5, CSS3, Vanilla JS | User interface |
| **Backend** | Flask 1.1+ (Python) | REST API server |
| **Database** | SQLite | User sessions & data |
| **ML/AI** | scikit-learn, TF-IDF | Job matching algorithm |
| **Data** | pandas, numpy | Data processing |
| **Auth** | Google OAuth 2.0 | User authentication |
| **Scraping** | requests, ThreadPoolExecutor | Parallel job fetching |
| **Deployment** | Python, pip | Production ready |

---

## 🤖 How Job Matching Works

### **Step 1: Data Collection**
- Parallel scraper fetches jobs from Adzuna
- Extracts: title, company, skills, salary, location, experience
- Stores in CSV and trains ML model

### **Step 2: Skill Extraction**
- Analyzes job description & title
- Identifies 30+ technology skills
- Categorizes job roles (Software Engineer, Data Scientist, etc.)

### **Step 3: ML Matching Algorithm**
```
TF-IDF Vectorization:
- Your skills → numerical vector
- Job requirements → numerical vector

Cosine Similarity:
- Compares vectors
- Score: 0-100%
- Top 10 matches returned

Score Breakdown:
- 70% - Skill match
- 20% - Experience level match
- 10% - Location preference match
```

### **Step 4: Results**
- Shows match percentage
- Highlights matching skills ✅
- Suggests skills to learn 📚
- Categories: Best/Average/Low Fit

---

## 📊 API Endpoints

### **Authentication**
- `GET /api/auth/login` - Redirect to Google OAuth
- `GET /api/auth/callback` - OAuth callback (auto-handled)
- `GET /api/auth/user` - Get current user info
- `GET /api/auth/logout` - Logout & clear session

### **Job Data**
- `POST /api/fetch-jobs` - Fetch fresh jobs from Adzuna
- `GET /api/jobs` - Get all jobs (paginated)
- `GET /api/roles` - Get all job roles

### **Recommendations**
- `POST /api/recommendations` - Get personalized job matches
- `POST /api/save-job` - Save/bookmark job
- `GET /api/saved-jobs` - Get user's saved jobs
- `DELETE /api/saved-job/<job_id>` - Remove saved job

### **Analytics**
- `GET /api/stats` - Overall job market stats
- `GET /api/role-distribution` - Jobs by role
- `GET /api/top-skills` - Top 15 skills needed
- `GET /api/salary-trends` - Salary data by role/location
- `GET /api/location-stats` - Jobs by location
- `GET /api/experience-distribution` - Jobs by experience level

---

## ⚙️ Configuration & Customization

### **Change Job Roles/Locations**
Edit `src/scrapers.py`:
```python
roles = [
    'software engineer',
    'data scientist',
    'devops engineer',
    # Add more roles
]

locations = [
    'Bangalore',
    'Mumbai',
    'Delhi',
    # Add more locations
]
```

### **Adjust ML Match Weights**
Edit `src/recommendation_engine.py`:
```python
# Change these weights
SKILL_WEIGHT = 0.7      # Was 70%
EXPERIENCE_WEIGHT = 0.2 # Was 20%
LOCATION_WEIGHT = 0.1   # Was 10%
```

### **Session Timeout**
Edit `server.py`:
```python
PERMANENT_SESSION_LIFETIME = 172800  # 2 days in seconds
```

---

## 🚀 Deployment Guide

### **For Production**

1. **Update `.env`:**
   ```bash
   GOOGLE_OAUTH_REDIRECT_URI=https://yourdomain.com/api/auth/callback
   FLASK_ENV=production
   SESSION_COOKIE_SECURE=True
   ```

2. **Update Google Cloud Console:**
   - Add production domain to:
     - Authorized JavaScript origins
     - Authorized redirect URIs

3. **Use WSGI server** (not Flask dev server):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 server:app
   ```

4. **Setup SSL/HTTPS:**
   - Use Let's Encrypt or AWS Certificate Manager
   - Redirect HTTP → HTTPS

5. **Database backup:**
   ```bash
   cp data/users.db data/users_backup.db
   ```

---

## 🐛 Troubleshooting

### **Problem: "Invalid client" OAuth error**
**Solution:**
- Verify Google OAuth Client ID/Secret in `.env`
- Check authorized redirect URI matches exactly
- Clear browser cookies & try incognito window
- Wait 5 minutes after updating Google Cloud Console

### **Problem: No jobs showing**
**Solution:**
- Click "Fetch Job Data" button
- Check Adzuna API credentials
- Verify `.env` file has correct keys
- Check internet connection

### **Problem: Server won't start**
**Solution:**
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check port 5000 not in use
netstat -ano | findstr :5000  # Windows
lsof -i :5000                  # macOS/Linux
```

### **Problem: ML model takes too long to train**
**Solution:**
- Normal for first run (few minutes)
- Retraining happens on job data refresh
- Model file: `models/recommendation_model.pkl`

### **Problem: Slow recommendations**
**Solution:**
- ML model is building initial vectors
- First recommendation takes 10-15 seconds
- Subsequent ones are instant (cached)

---

## 📞 Support & Documentation

- **GitHub Issues** - Report bugs
- **Adzuna Docs** - [API Documentation](https://developer.adzuna.com/)
- **Google OAuth** - [Setup Guide](https://developers.google.com/identity/protocols/oauth2)
- **Flask Docs** - [Official Docs](https://flask.palletsprojects.com/)

---

## 🎯 Future Enhancements

- 📧 Email job alerts
- 📄 Resume parser (auto-extract skills)
- 💼 Interview preparation resources
- 📈 Career progression recommendations
- 🏢 Company reviews & ratings
- 📱 Mobile app
- 🌐 Multi-language support

---

## 📄 License

MIT License - Free to use and modify

---

## ✨ Credits

Built with:
- **Flask** - Web framework
- **scikit-learn** - Machine Learning
- **Adzuna API** - Job data
- **Google OAuth** - Authentication
- **Font Awesome** - Icons

**Made with ❤️ for India's tech job seekers**

**v1.0 | January 2026 | TechScope India**
