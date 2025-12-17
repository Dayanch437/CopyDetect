"""
Find working Gemini models
"""
from google import genai
from config import settings

# Try different model name formats
models_to_try = [
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
    "models/gemini-pro",
    "models/gemini-2.0-flash-exp",
    "gemini-2.0-flash-exp",
    "models/gemini-exp-1206",
    "gemini-exp-1206",
]

print("Searching for working models...")
print("=" * 60)

working_models = []

for model_name in models_to_try:
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        chat = client.chats.create(model=model_name)
        response = chat.send_message("Hello")
        print(f"✓ WORKS: {model_name}")
        working_models.append(model_name)
        
        if hasattr(client, 'close'):
            client.close()
            
    except Exception as e:
        error_msg = str(e)[:150]
        print(f"✗ Failed: {model_name} - {error_msg}")

print("\n" + "=" * 60)
print(f"Working models found: {len(working_models)}")
for model in working_models:
    print(f"  - {model}")
