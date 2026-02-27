import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_groq():
    api_key = os.getenv('GROQ_API_KEY')
    print(f"Checking key: {api_key[:10]}...")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Using a common Groq model (Llama 3 8B) to test connection quickly, 
    # then we'll confirm DeepSeek R1 Distill.
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [

            {"role": "user", "content": "Explain what RigMaster is in one sentence."}
        ],
        "max_tokens": 50
    }

    print("Sending request to Groq Cloud...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            result = response.json()
            print("\n✅ STATUS: ACTIVE")
            print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"\n❌ STATUS: FAILED ({response.status_code})")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_groq()
