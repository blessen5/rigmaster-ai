from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

def test_resale():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['rigmaster']
    
    build = db.saved_builds.find_one()
    if not build:
        print("No builds found")
        return

    print(f"Testing build: {build['_id']}")
    
    col_map = {
        'cpu_id': 'cpus', 'gpu_id': 'gpus', 'motherboard_id': 'motherboards',
        'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
        'case_id': 'cases', 'cooler_id': 'coolers'
    }
    
    component_data = []
    for key, col in col_map.items():
        cid = build.get(key)
        if cid and cid != "None Selected":
            try:
                item = db[col].find_one({'_id': ObjectId(cid)})
                if item:
                    component_data.append({
                        'category': key.replace('_id', '').upper(),
                        'name': item.get('name'),
                        'status': item.get('status', 'Active')
                    })
            except:
                pass

    print(f"Components count: {len(component_data)}")

    schema = {
        "total_system_value": "$XXXX",
        "market_advice": "Detailed advice on selling...",
        "components": [
            {
                "category": "CPU",
                "name": "Component Name",
                "status": "Active/Deprecated",
                "estimated_resale": "$XXX"
            }
        ]
    }

    system_role = (
        "You are a PC Hardware Resale Expert. Analyze the provided PC components and their lifecycle status. "
        "Estimate current 'Used Market Price' for each component in USD. "
        f"Respond ONLY in JSON with this exact schema: {json.dumps(schema)}"
    )
    user_content = "Build Components:\n" + "\n".join([f"- {c['category']}: {c['name']} (Status: {c['status']})" for c in component_data])

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("GEMINI_API_KEY not found")
        return

    try:
        client_ai = genai.Client(api_key=api_key)
        resp = client_ai.models.generate_content(
            model='gemini-2.0-flash-exp', 
            contents=f"{system_role}\n\n{user_content}", 
            config={'response_mime_type': 'application/json'}
        )
        
        raw_text = resp.text
        data = json.loads(raw_text)
        
        findings = {
            "raw_response": raw_text,
            "parsed": data,
            "validation": {
                "has_total": 'total_system_value' in data,
                "has_advice": 'market_advice' in data,
                "has_components": 'components' in data,
                "component_count": len(data.get('components', [])),
                "first_component_has_resale": len(data.get('components', [])) > 0 and 'estimated_resale' in data['components'][0]
            }
        }
        with open('resale_test_findings.json', 'w') as f:
            json.dump(findings, f, indent=2)
            
        print("Success! Findings saved to resale_test_findings.json")

    except Exception as e:
        with open('resale_test_error.txt', 'w') as f:
            f.write(str(e))
        print(f"AI Error: {e}")

if __name__ == "__main__":
    test_resale()
