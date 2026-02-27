"""
Quick Setup Script for AI Integration
Run this to verify your AI setup is working correctly
"""
import os
import sys
from dotenv import load_dotenv

def check_env_file():
    """Check if .env file exists and has required keys"""
    print("=" * 60)
    print("Step 1: Checking .env file...")
    print("=" * 60)
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("\nPlease create a .env file with the following content:")
        print("""
GROQ_API_KEY=your_groq_key_here
MISTRAL_API_KEY=your_mistral_key_here
GEMINI_API_KEY=your_gemini_key_here
OLLAMA_URL=http://localhost:11434
        """)
        return False
    
    load_dotenv()
    
    groq_key = os.getenv('GROQ_API_KEY')
    mistral_key = os.getenv('MISTRAL_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    print("\nAPI Keys Status:")
    print(f"  Groq:    {'✓ Set' if groq_key else '✗ Not Set'}")
    print(f"  Mistral: {'✓ Set' if mistral_key else '✗ Not Set'}")
    print(f"  Gemini:  {'✓ Set' if gemini_key else '✗ Not Set'}")
    
    if not any([groq_key, mistral_key, gemini_key]):
        print("\n❌ No API keys found!")
        print("\nGet free API keys from:")
        print("  - Groq: https://console.groq.com")
        print("  - Mistral: https://console.mistral.ai")
        print("  - Gemini: https://aistudio.google.com/app/apikey")
        return False
    
    if groq_key and mistral_key and gemini_key:
        print("\n✓ All API keys are set!")
    else:
        print("\n⚠️  Some API keys are missing, but at least one is set.")
        print("   The system will work with available providers.")
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\n" + "=" * 60)
    print("Step 2: Checking dependencies...")
    print("=" * 60)
    
    required_packages = {
        'flask': 'Flask',
        'pymongo': 'PyMongo',
        'requests': 'Requests',
        'dotenv': 'python-dotenv',
        'groq': 'groq',
        'mistralai': 'mistralai',
        'google.genai': 'google-genai'
    }
    
    missing = []
    
    for module, package in required_packages.items():
        try:
            if module == 'dotenv':
                __import__('dotenv')
            elif module == 'google.genai':
                __import__('google.genai')
            else:
                __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("\nInstall them with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("\n✓ All dependencies installed!")
    return True

def check_ai_engine():
    """Check if AI engine can be imported"""
    print("\n" + "=" * 60)
    print("Step 3: Checking AI Engine...")
    print("=" * 60)
    
    try:
        from ai_engine import get_ai_engine
        print("  ✓ AI Engine module found")
        
        ai_engine = get_ai_engine()
        print(f"  ✓ AI Engine initialized")
        print(f"  ✓ Available providers: {', '.join(ai_engine.providers)}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_simple_recommendation():
    """Test a simple AI recommendation"""
    print("\n" + "=" * 60)
    print("Step 4: Testing AI Recommendation...")
    print("=" * 60)
    
    try:
        from ai_engine import get_ai_engine
        
        ai_engine = get_ai_engine()
        
        print("\n  Testing with: Budget=$1000, Use Case=Gaming")
        print("  This may take a few seconds...\n")
        
        result = ai_engine.get_pc_recommendation(
            budget="$1000",
            use_case="Gaming"
        )
        
        print(f"  ✓ Success! Provider used: {result.get('provider_used', 'unknown')}")
        print(f"  ✓ CPU: {result.get('cpu', 'N/A')}")
        print(f"  ✓ GPU: {result.get('gpu', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        print("\n  This is okay! The system will use heuristic fallback.")
        return False

def check_ollama():
    """Check if Ollama is available (optional)"""
    print("\n" + "=" * 60)
    print("Step 5: Checking Ollama (Optional)...")
    print("=" * 60)
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            print("  ✓ Ollama is running!")
            models = response.json().get('models', [])
            if models:
                print(f"  ✓ Available models: {', '.join([m['name'] for m in models])}")
            else:
                print("  ⚠️  Ollama is running but no models installed")
                print("     Install a model with: ollama pull llama3.2")
            return True
        else:
            print("  ⚠️  Ollama not running (optional)")
            return False
    except:
        print("  ⚠️  Ollama not installed or not running (optional)")
        print("     Download from: https://ollama.com/download")
        return False

def main():
    """Run all checks"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AI INTEGRATION SETUP CHECKER" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\nThis script will verify your AI integration is ready to use.\n")
    
    checks = [
        ("Environment Variables", check_env_file),
        ("Dependencies", check_dependencies),
        ("AI Engine", check_ai_engine),
        ("AI Recommendation Test", test_simple_recommendation),
        ("Ollama (Optional)", check_ollama)
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    required_checks = results[:4]  # First 4 are required
    all_required_passed = all(r[1] for r in required_checks)
    
    if all_required_passed:
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Your AI integration is ready to use!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Start your Flask app: python app.py")
        print("  2. Login to your account")
        print("  3. Visit: http://localhost:5000/ai-demo")
        print("  4. Try getting an AI recommendation!")
        print("\nDocumentation:")
        print("  - Quick Start: AI_QUICKSTART.md")
        print("  - Full Guide: AI_INTEGRATION_GUIDE.md")
        print("  - Summary: AI_IMPLEMENTATION_SUMMARY.md")
    else:
        print("\n" + "=" * 60)
        print("⚠️  SETUP INCOMPLETE")
        print("=" * 60)
        print("\nPlease fix the failed checks above.")
        print("See AI_QUICKSTART.md for detailed setup instructions.")
    
    print("\n")

if __name__ == "__main__":
    main()
