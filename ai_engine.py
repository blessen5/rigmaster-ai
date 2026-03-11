"""
AI Engine for RigMaster AI
Supports multiple free AI providers with automatic rotation and fallback
"""
import os
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
try:
    from huggingface_hub import InferenceClient
except ImportError:
    InferenceClient = None # Fallback if not installed

logger = logging.getLogger(__name__)


class AIEngine:
    """
    Multi-provider AI engine with automatic failover and rotation.
    Supports: Groq, Mistral, Google Gemini, and Hugging Face.
    """
    
    def __init__(self):
        # Load API keys from environment
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.mistral_key = os.getenv('MISTRAL_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        self.hf_key = os.getenv('HF_API_KEY')
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.cohere_key = os.getenv('COHERE_API_KEY')
        self.is_hf_installed = InferenceClient is not None
        
        # Provider rotation index
        self.current_provider_index = 0
        
        # Define available providers (in priority order)
        self.providers = []
        # Define available providers (in priority order)
        if self.hf_key:
            self.providers.append('hf')
        if self.groq_key:
            self.providers.append('groq')
        if self.gemini_key:
            self.providers.append('gemini')
        if self.mistral_key:
            self.providers.append('mistral')
        if self.deepseek_key:
            self.providers.append('deepseek')
        if self.openrouter_key:
            self.providers.append('openrouter')
        if self.cohere_key:
            self.providers.append('cohere')


        

        logger.info(f"AI Engine initialized with providers: {self.providers}")

    def update_api_keys(self, keys: Dict[str, str]):
        """Update API keys dynamically from database settings."""
        if keys.get('groq_key'): self.groq_key = keys.get('groq_key')
        if keys.get('mistral_key'): self.mistral_key = keys.get('mistral_key')
        if keys.get('gemini_key'): self.gemini_key = keys.get('gemini_key')
        if keys.get('deepseek_key'): self.deepseek_key = keys.get('deepseek_key')
        if keys.get('hf_key'): self.hf_key = keys.get('hf_key')
        if keys.get('openrouter_key'): self.openrouter_key = keys.get('openrouter_key')
        if keys.get('cohere_key'): self.cohere_key = keys.get('cohere_key')
        
        # Rebuild providers list
        self.providers = []
        if self.hf_key: self.providers.append('hf')
        if self.groq_key: self.providers.append('groq')
        if self.gemini_key: self.providers.append('gemini')
        if self.mistral_key: self.providers.append('mistral')
        if self.deepseek_key: self.providers.append('deepseek')
        if self.openrouter_key: self.providers.append('openrouter')
        if self.cohere_key: self.providers.append('cohere')
        
        # Reset provider index if it's out of bounds
        if self.providers and self.current_provider_index >= len(self.providers):
            self.current_provider_index = 0
            
        logger.info(f"AI Engine providers updated: {self.providers}")
    
    def get_pc_recommendation(
        self, 
        budget: str, 
        use_case: str, 
        preferences: Optional[Dict] = None,
        component_pool: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get AI-powered PC build recommendation.
        
        Args:
            budget: Budget string (e.g., "$1200")
            use_case: Use case description (e.g., "Gaming and Streaming")
            preferences: Optional dict with brand preferences, form factor, etc.
            component_pool: Optional dict with available components from database
            
        Returns:
            Dict with recommended components and reasoning
        """
        # Build the prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_recommendation_prompt(budget, use_case, preferences, component_pool)
        
        # Try providers in priority order
        providers = self._get_prioritized_providers()
        
        for provider in providers:
            try:
                logger.info(f"Attempting AI recommendation with provider: {provider}")
                response = self._call_provider(provider, system_prompt, user_prompt)
                
                if response:
                    # Parse and validate response
                    result = self._parse_recommendation_response(response)
                    if result:
                        result['provider_used'] = provider
                        return result
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                continue
        
        # All AI providers failed — return None so the caller uses real DB data instead
        logger.warning("All AI providers failed. Returning None so app.py selects from DB pool.")
        return None
    
    def analyze_compatibility(
        self, 
        cpu_name: str, 
        motherboard_name: str, 
        ram_name: str,
        other_components: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Use AI to analyze hardware compatibility and provide insights.
        """
        system_prompt = """You are a PC hardware compatibility expert.
Analyze the given components and identify any compatibility issues.
Return ONLY valid JSON with this structure:
{
    "compatible": true/false,
    "issues": ["list of issues if any"],
    "recommendations": ["list of recommendations"],
    "confidence": "high/medium/low"
}"""
        
        user_prompt = f"""Analyze compatibility:
CPU: {cpu_name}
Motherboard: {motherboard_name}
RAM: {ram_name}"""
        
        if other_components:
            for key, value in other_components.items():
                user_prompt += f"\n{key}: {value}"
        
        # Try providers
        providers = self._get_prioritized_providers()
        for provider in providers:
            try:
                response = self._call_provider(provider, system_prompt, user_prompt, json_mode=True)
                if response:
                    return json.loads(response)
            except Exception as e:
                logger.warning(f"Compatibility analysis failed with {provider}: {e}")
                continue
        
        return {
            "compatible": None,
            "issues": ["AI analysis unavailable"],
            "recommendations": [],
            "confidence": "low"
        }
    
    def estimate_performance(
        self,
        cpu_name: str,
        gpu_name: str,
        ram_name: str,
        games: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Estimate gaming/workload performance using AI.
        """
        if not games:
            games = ["Cyberpunk 2077", "Valorant", "Elden Ring", "COD: Warzone"]
        
        system_prompt = """You are a PC performance analysis expert.
Estimate FPS for the given hardware configuration.
Return ONLY valid JSON with this structure:
{
    "benchmarks": [
        {"game": "Game Name", "1080p": 120, "1440p": 90, "4k": 45}
    ],
    "bottleneck": "CPU/GPU/None",
    "bottleneck_severity": "None/Minor/Moderate/Severe",
    "notes": "Brief analysis"
}"""
        
        user_prompt = f"""Estimate performance for:
CPU: {cpu_name}
GPU: {gpu_name}
RAM: {ram_name}
Games: {', '.join(games)}

Provide realistic FPS estimates based on current benchmarks."""
        
        # Try providers
        providers = self._get_prioritized_providers()
        for provider in providers:
            try:
                response = self._call_provider(provider, system_prompt, user_prompt, json_mode=True)
                if response:
                    return json.loads(response)
            except Exception as e:
                logger.warning(f"Performance estimation failed with {provider}: {e}")
                continue
        
        return self._heuristic_performance_fallback(gpu_name)

    def generate_chat_response(self, system_role: str, user_message: str) -> Optional[str]:
        """
        Generate a conversational response for the AI assistant.
        """
        # Try providers in order
        providers = self._get_prioritized_providers()
        
        for provider in providers:
            try:
                logger.debug(f"Attempting AI chat response with provider: {provider}")
                # For chat, we don't necessarily want JSON mode
                response = self._call_provider(provider, system_role, user_message, json_mode=False)
                if response:
                    return response
            except Exception as e:
                logger.warning(f"Provider {provider} failed during chat: {e}")
                continue
        
        return "I'm sorry, I'm currently having trouble connecting to my AI core. Please try again in a moment."

    def get_resale_prediction(self, component_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict resale value for PC components.
        """
        schema = {
            "total_system_value": "$XXXX",
            "market_advice": "Detailed advice...",
            "components": [{"category": "CPU", "name": "Name", "status": "Active", "estimated_resale": "$XXX"}]
        }
        
        system_prompt = f"""You are a hardware market analyst. 
Estimate current used market prices in USD.
Respond ONLY in JSON with this schema: {json.dumps(schema)}"""
        
        user_prompt = "Build Components:\n" + "\n".join([f"- {c.get('category')}: {c.get('name')} (Status: {c.get('status')})" for c in component_data])
        
        providers = self._get_prioritized_providers()
        for provider in providers:
            try:
                response = self._call_provider(provider, system_prompt, user_prompt, json_mode=True)
                if response:
                    return json.loads(response)
            except Exception as e:
                logger.warning(f"Resale prediction failed with {provider}: {e}")
                continue
        
        # Heuristic fallback for resale will be handled in app.py or here
        return None

    def analyze_build(self, budget: float, usage: str, requirements: str, components_summary: Dict[str, Any]) -> str:
        """
        Deep analysis for a build request (DeepSeek-style).
        """
        system_prompt = """You are a PC system analyst. 
Analyze the budget and components, explain trade-offs and compatibility. 
Explain in simple, educational language."""
        
        user_prompt = f"""Budget: ${budget}
Use: {usage}
Requirements: {requirements}
Available: {json.dumps(components_summary)}
Provide analysis on allocation, priority, and expectations."""
        
        providers = self._get_prioritized_providers()
        for provider in providers:
            try:
                response = self._call_provider(provider, system_prompt, user_prompt, json_mode=False)
                if response:
                    return response
            except Exception as e:
                logger.warning(f"Build analysis failed with {provider}: {e}")
                continue
        
        return "AI analysis temporarily unavailable. Focus on balanced performance between CPU and GPU."

    def simulate_upgrade(self, original_resolved: Dict[str, Any], simulated_resolved: Dict[str, Any]) -> str:
        """
        Simulate and analyze a hardware upgrade.
        """
        system_role = """You are the RigMaster AI What-If Simulator. 
Analyze performance differences between original and proposed builds.
Use Markdown formatting, headers, tables for comparisons, and bold key metrics."""
        
        user_content = f"Original Build: {json.dumps(original_resolved)}\n\nProposed Build: {json.dumps(simulated_resolved)}\n\nAnalyze impact."
        
        providers = self._get_prioritized_providers()
        for provider in providers:
            try:
                response = self._call_provider(provider, system_role, user_content, json_mode=False)
                if response:
                    return response
            except Exception as e:
                logger.warning(f"Upgrade simulation failed with {provider}: {e}")
                continue
                
        return "### Upgrade Analysis\nThe proposed upgrade improves system capability. Ensure your PSU can handle the new power requirements."

    def enrich_component_specs(self, category: str, name: str) -> Dict[str, Any]:
        """
        Use AI to infer missing technical specifications from a component name.
        """
        schemas = {
            "cpu": {"brand": "Intel/AMD", "socket": "Socket Name", "cores": 8, "threads": 16, "base_clock": "X.X GHz", "tdp": "XXW"},
            "gpu": {"brand": "NVIDIA/AMD/Intel", "vram": "XGB GDDR6", "tdp": "XXW", "chipset": "Specific Chipset"},
            "motherboard": {"brand": "ASUS/MSI/etc", "socket": "Socket Name", "chipset": "Chipset Name", "ram_type": "DDR4/DDR5"},
            "ram": {"brand": "Corsair/G.Skill/etc", "capacity": "XGB", "type": "DDR4/DDR5", "speed": "XXXX MHz"},
            "storage": {"brand": "Samsung/WD/etc", "capacity": "XGB/XTB", "type": "NVMe SSD/SATA SSD"},
            "psu": {"brand": "EVGA/Corsair/etc", "wattage": "XXXW", "efficiency": "80+ Gold/etc"},
            "case": {"brand": "NZXT/Fractal/etc", "form_factor": "Mid Tower/etc"},
            "cooler": {"brand": "Noctua/Arctic/etc", "type": "Air/Liquid"}
        }
        
        target_schema = schemas.get(category, {"brand": "Manufacturer Name"})
        
        system_prompt = f"""You are a PC hardware database specialist. 
Provide the missing technical specifications for the exact component based on its name.
CRITICAL: Only provide GENUINE, FACTUAL data. If you are unsure about a specific detail (like the exact TDP or socket), do not guess; return "Unknown".
Return ONLY valid JSON with this schema: {json.dumps(target_schema)}"""
        
        user_prompt = f"Category: {category}\nComponent Name: {name}"
        
        # We'll use prioritized providers
        providers = self._get_prioritized_providers()
        for provider in providers:
            try:
                response = self._call_provider(provider, system_prompt, user_prompt, json_mode=True)
                if response:
                    # Clean markdown code blocks if present
                    clean_res = response.strip()
                    if clean_res.startswith("```"):
                        lines = clean_res.split('\n')
                        if lines[0].startswith("```"): lines = lines[1:]
                        if lines and lines[-1].strip().startswith("```"): lines = lines[:-1]
                        clean_res = "\n".join(lines).strip()
                    
                    return json.loads(clean_res)
            except Exception as e:
                logger.warning(f"Specification enrichment failed with {provider}: {e}")
                continue
        
        return {}

    def get_build_blueprint(self, components: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate a factual hardware blueprint and expansion map.
        Focuses on connectivity, ports, and expansion slots.
        """
        system_prompt = """You are a PC hardware technician. 
Provide a FACTUAL connectivity and expansion inventory for the given components.
Focus on:
1. Rear I/O Ports (USB, Video)
2. Storage Expansion (M.2 slots, SATA)
3. Internal Headers (USB-C, RGB)
4. Fitment (GPU Length approx, Case capacity)

Return ONLY valid JSON with this structure:
{
    "rear_io": ["List of likely ports"],
    "expansion": {
        "m2_total": 3,
        "sata_total": 4,
        "ram_slots": 4
    },
    "internal_connectivity": ["USB-C Header availability", "PWM Fan headers approx"],
    "fitment_check": "Detailed note on GPU length vs Case fitment",
    "build_order_hint": "One key tip for assembling this specific set"
}"""
        
        user_prompt = f"Components:\n" + "\n".join([f"- {k}: {v}" for k, v in components.items()])
        
        providers = self._get_prioritized_providers()
        for provider in providers:
            try:
                response = self._call_provider(provider, system_prompt, user_prompt, json_mode=True)
                if response:
                    # Clean markdown code blocks if present
                    clean_res = response.strip()
                    if clean_res.startswith("```"):
                        # Extract content between first and last ```
                        lines = clean_res.split('\n')
                        if lines[0].startswith("```"): lines = lines[1:]
                        if lines and lines[-1].strip().startswith("```"): lines = lines[:-1]
                        clean_res = "\n".join(lines).strip()
                    
                    return json.loads(clean_res)
            except Exception as e:
                logger.warning(f"Blueprint generation failed with {provider}: {e}")
                continue
        
        return {
            "rear_io": ["I/O data unavailable"],
            "expansion": {"m2_total": "Unknown", "sata_total": "Unknown", "ram_slots": 4},
            "internal_connectivity": ["Header data unavailable"],
            "fitment_check": "Standard ATX fitment expected.",
            "build_order_hint": "Install CPU and RAM before mounting in case."
        }

    def _get_prioritized_providers(self) -> List[Any]:
        """Get providers list with the preferred one at the front (if set)."""
        providers = self.providers.copy()
        pref = getattr(self, 'preferred_provider', 'auto')
        
        if pref != 'auto' and pref in providers:
            # Move preferred to front
            providers.remove(pref)
            providers.insert(0, pref)
        elif pref == 'auto' and len(providers) > 0:
            # Rotate for 'auto' mode
            idx = self.current_provider_index
            rotated = providers[idx:] + providers[:idx]
            # Update index for next time
            self.current_provider_index = (self.current_provider_index + 1) % len(providers)
            return rotated
            
        return providers

    def _get_next_provider(self) -> str:
        """DEPRECATED: Use _get_prioritized_providers for more robust fallback."""
        providers = self._get_prioritized_providers()
        return providers[0] if providers else None

    
    def _call_provider(
        self, 
        provider: str, 
        system_prompt: str, 
        user_prompt: str,
        json_mode: bool = True
    ) -> Optional[str]:
        """
        Call specific AI provider.
        """
        if provider == 'groq':
            return self._call_groq(system_prompt, user_prompt, json_mode)
        elif provider == 'deepseek':
            return self._call_deepseek(system_prompt, user_prompt, json_mode)
        elif provider == 'mistral':
            return self._call_mistral(system_prompt, user_prompt, json_mode)
        elif provider == 'gemini':
            return self._call_gemini(system_prompt, user_prompt, json_mode)
        elif provider == 'hf':
            return self._call_hf(system_prompt, user_prompt, json_mode)
        return None
    
    def _call_groq(self, system_prompt: str, user_prompt: str, json_mode: bool) -> Optional[str]:
        """Call Groq API (Fast, Free tier: 30 req/min)."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",  # High-performance recommendation


            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2048
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def _call_deepseek(self, system_prompt: str, user_prompt: str, json_mode: bool) -> Optional[str]:
        """Call DeepSeek API."""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.deepseek_key}",
            "Content-Type": "application/json"
        }
        
        # Use reasoner for non-JSON, chat for JSON-mode (better compatibility)
        model = "deepseek-chat" if json_mode else "deepseek-reasoner"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            logger.info(f"Calling DeepSeek with model: {model}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    def _call_mistral(self, system_prompt: str, user_prompt: str, json_mode: bool) -> Optional[str]:
        """Call Mistral API (Free tier available)."""
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.mistral_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistral-small-latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2048
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise
    
    def _call_gemini(self, system_prompt: str, user_prompt: str, json_mode: bool) -> Optional[str]:
        """Call Google Gemini API (Free tier: 15 req/min)."""
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=self.gemini_key)
        
        # Combine prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=2048,
        )
        
        if json_mode:
            config.response_mime_type = "application/json"
        
        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash', # Updated to stable version
                contents=full_prompt,
                config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    


    def _call_hf(self, system_prompt: str, user_prompt: str, json_mode: bool) -> Optional[str]:
        """Call Hugging Face Inference API via huggingface_hub."""
        if not InferenceClient:
            logger.warning("huggingface_hub library not installed. Skipping HF provider.")
            return None
            
        # Using a popular open-source model available on the free tier
        # Mistral-7B-v0.3 is more widely supported on modern inference providers
        model = "mistralai/Mistral-7B-Instruct-v0.3"
        
        try:
            client = InferenceClient(token=self.hf_key)
            logger.info(f"Calling Hugging Face with model: {model}")
            
            # Use chat_completion or normal completion based on model compatibility
            # Gemma 2 works best with the chat template
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            completion = client.chat_completion(
                messages, 
                model=model, 
                max_tokens=2048,
                temperature=0.3
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"Hugging Face API error (Model: {model}): {e}")
            return None
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for PC recommendation."""
        return """You are an expert PC hardware architect. Your goal is to design a complete, high-performance build within the user's budget using ONLY the provided hardware list.

Return ONLY a valid JSON object. No conversational text.

CRITICAL RULES:
1. BUDGET LOCK: The 'estimated_total' MUST NOT exceed the target budget.
2. COMPLETE BUILD: You MUST select ALL 16 component slots listed below. Every slot must have a value from the provided pool.
3. IDs REQUIRED: Always use the format "ID:<24-char-hex>|Component Name" from the pool.
4. SELECTION: Use ONLY components from the 'Available Components' list. Ensure compatibility.
5. FORMAT: Strict JSON only. No markdown, no code blocks.

JSON STRUCTURE (all 16 fields required):
{
    "cpu": "ID:69...|Component Name",
    "gpu": "ID:69...|Component Name",
    "motherboard": "ID:69...|Component Name",
    "ram": "ID:69...|Component Name",
    "storage": "ID:69...|Component Name",
    "psu": "ID:69...|Component Name",
    "case": "ID:69...|Component Name",
    "cooler": "ID:69...|Component Name",
    "monitor": "ID:69...|Component Name",
    "os": "ID:69...|Component Name",
    "fans": "ID:69...|Component Name",
    "keyboard": "ID:69...|Component Name",
    "mouse": "ID:69...|Component Name",
    "headset": "ID:69...|Component Name",
    "webcam": "ID:69...|Component Name",
    "peripherals": "ID:69...|Component Name",
    "estimated_total": 1500,
    "reasoning": "Markdown explanation of choices and budget allocation.",
    "performance_notes": "Expected FPS/Benchmarks"
}

Select ALL slots. Allocate budget proportionally across all 16 components."""

    
    def _build_recommendation_prompt(
        self, 
        budget: str, 
        use_case: str, 
        preferences: Optional[Dict],
        component_pool: Optional[Dict]
    ) -> str:
        """Build user prompt for recommendation."""
        prompt = f"""Build a PC with the following requirements:

Budget: {budget}
Use Case: {use_case}"""
        
        if preferences:
            prompt += "\n\nPreferences:"
            for key, value in preferences.items():
                prompt += f"\n- {key}: {value}"
        
        if component_pool:
            prompt += "\n\nCRITICAL: You MUST select components ONLY from the following lists. Do NOT suggest anything from your general knowledge that isn't here:"
            for category, items in component_pool.items():
                if items and len(items) > 0:
                    prompt += f"\n{category}: {', '.join(items[:35])}"  # Increased limit for better selection
        
        return prompt
    
    def _parse_recommendation_response(self, response: str) -> Optional[Dict]:
        """Parse and validate AI recommendation response."""
        try:
            # Strip markdown code fences if the model wrapped JSON in ```
            clean = response.strip()
            if clean.startswith('```'):
                lines = clean.split('\n')
                lines = [l for l in lines if not l.strip().startswith('```')]
                clean = '\n'.join(lines).strip()

            data = json.loads(clean)

            # Accept any response that has at least one recognised component key
            component_keys = [
                'cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu',
                'case', 'cooler', 'monitor', 'os', 'fans',
                'keyboard', 'mouse', 'headset', 'webcam', 'peripherals'
            ]
            found = [k for k in component_keys if k in data]
            if not found:
                logger.warning("AI response has no recognisable component keys")
                return None

            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}\nRaw: {response[:300]}")
            return None
    
        base_rec = {
            'cpu': 'AMD Ryzen 5 5600' if budget_num < 1000 else 'AMD Ryzen 7 7800X3D',
            'gpu': 'NVIDIA RTX 4060' if budget_num < 1000 else 'NVIDIA RTX 4080',
            'motherboard': 'B550 ATX' if budget_num < 1000 else 'X670 ATX',
            'ram': '16GB DDR4-3200' if budget_num < 1000 else '32GB DDR5-6000',
            'storage': '1TB NVMe SSD',
            'psu': '650W 80+ Bronze' if budget_num < 1000 else '850W 80+ Gold',
            'case': 'Mid-Tower ATX Case',
            'cooler': 'Stock Cooler' if budget_num < 1000 else '360mm AIO Liquid Cooler',
            'monitor': '24" 1080p 144Hz Monitor',
            'os': 'Windows 11 Home',
            'fans': '3x 120mm Case Fans',
            'keyboard': 'Mechanical Gaming Keyboard',
            'mouse': 'Optical Gaming Mouse',
            'headset': 'Gaming Headset with Mic',
            'webcam': '1080p HD Webcam',
            'peripherals': 'Misc Cable Management Kit',
            'estimated_total': f"${budget_num}",
            'reasoning': f"Heuristic selection for {use_case} build.",
            'performance_notes': "Solid performance for target use case."
        }
        
        # Customize based on tier
        if tier == 'high_end_gaming':
            base_rec.update({
                'cpu': 'AMD Ryzen 7 7800X3D',
                'gpu': 'NVIDIA RTX 4080 Super',
                'storage': '2TB NVMe Gen4 SSD',
                'monitor': '27" 1440p 240Hz Gaming Monitor'
            })
        elif tier == 'budget_gaming':
            base_rec.update({
                'cpu': 'Intel Core i3-12100F',
                'gpu': 'NVIDIA RTX 3060 12GB',
                'monitor': '24" 1080p 75Hz Monitor'
            })
        
        result = base_rec
        result['fallback'] = True
        return result
    
    def _heuristic_performance_fallback(self, gpu_name: str) -> Dict[str, Any]:
        """Heuristic performance estimation fallback."""
        gpu_upper = gpu_name.upper()
        
        # Determine multiplier based on GPU
        multiplier = 1.0
        if '4090' in gpu_upper:
            multiplier = 3.0
        elif '4080' in gpu_upper or '7900 XTX' in gpu_upper:
            multiplier = 2.5
        elif '4070' in gpu_upper or '7800 XT' in gpu_upper:
            multiplier = 1.8
        elif '4060' in gpu_upper or '7600' in gpu_upper:
            multiplier = 1.2
        elif '3060' in gpu_upper or '6600' in gpu_upper:
            multiplier = 1.0
        else:
            multiplier = 0.8
        
        return {
            "benchmarks": [
                {"game": "Cyberpunk 2077", "1080p": int(75 * multiplier), "1440p": int(50 * multiplier), "4k": int(25 * multiplier)},
                {"game": "Valorant", "1080p": int(300 * multiplier), "1440p": int(250 * multiplier), "4k": int(150 * multiplier)},
                {"game": "Elden Ring", "1080p": min(60, int(60 * multiplier)), "1440p": int(50 * multiplier), "4k": int(30 * multiplier)},
                {"game": "COD: Warzone", "1080p": int(100 * multiplier), "1440p": int(75 * multiplier), "4k": int(40 * multiplier)}
            ],
            "bottleneck": "None",
            "bottleneck_severity": "None",
            "notes": "Estimated performance based on GPU tier (AI unavailable)"
        }


# Global instance
_ai_engine = None

def get_ai_engine() -> AIEngine:
    """Get or create global AI engine instance."""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngine()
    return _ai_engine
