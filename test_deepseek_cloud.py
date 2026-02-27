import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_deepseek():
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ Error: No DEEPSEEK_API_KEY found in .env")
        return

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "Say 'DeepSeek Cloud is Active' if you can read this."}
        ],
        "max_tokens": 20
    }

    print(f"Testing DeepSeek Cloud API...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print("✅ SUCCESS!")
            print(f"Response: {answer}")
            print("\nYour Cloud API is active and working.")
        elif response.status_code == 401:
            print("❌ UNAUTHORIZED: Your API key is invalid or has expired.")
        elif response.status_code == 402:
            print("❌ INSUFFICIENT BALANCE: Your free credits have run out.")
        else:
            print(f"❌ FAILED: Status Code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_deepseek()
