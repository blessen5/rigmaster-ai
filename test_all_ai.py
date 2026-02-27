import os
import json
import traceback
import requests
from pymongo import MongoClient
from google import genai
from dotenv import load_dotenv

load_dotenv()

def run():
    results = {}
    with open('debug_all_ai.txt', 'w') as log:
        log.write("Starting multi-provider test...\n")

    # 1. Gemini
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        client_ai = genai.Client(api_key=api_key)
        resp = client_ai.models.generate_content(model='gemini-2.0-flash-exp', contents="Say hello")
        results['gemini'] = "Success: " + resp.text[:20]
    except Exception as e:
        results['gemini'] = f"Failed: {str(e)}"

    # 2. Groq
    try:
        api_key = os.getenv('GROQ_API_KEY')
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": "Say hello"}],
                "max_tokens": 10
            },
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            results['groq'] = "Success: " + resp.json()['choices'][0]['message']['content']
        else:
            results['groq'] = f"Failed: {resp.status_code} {resp.text}"
    except Exception as e:
        results['groq'] = f"Failed: {str(e)}"

    # 3. DeepSeek
    try:
        api_key = os.getenv('DEEPSEEK_API_KEY')
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Say hello"}],
                "max_tokens": 10
            },
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=10
        )
        if resp.status_code == 200:
            results['deepseek'] = "Success: " + resp.json()['choices'][0]['message']['content']
        else:
            results['deepseek'] = f"Failed: {resp.status_code} {resp.text}"
    except Exception as e:
        results['deepseek'] = f"Failed: {str(e)}"

    with open('debug_all_ai.txt', 'a') as log:
        log.write(json.dumps(results, indent=2))

if __name__ == "__main__":
    run()
