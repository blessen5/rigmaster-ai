"""
Pre-warm Ollama models for fast responses
Run this once when starting Ollama to load all models into memory
"""
import requests
import time

OLLAMA_URL = "http://localhost:11434"

MODELS = ['qwen2.5:1.5b', 'gemma2:2b', 'llama3.2:1b', 'phi3:mini']

def warm_up_model(model_name):
    """Send a quick request to load model into memory"""
    print(f"🔥 Warming up {model_name}...", end=" ", flush=True)
    
    try:
        start = time.time()
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": "Hello",
                "stream": False
            },
            timeout=120
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ Ready! ({elapsed:.1f}s)")
            return True
        else:
            print(f"❌ Failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔥 PRE-WARMING OLLAMA MODELS")
    print("=" * 60)
    print("\nThis will load all models into memory for fast responses.")
    print("First-time loading may take 10-40 seconds per model.\n")
    
    total_start = time.time()
    warmed = 0
    
    for model in MODELS:
        if warm_up_model(model):
            warmed += 1
    
    total_time = time.time() - total_start
    
    print("\n" + "=" * 60)
    print(f"✅ Warmed up {warmed}/{len(MODELS)} models in {total_time:.1f}s")
    print("=" * 60)
    print("\n🚀 All models are now loaded in memory!")
    print("⚡ Future requests will be FAST (1-3 seconds)")
    print("\n💡 Keep Ollama running to maintain warm models.")
    print("=" * 60)

if __name__ == "__main__":
    main()
