# 🚀 AUTO-STARTUP GUIDE

## ✅ Solution: Ollama Auto-Start

I've created **3 startup scripts** that automatically:
1. ✅ Check if Ollama is running
2. ✅ Start Ollama if needed
3. ✅ Warm up models (if needed)
4. ✅ Start your RigMaster AI app

---

## 🎯 How to Use

### Option 1: PowerShell Script (Recommended for Windows)

**Just run this:**

```powershell
.\start.ps1
```

**What it does:**
- ✅ Checks if Ollama is running
- ✅ Starts Ollama automatically if not running
- ✅ Warms up models (only if needed)
- ✅ Starts your app
- ✅ Smart: Skips warm-up if models are already warm!

---

### Option 2: Batch File (Simple Windows)

**Just double-click or run:**

```cmd
start.bat
```

**What it does:**
- ✅ Same as PowerShell version
- ✅ Simpler, but less smart
- ✅ Always warms up models

---

### Option 3: Python Script (Cross-Platform)

**Run this:**

```powershell
python start.py
```

**What it does:**
- ✅ Works on Windows, Linux, Mac
- ✅ Smart warm-up detection
- ✅ Best error handling

---

## 📋 Comparison

| Feature | PowerShell | Batch | Python |
|---------|-----------|-------|--------|
| **Auto-start Ollama** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Smart warm-up** | ✅ Yes | ❌ No | ✅ Yes |
| **Cross-platform** | ❌ Windows only | ❌ Windows only | ✅ All platforms |
| **Error handling** | ✅ Good | ⚠️ Basic | ✅ Excellent |
| **Ease of use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Recommendation**: Use **`start.ps1`** for Windows (best balance)

---

## 🎯 What Happens When You Run It

### First Time (Cold Start)

```
1️⃣  Checking Ollama service...
   ⚠️  Ollama is not running. Starting it now...
   ✅ Ollama started successfully!

2️⃣  Checking if models are warm...
   ⚠️  Models need warming up

3️⃣  Warming up models...
   🔥 Warming up qwen2.5:1.5b... ✅ Ready! (7.3s)
   🔥 Warming up gemma2:2b... ✅ Ready! (9.0s)
   🔥 Warming up llama3.2:1b... ✅ Ready! (6.6s)
   🔥 Warming up phi3:mini... ✅ Ready! (15.2s)

4️⃣  Starting RigMaster AI app...
   * Running on http://127.0.0.1:5000
```

**Total time**: ~45 seconds (one-time setup)

---

### Subsequent Runs (Already Warm)

```
1️⃣  Checking Ollama service...
   ✅ Ollama is already running

2️⃣  Checking if models are warm...
   ✅ Models are already warm (response in 1.2s)

3️⃣  Skipping warm-up (models already warm)

4️⃣  Starting RigMaster AI app...
   * Running on http://127.0.0.1:5000
```

**Total time**: ~2 seconds! ⚡

---

## 💡 Pro Tips

### Create a Desktop Shortcut

**For PowerShell:**
1. Right-click on `start.ps1`
2. Create shortcut
3. Edit shortcut properties:
   - Target: `powershell.exe -ExecutionPolicy Bypass -File "C:\path\to\start.ps1"`
4. Move shortcut to Desktop

**For Batch:**
1. Right-click on `start.bat`
2. Create shortcut
3. Move to Desktop

Now you can **double-click** to start everything!

---

### Auto-Start on System Boot

**Windows Task Scheduler:**

1. Open Task Scheduler
2. Create Basic Task
3. Name: "RigMaster AI Auto-Start"
4. Trigger: "When I log on"
5. Action: "Start a program"
6. Program: `powershell.exe`
7. Arguments: `-ExecutionPolicy Bypass -File "C:\path\to\start.ps1"`

Now RigMaster AI starts automatically when you log in!

---

## 🔧 Customization

### Skip Model Warm-Up

If you want to skip warm-up (faster startup, but first requests will be slower):

**In `start.ps1`**, comment out the warm-up section:
```powershell
# Step 3: Warm up models if needed
# if ($needsWarmup) {
#     Write-Host "3️⃣  Warming up models..." -ForegroundColor Yellow
#     python warm_up_models.py
# }
```

**In `start.bat`**, comment out:
```batch
REM python warm_up_models.py
```

---

### Change Startup Behavior

Edit the scripts to customize:
- Wait time for Ollama to start (default: 5 seconds)
- Which models to warm up
- Whether to show Ollama window or minimize it

---

## 📊 Startup Time Comparison

### Manual Method (Old Way)

```
1. Open terminal → Run: ollama serve          (manual)
2. Open another terminal → Run: python warm_up_models.py  (manual, 40s)
3. Run: python app.py                         (manual)
─────────────────────────────────────────────
Total: 3 manual steps, ~45 seconds
```

### Auto-Start Method (New Way)

```
1. Run: .\start.ps1                           (automatic!)
─────────────────────────────────────────────
Total: 1 step, ~45 seconds first time, ~2s after
```

**Benefit**: 
- ✅ **1 command** instead of 3
- ✅ **Automatic** Ollama management
- ✅ **Smart** warm-up (skips if not needed)
- ✅ **Fast** subsequent starts (~2s)

---

## 🎯 Recommended Workflow

### For Development

**Just run:**
```powershell
.\start.ps1
```

That's it! Everything is automatic.

---

### For Production

**Option A - Manual Control:**
```powershell
# Terminal 1: Keep Ollama running
ollama serve

# Terminal 2: Start app when needed
python app.py
```

**Option B - Fully Automatic:**
```powershell
# Just run the auto-start script
.\start.ps1
```

---

## 🐛 Troubleshooting

### Script Won't Run (PowerShell)

**Error**: "Execution policy prevents running scripts"

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try again:
```powershell
.\start.ps1
```

---

### Ollama Doesn't Start

**Check if Ollama is installed:**
```powershell
ollama --version
```

If not found, install Ollama from: https://ollama.ai

---

### Models Don't Warm Up

**Check if warm_up_models.py exists:**
```powershell
ls warm_up_models.py
```

If missing, the script will skip warm-up (models will warm on first use).

---

## 📝 Summary

### Before (Manual)
```
❌ 3 separate commands
❌ Have to remember to start Ollama
❌ Have to remember to warm up models
❌ Multiple terminals needed
```

### After (Auto-Start)
```
✅ 1 single command: .\start.ps1
✅ Ollama starts automatically
✅ Models warm up automatically
✅ Everything in one terminal
✅ Smart: Skips unnecessary steps
```

---

## 🎉 Quick Start

**To start your RigMaster AI from now on:**

```powershell
.\start.ps1
```

**That's it!** Everything else is automatic! 🚀

---

*Now you can start your entire AI-powered PC building app with just one command!*
