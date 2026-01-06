#!/usr/bin/env python
"""Test the recommendations API"""

import requests
import json

url = 'http://localhost:5000/api/recommendations'
payload = {
    'skills': ['Python', 'Django'],
    'role': 'Software Engineer',
    'experience': '2-4 years',
    'location': 'Bangalore'
}

response = requests.post(url, json=payload)
print(f'Status Code: {response.status_code}')
print(f'Response:')
data = response.json()
print(json.dumps(data, indent=2))

if data.get('success'):
    print(f'\nTotal recommendations: {data.get("count", 0)}')
    if data.get('data'):
        print(f'First recommendation: {data["data"][0]["title"]} at {data["data"][0]["company"]}')
else:
    print(f'Error: {data.get("message", "Unknown error")}')
