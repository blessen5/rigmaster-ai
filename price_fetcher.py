"""
Price Fetching Module for RigMaster AI
Fetches real-time prices from Google Shopping using SerpAPI
"""

import os
import requests
import json
import logging
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class PriceFetcher:
    """Fetches real-time component prices from Google Shopping"""

    def __init__(self, db=None):
        self.db = db
        self.api_key = os.getenv('SERPAPI_KEY')
        self.base_url = "https://serpapi.com/search.json"
        self.cache_timeout = 21600  # 6 hours cache

    def _get_api_key(self):
        """Get SerpAPI key from site settings or environment"""
        if self.db:
            try:
                # Direct check avoid circular import with app.py helpers
                settings = self.db.settings.find_one({'key': 'site_settings'})
                if settings and 'api_keys' in settings.get('value', {}):
                    db_key = settings['value']['api_keys'].get('serpapi_key')
                    if db_key: return db_key
            except:
                pass
        return self.api_key

    def _get_cached_price(self, key: str) -> Optional[Dict]:
        """Get price from MongoDB cache if valid"""
        if not self.db: return None
        
        cached = self.db.shopping_cache.find_one({'query': f"LIVE_{key}"})
        if cached and 'expires_at' in cached:
            # Handle both aware and naive datetimes if necessary, though mostly naive in this app
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            expires = cached['expires_at']
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
                
            if expires > now:
                return cached.get('data')
        return None

    def _cache_price(self, key: str, data: Dict):
        """Cache price data in MongoDB"""
        if not self.db: return
        
        from datetime import datetime, timedelta, timezone
        self.db.shopping_cache.update_one(
            {'query': f"LIVE_{key}"},
            {'$set': {
                'data': data,
                'last_updated': datetime.now(timezone.utc),
                'expires_at': datetime.now(timezone.utc) + timedelta(seconds=self.cache_timeout)
            }},
            upsert=True
        )

    def fetch_component_price(self, component_name: str, category: str = "") -> Optional[Dict[str, Any]]:
        """
        Fetch price for a PC component from Google Shopping

        Args:
            component_name: Name of the component (e.g., "RTX 4070 Super")
            category: Component category for better search (e.g., "gpu", "cpu")

        Returns:
            Dict with price info or None if not found
        """
        api_key = self._get_api_key()
        if not api_key:
            logger.error("SERPAPI_KEY not configured")
            return None

        # Create cache key
        cache_key = f"{component_name}_{category}".lower().replace(" ", "_")

        # Check cache first
        cached = self._get_cached_price(cache_key)
        if cached:
            logger.info(f"Using cached price for {component_name}")
            return cached

        try:
            # Build search query
            query = component_name
            if category:
                # Add category-specific keywords for better results
                category_keywords = {
                    'gpu': 'graphics card nvidia amd',
                    'cpu': 'processor intel amd',
                    'motherboard': 'motherboard atx',
                    'ram': 'memory ddr4 ddr5',
                    'storage': 'ssd nvme hard drive',
                    'psu': 'power supply',
                    'case': 'pc case',
                    'cooler': 'cpu cooler',
                    'monitor': 'display screen',
                    'keyboard': 'mechanical keyboard',
                    'mouse': 'gaming mouse',
                    'headset': 'gaming headset'
                }
                if category in category_keywords:
                    query += f" {category_keywords[category]}"

            # SerpAPI parameters
            params = {
                'api_key': api_key,
                'engine': 'google_shopping',
                'q': query,
                'num': 5,  # Get top 5 results
                'gl': 'us',  # Country: US
                'hl': 'en'   # Language: English
            }

            logger.info(f"Fetching price for: {query}")

            # Make API request
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Parse shopping results
            if 'shopping_results' in data and data['shopping_results']:
                # Get the lowest price from top results
                prices = []
                for result in data['shopping_results'][:3]:  # Check top 3 results
                    if 'price' in result and result['price']:
                        try:
                            # Extract numeric price (remove currency symbols)
                            price_str = str(result['price']).replace('$', '').replace(',', '').strip()
                            price = float(price_str)
                            if price > 0:  # Valid price
                                prices.append({
                                    'price': price,
                                    'currency': 'USD',
                                    'source': result.get('source', 'Google Shopping'),
                                    'title': result.get('title', ''),
                                    'link': result.get('link', '')
                                })
                        except (ValueError, TypeError):
                            continue

                if prices:
                    # Return the lowest price
                    lowest_price = min(prices, key=lambda x: x['price'])

                    result = {
                        'component_name': component_name,
                        'category': category,
                        'price_usd': lowest_price['price'],
                        'currency': 'USD',
                        'source': lowest_price['source'],
                        'title': lowest_price['title'],
                        'link': lowest_price['link'],
                        'search_query': query,
                        'timestamp': time.time()
                    }

                    # Cache the result
                    self._cache_price(cache_key, result)

                    logger.info(f"Found price for {component_name}: ${lowest_price['price']}")
                    return result

            logger.warning(f"No valid prices found for {component_name}")
            return None

        except requests.RequestException as e:
            logger.error(f"API request failed for {component_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching price for {component_name}: {e}")
            return None

    def get_price_with_fallback(self, component_name: str, category: str = "", fallback_price: float = 0) -> Dict[str, Any]:
        """
        Get price with fallback to provided price if API fails

        Args:
            component_name: Component name
            category: Component category
            fallback_price: Price to use if API fails

        Returns:
            Price data dict
        """
        price_data = self.fetch_component_price(component_name, category)

        if price_data:
            return price_data
        else:
            # Return fallback price structure
            return {
                'component_name': component_name,
                'category': category,
                'price_usd': fallback_price,
                'currency': 'USD',
                'source': 'Database Fallback',
                'title': component_name,
                'link': '',
                'search_query': component_name,
                'timestamp': time.time(),
                'fallback': True
            }

# Global price fetcher instance
_price_fetcher = None

def get_price_fetcher(db=None) -> PriceFetcher:
    """Get global price fetcher instance"""
    global _price_fetcher
    if _price_fetcher is None:
        _price_fetcher = PriceFetcher(db=db)
    elif db and _price_fetcher.db is None:
        _price_fetcher.db = db
    return _price_fetcher
