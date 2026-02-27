
import os
import re

path = r"c:\Users\bless\.gemini\antigravity\scratch\rigmaster-ui\app.py"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Section 2: ai_assistant (/ai-assistant)
# Find the start of the providers list and the end of the rotation loop
# Look for: providers = [ ... for p_name, p_key in providers: ... continue ... ]
asst_pattern = r'providers = \[\s+.*?os\.getenv\(\'GROQ_API_KEY\'\).*?\].*?for p_name, p_key in providers:.*?app\.logger\.warning\(f"AI Assistant provider {p_name} failed: {e}"\)\s+continue'
asst_replacement = """# Use unified AI Engine for chat
        ai_engine = get_ai_engine()
        ai_response = ai_engine.generate_chat_response(system_role, user_message)
        provider_used = 'RigMaster AI Assistant'

        if ai_response:
            return jsonify({
                'status': 'success',
                'response': ai_response,
                'provider': provider_used
            })"""

# Section 3: api_performance_analysis (/api/performance-analysis)
perf_pattern = r'providers = \[\s+.*?os\.getenv\(\'GROQ_API_KEY\'\).*?\].*?for p_name, p_key in providers:.*?app\.logger\.warning\(f"Performance Analysis provider {p_name} failed: {e}"\)\s+continue'
perf_replacement = """# Unified AI Engine for performance analysis
        ai_engine = get_ai_engine()
        res_pkg = ai_engine.estimate_performance(
            cpu_name=comp_context['CPU']['name'],
            gpu_name=comp_context['GPU']['name'],
            ram_name=comp_context['RAM']
        )

        if res_pkg:
            result = res_pkg
            result['provider'] = 'RigMaster Engine'"""

# Apply Section 2
content = re.sub(asst_pattern, asst_replacement, content, flags=re.DOTALL)

# Apply Section 3
content = re.sub(perf_pattern, perf_replacement, content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Regex patch applied!")
