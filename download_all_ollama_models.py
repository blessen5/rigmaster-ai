"""
Download All Free Ollama Models for RigMaster AI
This script downloads all 12 free Ollama models used by the AI engine
"""

import subprocess
import sys

# All free Ollama models (in order of priority)
MODELS = [
    # Ultra-Fast Tier
    ('qwen2.5:1.5b', 'Alibaba 1.5B - FASTEST'),
    ('gemma2:2b', 'Google 2B - Very Fast'),
    ('llama3.2:1b', 'Meta 1B - Fast & Quality'),
    
    # Fast Tier
    ('phi3:mini', 'Microsoft 3.8B - Best Quality/Size'),
    ('qwen2.5:3b', 'Alibaba 3B - Balanced'),
    ('llama3.2:3b', 'Meta 3B - Good Reasoning'),
    
    # Quality Tier
    ('mistral:7b', 'Mistral 7B - Technical Tasks'),
    ('gemma2:9b', 'Google 9B - High Quality'),
    ('llama3.1:8b', 'Meta 8B - All-Rounder'),
    
    # Premium Tier
    ('deepseek-r1:7b', 'DeepSeek 7B - Reasoning'),
    ('qwen2.5:7b', 'Alibaba 7B - Strong'),
    ('phi3:medium', 'Microsoft 14B - Best Quality'),
]

def download_model(model_name, description):
    """Download a single Ollama model"""
    print(f"\n{'='*70}")
    print(f"Downloading: {model_name}")
    print(f"Description: {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            ['ollama', 'pull', model_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',  # Ignore encoding errors from progress bars
            check=True
        )
        print(f"✅ SUCCESS: {model_name} downloaded!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {model_name}")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ ERROR: Ollama is not installed or not in PATH")
        print("Please install Ollama from: https://ollama.ai")
        sys.exit(1)

def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         RigMaster AI - Free Ollama Models Downloader            ║
║                  Download 12 FREE AI Models                      ║
╚══════════════════════════════════════════════════════════════════╝

This will download 12 completely FREE AI models:
- 3 Ultra-Fast models (< 20s response)
- 3 Fast models (20-40s response)
- 3 Quality models (40-60s response)
- 3 Premium models (best quality)

Total Download Size: ~15-20 GB
Estimated Time: 30-60 minutes (depending on internet speed)

ALL MODELS ARE 100% FREE - No API keys, no rate limits!
""")
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Download cancelled.")
        sys.exit(0)
    
    print("\n🚀 Starting downloads...\n")
    
    success_count = 0
    failed_models = []
    
    for i, (model_name, description) in enumerate(MODELS, 1):
        print(f"\n[{i}/{len(MODELS)}] Processing {model_name}...")
        if download_model(model_name, description):
            success_count += 1
        else:
            failed_models.append(model_name)
    
    # Summary
    print(f"\n\n{'='*70}")
    print("DOWNLOAD SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Successfully downloaded: {success_count}/{len(MODELS)} models")
    
    if failed_models:
        print(f"\n❌ Failed models ({len(failed_models)}):")
        for model in failed_models:
            print(f"   - {model}")
        print("\nYou can retry failed models manually with:")
        print("   ollama pull <model_name>")
    else:
        print("\n🎉 ALL MODELS DOWNLOADED SUCCESSFULLY!")
        print("\nYour RigMaster AI now has access to 12 free AI models!")
        print("The AI engine will automatically rotate between them.")
    
    print(f"\n{'='*70}")
    print("Next Steps:")
    print("1. Restart your RigMaster AI application")
    print("2. The AI will automatically use these models")
    print("3. No configuration needed - it just works!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
