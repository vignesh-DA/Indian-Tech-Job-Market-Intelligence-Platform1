#!/usr/bin/env python
"""Test chatbot engine"""

from src.chatbot_engine import ChatbotEngine

# Test chatbot
chatbot = ChatbotEngine()

# Test 1: Intent detection
print("=" * 60)
print("TEST 1: Intent Detection")
print("=" * 60)

test_messages = [
    "I want to assess my skills",
    "Tell me about job roles",
    "What's the salary range?",
    "How do I learn Python?"
]

for msg in test_messages:
    intent, category, conf = chatbot.detect_intent(msg)
    print(f"\nMessage: '{msg}'")
    print(f"  Intent: {intent}")
    print(f"  Category: {category}")
    print(f"  Confidence: {conf:.2f}")

# Test 2: Response generation
print("\n" + "=" * 60)
print("TEST 2: Response Generation (Fallback Mode)")
print("=" * 60)

user_profile = {
    'role': 'Backend Developer',
    'experience': '4-6 years',
    'location': 'Bangalore',
    'skills': ['Python', 'Java', 'SQL', 'AWS'],
    'total_matched_jobs': 24
}

test_questions = [
    "What skills should I focus on?",
    "What's my career path?",
    "Tell me about DevOps jobs",
    "What's the market salary?"
]

for question in test_questions:
    response = chatbot.generate_response(
        user_message=question,
        user_profile=user_profile,
        conversation_history=[]
    )
    
    print(f"\nQuestion: '{question}'")
    print(f"  Intent: {response['intent']}")
    print(f"  Category: {response['category']}")
    print(f"  Response preview: {response['message'][:80]}...")

print("\n" + "=" * 60)
print("✅ All tests completed successfully!")
print("=" * 60)
