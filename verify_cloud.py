import os
import json
import logging
from dotenv import load_dotenv
from ai_engine import get_ai_engine

logging.basicConfig(level=logging.INFO)
load_dotenv()

def verify_cloud():
    engine = get_ai_engine()
    print("Testing DeepSeek Cloud Integration...")
    
    # Force attempt to use groq provider
    try:
        # Pass JSON mode as True for a structured response check
        response = engine._call_groq(
            system_prompt="You are a system validator.",
            user_prompt="Return a JSON object with 'status': 'ok'.",
            json_mode=True
        )
        
        if response:
            with open('cloud_status.txt', 'w') as f:
                f.write(f"SUCCESS (GROQ): {response}")
            print("✅ Groq Cloud (DeepSeek R1) is ACTIVE.")

        else:
            with open('cloud_status.txt', 'w') as f:
                f.write("FAILED: No response content")
            print("❌ DeepSeek Cloud returned empty response.")
            
    except Exception as e:
        err_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            err_msg += f" - Response: {e.response.text}"
        with open('cloud_status.txt', 'w') as f:
            f.write(f"ERROR: {err_msg}")
        print(f"❌ Groq Cloud Error: {err_msg}")


if __name__ == "__main__":
    verify_cloud()
