import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_groq():
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("GROQ_API_KEY not found")
        return

    schema = {
        "total_system_value": "$XXXX",
        "market_advice": "Detailed advice...",
        "components": [
            {
                "category": "CPU",
                "name": "AMD A10-7850K",
                "status": "Active",
                "estimated_resale": "$XXX"
            }
        ]
    }

    system_role = (
        "You are the RigMaster Pro AI, a world-class hardware market analyst. "
        "Analyze the provided PC components with extreme precision. "
        "For each component, provide a realistic current Used Market Price (eBay/Reddit/Marketplace) in USD. "
        "Never use 'N/A' or '$0'. Even for e-waste, use a symbolic value like '$4.50'. "
        "Provide a total system value that captures the synergy of the build. "
        "Provide elite, aggressive market advice on selling strategies, cleaning, and descriptions. "
        "Include your AI reasoning for the valuation in the market_advice. "
        f"Respond ONLY in JSON with this exact schema: {json.dumps(schema)}"
    )

    user_content = "Build Components:\n- CPU: AMD A10-7850K (Status: Active)\n- GPU: AMD 100-435415 (Status: Active)"

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_role}, {"role": "user", "content": user_content}],
                "response_format": {"type": "json_object"}
            },
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=15
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content']
            print("Content:")
            print(content)
            data = json.loads(content)
            print("Parsed keys:", data.keys())
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_groq()
