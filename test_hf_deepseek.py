import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_hf_deepseek():
    api_key = os.getenv('HF_API_KEY')
    if not api_key:
        print("❌ Error: No HF_API_KEY found in .env")
        return

    # DeepSeek-R1-Distill-Qwen-1.5B (Small, fast, usually free on Inference API)
    model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    payload = {
        "inputs": "Say 'DeepSeek via Hugging Face is Active'",
        "parameters": {"max_new_tokens": 50}
    }

    print(f"Testing DeepSeek on Hugging Face Free Inference API...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            # HF returns a list of results
            answer = result[0]['generated_text'] if isinstance(result, list) else result
            print("✅ SUCCESS!")
            print(f"Response: {answer}")
        else:
            print(f"❌ FAILED: Status Code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_hf_deepseek()
