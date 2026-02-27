import requests
import os
from dotenv import load_dotenv

load_dotenv()

def check_providers():
    results = []
    
    # 1. Test Groq
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json={
                    "model": "deepseek-r1-distill-llama-70b",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5
                },
                timeout=10
            )
            results.append(f"Groq: {res.status_code}")
            if res.status_code == 200:
                with open('PROV_GROQ_OK.txt', 'w') as f: f.write("WORKING")
        except Exception as e:
            results.append(f"Groq Error: {str(e)}")

    # 2. Test OpenRouter
    or_key = os.getenv('OPENROUTER_API_KEY')
    if or_key:
        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {or_key}"},
                json={
                    "model": "deepseek/deepseek-r1:free",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5
                },
                timeout=10
            )
            results.append(f"OpenRouter: {res.status_code}")
            if res.status_code == 200:
                with open('PROV_OR_OK.txt', 'w') as f: f.write("WORKING")
        except Exception as e:
            results.append(f"OpenRouter Error: {str(e)}")

    with open('provider_test_log.txt', 'w') as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    check_providers()
