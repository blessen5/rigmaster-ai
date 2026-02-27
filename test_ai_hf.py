
import os
from dotenv import load_dotenv
from ai_engine import get_ai_engine

def test_ai_engine_hf():
    load_dotenv()
    engine = get_ai_engine()
    
    # Find HF in providers
    hf_index = -1
    for i, p in enumerate(engine.providers):
        if p == 'hf':
            hf_index = i
            break
            
    if hf_index == -1:
        print("HF provider not available in engine.")
        return

    engine.current_provider_index = hf_index
    print(f"Testing AI Engine with provider: {engine.providers[hf_index]}")
    
    log_file = "ai_engine_hf_test.log"
    with open(log_file, "w") as f:
        try:
            response = engine.generate_chat_response(
                "You are a helpful PC assistant.",
                "Say 'HF_IS_WORKING' if you can hear me."
            )
            f.write(f"Response: {response}\n")
            print(f"Response: {response}")
        except Exception as e:
            f.write(f"Error: {e}\n")
            print(f"Error: {e}")

if __name__ == "__main__":
    test_ai_engine_hf()
