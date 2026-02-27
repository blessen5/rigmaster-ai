import requests, os
from dotenv import load_dotenv
load_dotenv()
k = os.getenv('GROQ_API_KEY')
models = ["deepseek-r1-distill-qwen-32b", "deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile", "qwen-2.5-32b"]
for m in models:
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                      headers={"Authorization": f"Bearer {k}"},
                      json={"model": m, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5})
    print(f"Model {m}: {r.status_code}")
    if r.status_code == 200:
        print(f"  -> {m} is WORKING!")
        break
