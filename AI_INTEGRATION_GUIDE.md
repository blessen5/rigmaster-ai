# AI Integration Guide for RigMaster AI

## Overview

RigMaster AI now includes a **free, unlimited AI integration** system that provides intelligent PC build recommendations, compatibility analysis, and performance estimation.

## Architecture

### Multi-Provider AI Engine

The system uses a **hybrid approach** with automatic failover:

1. **Primary Providers** (Cloud-based, Free Tier):
   - **Groq** (30 req/min) - Fast, uses Llama 3.3 70B
   - **Mistral** (Free tier) - Reliable, good for structured output
   - **Google Gemini** (15 req/min) - Large context window

2. **Fallback Provider**:
   - **Ollama** (Unlimited, local) - Requires local installation

3. **Final Fallback**:
   - **Heuristic Rules** - Always available, no AI required

### RAG Strategy (Retrieval-Augmented Generation)

The system implements a **RAG approach**:
- **AI Role**: Logic and reasoning (which components pair well, performance estimates)
- **Database Role**: Facts (actual component names, prices, availability)

This ensures:
- AI provides intelligent recommendations
- Database provides current, accurate data
- No hallucinations about non-existent components

## API Endpoints

### 1. AI-Powered PC Recommendation

**Endpoint**: `POST /api/ai-recommend`

**Request**:
```json
{
  "budget": "$1500",
  "use_case": "Gaming and Streaming",
  "preferences": {
    "brand_preference": "AMD for CPU",
    "form_factor": "ATX",
    "rgb": true
  }
}
```

**Response**:
```json
{
  "status": "success",
  "recommendation": {
    "cpu": "AMD Ryzen 7 7800X3D",
    "gpu": "NVIDIA RTX 4070",
    "motherboard": "ASUS ROG STRIX B650-A",
    "ram": "32GB DDR5-6000",
    "storage": "1TB NVMe Gen4 SSD",
    "psu": "750W 80+ Gold",
    "case": "NZXT H510 Flow",
    "cooler": "Arctic Liquid Freezer II 280",
    "estimated_total": "$1450",
    "reasoning": "Balanced gaming build...",
    "performance_notes": "144+ FPS at 1440p..."
  },
  "matched_components": {
    "cpu_id": "507f1f77bcf86cd799439011",
    "cpu_name": "AMD Ryzen 7 7800X3D",
    "gpu_id": "507f1f77bcf86cd799439012",
    "gpu_name": "NVIDIA GeForce RTX 4070"
  },
  "provider": "groq"
}
```

### 2. AI Compatibility Check

**Endpoint**: `POST /api/ai-compatibility-check`

**Request**:
```json
{
  "cpu_id": "507f1f77bcf86cd799439011",
  "motherboard_id": "507f1f77bcf86cd799439012",
  "ram_id": "507f1f77bcf86cd799439013",
  "gpu_id": "507f1f77bcf86cd799439014",
  "psu_id": "507f1f77bcf86cd799439015"
}
```

**Response**:
```json
{
  "status": "success",
  "analysis": {
    "compatible": true,
    "issues": [],
    "recommendations": [
      "Consider upgrading to DDR5-6000 for optimal performance"
    ],
    "confidence": "high"
  }
}
```

### 3. AI Performance Estimation

**Endpoint**: `POST /api/ai-performance-estimate`

**Request**:
```json
{
  "cpu_id": "507f1f77bcf86cd799439011",
  "gpu_id": "507f1f77bcf86cd799439012",
  "ram_id": "507f1f77bcf86cd799439013",
  "games": ["Cyberpunk 2077", "Valorant", "Elden Ring"]
}
```

**Response**:
```json
{
  "status": "success",
  "performance": {
    "benchmarks": [
      {"game": "Cyberpunk 2077", "1080p": 120, "1440p": 85, "4k": 45},
      {"game": "Valorant", "1080p": 400, "1440p": 350, "4k": 200},
      {"game": "Elden Ring", "1080p": 60, "1440p": 60, "4k": 45}
    ],
    "bottleneck": "None",
    "bottleneck_severity": "None",
    "notes": "Excellent 1440p gaming performance"
  }
}
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit your `.env` file:

```env
# AI Provider API Keys (Get free keys from respective websites)
GROQ_API_KEY=your_groq_key_here
MISTRAL_API_KEY=your_mistral_key_here
GEMINI_API_KEY=your_gemini_key_here

# Optional: Local Ollama (for unlimited, offline AI)
OLLAMA_URL=http://localhost:11434
```

### 3. Get Free API Keys

#### Groq (Recommended - Fast & Free)
1. Visit: https://console.groq.com
2. Sign up for free account
3. Generate API key
4. Free tier: 30 requests/minute

#### Mistral AI
1. Visit: https://console.mistral.ai
2. Sign up for free account
3. Generate API key
4. Free tier available

#### Google Gemini
1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Create API key
4. Free tier: 15 requests/minute

### 4. Optional: Install Ollama (Local AI)

For **unlimited, free, offline AI**:

1. Download Ollama: https://ollama.com/download
2. Install and run Ollama
3. Pull a model:
   ```bash
   ollama pull llama3.2
   ```
4. Ollama will run on `http://localhost:11434` by default

**Benefits of Ollama**:
- ✓ Unlimited requests
- ✓ No API costs
- ✓ Works offline
- ✓ Full privacy

**Drawbacks**:
- ✗ Requires ~8GB RAM
- ✗ Slower than cloud APIs
- ✗ Requires local installation

## Testing

Run the test suite to verify everything works:

```bash
python test_ai_engine.py
```

This will test:
- Provider availability
- PC recommendation generation
- Compatibility analysis
- Performance estimation

## Usage in Frontend

### Example: Get AI Recommendation

```javascript
async function getAIRecommendation() {
    const response = await fetch('/api/ai-recommend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            budget: '$1500',
            use_case: 'Gaming and Streaming',
            preferences: {
                brand_preference: 'AMD',
                form_factor: 'ATX'
            }
        })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
        console.log('AI Recommendation:', data.recommendation);
        console.log('Provider used:', data.provider);
        
        // Auto-populate builder with matched components
        if (data.matched_components.cpu_id) {
            document.getElementById('cpu-select').value = data.matched_components.cpu_id;
        }
        // ... populate other components
    }
}
```

### Example: Check Compatibility

```javascript
async function checkCompatibility() {
    const buildData = {
        cpu_id: document.getElementById('cpu-select').value,
        motherboard_id: document.getElementById('motherboard-select').value,
        ram_id: document.getElementById('ram-select').value,
        gpu_id: document.getElementById('gpu-select').value
    };
    
    const response = await fetch('/api/ai-compatibility-check', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(buildData)
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
        const analysis = data.analysis;
        if (analysis.compatible) {
            showSuccess('Build is compatible!');
        } else {
            showWarning('Issues found: ' + analysis.issues.join(', '));
        }
    }
}
```

## Provider Rotation

The AI engine automatically rotates between providers:

1. First request → Groq
2. Second request → Mistral
3. Third request → Gemini
4. Fourth request → Ollama (if available)
5. Fifth request → Back to Groq

If a provider fails, it automatically tries the next one.

## Cost Analysis

### Current Setup (FREE)

| Provider | Cost | Limit | Notes |
|----------|------|-------|-------|
| Groq | $0 | 30 req/min | Fast, reliable |
| Mistral | $0 | Free tier | Good for JSON |
| Gemini | $0 | 15 req/min | Large context |
| Ollama | $0 | Unlimited | Requires local install |

**Total Monthly Cost**: **$0**

### Scalability

With 3 cloud providers rotating:
- **Groq**: 30 req/min = 1,800 req/hour = 43,200 req/day
- **Mistral**: Similar capacity
- **Gemini**: 15 req/min = 900 req/hour = 21,600 req/day

**Combined capacity**: ~100,000+ requests/day **for free**

For unlimited capacity, add Ollama as fallback.

## Troubleshooting

### Issue: All providers failing

**Solution**: Check API keys in `.env` file

```bash
# Verify keys are set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Groq:', bool(os.getenv('GROQ_API_KEY')))"
```

### Issue: Slow responses

**Solution**: 
1. Groq is fastest (usually < 2 seconds)
2. If Groq fails, it falls back to slower providers
3. Install Ollama for consistent local performance

### Issue: JSON parsing errors

**Solution**: The engine automatically handles this with fallbacks. Check logs:

```python
app.logger.error(f"AI recommendation error: {e}")
```

## Advanced Configuration

### Custom Ollama Model

Edit `ai_engine.py`:

```python
payload = {
    "model": "mistral",  # or "llama3", "codellama", etc.
    "prompt": f"{system_prompt}\n\nUser Request: {user_prompt}",
    "stream": False
}
```

### Adjust Temperature

For more creative/varied recommendations:

```python
payload = {
    "temperature": 0.7,  # Higher = more creative, Lower = more consistent
    ...
}
```

### Custom System Prompts

Edit the `_build_system_prompt()` method in `ai_engine.py` to customize AI behavior.

## Best Practices

1. **Always use RAG**: Pass component pool from database to AI
2. **Validate AI output**: Match AI suggestions to actual database components
3. **Cache results**: Store AI recommendations to reduce API calls
4. **Fallback gracefully**: Always have heuristic fallback for critical features
5. **Monitor usage**: Track which provider is used most

## Future Enhancements

- [ ] Add caching layer for common queries
- [ ] Implement rate limiting per provider
- [ ] Add more AI providers (Claude, DeepSeek, etc.)
- [ ] Fine-tune prompts for better accuracy
- [ ] Add user feedback loop to improve recommendations

## Support

For issues or questions:
1. Check logs: `app.logger.error()`
2. Run test suite: `python test_ai_engine.py`
3. Verify API keys are valid
4. Check provider status pages

---

**Built with ❤️ for RigMaster AI**
