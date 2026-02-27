
import os
import requests
import json
from dotenv import load_dotenv

def test_hf_requests():
    load_dotenv()
    api_key = os.getenv('HF_API_KEY')
    log_file = "hf_requests_test.log"
    
    with open(log_file, "w") as f:
        if not api_key:
            f.write("❌ HF_API_KEY not found.\n")
            return
            
        # Try Gemma 2 2B (usually open)
        model_id = "google/gemma-2-2b-it" 
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        f.write(f"Sending request to {url}\n")
        try:
            payload = {
                "inputs": "The best PC build for $1000 is",
                "parameters": {"max_new_tokens": 10}
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            f.write(f"Status Code: {response.status_code}\n")
            f.write(f"Response: {response.text}\n")
            
        except Exception as e:
            f.write(f"❌ Error: {str(e)}\n")

if __name__ == "__main__":
    test_hf_requests()
