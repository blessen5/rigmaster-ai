from app import get_build_insights_data
import json

# Mock build
build = {
    'name': 'Test Build',
    'cpu_id': '65ba3a8f5f4b5d4b5d4b5d4b', # Just a random hex
    'gpu_id': None,
    'quantity': 1
}

# This will probably fail because get_component_by_id accesses db
# So I need to set up a mock db or just use the real one if it's there
try:
    data = get_build_insights_data(build)
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
