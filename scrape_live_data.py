"""
Advanced Web Scraper for Hardware Data
Scrapes real component data from public sources with live pricing

Requirements: pip install requests beautifulsoup4 lxml selenium
Note: Some sources may require selenium for JavaScript rendering
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client['rigmaster']

print("🕷️  Advanced Hardware Data Web Scraper")
print("=" * 70)

# ========== CONFIGURATION ==========

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# ========== HELPER FUNCTIONS ==========

def clean_price(price_str):
    """Extract numeric price from string"""
    if not price_str:
        return None
    price_str = re.sub(r'[^\d.]', '', str(price_str))
    try:
        return float(price_str)
    except:
        return None

def safe_request(url, delay=2):
    """Make HTTP request with rate limiting"""
    try:
        time.sleep(delay)  # Rate limiting
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return None

# ========== SCRAPER 1: NEWEGG PRODUCT SEARCH ==========

def scrape_newegg_category(category, search_term, limit=20):
    """
    Scrape Newegg for component data
    Note: This is a simplified example. Real scraping requires handling pagination, etc.
    """
    print(f"\n🛒 Scraping Newegg: {category}")
    print("-" * 70)
    
    components = []
    
    # Newegg search URL format
    search_url = f"https://www.newegg.com/p/pl?d={search_term.replace(' ', '+')}"
    
    response = safe_request(search_url)
    if not response:
        print("  ⚠️  Failed to fetch Newegg data")
        return components
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find product listings (Newegg structure may change)
    items = soup.find_all('div', class_='item-cell', limit=limit)
    
    for item in items:
        try:
            # Extract product name
            title_elem = item.find('a', class_='item-title')
            if not title_elem:
                continue
            name = title_elem.text.strip()
            
            # Extract price
            price_elem = item.find('li', class_='price-current')
            if price_elem:
                price_str = price_elem.text.strip()
                price = clean_price(price_str)
            else:
                price = None
            
            if name and price:
                component = {
                    'name': name,
                    'price': price,
                    'status': 'Active',
                    'source': 'Newegg'
                }
                components.append(component)
                print(f"  ✅ {name} - ${price}")
        
        except Exception as e:
            print(f"  ⚠️  Error parsing item: {e}")
            continue
    
    return components

# ========== SCRAPER 2: AMAZON PRODUCT API (Simplified) ==========

def scrape_amazon_search(search_term, limit=20):
    """
    Scrape Amazon for component data
    Note: Amazon has strong anti-bot measures. This is a simplified example.
    For production, use Amazon Product Advertising API.
    """
    print(f"\n📦 Scraping Amazon: {search_term}")
    print("-" * 70)
    
    components = []
    
    # Amazon search URL
    search_url = f"https://www.amazon.com/s?k={search_term.replace(' ', '+')}"
    
    response = safe_request(search_url, delay=3)
    if not response:
        print("  ⚠️  Failed to fetch Amazon data (anti-bot protection)")
        return components
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find product listings
    items = soup.find_all('div', {'data-component-type': 's-search-result'}, limit=limit)
    
    for item in items:
        try:
            # Extract product name
            title_elem = item.find('h2', class_='s-line-clamp-2')
            if not title_elem:
                continue
            name = title_elem.text.strip()
            
            # Extract price
            price_elem = item.find('span', class_='a-price-whole')
            if price_elem:
                price = clean_price(price_elem.text)
            else:
                price = None
            
            if name and price:
                component = {
                    'name': name,
                    'price': price,
                    'status': 'Active',
                    'source': 'Amazon'
                }
                components.append(component)
                print(f"  ✅ {name} - ${price}")
        
        except Exception as e:
            continue
    
    return components

# ========== SCRAPER 3: PUBLIC API (Example: OpenPrices) ==========

def fetch_from_public_api():
    """
    Fetch data from public hardware price APIs
    Example: Using a hypothetical open hardware price API
    """
    print(f"\n🌐 Fetching from Public APIs")
    print("-" * 70)
    
    # This is a placeholder - replace with actual public API
    # Example APIs: PriceAPI, RapidAPI hardware endpoints, etc.
    
    print("  ℹ️  No public API configured (add your API key)")
    print("  💡 Tip: Sign up for RapidAPI or similar services")
    
    return []

# ========== MAIN SCRAPING FUNCTION ==========

def scrape_all_sources():
    """
    Scrape data from all configured sources
    """
    
    all_components = {
        'cpus': [],
        'gpus': [],
        'motherboards': [],
        'ram': [],
        'storage': [],
        'psu': [],
        'cases': [],
        'coolers': []
    }
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("  - Web scraping may be blocked by anti-bot measures")
    print("  - Respect robots.txt and terms of service")
    print("  - Use delays between requests")
    print("  - For production, use official APIs when available")
    
    # Example scraping (commented out to avoid actual scraping without permission)
    # Uncomment and modify as needed
    
    # all_components['gpus'] = scrape_newegg_category('GPU', 'RTX 4090', limit=10)
    # all_components['cpus'] = scrape_newegg_category('CPU', 'Intel Core i9', limit=10)
    
    print("\n💡 Web scraping is disabled by default.")
    print("   To enable, uncomment the scraping calls in the script.")
    print("   For best results, use official APIs or curated datasets.")
    
    return all_components

# ========== IMPORT TO DATABASE ==========

def import_to_database(components_dict):
    """Import scraped components to database"""
    
    total_added = 0
    total_skipped = 0
    
    for collection_name, components in components_dict.items():
        if not components:
            continue
        
        collection = db[collection_name]
        print(f"\n📦 Importing {len(components)} {collection_name}")
        
        for component in components:
            existing = collection.find_one({"name": component['name']})
            if not existing:
                collection.insert_one(component)
                total_added += 1
            else:
                total_skipped += 1
    
    return total_added, total_skipped

# ========== RUN SCRAPER ==========

if __name__ == "__main__":
    print("\n🚀 Starting web scraping...")
    print("=" * 70)
    
    # Scrape data
    scraped_data = scrape_all_sources()
    
    # Import to database
    added, skipped = import_to_database(scraped_data)
    
    print("\n" + "=" * 70)
    print("🎉 SCRAPING COMPLETE!")
    print("=" * 70)
    print(f"✅ Added: {added} components")
    print(f"⏭️  Skipped: {skipped} existing components")
    
    print("\n📝 Recommendations:")
    print("  1. Use the curated dataset scripts for reliable data")
    print("  2. For live prices, use official APIs (Amazon, Newegg)")
    print("  3. Web scraping should be used carefully and ethically")
    print("  4. Consider using the import_from_sources.py script instead")
