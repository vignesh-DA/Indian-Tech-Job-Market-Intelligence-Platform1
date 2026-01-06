#!/usr/bin/env python3
"""
OAuth Setup Guide and Verification
Steps to get Google OAuth credentials and test the implementation
"""

import os
from dotenv import load_dotenv

print("=" * 80)
print("GOOGLE OAUTH 2.0 SETUP GUIDE")
print("=" * 80)

print("""
STEP 1: Create Google Cloud Project
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to https://console.cloud.google.com/
2. Click "Select a Project" → "New Project"
3. Name it "Gravito" or "Career Assistant"
4. Click "Create"
5. Wait for project to be created (30 seconds)

STEP 2: Enable Google+ API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. In Cloud Console, search for "Google+ API"
2. Click on it → "Enable"
3. Wait for it to enable

STEP 3: Create OAuth 2.0 Credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to "Credentials" (left sidebar)
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. You'll be asked to create a consent screen first:
   - Click "Consent Screen"
   - Select "External"
   - Fill in:
     - App name: "Gravito"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - Skip "Scopes" (click "Save and Continue")
   - Skip "Test users" (click "Save and Continue")
4. Back to credentials, click "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Web application"
6. Under "Authorized redirect URIs", add:
   - http://localhost:5000/api/auth/callback
   - http://127.0.0.1:5000/api/auth/callback
7. Click "Create"

STEP 4: Copy Your Credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. A popup will show your Client ID and Client Secret
2. Copy both (or download JSON)
3. Keep these SECRET - don't share them!

STEP 5: Update .env File
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Open .env in project root
2. Find these lines:
   GOOGLE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID_HERE
   GOOGLE_OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
3. Replace with your actual credentials
4. Save file

STEP 6: Test the Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run: python oauth_setup.py verify

STEP 7: Start the Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. python server.py
2. Visit http://localhost:5000/login
3. Click "Sign in with Google"
4. Follow Google's login flow
5. Should redirect to dashboard

TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ "Invalid OAuth credentials":
   - Check .env has correct Client ID and Secret
   - Make sure redirect URI matches: http://localhost:5000/api/auth/callback

❌ "Redirect URI mismatch":
   - Add both HTTP and HTTPS variants in Google Console
   - Ensure trailing slash matches exactly

❌ "Sign in button not working":
   - Check browser console for errors (F12)
   - Verify flask-session is installed: pip install flask-session

❌ "Can't find .env file":
   - Create .env in project root (same folder as server.py)
   - Add the OAuth credentials

QUICK VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# Load and check current setup
load_dotenv()

client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

print("\nCurrent Configuration:")
print(f"✓ Client ID: {client_id[:20]}..." if client_id and client_id != "YOUR_CLIENT_ID_HERE" else "✗ Client ID: NOT SET")
print(f"✓ Client Secret: {client_secret[:20]}..." if client_secret and client_secret != "YOUR_CLIENT_SECRET_HERE" else "✗ Client Secret: NOT SET")

if client_id == "YOUR_CLIENT_ID_HERE" or client_secret == "YOUR_CLIENT_SECRET_HERE":
    print("\n⚠️ OAuth credentials not yet configured in .env")
    print("Follow the steps above to get your credentials from Google Cloud Console")
else:
    print("\n✅ OAuth credentials are configured!")
    print("Ready to start the server and test login")
