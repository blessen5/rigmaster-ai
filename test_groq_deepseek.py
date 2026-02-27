import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_groq():
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ Error: No GROQ_API_KEY found in .env")
        return

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Testing with DeepSeek R1 Distill Llama 70B (Currently free on Groq in preview)
    payload = {
        "model": "deepseek-r1-distill-llama-70b",
        "messages": [
            {"role": "user", "content": "Say 'DeepSeek via Groq is Active' if you can read this."}
        ],
        "max_tokens": 20
    }

    print(f"Testing DeepSeek on Groq Cloud...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
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
    test_groq()
