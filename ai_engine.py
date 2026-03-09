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
        
        # All providers failed - return heuristic fallback
        logger.warning("All AI providers failed, using heuristic fallback")
        return self._heuristic_fallback(budget, use_case)
    
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
        model = "mistralai/Mistral-7B-Instruct-v0.2"
        
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
        return """You are an expert PC hardware architect. Your goal is to design a high-performance build within the user's budget using ONLY the provided hardware list.

Return ONLY a valid JSON object. No conversational text.

CRITICAL RULES:
1. BUDGET LOCK: The 'estimated_total' MUST NOT exceed the target budget. It should be between 95% and 100% of the budget.
2. SACRIFICE PERFORMANCE FOR BUDGET: If you cannot hit the budget target with high-tier parts, you MUST drop to a lower-tier part (e.g. drop from i9 to i7, or 4080 to 4070).
3. PRICE MATH: Every item in your JSON must include the price from the pool. Sum them exactly.
4. SELECTION: Use components from the 'Available Components' list provided. Ensure they are compatible.
5. FORMAT: Strict JSON only.

JSON STRUCTURE:
{
    "cpu": "ID:69...|Component Name",
    "gpu": "ID:69...|Component Name",
    "motherboard": "ID:69...|Component Name",
    "ram": "ID:69...|Component Name",
    "storage": "ID:69...|Component Name",
    "psu": "ID:69...|Component Name",
    "case": "ID:69...|Component Name",
    "cooler": "ID:69...|Component Name",
    "estimated_total": 1500,
    "reasoning": "Markdown explanation of why these parts were chosen for this specific budget (emphasize why high-tier parts were selected to hit the budget).",
    "performance_notes": "Expected FPS/Benchmarks"
}

Ensure all components (including Case and Cooler) are selected to create a complete, ready-to-build system."""
    
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
            data = json.loads(response)
            
            # Validate required fields
            required_fields = ['cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return None
            
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return None
    
    def _heuristic_fallback(self, budget: str, use_case: str) -> Dict[str, Any]:
        """Heuristic fallback when all AI providers fail."""
        # Extract numeric budget
        import re
        budget_match = re.search(r'(\d+)', budget.replace(',', ''))
        budget_num = int(budget_match.group(1)) if budget_match else 1000
        
        # Simple rule-based recommendation
        use_case_lower = use_case.lower()
        
        if 'gaming' in use_case_lower or 'stream' in use_case_lower:
            if budget_num >= 2000:
                tier = 'high_end_gaming'
            elif budget_num >= 1200:
                tier = 'mid_gaming'
            else:
                tier = 'budget_gaming'
        elif 'workstation' in use_case_lower or 'editing' in use_case_lower:
            tier = 'workstation'
        else:
            tier = 'general'
        
        recommendations = {
            'high_end_gaming': {
                'cpu': 'AMD Ryzen 7 7800X3D or Intel Core i7-14700K',
                'gpu': 'NVIDIA RTX 4080 or AMD RX 7900 XTX',
                'motherboard': 'B650 or Z790 ATX',
                'ram': '32GB DDR5-6000',
                'storage': '2TB NVMe Gen4 SSD',
                'psu': '850W 80+ Gold',
                'case': 'Mid-Tower with good airflow',
                'cooler': '280mm AIO or high-end air cooler',
                'estimated_total': '$2000-2500',
                'reasoning': 'High-end gaming build for 1440p/4K gaming',
                'performance_notes': '144+ FPS at 1440p, 60+ FPS at 4K in AAA games'
            },
            'mid_gaming': {
                'cpu': 'AMD Ryzen 5 7600X or Intel Core i5-13600K',
                'gpu': 'NVIDIA RTX 4070 or AMD RX 7800 XT',
                'motherboard': 'B650 or B760 ATX',
                'ram': '16GB DDR5-5600 or 32GB DDR4-3200',
                'storage': '1TB NVMe Gen4 SSD',
                'psu': '650W 80+ Gold',
                'case': 'Mid-Tower ATX',
                'cooler': 'Tower air cooler or 240mm AIO',
                'estimated_total': '$1200-1500',
                'reasoning': 'Balanced gaming build for 1080p/1440p',
                'performance_notes': '100+ FPS at 1080p, 60+ FPS at 1440p in most games'
            },
            'budget_gaming': {
                'cpu': 'AMD Ryzen 5 5600 or Intel Core i3-12100F',
                'gpu': 'NVIDIA RTX 4060 or AMD RX 7600',
                'motherboard': 'B550 or B660 mATX',
                'ram': '16GB DDR4-3200',
                'storage': '500GB NVMe SSD',
                'psu': '550W 80+ Bronze',
                'case': 'Budget Mid-Tower',
                'cooler': 'Stock or budget tower cooler',
                'estimated_total': '$700-900',
                'reasoning': 'Budget-friendly 1080p gaming build',
                'performance_notes': '60+ FPS at 1080p in most games'
            },
            'workstation': {
                'cpu': 'AMD Ryzen 9 7950X or Intel Core i9-14900K',
                'gpu': 'NVIDIA RTX 4070 or AMD RX 7800 XT',
                'motherboard': 'X670 or Z790 ATX',
                'ram': '64GB DDR5-5600',
                'storage': '2TB NVMe Gen4 SSD',
                'psu': '850W 80+ Gold',
                'case': 'Full-Tower with excellent airflow',
                'cooler': '360mm AIO',
                'estimated_total': '$2500-3000',
                'reasoning': 'Professional workstation for content creation',
                'performance_notes': 'Excellent for video editing, 3D rendering, and multitasking'
            },
            'general': {
                'cpu': 'AMD Ryzen 5 5600 or Intel Core i5-12400',
                'gpu': 'Integrated or GTX 1650',
                'motherboard': 'B550 or B660 mATX',
                'ram': '16GB DDR4-3200',
                'storage': '512GB NVMe SSD',
                'psu': '500W 80+ Bronze',
                'case': 'Compact mATX case',
                'cooler': 'Stock cooler',
                'estimated_total': '$600-800',
                'reasoning': 'General purpose PC for productivity and light gaming',
                'performance_notes': 'Suitable for office work, web browsing, and casual gaming'
            }
        }
        
        result = recommendations.get(tier, recommendations['general'])
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
