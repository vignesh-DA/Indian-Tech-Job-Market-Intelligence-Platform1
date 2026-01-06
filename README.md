# 🇮🇳 Tech Job Intelligence Platform

An **AI-powered job recommendation system** that matches you with the best tech jobs in India using machine learning.

## ✨ What It Does

- **🎯 Smart Job Matching** - AI analyzes your skills and finds jobs perfect for you
- **📊 Live Market Insights** - See salary trends, top skills, and hot companies
- **💾 Save & Track** - Bookmark jobs and track your applications
- **🔄 Real-Time Data** - Always updated with the latest job postings

## 🚀 Quick Start

### 1. Install
```bash
git clone https://github.com/vignesh-DA/Indian-Tech-Job-Market-Intelligence-Platform1.git
cd gravito
pip install -r requirements.txt
```

### 2. Setup API Keys
Get free API credentials from [Adzuna](https://developer.adzuna.com/)

Create a `.env` file:
```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

### 3. Run the Server
```bash
python server.py
```

Visit: `http://localhost:5000`

## 📁 Project Structure

```
gravito/
├── server.py                   # Flask API backend
├── frontend/                   # HTML/CSS/JS frontend
│   ├── recommendations.html   # Job recommendations page
│   ├── dashboard.html         # Market insights
│   └── assets/
│       ├── css/               # Styling
│       └── js/                # Frontend logic
├── src/                       # Core modules
│   ├── recommendation_engine.py  # ML matching
│   ├── scrapers.py              # Job fetching
│   └── data_loader.py           # Data management
├── data/                      # CSV job data
└── models/                    # Saved ML models
```

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **AI/ML**: scikit-learn (TF-IDF + Cosine Similarity)
- **Data**: pandas, numpy
- **API**: Adzuna Jobs API

## 🤖 How It Works

1. **Data Collection** - Fetches latest job postings from Adzuna
2. **ML Training** - Analyzes job skills, experience, location
3. **Matching** - Compares your profile with jobs
4. **Scoring** - Rates matches (Skills: 70%, Exp: 20%, Location: 10%)
5. **Results** - Shows best-fit jobs with skill gaps

## 📱 Features

### Job Recommendations Page
- Enter your role, experience, location, and skills
- Get 10 personalized job matches
- See which skills you have ✅ and what to learn 📚
- View match score and fit category
- Save jobs & apply directly

### Market Dashboard
- Salary trends by location & role
- Top in-demand skills
- Active hiring companies
- Job market statistics

### Saved Jobs
- Bookmark your favorite jobs
- Track applications
- Export data to CSV

## 🔄 Data Refresh Workflow

Click **"Refresh Job Data"** to:
1. Delete old job data
2. Fetch fresh postings from Adzuna API
3. Train new ML model
4. Ready for new recommendations

## 📊 Recommendation Algorithm

```
Match Score = (Skills × 0.7) + (Experience × 0.2) + (Location × 0.1)
```

**Fit Categories:**
- 🟢 **Best Fit** (70%+) - Apply now!
- 🟡 **Average Fit** (40-69%) - Could work with some learning
- 🔴 **Low Fit** (<40%) - Not ideal match

## ⚙️ Configuration

### Environment Variables
```
ADZUNA_APP_ID        # Your Adzuna app ID
ADZUNA_APP_KEY       # Your Adzuna app key
FLASK_ENV           # development/production
DEBUG               # True/False
```

### Ports
- Frontend: `http://localhost:5000`
- API: `http://localhost:5000/api/`

## 🚀 API Endpoints

- `GET /api/roles` - Available job roles
- `GET /api/jobs` - List all jobs
- `POST /api/recommendations` - Get job matches
- `POST /api/fetch-jobs` - Refresh job data
- `GET /api/stats` - Market statistics

## 🐛 Troubleshooting

**No jobs showing?**
- Click "Refresh Job Data" to fetch latest jobs
- Check API credentials in `.env`

**Server won't start?**
- Ensure Python 3.7+ installed
- Run `pip install -r requirements.txt`
- Check port 5000 is not in use

**API errors?**
- Verify Adzuna credentials
- Check internet connection
- Review API rate limits

## 📞 Support

- 📧 GitHub Issues
- 📖 Check troubleshooting section
- 🔗 [Adzuna API Docs](https://developer.adzuna.com/)

## 🎯 Future Features

- 📧 Email alerts for matching jobs
- 📄 Resume parser (auto-extract skills)
- 💼 Interview prep resources
- 📈 Career path recommendations
- 🏢 Company reviews & ratings

## 📄 License

MIT License - Feel free to use and modify

---

**Built with ❤️ using Flask, Python & ML**

v1.0 | January 2026
