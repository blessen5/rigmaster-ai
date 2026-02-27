"""
Quick check for installed Ollama models
"""
import subprocess
import json

def check_models():
    """Check which models are installed"""
    print("=" * 60)
    print("🔍 Checking Ollama Models")
    print("=" * 60)
    
    try:
        # Run ollama list command
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("\n✅ Ollama is running!\n")
            print("Installed models:")
            print("-" * 60)
            print(result.stdout)
            
            # Check for our target models
            target_models = ['llama3.2:1b', 'phi3:mini', 'gemma2:2b', 'qwen2.5:1.5b']
            installed = []
            missing = []
            
            for model in target_models:
                if model in result.stdout or model.split(':')[0] in result.stdout:
                    installed.append(model)
                else:
                    missing.append(model)
            
            print("\n" + "=" * 60)
            print(f"✅ Installed: {len(installed)}/{len(target_models)} models")
            print("=" * 60)
            
            if installed:
                print("\n✅ Ready to use:")
                for model in installed:
                    print(f"   • {model}")
            
            if missing:
                print("\n📥 Still need to install:")
                for model in missing:
                    print(f"   • {model}")
                print("\nTo install missing models, run:")
                for model in missing:
                    print(f"   ollama pull {model}")
            
            if len(installed) == len(target_models):
                print("\n" + "=" * 60)
                print("🎉 ALL MODELS INSTALLED! You're ready to go!")
                print("=" * 60)
                print("\n💡 Your AI engine will automatically rotate through:")
                for i, model in enumerate(installed, 1):
                    print(f"   {i}. {model}")
                print("\n🚀 Start your app with: python app.py")
            
        else:
            print("❌ Error running ollama list")
            print(result.stderr)
            
    except FileNotFoundError:
        print("❌ Ollama not found. Is it installed?")
    except subprocess.TimeoutExpired:
        print("⏱️  Command timed out. Is Ollama running?")
        print("   Try: ollama serve")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_models()
