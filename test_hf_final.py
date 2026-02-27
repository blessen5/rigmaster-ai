
import requests
import os
from dotenv import load_dotenv

load_dotenv()

OUTPUT_FILE = "hf_status.txt"
HF_KEY = os.getenv("HF_API_KEY")

def test():
    model = "Qwen/Qwen2.5-7B-Instruct"
    # Testing router endpoint again with a different model
    url = f"https://router.huggingface.co/hf-inference/models/{model}"
    
    headers = {
        "Authorization": f"Bearer {HF_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": "Hi"
    }
    
    with open(OUTPUT_FILE, "w") as f:
        f.write(f"Testing {model} on Router...\n")
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            f.write(f"Status: {resp.status_code}\n")
            if resp.status_code == 200:
                f.write(f"Success Response: {resp.text[:200]}\n")
                print("Success!")
                print(resp.json())
            else:
                f.write(f"Error Response: {resp.text[:200]}\n")
                print(f"Failed: {resp.status_code}")
                # print(resp.text)
        except Exception as e:
            f.write(f"Exception: {e}\n")
            print(f"Exception: {e}")

if __name__ == "__main__":
    test()
