"""
RigMaster AI Auto-Startup Script
Automatically starts Ollama, warms up models, and launches the app
"""
import subprocess
import sys
import time
import requests
import os

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def check_ollama_running():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start Ollama service"""
    print("⚠️  Ollama is not running. Starting it now...")
    
    try:
        if sys.platform == "win32":
            # Windows
            subprocess.Popen(
                ["ollama", "serve"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Linux/Mac
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        print("⏳ Waiting for Ollama to start...")
        time.sleep(5)
        
        if check_ollama_running():
            print("✅ Ollama started successfully!\n")
            return True
        else:
            print("❌ Failed to start Ollama")
            return False
    except Exception as e:
        print(f"❌ Error starting Ollama: {e}")
        return False

def check_models_warm():
    """Check if models are already warm"""
    try:
        start = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:1.5b",
                "prompt": "hi",
                "stream": False
            },
            timeout=10
        )
        elapsed = time.time() - start
        
        return elapsed < 5, elapsed
    except:
        return False, 0

def warm_up_models():
    """Warm up all models"""
    print("🔥 Warming up models (this takes ~40 seconds)...\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "warm_up_models.py"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        print()
        return result.returncode == 0
    except Exception as e:
        print(f"⚠️  Warning: Could not warm up models: {e}")
        print("   Models will warm up on first use (may be slower)\n")
        return False

def start_app():
    """Start the RigMaster AI app"""
    print("🚀 Starting RigMaster AI app...\n")
    print("=" * 70 + "\n")
    
    try:
        subprocess.run(
            [sys.executable, "app.py"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  App stopped by user")
    except Exception as e:
        print(f"\n❌ Error running app: {e}")

def main():
    print_header("🚀 RIGMASTER AI - AUTO STARTUP")
    
    # Step 1: Check/Start Ollama
    print("1️⃣  Checking Ollama service...")
    
    if check_ollama_running():
        print("   ✅ Ollama is already running\n")
    else:
        if not start_ollama():
            print("\n❌ Could not start Ollama")
            print("   Please start Ollama manually: ollama serve")
            input("\nPress Enter to exit...")
            sys.exit(1)
    
    # Step 2: Check if models are warm
    print("2️⃣  Checking if models are warm...")
    
    is_warm, elapsed = check_models_warm()
    
    if is_warm:
        print(f"   ✅ Models are already warm (response in {elapsed:.1f}s)\n")
        needs_warmup = False
    else:
        print(f"   ⚠️  Models need warming up\n")
        needs_warmup = True
    
    # Step 3: Warm up if needed
    if needs_warmup:
        print("3️⃣  Warming up models...")
        warm_up_models()
    else:
        print("3️⃣  Skipping warm-up (models already warm)\n")
    
    # Step 4: Start app
    print("4️⃣  Starting RigMaster AI app...")
    start_app()
    
    # Cleanup
    print("\n" + "=" * 70)
    print("  RigMaster AI has stopped")
    print("=" * 70 + "\n")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Startup cancelled by user")
        sys.exit(0)
