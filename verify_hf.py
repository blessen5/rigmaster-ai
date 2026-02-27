
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv()
HF_KEY = os.getenv("HF_API_KEY")

def verify():
    print("Verifying Hugging Face Model: meta-llama/Meta-Llama-3-8B-Instruct")
    try:
        client = InferenceClient(token=HF_KEY)
        messages = [{"role": "user", "content": "Are you working? Reply with 'Yes, I am working!'"}]
        completion = client.chat_completion(messages, model="meta-llama/Meta-Llama-3-8B-Instruct", max_tokens=50)
        print("Response received:")
        print(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
