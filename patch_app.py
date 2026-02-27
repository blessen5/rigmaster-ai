
import os

path = r"c:\Users\bless\AppData\Local\Temp\antigravity_rigmaster_ui_app.py" # Placeholder, I'll use the real path
path = r"c:\Users\bless\.gemini\antigravity\scratch\rigmaster-ui\app.py"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Section 1: api_ai_recommend (/api/ai-recommend)
# We already replaced the providers list, so we are looking for the loop starting after ai_engine = get_ai_engine()
start_rec = -1
end_rec = -1
for i, line in enumerate(lines):
    if "ai_engine = get_ai_engine()" in line and i > 1580 and i < 1620:
        start_rec = i + 1
    if "continue" in line and i > 1680 and i < 1700:
        # Looking for the 'continue' at the end of the provider loop
        if "app.logger.warning" in lines[i-1]:
            end_rec = i + 1
            break

if start_rec != -1 and end_rec != -1:
    new_rec_code = [
        "        # Prepare sample pool for AI Engine (mapping IDs to names)\n",
        "        engine_pool = {}\n",
        "        for cat_key, items in sample_data.items():\n",
        "            engine_pool[cat_key.lower()] = [f\"ID:{i['_id']}|{i['name']}\" for i in items[:25]]\n\n",
        "        recommendation = ai_engine.get_pc_recommendation(\n",
        "            budget=f\"${int(budget)}\",\n",
        "            use_case=usage,\n",
        "            preferences={\"requirements\": requirements},\n",
        "            component_pool=engine_pool\n",
        "        )\n\n",
        "        if recommendation:\n",
        "            result = {\n",
        "                'build': {},\n",
        "                'total_estimated_cost': budget,\n",
        "                'explanation': recommendation.get('reasoning', ''),\n",
        "                'provider': 'RigMaster Engine'\n",
        "            }\n\n",
        "            id_mapping = {'cpu': 'CPU', 'gpu': 'GPU', 'motherboard': 'Motherboard', 'ram': 'RAM', 'storage': 'Storage', 'psu': 'PSU', 'case': 'Case', 'cooler': 'Cooler'}\n",
        "            for ai_key, target_key in id_mapping.items():\n",
        "                val = str(recommendation.get(ai_key, ''))\n",
        "                import re\n",
        "                id_match = re.search(r'ID:([0-9a-fA-F]{24})', val)\n",
        "                if id_match:\n",
        "                    result['build'][target_key] = id_match.group(1)\n",
        "                else:\n",
        "                    cat_name = target_key + 's' if target_key != 'PSU' else 'PSU'\n",
        "                    cat_name = next((k for k in sample_data.keys() if k.lower() == cat_name.lower()), cat_name)\n",
        "                    for item in sample_data.get(cat_name, []):\n",
        "                        if val.upper() in str(item['name']).upper() or str(item['name']).upper() in val.upper():\n",
        "                            result['build'][target_key] = str(item['_id'])\n",
        "                            break\n",
        "                    if target_key not in result['build']: result['build'][target_key] = val\n"
    ]
    lines[start_rec:end_rec] = new_rec_code

# Section 2: ai_assistant (/ai-assistant)
# Replacing providers list and loop
start_asst = -1
end_asst = -1
for i, line in enumerate(lines):
    if "providers = [" in line and i > 1900 and i < 1960:
        start_asst = i
    if "continue" in line and i > 2100 and i < 2200:
        if "app.logger.warning" in lines[i-1]:
            end_asst = i + 1
            break

if start_asst != -1 and end_asst != -1:
    new_asst_code = [
        "        # Use unified AI Engine for chat\n",
        "        ai_engine = get_ai_engine()\n",
        "        ai_response = ai_engine.generate_chat_response(system_role, user_message)\n",
        "        provider_used = 'RigMaster AI Assistant'\n\n",
        "        if ai_response:\n",
        "            return jsonify({\n",
        "                'status': 'success',\n",
        "                'response': ai_response,\n",
        "                'provider': provider_used\n",
        "            })\n"
    ]
    lines[start_asst:end_asst] = new_asst_code

# Section 3: api_performance_analysis (/api/performance-analysis)
start_perf = -1
end_perf = -1
for i, line in enumerate(lines):
    if "providers = [" in line and i > 2500 and i < 2650:
        start_perf = i
    if "continue" in line and i > 2700 and i < 2850:
        if "app.logger.warning" in lines[i-1]:
            end_perf = i + 1
            break

if start_perf != -1 and end_perf != -1:
    new_perf_code = [
        "        # Unified AI Engine for performance analysis\n",
        "        ai_engine = get_ai_engine()\n",
        "        res_pkg = ai_engine.estimate_performance(\n",
        "            cpu_name=comp_context['CPU']['name'],\n",
        "            gpu_name=comp_context['GPU']['name'],\n",
        "            ram_name=comp_context['RAM']\n",
        "        )\n\n",
        "        if res_pkg:\n",
        "            result = res_pkg\n",
        "            result['provider'] = 'RigMaster Engine'\n"
    ]
    lines[start_perf:end_perf] = new_perf_code

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Patch applied successfully!")
