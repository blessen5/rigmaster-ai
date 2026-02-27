"""
Auto-startup module for RigMaster AI
Automatically starts Ollama and warms up models when app.py is run
"""
import subprocess
import sys
import time
import requests
import os

def print_startup_header():
    """Print startup header"""
    print("\n" + "=" * 70)
    print("  RIGMASTER AI - AUTO STARTUP")
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
    print("  Ollama is not running. Starting it now...")
    
    try:
        if sys.platform == "win32":
            # Windows - start in background
            subprocess.Popen(
                ["ollama", "serve"],
                creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NO_WINDOW,
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
        
        print(" Waiting for Ollama to start...")
        time.sleep(5)
        
        if check_ollama_running():
            print(" Ollama started successfully!\n")
            return True
        else:
            print("  Ollama may not have started properly")
            print("   You can start it manually: ollama serve\n")
            return False
    except FileNotFoundError:
        print("  Ollama not found. Please install Ollama from: https://ollama.ai")
        print("   Continuing without Ollama (will use cloud APIs only)\n")
        return False
    except Exception as e:
        print(f"  Could not start Ollama: {e}")
        print("   Continuing without Ollama (will use cloud APIs only)\n")
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
            timeout=5
        )
        elapsed = time.time() - start
        
        return elapsed < 3, elapsed
    except:
        return False, 0

def warm_up_models_quick():
    """Quick warm-up of the fastest model only"""
    print(" Warming up fastest model (qwen2.5:1.5b)...")
    
    try:
        start = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:1.5b",
                "prompt": "Hello",
                "stream": False
            },
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f" Model ready! ({elapsed:.1f}s)\n")
            return True
        else:
            print("  Model warm-up failed\n")
            return False
    except Exception as e:
        print(f"  Could not warm up model: {e}\n")
        return False

def auto_startup():
    """Main auto-startup function"""
    print_startup_header()
    
    # Step 1: Check/Start Ollama
    # print("1.  Checking Ollama service...")
    
    # if check_ollama_running():
    #     print("    Ollama is already running\n")
    #     ollama_running = True
    # else:
    #     ollama_running = start_ollama()
    
    # if not ollama_running:
    #     print("  Ollama is not available. App will use cloud APIs only.\n")
    #     print("=" * 70 + "\n")
    #     return
    
    # # Step 2: Check if models are warm
    # print("2.  Checking if models are warm...")
    
    # is_warm, elapsed = check_models_warm()
    
    # if is_warm:
    #     print(f"    Models are already warm (response in {elapsed:.1f}s)\n")
    # else:
    #     print("     Models need warming up\n")
        
    #     # Step 3: Quick warm-up (only fastest model to save time)
    #     print("3.  Warming up fastest model...")
    #     warm_up_models_quick()
    
    print("   Cloud Mode Enabled (Ollama Disabled)")
    print("=" * 70)
    print("   STARTUP COMPLETE - Starting Flask App")
    print("=" * 70 + "\n")

# Run auto-startup when this module is imported
if __name__ != "__main__":
    # Only run if imported (not if run directly)
    try:
        auto_startup()
    except KeyboardInterrupt:
        print("\n  Startup interrupted by user\n")
    except Exception as e:
        print(f"\n  Startup error: {e}")
        print("   Continuing anyway...\n")
