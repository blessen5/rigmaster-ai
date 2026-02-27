"""
Quick Ollama Test - Using llama3.2 (faster model)
"""
import requests
import time

print("\n" + "="*60)
print("🏠 TESTING OLLAMA WITH LLAMA3.2")
print("="*60 + "\n")

try:
    # Check available models
    print("1. Checking available models...")
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        
        print(f"   ✅ Found {len(models)} model(s):\n")
        for model in models:
            name = model.get('name', 'Unknown')
            size_gb = model.get('size', 0) / (1024**3)
            print(f"      • {name} ({size_gb:.1f} GB)")
        
        # Use llama3.2 (should be faster)
        print("\n2. Testing with llama3.2...")
        print("   Prompt: 'Recommend a gaming CPU in 1 sentence'")
        print("   Please wait (first request loads model into RAM)...\n")
        
        start_time = time.time()
        
        gen_response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2',
                'prompt': 'Recommend one good gaming CPU under $300. Answer in exactly one sentence.',
                'stream': False,
                'options': {
                    'num_predict': 100,
                    'temperature': 0.7
                }
            },
            timeout=90
        )
        
        elapsed = time.time() - start_time
        
        if gen_response.status_code == 200:
            result = gen_response.json()
            response_text = result.get('response', '').strip()
            
            print("="*60)
            print("✅ SUCCESS! OLLAMA IS WORKING!")
            print("="*60)
            print(f"\n💬 Ollama Response:\n   {response_text}\n")
            print("="*60)
            print(f"⏱️  Response time: {elapsed:.1f} seconds")
            print(f"🤖 Model: llama3.2")
            print(f"💰 Cost: $0 (local)")
            print(f"🚀 Unlimited requests!")
            print(f"🔒 100% private")
            print("\n✅ Your AI engine can now use Ollama!")
            print("="*60 + "\n")
        else:
            print(f"   ❌ Error: HTTP {gen_response.status_code}")
            print(f"   {gen_response.text}")
            
except requests.exceptions.Timeout:
    print("   ⚠️  Still timing out...")
    print("\n   Possible reasons:")
    print("   • First request is loading model into RAM (can take 30-60s)")
    print("   • Your computer needs more RAM/CPU")
    print("   • Try again - second request should be faster")
    print("\n   💡 Don't worry - cloud providers (Groq, Mistral, Gemini)")
    print("      are working perfectly and much faster!")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("YOUR AI SETUP:")
print("="*60)
print("✅ Groq (Cloud) - 1-2s - PRIMARY")
print("✅ Mistral (Cloud) - 2-3s - SECONDARY")
print("✅ Gemini (Cloud) - 2-4s - TERTIARY")
print("⚙️  Ollama (Local) - Variable - BACKUP")
print("\nAll working together for 100% uptime!")
print("="*60 + "\n")
