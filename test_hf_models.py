
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv
import time

load_dotenv()
HF_KEY = os.getenv("HF_API_KEY")

def test_model(model_id):
    print(f"Testing {model_id}...")
    try:
        client = InferenceClient(token=HF_KEY)
        # Try a simple chat completion
        messages = [{"role": "user", "content": "Hi"}]
        completion = client.chat_completion(messages, model=model_id, max_tokens=10)
        print(f"SUCCESS: {model_id}")
        return True
    except Exception as e:
        print(f"FAILED: {model_id} - {e}")
        return False

models_to_test = [
    "meta-llama/Meta-Llama-3-8B-Instruct",
    "google/gemma-1.1-7b-it",
    "mistralai/Mistral-7B-Instruct-v0.2",
    "HuggingFaceH4/zephyr-7b-beta",
    "microsoft/Phi-3-mini-4k-instruct",
    "Qwen/Qwen2.5-7B-Instruct"
]

print("--- Starting Model Availability Test ---")
found = False
for m in models_to_test:
    if test_model(m):
        found = True
        print(f"Found working model: {m}")
        break  # distinct from "break" in the user request, I just want one working model
    time.sleep(1)

if not found:
    print("No working models found on free tier.")
