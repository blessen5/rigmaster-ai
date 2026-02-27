"""
Configuration: Use only the fastest Ollama model for maximum speed
"""

# OPTION 1: Single Fastest Model (Recommended for Speed)
# Uncomment this section in ai_engine.py if you want ONLY the fastest model:

"""
self.ollama_models = [
    'qwen2.5:1.5b',     # ONLY use the fastest model
]
"""

# OPTION 2: Top 2 Fastest Models (Good Balance)
"""
self.ollama_models = [
    'qwen2.5:1.5b',     # Fastest (13.95s first load)
    'gemma2:2b',        # Very fast (19.90s first load)
]
"""

# OPTION 3: Current Setup - All 4 Models (Best Variety)
"""
self.ollama_models = [
    'qwen2.5:1.5b',     # Fastest
    'gemma2:2b',        # Very fast
    'llama3.2:1b',      # Fast, excellent quality
    'phi3:mini',        # Best quality, slower
]
"""

print("""
╔════════════════════════════════════════════════════════════╗
║              SPEED OPTIMIZATION OPTIONS                    ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Option 1: Single Fastest Model                           ║
║  ────────────────────────────────                          ║
║  • Use only: qwen2.5:1.5b                                  ║
║  • Fastest possible responses                              ║
║  • Less variety in answers                                 ║
║  • First load: ~14s, then 1-2s                             ║
║                                                            ║
║  Option 2: Top 2 Fastest                                   ║
║  ────────────────────────                                  ║
║  • Use: qwen2.5:1.5b + gemma2:2b                           ║
║  • Very fast responses                                     ║
║  • Some variety                                            ║
║  • First load: ~14-20s, then 1-2s                          ║
║                                                            ║
║  Option 3: All 4 Models (Current)                          ║
║  ────────────────────────────────                          ║
║  • Use all 4 models                                        ║
║  • Best variety and quality                                ║
║  • Slightly slower first loads                             ║
║  • First load: ~14-40s, then 1-3s                          ║
║                                                            ║
║  💡 RECOMMENDATION:                                        ║
║  ─────────────────                                         ║
║  1. Run warm_up_models.py once when starting               ║
║  2. Keep all 4 models for variety                          ║
║  3. After warm-up, all responses are 1-3s!                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")
