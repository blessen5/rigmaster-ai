"""
Simple Ollama Model Downloader - No Unicode Issues
Just runs ollama pull commands directly without capturing output
"""

import subprocess
import sys

MODELS = [
    'qwen2.5:1.5b',
    'gemma2:2b',
    'llama3.2:1b',
    'phi3:mini',
    'qwen2.5:3b',
    'llama3.2:3b',
    'mistral:7b',
    'gemma2:9b',
    'llama3.1:8b',
    'deepseek-r1:7b',
    'qwen2.5:7b',
    'phi3:medium',
]

print("=" * 70)
print("RigMaster AI - Simple Model Downloader")
print("=" * 70)
print(f"\nThis will download {len(MODELS)} FREE models")
print("Total size: ~20GB | Time: 30-60 minutes\n")

response = input("Continue? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("Cancelled.")
    sys.exit(0)

print("\n" + "=" * 70)
print("Starting downloads...")
print("=" * 70 + "\n")

for i, model in enumerate(MODELS, 1):
    print(f"\n[{i}/{len(MODELS)}] Downloading: {model}")
    print("-" * 70)
    
    try:
        # Run ollama pull directly - output goes straight to console
        # This avoids all encoding issues!
        result = subprocess.run(
            ['ollama', 'pull', model],
            check=False  # Don't raise exception on error
        )
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS: {model}")
        else:
            print(f"\n❌ FAILED: {model}")
            
    except FileNotFoundError:
        print("\n❌ ERROR: Ollama not found!")
        print("Install from: https://ollama.ai")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        print("Already downloaded models are saved.")
        print("Run this script again to continue.")
        sys.exit(0)

print("\n" + "=" * 70)
print("🎉 ALL DOWNLOADS COMPLETE!")
print("=" * 70)
print("\nNext step: Restart your app with 'python app.py'")
print("=" * 70 + "\n")
