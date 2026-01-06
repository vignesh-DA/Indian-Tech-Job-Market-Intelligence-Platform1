#!/usr/bin/env python
"""Test chatbot API endpoint"""

import requests
import json

url = 'http://localhost:5000/api/chat'

# Test different intents
test_cases = [
    'What skills should I focus on?',
    'Tell me about salary ranges',
    'How do I learn Kubernetes?',
    'What are trending skills in DevOps?',
    'Explain this backend developer role',
    'Plan my career progression'
]

print("=" * 70)
print("CHATBOT API ENDPOINT TESTS")
print("=" * 70)

for msg in test_cases:
    payload = {
        'message': msg,
        'user_profile': {
            'role': 'Backend Developer',
            'experience': '4-6 years',
            'location': 'Bangalore',
            'skills': ['Python', 'Java', 'SQL', 'AWS'],
            'total_matched_jobs': 24
        },
        'conversation_history': []
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        print(f"\nQuestion: {msg}")
        print(f"  ✓ Intent: {result['intent']}")
        print(f"  ✓ Category: {result['category']}")
        print(f"  ✓ Response: {result['message'][:100]}...")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 70)
print("✅ All API tests completed!")
print("=" * 70)
