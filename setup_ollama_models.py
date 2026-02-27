"""
Setup and test multiple fast Ollama models
"""
import requests
import json
import time

OLLAMA_URL = "http://localhost:11434"

# Fast models to install (no rate limits!)
FAST_MODELS = [
    {
        "name": "llama3.2:1b",
        "description": "Meta's 1B - Very fast, excellent quality",
        "size": "~1.3GB",
        "speed": "⚡⚡⚡⚡⚡"
    },
    {
        "name": "phi3:mini",
        "description": "Microsoft's 3.8B - Fast, great reasoning",
        "size": "~2.3GB",
        "speed": "⚡⚡⚡⚡"
    },
    {
        "name": "gemma2:2b",
        "description": "Google's 2B - Fast, good for structured output",
        "size": "~1.6GB",
        "speed": "⚡⚡⚡⚡⚡"
    },
    {
        "name": "qwen2.5:1.5b",
        "description": "Alibaba's 1.5B - Very fast, multilingual",
        "size": "~1.0GB",
        "speed": "⚡⚡⚡⚡⚡"
    }
]

def check_ollama():
    """Check if Ollama is running"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except:
        return False, None

def pull_model(model_name):
    """Pull a model from Ollama"""
    print(f"\n📥 Pulling {model_name}...")
    print("   This may take a few minutes depending on your internet speed...")
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=600
        )
        
        last_status = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                status = data.get('status', '')
                
                # Show progress
                if status != last_status:
                    print(f"   {status}")
                    last_status = status
                
                if data.get('status') == 'success':
                    print(f"   ✅ Successfully pulled {model_name}!")
                    return True
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_model(model_name):
    """Test a model with a quick inference"""
    print(f"\n🧪 Testing {model_name}...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": "You are a PC builder AI. Respond with only: 'Ready to build PCs!'",
                "stream": False
            },
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Response: {result.get('response', 'No response')[:50]}...")
            print(f"   ⏱️  Time: {elapsed:.2f}s")
            return True, elapsed
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
            return False, 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0

def main():
    print("=" * 70)
    print("🚀 OLLAMA MULTI-MODEL SETUP - UNLIMITED & FAST!")
    print("=" * 70)
    
    # Check Ollama
    print("\n1️⃣  Checking Ollama service...")
    is_running, tags = check_ollama()
    
    if not is_running:
        print("   ❌ Ollama is not running!")
        print("   Please start it with: ollama serve")
        return
    
    print("   ✅ Ollama is running!")
    
    # Show currently installed models
    if tags and 'models' in tags and tags['models']:
        print(f"\n   Currently installed models:")
        for model in tags['models']:
            print(f"      • {model['name']}")
    
    # Pull all fast models
    print("\n2️⃣  Installing fast models...")
    print(f"   Total models to install: {len(FAST_MODELS)}")
    
    installed = []
    for model_info in FAST_MODELS:
        model_name = model_info['name']
        print(f"\n   📦 {model_name}")
        print(f"      {model_info['description']}")
        print(f"      Size: {model_info['size']} | Speed: {model_info['speed']}")
        
        if pull_model(model_name):
            installed.append(model_name)
    
    # Test all models
    print("\n3️⃣  Testing all models...")
    results = []
    
    for model_name in installed:
        success, elapsed = test_model(model_name)
        if success:
            results.append((model_name, elapsed))
    
    # Show results
    print("\n" + "=" * 70)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 70)
    
    if results:
        # Sort by speed
        results.sort(key=lambda x: x[1])
        
        print("\n🏆 Models ranked by speed (fastest first):\n")
        for i, (model, elapsed) in enumerate(results, 1):
            speed_rating = "⚡" * (6 - min(5, int(elapsed)))
            print(f"   {i}. {model:20s} - {elapsed:.2f}s {speed_rating}")
    
    print("\n" + "=" * 70)
    print("✅ SETUP COMPLETE!")
    print("=" * 70)
    print("\n💡 Benefits:")
    print("   • Unlimited requests - NO rate limits!")
    print("   • Fast responses - 1-3 seconds average")
    print("   • Automatic rotation - Load balanced across models")
    print("   • Local & Private - All processing on your machine")
    print("   • Always available - No API dependencies")
    
    print("\n🎯 Your RigMaster AI now has:")
    print(f"   • {len(installed)} fast Ollama models")
    print("   • Automatic model rotation")
    print("   • Instant PC build recommendations")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
