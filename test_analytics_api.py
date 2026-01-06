#!/usr/bin/env python
"""Test new analytics endpoints"""

import requests
import json

endpoints = [
    '/api/summary-stats',
    '/api/top-skills?top_n=10',
    '/api/role-distribution?top_n=10',
    '/api/experience-distribution',
    '/api/location-stats',
    '/api/salary-trends?group_by=location',
    '/api/posting-trends?days=30'
]

print('Testing Analytics API Endpoints')
print('=' * 60)

for endpoint in endpoints:
    try:
        response = requests.get(f'http://localhost:5000{endpoint}', timeout=5)
        data = response.json()
        print(f'\n✅ {endpoint}')
        print(f'   Status: {response.status_code}')
        print(f'   Success: {data.get("success")}')
        if 'data' in data:
            if isinstance(data['data'], list):
                print(f'   Records: {len(data["data"])}')
                if len(data['data']) > 0:
                    print(f'   Sample: {data["data"][0]}')
            elif isinstance(data['data'], dict):
                print(f'   Keys: {list(data["data"].keys())[:5]}')
    except Exception as e:
        print(f'\n❌ {endpoint}')
        print(f'   Error: {e}')

print('\n' + '=' * 60)
print('Analytics API Testing Complete')
