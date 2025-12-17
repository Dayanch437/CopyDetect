"""
Test script to verify Gemini models
"""
from google import genai
from config import settings

print("Testing Gemini models...")
print("=" * 60)

for model_name in settings.AI_MODELS:
    print(f"\nTesting model: {model_name}")
    print("-" * 60)
    
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        chat = client.chats.create(model=model_name)
        response = chat.send_message("Say 'Hello' in Turkmen language.")
        print(f"✓ SUCCESS: {model_name}")
        print(f"  Response: {response.text[:100]}")
        
        if hasattr(client, 'close'):
            client.close()
            
    except Exception as e:
        error_msg = str(e)[:200]
        print(f"✗ FAILED: {model_name}")
        print(f"  Error: {error_msg}")

print("\n" + "=" * 60)
print("Test complete!")
