#!/usr/bin/env python
"""Test dashboard APIs"""

import requests
import json

print("=" * 60)
print("Testing Dashboard APIs")
print("=" * 60)

# Test jobs endpoint
print("\n1. Testing /api/jobs endpoint...")
try:
    response = requests.get('http://localhost:5000/api/jobs?page=1&limit=5&days=30', timeout=5)
    data = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   Success: {data.get('success')}")
    print(f"   Data Count: {len(data.get('data', []))}")
    if data.get('pagination'):
        print(f"   Total Jobs: {data['pagination'].get('total')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test analytics endpoint
print("\n2. Testing /api/analytics endpoint...")
try:
    response = requests.get('http://localhost:5000/api/analytics', timeout=5)
    data = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   Success: {data.get('success')}")
    if data.get('data'):
        print(f"   Top Companies: {len(data['data'].get('top_companies', {}))} companies")
        print(f"   Top Locations: {len(data['data'].get('top_locations', {}))} locations")
        print(f"   Salary Ranges: {data['data'].get('salary_ranges')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test stats endpoint
print("\n3. Testing /api/stats endpoint...")
try:
    response = requests.get('http://localhost:5000/api/stats', timeout=5)
    data = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   Success: {data.get('success')}")
    if data.get('data'):
        print(f"   Stats: {data['data']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("Dashboard API test complete")
print("=" * 60)
