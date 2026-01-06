#!/usr/bin/env python
"""Test chatbot with learning links"""

from src.chatbot_engine import ChatbotEngine

chatbot = ChatbotEngine()

# User profile
user_profile = {
    'role': 'Frontend Developer',
    'experience': '2-3 years',
    'location': 'Bangalore',
    'skills': ['HTML', 'CSS', 'JavaScript', 'React'],
    'total_matched_jobs': 15
}

# Test messages that should provide links
test_messages = [
    "How do I learn Python?",
    "teach me data science from scratch",
    "I want to learn backend development, provide resources",
    "Give me a learning roadmap for web development",
    "How do I master JavaScript?",
    "What are the best resources to learn Docker?"
]

print("="*70)
print("🤖 TESTING CHATBOT WITH LEARNING LINKS")
print("="*70)

for msg in test_messages:
    print(f"\n{'='*70}")
    print(f"👤 User: {msg}")
    print('='*70)
    
    response = chatbot.generate_response(
        user_message=msg,
        user_profile=user_profile,
        conversation_history=[],
        use_gemini=True
    )
    
    print(f"\n🤖 Intent: {response['intent']} ({response['confidence']:.2f} confidence)")
    print(f"📂 Category: {response['category']}")
    print(f"\n💬 Response:\n{response['message']}")
    print()

print("\n" + "="*70)
print("✅ Test completed!")
print("="*70)
