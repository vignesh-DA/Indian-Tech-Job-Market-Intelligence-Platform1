# OAuth Authentication Implementation Complete ✅

## What Was Built

### 1. **User Database** (`src/user_db.py`)
- SQLite database for storing user information
- Stores: email, name, profile picture, Google ID, login timestamp
- Methods to create/retrieve/update users

### 2. **OAuth Handler** (`src/oauth_handler.py`)
- Handles Google OAuth 2.0 flow
- Exchanges authorization code for access token
- Retrieves user information from Google
- Creates/updates users in database

### 3. **Login Page** (`frontend/login.html`)
- Clean, modern login UI
- Google "Sign in" button
- Handles loading states and errors
- Responsive design

### 4. **Server Routes** (added to `server.py`)
```
GET  /login                    → Login page
GET  /api/auth/login           → Get Google OAuth URL
GET  /api/auth/callback        → Handle OAuth callback
POST /api/auth/logout          → Logout user
GET  /api/auth/user            → Get current user info
```

### 5. **Session Management**
- Flask-Session for secure session handling
- User data stored in session during login
- Session cleared on logout

### 6. **Authentication Middleware**
- `@login_required` decorator for protecting routes
- Returns 401 if user not authenticated

---

## Setup Instructions

### Get Google OAuth Credentials

1. **Go to Google Cloud Console:**
   - https://console.cloud.google.com/

2. **Create New Project:**
   - Click "Select a Project" → "New Project"
   - Name: "Gravito"
   - Click "Create"

3. **Enable Google+ API:**
   - Search for "Google+ API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials:**
   - Go to "Credentials" (left sidebar)
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Create "Consent Screen" first if prompted (select "External")
   - Choose "Web application"
   - Add Redirect URI:
     ```
     http://localhost:5000/api/auth/callback
     ```
   - Click "Create"

5. **Copy Credentials:**
   - Copy **Client ID**
   - Copy **Client Secret**

### Configure in .env

Edit `.env` file and add:

```dotenv
GOOGLE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID_HERE
GOOGLE_OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5000/api/auth/callback
FLASK_SECRET_KEY=your-secret-key-change-this
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or specifically:
```bash
pip install flask-session requests
```

---

## How It Works

### Login Flow
```
1. User visits /login
2. Clicks "Sign in with Google"
3. Redirected to Google login
4. User signs in with Google account
5. Google redirects to /api/auth/callback with code
6. App exchanges code for user info
7. User created/updated in database
8. Session created
9. Redirected to /dashboard
```

### Access Protected Routes
```
GET /api/auth/user
Headers: (session automatically sent by browser)
Response: {
  "authenticated": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://...",
    "created_at": "2026-01-04...",
    "last_login": "2026-01-04..."
  }
}
```

### Logout
```
POST /api/auth/logout
Response: {
  "success": true,
  "message": "Logged out successfully"
}
```

---

## File Structure

```
gravito/
├── frontend/
│   ├── login.html                 ← New login page
│   ├── index.html
│   ├── market-dashboard.html
│   └── ...
├── src/
│   ├── user_db.py                 ← New: User database
│   ├── oauth_handler.py           ← New: OAuth logic
│   ├── chatbot_engine.py
│   ├── ...
├── server.py                       ← Updated: Added OAuth routes
├── .env                            ← Updated: OAuth credentials
├── requirements.txt                ← Updated: Added flask-session
└── oauth_setup_guide.py           ← New: Setup instructions
```

---

## Testing

### Test OAuth Setup
```bash
python oauth_setup_guide.py
```

### Manual Testing
1. Start server: `python server.py`
2. Visit: `http://localhost:5000/login`
3. Click "Sign in with Google"
4. Complete Google login flow
5. Should redirect to dashboard
6. Check database: `data/users.db` should have new user

---

## Next Steps

1. **Deploy with HTTPS:**
   - In production, change `GOOGLE_OAUTH_REDIRECT_URI` to `https://yourdomain.com/api/auth/callback`
   - Update Google Console with new redirect URI

2. **Protect Routes:**
   - Add `@login_required` decorator to routes that need authentication
   - Example: chatbot, recommendations, saved jobs

3. **Enhance User Profile:**
   - Add experience level, location, skills preference
   - Save user preferences for personalized chatbot responses
   - Link RAG data to user profile

4. **Add Email/Password (Optional):**
   - Phase 2 feature
   - Create signup form for email+password
   - Add password reset flow

---

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to git
- Never share Client Secret
- In production, use environment variables, not .env file
- Use HTTPS for all OAuth redirects in production
- Keep `FLASK_SECRET_KEY` secret and complex

---

## Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    picture TEXT,
    google_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

---

## Troubleshooting

**Issue:** "Invalid OAuth credentials"
- Check Client ID and Secret in .env
- Verify they match Google Console

**Issue:** "Redirect URI mismatch"
- Ensure URI matches exactly in Google Console
- Check for trailing slashes
- Verify protocol (http vs https)

**Issue:** "Sign in button not working"
- Check browser console (F12) for errors
- Verify flask-session is installed
- Check .env is in project root

**Issue:** "Session not persisting"
- Verify `flask-session` is installed
- Check `SESSION_TYPE` is set to 'filesystem'
- Verify `flask/sessions/` directory exists

---

## API Examples

### Get Current User
```bash
curl http://localhost:5000/api/auth/user \
  -b "session_id=xxxxx"
```

### Logout
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -b "session_id=xxxxx"
```

### Get Auth URL (for frontend)
```bash
curl http://localhost:5000/api/auth/login
# Returns: {"auth_url": "https://accounts.google.com/..."}
```

---

**Setup Complete! Ready to test OAuth flow.** 🚀
