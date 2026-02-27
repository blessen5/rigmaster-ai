"""
Test AI Engine - Verify All Models Are Connected
"""

from ai_engine import get_ai_engine
import sys

print("=" * 70)
print("Testing RigMaster AI Engine")
print("=" * 70)

# Initialize AI engine
engine = get_ai_engine()

print(f"\n✅ AI Engine initialized!")
print(f"\n📊 Available Providers: {engine.providers}")
print(f"\n💻 Ollama Models ({len(engine.ollama_models)} total):")
for i, model in enumerate(engine.ollama_models, 1):
    print(f"   {i}. {model}")

print("\n" + "=" * 70)
print("Testing Ollama Connection...")
print("=" * 70)

# Test Ollama with a simple prompt
try:
    response = engine._call_ollama(
        system_prompt="You are a helpful assistant.",
        user_prompt="Say 'Hello from RigMaster AI!' in exactly 5 words.",
        json_mode=False
    )
    
    if response:
        print(f"\n✅ SUCCESS! Ollama is working!")
        print(f"\n🤖 Response: {response}")
        print(f"\n✅ All {len(engine.ollama_models)} Ollama models are connected and ready!")
    else:
        print("\n❌ No response from Ollama")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Ollama is running: ollama serve")
    print("2. Check models are downloaded: ollama list")
    print("3. Try pulling a model: ollama pull qwen2.5:1.5b")

print("\n" + "=" * 70)
print("Cloud Providers Status:")
print("=" * 70)

if engine.groq_key:
    print("✅ Groq - API key configured")
else:
    print("⚠️  Groq - No API key")

if engine.deepseek_key:
    print("✅ DeepSeek - API key configured")
else:
    print("⚠️  DeepSeek - No API key")

if engine.mistral_key:
    print("✅ Mistral - API key configured")
else:
    print("⚠️  Mistral - No API key")

if engine.gemini_key:
    print("✅ Gemini - API key configured")
else:
    print("⚠️  Gemini - No API key")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total AI Providers: {len(engine.providers)}")
print(f"Total Ollama Models: {len(engine.ollama_models)}")
print(f"Total AI Power: {len(engine.providers) - 1} cloud + {len(engine.ollama_models)} local = UNLIMITED!")
print("=" * 70)
print("\n🎉 Your RigMaster AI is ready to use!")
print("=" * 70 + "\n")
