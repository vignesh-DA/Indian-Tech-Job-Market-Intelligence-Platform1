# Quick Start Guide - Chatbot

## 🚀 Start Using Chatbot in 2 Minutes

### **Step 1: Run the Server**
```bash
python server.py
```

Visit: http://localhost:5000/recommendations

### **Step 2: Click the Chatbot Button**
Look for the **💬** button at the **bottom-right corner** of the screen

### **Step 3: Start Asking Questions**
Try these example questions:

**User Profiling Questions:**
- "Assess my skills"
- "What career path suits me?"

**Job Questions:**
- "Tell me about backend developer role"
- "What skills are trending?"

**Career Guidance:**
- "How do I learn Python?"
- "Plan my career progression"

**Salary & Market:**
- "What's the salary range for my role?"
- "Which skills are in high demand?"

---

## ⚙️ Optional: Enable Gemini API

### Get Free API Key:
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### Setup:
```bash
# Edit .env file
echo "GEMINI_API_KEY=your_key_here" > .env
```

That's it! Restart the server and you'll get AI-powered responses.

---

## 🎮 Features

- **Chat anywhere** - Available on all 4 pages
- **Persistent history** - Your conversations are saved
- **Smart detection** - Understands your intent
- **Mobile friendly** - Works on all devices
- **Fast responses** - Real-time with typing indicators

---

## 📍 Location

The chatbot button appears on:
- ✅ Home page (/)
- ✅ Recommendations (/recommendations)
- ✅ Dashboard (/dashboard)
- ✅ Saved Jobs (/saved-jobs)

---

## 🆘 Troubleshooting

**Chatbot not responding?**
1. Check server: `http://localhost:5000/health`
2. Open browser console (F12) for errors
3. Check .env file exists

**Want to clear chat history?**
Open browser console and run:
```javascript
localStorage.removeItem('chatbot_history');
location.reload();
```

---

Enjoy your AI Career Assistant! 🎉
