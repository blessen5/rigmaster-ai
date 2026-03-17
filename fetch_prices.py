#!/usr/bin/env python3
"""
Fetch real hardware prices from PCPartPicker

This script scrapes current prices from PCPartPicker.com
and updates the MongoDB components collection with real pricing data.

Usage: python fetch_prices.py
"""

import os
import sys
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import time

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/rigmaster')
client = MongoClient(MONGO_URI)
db = client.rigmaster
components_collection = db.components

# Headers to mimic browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# PCPartPicker URLs for different categories
PCPARTPICKER_URLS = {
    'cpu': 'https://pcpartpicker.com/products/cpu/',
    'motherboard': 'https://pcpartpicker.com/products/motherboard/',
    'memory': 'https://pcpartpicker.com/products/memory/',
    'gpu': 'https://pcpartpicker.com/products/video-card/',
    'psu': 'https://pcpartpicker.com/products/power-supply/',
    'case': 'https://pcpartpicker.com/products/case/',
    'cooler': 'https://pcpartpicker.com/products/cpu-cooler/',
    'storage': 'https://pcpartpicker.com/products/internal-hard-drive/',
    'monitor': 'https://pcpartpicker.com/products/monitor/',
}

def fetch_prices_for_category(category_name, page_url, delay=2):
    """
    Fetch prices for a specific category from PCPartPicker
    
    Args:
        category_name: MongoDB category name (cpu, gpu, etc.)
        page_url: PCPartPicker URL for the category
        delay: Delay between requests (seconds)
    """
    print(f"\nFetching prices for {category_name}...")
    
    try:
        # Respect rate limiting
        time.sleep(delay)
        
        response = requests.get(page_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all product rows (PCPartPicker specific structure)
        # Note: This selector may need updating if PCPartPicker changes their HTML
        products = soup.find_all('tr', class_='tr__product')
        
        if not products:
            print(f"No products found on page (HTML structure may have changed)")
            return 0
        
        updated_count = 0
        
        for product in products:
            try:
                # Extract product name
                name_elem = product.find('a', class_='td__nameWrapper')
                if not name_elem:
                    continue
                product_name = name_elem.get_text(strip=True)
                
                # Extract price
                price_elem = product.find('td', class_='td__price')
                if not price_elem:
                    continue
                
                price_text = price_elem.get_text(strip=True)
                # Parse price (e.g., "$299.99" -> 299.99)
                try:
                    price = float(price_text.replace('$', '').replace(',', ''))
                except ValueError:
                    continue
                
                if price <= 0:
                    continue
                
                # Update in MongoDB
                result = components_collection.update_one(
                    {'name': product_name, 'category': category_name},
                    {
                        '$set': {
                            'price': price,
                            'price_usd': price,
                            'last_price_update': datetime.utcnow()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    print(f"Updated price: {product_name} - ${price:.2f}")
                    updated_count += 1
                
            except Exception as e:
                continue
        
        print(f"Updated {updated_count} prices for {category_name}")
        return updated_count
    
    except Exception as e:
        print(f"Error fetching prices for {category_name}: {e}")
        return 0


def fetch_amazon_prices():
    """
    Alternative: Estimate prices based on component tier and specs
    This is a fallback when real-time scraping isn't possible
    """
    print("\nEstimating prices based on component specifications...")
    
    updated_count = 0
    
    # Price estimation heuristics
    cpu_price_map = {
        'Threadripper': 1000,
        'Core i9': 500,
        'Core i7': 350,
        'Core i5': 200,
        'Ryzen 9': 450,
        'Ryzen 7': 300,
        'Ryzen 5': 200,
    }
    
    # Estimate prices for CPUs
    cpus = components_collection.find({'category': 'cpu', 'price': None})
    
    for cpu in cpus:
        estimated_price = 150  # base price
        cpu_name = cpu.get('name', '')
        
        # Check name for price tiers
        for tier_name, base_price in cpu_price_map.items():
            if tier_name in cpu_name:
                estimated_price = base_price
                break
        
        # Adjust based on core count
        cores = cpu.get('cores', 0)
        if cores > 16:
            estimated_price += (cores - 16) * 30
        elif cores > 8:
            estimated_price += (cores - 8) * 50
        
        result = components_collection.update_one(
            {'_id': cpu['_id']},
            {
                '$set': {
                    'price': estimated_price,
                    'price_estimated': True,
                    'price_usd': estimated_price
                }
            }
        )
        
        if result.modified_count > 0:
            updated_count += 1
    
    print(f"Estimated prices for {updated_count} components")
    return updated_count


def main():
    print("Starting real price fetch for RigMaster UI")
    print(f"MongoDB URI: {MONGO_URI}")
    
    total_updated = 0
    
    try:
        # Try to fetch from PCPartPicker
        for category, url in PCPARTPICKER_URLS.items():
            updated = fetch_prices_for_category(category, url)
            total_updated += updated
        
        # Fallback to price estimation for missing data
        estimated = fetch_amazon_prices()
        total_updated += estimated
        
        print(f"\n✓ Price update complete! Updated {total_updated} components")
        
    except Exception as e:
        print(f"Error during price fetch: {e}")
        print("Falling back to price estimation...")
        fetch_amazon_prices()
        sys.exit(1)


if __name__ == "__main__":
    main()
