"""Quick script to find the first working Gemini model for this API key."""
import warnings
warnings.filterwarnings('ignore')
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

# Get all available models
all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
print("All available models:")
for m in all_models:
    print(f"  {m}")

# Test which one actually works
print("\nTesting models...")
for name in all_models:
    try:
        model = genai.GenerativeModel(model_name=name)
        resp = model.generate_content('Say hello in one word.')
        print(f"\nFIRST WORKING MODEL: {name}")
        print(f"Response: {resp.text.strip()}")
        break
    except Exception as e:
        short = str(e)[:80]
        print(f"  SKIP {name}: {short}")
