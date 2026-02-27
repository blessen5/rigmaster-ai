import os
import time
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from ai_engine import get_ai_engine
from bson.objectid import ObjectId

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://127.0.0.1:27017/')
client = MongoClient(MONGO_URI)
db = client['rigmaster']
ai_engine = get_ai_engine()

def get_missing_fields(category):
    """Define what constitutes 'missing' for each category."""
    common = ['brand', 'status']
    mapping = {
        "cpu": common + ['socket', 'cores', 'threads', 'tdp'],
        "gpu": common + ['vram', 'tdp', 'chipset'],
        "motherboard": common + ['socket', 'chipset', 'ram_type'],
        "ram": common + ['capacity', 'type', 'speed'],
        "storage": common + ['capacity', 'type'],
        "psu": common + ['wattage', 'efficiency'],
        "case": common + ['form_factor'],
        "cooler": common + ['type']
    }
    return mapping.get(category, common)

def validate_specs(cat, specs):
    """Sanity check for critical specs to ensure genuineness."""
    if not specs: return False
    
    # Hardcoded rules for common patterns
    if cat == 'cpu':
        # Socket consistency
        if '12' in specs.get('name', '') and 'LGA1700' not in specs.get('socket', ''):
            if 'Intel' in specs.get('brand', ''): return False # Should be LGA1700
    
    # VRAM sanity
    if cat == 'gpu':
        vram = str(specs.get('vram', '')).upper()
        if '4090' in specs.get('name', '') and '24' not in vram: return False
        
    return True

def enrich_database(limit=50, categories=None):
    # Mapping plural collections to singular categories for spec schemas
    col_to_cat = {
        'cpus': 'cpu', 'gpus': 'gpu', 'motherboards': 'motherboard',
        'ram': 'ram', 'storage': 'storage', 'psu': 'psu',
        'cases': 'case', 'coolers': 'cooler',
        'components': None # Special handling
    }
    
    # Collections to process
    collections = list(col_to_cat.keys())
    if categories: # If user provided specific categories, filter
        collections = [c for c in collections if col_to_cat.get(c) in categories or c == categories]

    total_processed = 0
    total_updated = 0
    
    print(f"Starting enrichment across collections: {collections}")
    print(f"Limit: {limit} items total")
    
    for col_name in collections:
        if total_processed >= limit:
            break
            
        collection = db[col_name]
        print(f"\nProcessing collection: {col_name}")
        
        # Get plural or singular category
        cat = col_to_cat[col_name]
        
        # Build query for documents missing critical info
        # For simplicity, we check if 'brand' is missing
        remaining_limit = limit - total_processed
        query = {'$or': [{'brand': None}, {'brand': ""}, {'brand': {'$exists': False}}]}
        
        docs = list(collection.find(query).limit(remaining_limit))
        
        if not docs:
            print(f"  All items in {col_name} have a brand or no items found.")
            continue
            
        for doc in docs:
            name = doc.get('name')
            # Determine actual category for AI schema
            doc_cat = cat if cat else doc.get('category')
            if not doc_cat: continue
            
            print(f"  - Ensuring Genuineness for: {name}...", end="", flush=True)
            
            try:
                # 1. AI Enrichment with "Genuineness" instruction
                ai_specs = ai_engine.enrich_component_specs(doc_cat, name)
                
                # 2. Validation Layer
                if ai_specs and validate_specs(doc_cat, ai_specs):
                    # 3. Update logic
                    update_data = {k: v for k, v in ai_specs.items() if not doc.get(k)}
                    if 'status' not in doc: update_data['status'] = 'Active'
                    
                    if update_data:
                        collection.update_one({'_id': doc['_id']}, {'$set': update_data})
                        print(f" OK (Updated: {list(update_data.keys())})")
                        total_updated += 1
                    else:
                        print(" Verified (No changes needed)")
                else:
                    print(f" SKIPPED (AI failed or validation mismatch)")
                    
            except Exception as e:
                print(f" ERROR: {e}")
                
            total_processed += 1
            if total_processed >= limit:
                break
            time.sleep(0.5)

    print(f"\nAuthentic Enrichment Complete!")
    print(f"Items processed: {total_processed}")
    print(f"Items updated: {total_updated}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Enrich RigMaster database with AI-inferred specs.')
    parser.add_argument('--limit', type=int, default=10, help='Max items to process')
    parser.add_argument('--cat', type=str, help='Specific category to process')
    parser.add_argument('--local-only', action='store_true', help='Use only local Ollama to avoid API limits')
    
    args = parser.parse_args()
    
    if args.local_only:
        print("Using LOCAL-ONLY mode for bulk processing.")
        # Re-initialize engine to only use ollama if possible
        if 'ollama' in ai_engine.providers:
            ai_engine.providers = ['ollama']
        else:
            print("Warning: Ollama not found in providers. Falling back to default rotation.")
    
    cats = [args.cat] if args.cat else None
    enrich_database(limit=args.limit, categories=cats)
