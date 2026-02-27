import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_openrouter_free():
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: No OPENROUTER_API_KEY found in .env")
        return

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000", # Required by OpenRouter
        "X-Title": "RigMaster AI Project"
    }
    
    # Using the exact free model name
    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [
            {"role": "user", "content": "Say 'DeepSeek Free Cloud is Active'"}
        ],
        "max_tokens": 50
    }

    print(f"Testing DeepSeek on OpenRouter Free Tier...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print("✅ SUCCESS!")
            print(f"Response: {answer}")
        else:
            print(f"❌ FAILED: Status Code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_openrouter_free()
