"""
Test Ollama connection and pull fast model
"""
import requests
import json

OLLAMA_URL = "http://localhost:11434"

def check_ollama():
    """Check if Ollama is running"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print("✅ Ollama is running!")
            print(f"\nInstalled models:")
            if 'models' in models and models['models']:
                for model in models['models']:
                    print(f"  - {model['name']} ({model.get('size', 'unknown size')})")
            else:
                print("  No models installed yet")
            return True
        else:
            print(f"❌ Ollama returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama. Is it running?")
        print("   Try running: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def pull_model(model_name):
    """Pull a model from Ollama"""
    print(f"\n📥 Pulling model: {model_name}")
    print("This may take a few minutes...")
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=300
        )
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if 'status' in data:
                    print(f"  {data['status']}", end='\r')
                if data.get('status') == 'success':
                    print(f"\n✅ Successfully pulled {model_name}!")
                    return True
        
        return True
    except Exception as e:
        print(f"\n❌ Error pulling model: {e}")
        return False

def test_model(model_name):
    """Test a quick inference"""
    print(f"\n🧪 Testing {model_name}...")
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": "Say 'Hello, I am ready!' in one sentence.",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Model response: {result.get('response', 'No response')}")
            return True
        else:
            print(f"❌ Model test failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing model: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Ollama Setup & Test")
    print("=" * 60)
    
    # Check if Ollama is running
    if not check_ollama():
        print("\n⚠️  Please start Ollama first:")
        print("   Run: ollama serve")
        exit(1)
    
    # Pull the fast model
    model_name = "llama3.2:1b"
    pull_model(model_name)
    
    # Test the model
    test_model(model_name)
    
    print("\n" + "=" * 60)
    print("✅ Setup complete! Your AI engine is ready to use.")
    print("=" * 60)
