import os
import requests
import json
from dotenv import load_dotenv
from google import genai
import time

# Load environment variables
load_dotenv()

def check_ai_health():
    output_lines = []
    output_lines.append(f"{'Provider':<15} | {'Key Status':<15} | {'Response':<10} | {'Quota/Status':<30}")
    output_lines.append("-" * 80)

    providers = [
        ('groq', os.getenv('GROQ_API_KEY'), "https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
        ('openrouter', os.getenv('OPENROUTER_API_KEY'), "https://openrouter.ai/api/v1/chat/completions", "meta-llama/llama-3.2-3b-instruct:free"),
        ('cohere', os.getenv('COHERE_API_KEY'), "https://api.cohere.ai/v1/chat", "command-r"),
        ('mistral', os.getenv('MISTRAL_API_KEY'), "https://api.mistral.ai/v1/chat/completions", "mistral-small-latest"),
        ('deepseek', os.getenv('DEEPSEEK_API_KEY'), "https://api.deepseek.com/v1/chat/completions", "deepseek-reasoner")
    ]

    for name, key, url, model in providers:
        key_status = "Present" if key else "MISSING"
        response_status = "N/A"
        quota_status = "Unknown"
        
        if not key:
            output_lines.append(f"{name:<15} | {key_status:<15} | {response_status:<10} | {quota_status:<30}")
            continue

        try:
            # Special case for Gemini
            if name == 'gemini':
                try:
                    client = genai.Client(api_key=key)
                    resp = client.models.generate_content(
                        model=model, 
                        contents="Say hello", 
                    )
                    response_status = "200 OK"
                    quota_status = "Active"
                except Exception as e:
                    response_status = "Error"
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        quota_status = "QUOTA EXHAUSTED"
                    else:
                        quota_status = f"Error: {str(e)}"
                        print(f"DEBUG GEMINI ERROR: {str(e)}")
            
            # Special case for others using requests
            else:
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                data = {}
                
                if name == 'cohere':
                    data = {
                        "model": model, 
                        "message": "Say hello",
                        "max_tokens": 10
                    }
                elif name == 'huggingface':
                    data = {
                        "inputs": "Say hello",
                        "parameters": {"max_new_tokens": 10}
                    }
                    pass 

                # Standard OpenAI/Chat format for most
                if name not in ['cohere']:
                    data = {
                        "model": model,
                        "messages": [{"role": "user", "content": "Say hello"}],
                        "max_tokens": 10
                    }
                
                resp = requests.post(url, json=data, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    response_status = "200 OK"
                    quota_status = "Active"
                elif resp.status_code == 429:
                    response_status = "429"
                    quota_status = "QUOTA EXHAUSTED"
                elif resp.status_code == 401:
                    response_status = "401"
                    quota_status = "Invalid Key"
                elif resp.status_code == 503: # Service Unavailable (common for overloaded free tiers)
                     response_status = "503"
                     quota_status = "Service Overloaded"
                else:
                    response_status = str(resp.status_code)
                    try:
                        err_msg = resp.json().get('error', {}).get('message', '')
                        quota_status = f"Error: {err_msg[:20]}"
                    except:
                        quota_status = "Unknown Error"

        except Exception as e:
            response_status = "Exc"
            quota_status = f"Ex: {str(e)[:20]}"

        output_lines.append(f"{name:<15} | {key_status:<15} | {response_status:<10} | {quota_status}")
    
    with open("ai_health_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print("Health check completed. Results written to ai_health_results.txt")

if __name__ == "__main__":
    check_ai_health()
