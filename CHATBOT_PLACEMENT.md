# Chatbot Placement Guide

## Visual Layout

```
┌─────────────────────────────────────────────────────────┐
│                     PAGE CONTENT                         │
│                                                          │
│  • Job Recommendations Cards                            │
│  • Skills Development Path                              │
│  • Filters & Search                                     │
│                                                          │
│                                                    ╱─────┤
│                                               ╱────│ 💬  │ ← Floating Chatbot Button
│                                          ╱────     └─────┘   (Bottom-Right Corner)
│                                                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## When Chatbot is Closed
- **Floating button** (60px × 60px) appears at **bottom-right corner**
- Button shows **💬 (comments icon)** 
- On hover: Button scales up with enhanced shadow
- Position: `bottom: 20px; right: 20px;` (from edges)

## When Chatbot is Opened
- **Chat widget** (400px × 600px) appears at **bottom-right corner**
- Floating button **hides** automatically
- Chat widget shows with smooth animation
- Contains:
  - **Header**: "🤖 Career Assistant" with close button (X)
  - **Messages Area**: Scrollable chat history with bot/user messages
  - **Input Field**: Text input + send button
  - **Initial Message**: Bot greeting with 4 categories

## Chat Widget Structure

```
┌──────────────────────────────────┐
│ 🤖 Career Assistant       [X]    │  ← Header with close button
├──────────────────────────────────┤
│                                  │
│ 👋 Hi! I'm your Career Assistant │
│ I can help you with:             │
│  • 💼 Understanding jobs         │  ← Initial greeting message
│  • 🎯 Planning career path       │
│  • 📚 Building missing skills    │
│  • 📊 Market insights & salary   │
│                                  │
│ You: I want to understand SQL    │  ← User message
│                                  │
│ Bot: Based on your profile...    │  ← Bot response
│                                  │
├──────────────────────────────────┤
│ [Type your question...    ] [➤]  │  ← Input area with send button
└──────────────────────────────────┘
```

## Features Implemented

### 1. **Floating Button**
- ✅ Fixed position at bottom-right
- ✅ 60px circular button with gradient background
- ✅ Icon: `<i class="fas fa-comments"></i>`
- ✅ Hover effect: Scale up + enhanced shadow
- ✅ Click to toggle chat widget

### 2. **Chat Widget**
- ✅ 400px wide × 600px tall (responsive on mobile)
- ✅ Smooth slide-in animation from bottom-right
- ✅ Stays on top (z-index: 998)
- ✅ Clean, modern design with gradient header

### 3. **Messages Display**
- ✅ User messages: Right-aligned, blue background, white text
- ✅ Bot messages: Left-aligned, gray background, dark text
- ✅ Messages animate in with slideIn effect
- ✅ Timestamps on each message
- ✅ Auto-scroll to latest message
- ✅ Custom scrollbar styling

### 4. **Input Handling**
- ✅ Text input field with placeholder
- ✅ Send button with icon `<i class="fas fa-paper-plane"></i>`
- ✅ Enter key to send (Shift+Enter for multiline)
- ✅ Disabled state while waiting for response
- ✅ Focus management

### 5. **Typing Indicator**
- ✅ 3 animated dots while waiting for bot response
- ✅ Smooth animation showing typing simulation
- ✅ Removed after response arrives

### 6. **Conversation History**
- ✅ Saves chat history to localStorage
- ✅ Loads previous messages on page reload
- ✅ Maintains context across sessions

## Desktop vs Mobile

### Desktop (≥600px)
- Floating button: 60px, bottom-right
- Chat widget: 400px wide, 600px tall
- Positioned with 20px margin from edges

### Mobile (<600px)
- Floating button: 50px (slightly smaller)
- Chat widget: Full width minus 32px margin
- Height: 70vh (max 500px)
- Auto-adjusts to screen size

## Integration with Existing System

```
User Profile (from form)
    ↓
Send message via chatbot
    ↓
POST /api/chat endpoint
    ├─ message: User's question
    ├─ user_profile: Skills, experience, role, location
    ├─ conversation_history: Previous messages
    └─ context: Current job recommendations
    ↓
Gemini API (Categories 1-4)
    ↓
Response returned with suggestions
    ↓
Display in chat widget
    ├─ Message text
    ├─ Suggestions
    ├─ Related jobs
    └─ Action buttons
```

## File Structure Changes

```
frontend/
├─ recommendations.html (UPDATED)
│  └─ Added chatbot button + widget HTML
│
└─ assets/css/
   └─ styles.css (UPDATED)
      └─ Added 200+ lines of chatbot styling
      
└─ assets/js/
   └─ recommendations.js (UPDATED)
      └─ Added chatbot initialization & functions
```

## Key CSS Classes

| Class | Purpose |
|-------|---------|
| `.chatbot-button` | Floating button at bottom-right |
| `.chatbot-widget` | Main chat container |
| `.chatbot-widget.active` | Shows chat (display flex + opacity) |
| `.chatbot-header` | Header with title and close btn |
| `.chatbot-messages` | Scrollable message container |
| `.chatbot-message` | Individual message wrapper |
| `.user-message` | User's message styling |
| `.bot-message` | Bot's message styling |
| `.chatbot-input-area` | Input field container |
| `.typing-indicator` | Loading dots animation |

## Key JavaScript Functions

| Function | Purpose |
|----------|---------|
| `initializeChatbot()` | Setup event listeners |
| `sendChatbotMessage()` | Handle user input & API call |
| `addChatMessage()` | Add message to UI |
| `showTypingIndicator()` | Show loading animation |
| `removeTypingIndicator()` | Hide loading animation |
| `getUserProfileContext()` | Get form data for API |
| `saveChatHistory()` | Store history in localStorage |
| `loadChatHistory()` | Restore previous messages |

## Responsive Breakpoint

```css
/* Desktop (≥600px) */
.chatbot-button: 60px × 60px
.chatbot-widget: 400px × 600px

/* Mobile (<600px) */
.chatbot-button: 50px × 50px
.chatbot-widget: calc(100vw - 32px) × 70vh (max 500px)
```

## Next Steps

Once `/api/chat` endpoint is ready in server.py:

1. ✅ Chatbot UI is ready
2. ✅ Event listeners connected
3. ✅ Message display working
4. ✅ localStorage integration working
5. ⏳ Backend API endpoint (`/api/chat`) needs implementation
6. ⏳ Gemini API integration needed
7. ⏳ Context builder and category router needed

The frontend is **100% ready** to receive chat responses from the backend!
