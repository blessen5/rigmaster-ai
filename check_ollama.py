import requests
import json

try:
    response = requests.get('http://localhost:11434/api/tags', timeout=2)
    with open('ollama_test_result.txt', 'w', encoding='utf-8') as f:
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            f.write("OLLAMA STATUS: RUNNING\n")
            f.write(f"Models installed: {len(models)}\n\n")
            for model in models:
                f.write(f"  - {model.get('name', 'Unknown')}\n")
            if models:
                f.write("\nOK - Ollama is fully working!\n")
            else:
                f.write("\nWARNING - Ollama running but no models installed\n")
                f.write("Run: ollama pull llama3.2\n")
        else:
            f.write(f"OLLAMA STATUS: ERROR (HTTP {response.status_code})\n")
except requests.exceptions.ConnectionError:
    with open('ollama_test_result.txt', 'w', encoding='utf-8') as f:
        f.write("OLLAMA STATUS: NOT RUNNING\n\n")
        f.write("Ollama is not installed or not running.\n")
        f.write("This is OPTIONAL - your AI engine works without it!\n\n")
        f.write("To install Ollama:\n")
        f.write("1. Download from: https://ollama.com/download\n")
        f.write("2. Install and run\n")
        f.write("3. Run: ollama pull llama3.2\n")
except Exception as e:
    with open('ollama_test_result.txt', 'w', encoding='utf-8') as f:
        f.write(f"OLLAMA STATUS: ERROR\n{str(e)}\n")

print("Test complete! Check ollama_test_result.txt")
