# 🚀 Quick Start Guide - Ollama Multi-Model Setup

## ✅ What You Now Have

Your RigMaster AI has been upgraded with **multi-model Ollama support**!

### 📦 Files Added

1. **`ai_engine.py`** - Updated with 4-model rotation
2. **`setup_models.bat`** - Windows batch setup script
3. **`setup_models.ps1`** - PowerShell setup script  
4. **`setup_ollama_models.py`** - Python setup script
5. **`check_models.py`** - Quick model checker
6. **`OLLAMA_MULTI_MODEL.md`** - Full documentation

---

## 🎯 Quick Setup (Choose One Method)

### Method 1: PowerShell Script (Recommended)

```powershell
# Run this in PowerShell
.\setup_models.ps1
```

### Method 2: Batch Script

```cmd
# Run this in Command Prompt
setup_models.bat
```

### Method 3: Python Script

```powershell
python setup_ollama_models.py
```

### Method 4: Manual Installation

```powershell
# Pull each model individually
ollama pull llama3.2:1b
ollama pull phi3:mini
ollama pull gemma2:2b
ollama pull qwen2.5:1.5b
```

---

## 🔍 Verify Installation

Check which models are installed:

```powershell
# Quick check
ollama list

# Or use the Python checker
python check_models.py
```

You should see all 4 models listed.

---

## 🚀 Start Using It

### 1. Start Ollama Service

```powershell
ollama serve
```

Keep this terminal open.

### 2. Start Your RigMaster AI App

In a new terminal:

```powershell
python app.py
```

### 3. Test It!

- Go to your RigMaster AI web interface
- Request a PC build recommendation
- Watch the logs to see model rotation in action!

---

## 📊 What Changed in `ai_engine.py`

### Before (Single Model)
```python
"model": "llama3.2:1b"  # Fixed model
```

### After (Multi-Model Rotation)
```python
self.ollama_models = [
    'llama3.2:1b',      # Meta's 1B
    'phi3:mini',        # Microsoft's 3.8B
    'gemma2:2b',        # Google's 2B
    'qwen2.5:1.5b',     # Alibaba's 1.5B
]
# Automatically rotates on each request!
```

---

## 🎯 The 4 Models

| # | Model | Speed | Best For |
|---|-------|-------|----------|
| 1 | **llama3.2:1b** | ⚡⚡⚡⚡⚡ | General recommendations |
| 2 | **phi3:mini** | ⚡⚡⚡⚡ | Complex reasoning |
| 3 | **gemma2:2b** | ⚡⚡⚡⚡⚡ | Structured JSON output |
| 4 | **qwen2.5:1.5b** | ⚡⚡⚡⚡⚡ | Fast responses |

**Total Size**: ~6.2GB

---

## 💡 Key Benefits

✅ **UNLIMITED** - No rate limits whatsoever  
⚡ **FAST** - 1-3 second responses  
🔄 **ROTATION** - Automatic load balancing  
🔒 **PRIVATE** - 100% local processing  
💰 **FREE** - No API costs ever  
🎲 **VARIETY** - Different models, diverse outputs  

---

## 🔍 Monitoring

### See Which Model Is Being Used

Check your app logs:

```
INFO - Calling Ollama with model: llama3.2:1b
INFO - Calling Ollama with model: phi3:mini
INFO - Calling Ollama with model: gemma2:2b
INFO - Calling Ollama with model: qwen2.5:1.5b
```

The models rotate automatically on each request!

---

## 🆚 Before vs After

### Before (Cloud APIs Only)
- ⚠️ Rate limits: 15-30 requests/minute
- ⚠️ Depends on internet
- ⚠️ API keys required
- ⚠️ Data sent to cloud

### After (With Ollama Multi-Model)
- ✅ **UNLIMITED** requests
- ✅ Works offline
- ✅ No API keys needed
- ✅ 100% private & local

---

## 🐛 Troubleshooting

### Models Still Downloading?

The pull commands may take 10-20 minutes depending on your internet speed. You can check progress:

```powershell
# Check what's installed so far
ollama list
```

### Ollama Not Running?

```powershell
# Start Ollama
ollama serve
```

### Want to Test a Single Model?

```powershell
ollama run llama3.2:1b "Recommend a gaming PC for $1500"
```

---

## 📚 Full Documentation

For complete details, see:
- **`OLLAMA_MULTI_MODEL.md`** - Comprehensive guide
- **`OLLAMA_FAST_MODEL.md`** - Original single-model guide

---

## 🎉 You're Ready!

Once the models are downloaded:

1. ✅ Start Ollama: `ollama serve`
2. ✅ Start your app: `python app.py`
3. ✅ Make unlimited PC recommendations!

**Enjoy your supercharged, unlimited AI engine!** 🚀

---

## 📞 Quick Commands Reference

```powershell
# Check installed models
ollama list

# Start Ollama service
ollama serve

# Pull a specific model
ollama pull llama3.2:1b

# Test a model
ollama run llama3.2:1b "Hello"

# Check model status
python check_models.py

# Run full setup
.\setup_models.ps1
```

---

*Setup completed on: 2026-02-01*
