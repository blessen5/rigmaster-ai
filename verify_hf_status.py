
import os
import sys
import traceback
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

def test_huggingface():
    log_file = "hf_test_result.log"
    with open(log_file, "w") as f:
        try:
            load_dotenv()
            api_key = os.getenv('HF_API_KEY')
            if not api_key:
                f.write("❌ Error: HF_API_KEY not found in .env\n")
                return

            f.write(f"Testing Hugging Face with key: {api_key[:10]}...\n")
            
            # Zephyr 7B Beta is usually very reliable on the free inference API
            model = "HuggingFaceH4/zephyr-7b-beta" 
            
            client = InferenceClient(token=api_key)
            f.write(f"Client created. Calling model: {model}\n")
            
            # Using chat_completion (OpenAI-compatible) which is the modern way
            messages = [
                {"role": "user", "content": "Tell me a joke about computers."}
            ]
            
            response = client.chat_completion(
                model=model,
                messages=messages,
                max_tokens=50
            )
            
            content = response.choices[0].message.content
            f.write(f"✅ Success! Response: {content}\n")
            print(f"Result: {content}")
            
        except Exception as e:
            f.write(f"❌ Failed with Exception: {str(e)}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    test_huggingface()
