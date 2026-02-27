
import sys
import os
try:
    import huggingface_hub
    version = huggingface_hub.__version__
except ImportError:
    version = "NOT INSTALLED"

with open("pkg_check.txt", "w") as f:
    f.write(f"Hugging Face Hub: {version}\n")
    f.write(f"Python: {sys.version}\n")
