#!/usr/bin/env python3
"""Check available Gemini models"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

print("=" * 60)
print("AVAILABLE GEMINI MODELS")
print("=" * 60)

try:
    models = genai.list_models()
    for model in models:
        print(f"\n📦 {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"   Supported: {model.supported_generation_methods}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
