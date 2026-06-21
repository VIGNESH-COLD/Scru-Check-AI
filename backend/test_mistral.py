
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from mistralai import Mistral
    print("✅ mistralai library found")
except ImportError as e:
    print(f"❌ mistralai import failed: {e}")
    exit(1)

api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    print("❌ MISTRAL_API_KEY not found in .env")
    exit(1)

print(f"🔑 API Key found: {api_key[:5]}...")

try:
    print("🔄 Testing connection...")
    client = Mistral(api_key=api_key)
    
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": "Hello, are you working?"}]
    )
    
    print(f"✅ Success! Response: {response.choices[0].message.content}")

except Exception as e:
    print(f"❌ Connection failed: {e}")
