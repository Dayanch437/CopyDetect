"""
Script to list available Gemini models
"""
from google import genai
from config import settings

try:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    print("Available Gemini models:")
    print("-" * 50)
    
    models = client.models.list()
    gemini_models = [m for m in models if 'gemini' in m.name.lower()]
    
    for model in gemini_models:
        print(f"✓ {model.name}")
    
    print("-" * 50)
    print(f"\nTotal models found: {len(gemini_models)}")
    
except Exception as e:
    print(f"Error: {e}")
