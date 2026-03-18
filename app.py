from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash, send_file
import io
import csv
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os
import json
import requests
import urllib.parse
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from google import genai
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from collections import defaultdict, deque
from threading import Lock
import time


load_dotenv()
from pymongo import MongoClient
from bson.objectid import ObjectId
from ai_engine import get_ai_engine
from currencies_config import EXCHANGE_RATES, CURRENCY_SYMBOLS
from price_fetcher import get_price_fetcher



app = Flask(__name__)
_secret = os.getenv('SECRET_KEY')
if not _secret:
    import secrets
    _secret = secrets.token_hex(32)
    app.logger.warning("SECRET_KEY not set in environment — using a random key. Sessions will not survive restarts.")
app.secret_key = _secret
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB Limit

DEFAULT_AI_PROVIDER = os.getenv('DEFAULT_AI_PROVIDER', 'deepseek')
AI_RATE_LIMIT_DEFAULTS = {
    'assistant': (20, 300),
    'recommend': (8, 600),
    'analysis': (12, 300),
}
AI_RATE_LIMIT_PATHS = {
    '/ai-assistant': 'assistant',
    '/api/ai-recommend': 'recommend',
    '/api/ai-engine/recommend': 'recommend',
    '/api/ai-engine/compatibility': 'analysis',
    '/api/ai-engine/performance': 'analysis',
    '/ai/analyze': 'analysis',
    '/api/benchmark-simulator': 'analysis',
    '/api/analyze_upgrade': 'analysis',
}
_ai_rate_limit_state = defaultdict(deque)
_ai_rate_limit_lock = Lock()

# Register format_price as a template filter
@app.template_filter('format_price')
def format_price_filter(amount):
    return format_price(amount)

# Global context processor for currencies
@app.context_processor
def inject_currencies():
    return {
        'all_currencies': CURRENCY_SYMBOLS,
        'exchange_rates': EXCHANGE_RATES
    }
 
# Decorator to protect routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Access denied: Admin privileges required')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Global Helpers
def clean_comp_name(name):
    if not name: return "Unknown Component"
    s = str(name)
    # Remove "ID:..." prefix (very greedy/loose match to catch all variations)
    # This matches "ID" followed by anything up to a pipe
    s = re.sub(r'^(?i)id\s*:?.*?[|]\s*', '', s)
    # Fallback: matches a 24-char hex ID if it's at the start
    s = re.sub(r'^[0-9a-fA-F]{24}\s*[|]\s*', '', s)
    
    # Remove "Specs:[...]" suffix
    s = re.sub(r'\s*\|\s*Specs:\[.*?\]', '', s)
    # Remove any remaining leading/trailing pipes or whitespace
    s = s.strip(' |').strip()
    return s if s else "Unknown Component"

def get_estimated_price(comp_name, cat):
    name = str(comp_name).upper()
    if cat == 'cpus' or cat == 'cpu':
        if 'THREADRIPPER' in name: return 1500
        if 'RYZEN 9' in name or 'CORE I9' in name: return 580
        if 'RYZEN 7' in name or 'CORE I7' in name: return 380
        if 'RYZEN 5' in name or 'CORE I5' in name: return 240
        return 140
    if cat == 'gpus' or cat == 'gpu':
        if '4090' in name: return 1800
        if '4080' in name or '7900 XTX' in name: return 1100
        if '4070 TI' in name or '7900 XT' in name: return 850
        if '4070 SUPER' in name or '4070' in name or '7800 XT' in name: return 650
        if '4060 TI' in name or '7700 XT' in name: return 420
        if '4060' in name or '7600' in name: return 320
        return 250
    if cat == 'motherboards' or cat == 'motherboard': 
        if 'Z790' in name or 'X670' in name: return 320
        if 'B650' in name or 'B760' in name: return 200
        return 150
    if cat == 'ram': 
        if '64GB' in name: return 240
        if '32GB' in name: return 130
        return 80
    if cat == 'storage': 
        if '4TB' in name: return 280
        if '2TB' in name: return 150
        if '1TB' in name: return 90
        return 60
    if cat == 'psu': 
        if '1000W' in name: return 200
        if '850W' in name: return 160
        if '750W' in name: return 130
        return 100
    if cat == 'cases' or cat == 'case': return 130
    if cat == 'coolers' or cat == 'cooler': 
        if 'LIQUID' in name or 'AIO' in name or '420' in name or '360' in name: return 160
        return 60
    if cat == 'monitors' or cat == 'monitor':
        if '4K' in name: return 600
        if '1440P' in name or '2K' in name: return 350
        return 180
    if cat == 'os':
        if 'PRO' in name: return 150
        return 110
    if cat == 'peripherals':
        return 80
    if cat == 'keyboards' or cat == 'keyboard':
        if 'MECHANICAL' in name: return 120
        return 70
    if cat == 'mice' or cat == 'mouse':
        if 'WIRELESS' in name or 'LIGHTSPEED' in name: return 90
        return 60
    if cat == 'headsets' or cat == 'headset':
        if 'WIRELESS' in name or 'NOISE' in name: return 150
        return 80
    if cat == 'webcams' or cat == 'webcam':
        if '4K' in name or 'BRIO' in name: return 200
        return 100
    if cat == 'fans':
        return 30
    if cat == 'thermal_paste':
        return 15
    if cat == 'microphones' or cat == 'microphone':
        return 120
    if cat == 'wifi_adapters' or cat == 'wifi':
        return 40
    if cat == 'speakers':
        return 100
    if cat == 'ups':
        return 200
    if cat == 'tools':
        return 50
    return 100

# Shared price-reading fallback map (used by saved_builds & analysis routes)
_PRICE_CAT_MAP = {
    'cpu_id': 'cpus', 'gpu_id': 'gpus', 'motherboard_id': 'motherboards',
    'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
    'case_id': 'cases', 'cooler_id': 'coolers',
    'monitor_id': 'monitors', 'os_id': 'os',
    'peripherals_id': 'peripherals', 'fans_id': 'fans',
    'keyboard_id': 'keyboards', 'mouse_id': 'mice',
    'headset_id': 'headsets', 'webcam_id': 'webcams',
    'thermal_paste_id': 'thermal_paste', 'wifi_id': 'wifi_adapters',
    'speakers_id': 'speakers', 'microphone_id': 'microphones',
    'ups_id': 'ups', 'tool_id': 'tools'
}

def get_comp_price_usd(comp, id_key=None, est_cat=None):
    """Return the USD price for a component document.
    Reads the real 'price'/'msrp'/'cost' field first; falls back to
    keyword-based heuristics if no price field is stored or if price is 0.
    Automatically normalizes local currency prices (matching ₹, £, €, etc.) to USD."""
    if comp is None:
        return 0.0
    
    # Try multiple common price fields in order of reliability
    price_fields = ['price', 'msrp', 'cost', 'retail_price', 'sale_price']
    raw = None
    for field in price_fields:
        val = comp.get(field)
        if val is not None and val != "" and val != 0 and val != 0.0 and str(val).strip() != "0":
            raw = val
            break
            
    if raw is not None:
        try:
            # Detect currency symbol and determine normalization rate
            raw_s = str(raw).strip().upper()
            norm_rate = 1.0
            
            # Prioritize non-USD symbols to avoid false positives with $
            for code, sym in CURRENCY_SYMBOLS.items():
                if sym and sym != '$' and sym in raw_s:
                    norm_rate = EXCHANGE_RATES.get(code, 1.0)
                    break
            else:
                # Fallback check for $ if no other symbol was found
                if '$' in raw_s:
                    norm_rate = EXCHANGE_RATES.get('USD', 1.0)

            # Extract numeric value (remove currency symbols, commas, etc.)
            # Match digits and decimal point only
            clean_match = re.search(r'[\d,.]+', raw_s)
            if clean_match:
                p_str = clean_match.group(0).replace(',', '')
                p = float(p_str)
                if p > 0:
                    return p / norm_rate
        except Exception:
            pass
            
    # Determine fallback category for estimation
    fallback_cat = est_cat
    if fallback_cat is None and id_key:
        fallback_cat = _PRICE_CAT_MAP.get(id_key, id_key)
        
    return get_estimated_price(comp.get('name', ''), fallback_cat or 'peripherals')

def get_component_by_id(comp_id):
    if db is None or not comp_id: return None
    try:
        if isinstance(comp_id, str) and comp_id == "None Selected": return None
        return db.components.find_one({'_id': ObjectId(comp_id)})
    except:
        return None

# Currency Support
# Currencies imported from currencies_config.py

def format_price(amount, currency=None, for_pdf=False):
    if currency is None:
        currency = session.get('currency', 'USD')
    
    rate = EXCHANGE_RATES.get(currency, 1.0)
    converted_amount = (amount or 0) * rate
    
    if for_pdf:
        # Use currency code or ASCII equivalent for PDF compatibility
        if currency == 'INR':
            return f"Rs. {int(converted_amount):,}"
        if currency == 'USD':
            return f"${converted_amount:,.2f}"
            
        # Fallback for other currencies to avoid Unicode symbol errors in FPDF
        return f"{currency} {converted_amount:,.2f}"

    symbol = CURRENCY_SYMBOLS.get(currency, '$')
    
    # Format with appropriate decimals
    zero_decimal_currencies = ['JPY', 'KRW', 'IDR', 'VND', 'HUF', 'INR', 'PKR', 'BDT', 'UGX', 'TZS', 'AMD', 'BIF', 'CLP', 'DJF', 'GNF', 'IQD', 'KMF', 'LAK', 'LBP', 'MGA', 'MMK', 'MNT', 'PYG', 'RWF', 'SOS', 'SYP', 'VUV', 'YER']
    if currency in zero_decimal_currencies:
        return f"{symbol}{int(converted_amount):,}"
    return f"{symbol}{converted_amount:,.2f}"

@app.route('/api/set-currency', methods=['POST'])
@login_required
def set_currency():
    try:
        data = request.get_json(silent=True, force=True) or {}
        currency = data.get('currency', 'USD')
        if currency in EXCHANGE_RATES:
            session['currency'] = currency
            session['currency_symbol'] = CURRENCY_SYMBOLS.get(currency, '$')
            # Persist to DB for logged-in users so it survives future logins
            user_id = session.get('user_id')
            if user_id and db is not None:
                try:
                    db.users.update_one(
                        {'_id': ObjectId(user_id)},
                        {'$set': {'preferred_currency': currency}}
                    )
                except Exception:
                    pass  # Non-critical — session is already updated
            return jsonify({'status': 'success', 'currency': currency, 'symbol': CURRENCY_SYMBOLS.get(currency, '$')})
        return jsonify({'status': 'error', 'message': f'Invalid currency: {currency}'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    # Fallback only for local development — set MONGO_URI in production!
    MONGO_URI = 'mongodb://localhost:27017/rigmaster'
    app.logger.warning("MONGO_URI not set — connecting to localhost. Set it in your .env for production.")
_mongo_client = None

def get_db():
    """Returns database instance, using a singleton client to avoid repeated handshakes."""
    global _mongo_client
    try:
        if _mongo_client is None:
            from pymongo import MongoClient
            import certifi
            try:
                # First try with certifi for proper SSL, with conservative pool settings
                _mongo_client = MongoClient(
                    MONGO_URI, 
                    serverSelectionTimeoutMS=5000,
                    tz_aware=True,
                    tlsCAFile=certifi.where(),
                    maxPoolSize=10,       # Keep max connections low for Atlas free tier
                    minPoolSize=0,        # Don't keep idle connections open
                    maxIdleTimeMS=30000,  # Close idle connections after 30 seconds
                    connectTimeoutMS=10000,
                    socketTimeoutMS=30000,
                    retryWrites=True
                )
                _mongo_client.admin.command('ping')
            except Exception as e:
                app.logger.warning(f"Certifi SSL failed, falling back: {e}")
                # Append tlsAllowInvalidCertificates to the URI to bypass verification
                fallback_uri = MONGO_URI + "&tlsAllowInvalidCertificates=true"
                _mongo_client = MongoClient(
                    fallback_uri,
                    serverSelectionTimeoutMS=5000,
                    tz_aware=True,
                    maxPoolSize=10,
                    minPoolSize=0,
                    maxIdleTimeMS=30000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=30000,
                )
                _mongo_client.admin.command('ping')
        return _mongo_client['rigmaster']
    except Exception as e:
        app.logger.warning(f"MongoDB connection failed: {e}")
        _mongo_client = None
        return None

# Initial check
db = get_db()
_last_db_retry = 0
DB_RETRY_INTERVAL = 30  # Only retry connection every 30 seconds

def _ensure_indexes():
    """Create MongoDB indexes on startup for performance. Safe to re-run (idempotent)."""
    if db is None:
        return
    try:
        # Speed up category/name lookups (used heavily by component selects + AI pool)
        db.components.create_index([("category", 1), ("name", 1)], background=True)
        db.components.create_index([("category", 1), ("sub_category", 1)], background=True)
        
        # Make shopping cache lookups unique and fast
        db.shopping_cache.create_index("query", unique=True, background=True)
        
        # Auto-delete expired shopping cache entries (TTL index)
        db.shopping_cache.create_index("expires_at", expireAfterSeconds=0, background=True)

        # Speed up saved build lookups per user
        db.saved_builds.create_index([("user_id", 1), ("created_at", -1)], background=True)
        
        # Speed up AI recommendation cache lookups - MUST BE SPARSE to allow logging entries without cache keys
        try:
            # Drop old non-sparse index if it exists
            db.ai_cache.drop_index("cache_key_1")
        except: pass
        db.ai_cache.create_index("cache_key", unique=True, sparse=True, background=True)
        
        app.logger.info("MongoDB indexes verified/created (AI Cache Sparke/Unique).")
    except Exception as e:
        app.logger.warning(f"Could not create indexes: {e}")

_ensure_indexes()

# AI key sync throttling — avoid hitting DB on every request
_last_key_sync = 0.0
_KEY_SYNC_INTERVAL = 60  # seconds

@app.before_request
def ensure_db():
    global db, _last_db_retry
    if db is None:
        now = time.time()
        if now - _last_db_retry > DB_RETRY_INTERVAL:
            _last_db_retry = now
            db = get_db()
    
    # Sync API keys from DB to AI Engine — throttled to once every 60 seconds
    global _last_key_sync
    now = time.time()
    if now - _last_key_sync < _KEY_SYNC_INTERVAL:
        return  # Skip sync, not due yet
    _last_key_sync = now

    # Dynamically sync API keys from Database to AI Engine
    try:
        from ai_engine import get_ai_engine
        ai_engine = get_ai_engine()
        ai_engine.preferred_provider = get_preferred_ai_provider()
        
        # Priority: 1. Admin UI 'api_keys' dict, 2. Individual DB settings, 3. Env variables
        custom_keys = get_site_setting('api_keys', {})
        
        db_keys = {
            'groq_key': custom_keys.get('groq_key') or get_site_setting('GROQ_API_KEY') or os.getenv('GROQ_API_KEY'),
            'gemini_key': custom_keys.get('gemini_key') or get_site_setting('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY'),
            'mistral_key': custom_keys.get('mistral_key') or get_site_setting('MISTRAL_API_KEY') or os.getenv('MISTRAL_API_KEY'),
            'deepseek_key': custom_keys.get('deepseek_key') or get_site_setting('DEEPSEEK_API_KEY') or os.getenv('DEEPSEEK_API_KEY'),
            'hf_key': custom_keys.get('hf_key') or get_site_setting('HF_API_KEY') or os.getenv('HF_API_KEY'),
            'openrouter_key': custom_keys.get('openrouter_key') or get_site_setting('OPENROUTER_API_KEY') or os.getenv('OPENROUTER_API_KEY'),
        }
        ai_engine.update_api_keys(db_keys)
    except Exception as e:
        app.logger.error(f"Failed to sync AI keys: {e}")


# Global System Settings Helpers
def get_site_setting(key, default=None):
    try:
        if db is None: return default
        setting = db.settings.find_one({'key': key})
        return setting['value'] if setting else default
    except:
        return default

def log_ai_request(request_type, provider, cached=False):
    """Logs an AI request to the ai_cache collection for analytics."""
    if db is None: return
    try:
        db.ai_cache.insert_one({
            'created_at': datetime.now(timezone.utc),
            'type': request_type,
            'provider': provider or 'Unknown',
            'cached': cached
        })
    except Exception as e:
        app.logger.error(f"Failed to log AI request: {e}")

def get_preferred_ai_provider():
    return get_site_setting('preferred_ai_provider', DEFAULT_AI_PROVIDER)

def _get_ai_rate_limit_config(bucket):
    default_requests, default_window = AI_RATE_LIMIT_DEFAULTS.get(bucket, (10, 300))
    req_key = f'AI_{bucket.upper()}_RATE_LIMIT_REQUESTS'
    win_key = f'AI_{bucket.upper()}_RATE_LIMIT_WINDOW_SECONDS'
    try:
        request_limit = int(get_site_setting(req_key, os.getenv(req_key, str(default_requests))) or default_requests)
    except (TypeError, ValueError):
        request_limit = default_requests
    try:
        window_seconds = int(get_site_setting(win_key, os.getenv(win_key, str(default_window))) or default_window)
    except (TypeError, ValueError):
        window_seconds = default_window
    return max(1, request_limit), max(60, window_seconds)

def _get_ai_rate_limit_identity(bucket):
    user_id = session.get('user_id') or session.get('username')
    forwarded = request.headers.get('X-Forwarded-For', '')
    client_ip = forwarded.split(',')[0].strip() if forwarded else (request.remote_addr or 'unknown')
    return f"{bucket}:{user_id or client_ip}"

@app.before_request
def apply_ai_rate_limit():
    bucket = AI_RATE_LIMIT_PATHS.get(request.path)
    if not bucket or request.method != 'POST':
        return None
    if session.get('is_admin'):
        return None

    request_limit, window_seconds = _get_ai_rate_limit_config(bucket)
    key = _get_ai_rate_limit_identity(bucket)
    now = time.time()

    with _ai_rate_limit_lock:
        hits = _ai_rate_limit_state[key]
        while hits and now - hits[0] >= window_seconds:
            hits.popleft()

        if len(hits) >= request_limit:
            retry_after = max(1, int(window_seconds - (now - hits[0])))
            return jsonify({
                'status': 'error',
                'message': f'AI request limit reached. Try again in {retry_after} seconds.',
                'retry_after': retry_after
            }), 429

        hits.append(now)

    return None

@app.before_request
def check_maintenance():
    # Allow static files, admin routes, and critical pages
    path = request.path
    if path.startswith('/static') or path.startswith('/admin') or \
       path in ['/login', '/logout', '/maintenance'] or \
       path.startswith('/api/admin'):
        return None
        
    if get_site_setting('maintenance_mode', False):
        if not session.get('is_admin', False):
            return render_template('maintenance.html'), 503
    return None

@app.context_processor
def inject_global_settings():
    return {
        'global_announcement': get_site_setting('global_announcement', ''),
        'maintenance_mode': get_site_setting('maintenance_mode', False),
        'preferred_ai_provider': get_preferred_ai_provider()
    }

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    
    # Catch DB NoneType errors
    if isinstance(e, AttributeError) and "'NoneType' object has no attribute" in str(e):
        app.logger.error(f"MongoDB connection might be down: {e}")
        if request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'message': 'Database connection unavailable.'}), 503
        return render_template('error.html', message="Database connection unavailable. Please check your network or try again later."), 503
        
    app.logger.error(f"Unexpected error: {e}")
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'An unexpected server error occurred.'}), 500
    return render_template('error.html', message="An unexpected server error occurred."), 500


@app.route('/maintenance')
def maintenance_page():
    return render_template('maintenance.html')

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/hardware')
@login_required
def hardware_encyclopedia():
    try:
        # Category now maps to the 'category' field string in components table
        # We handle the plural -> singular mapping here or just rely on 'cpus' -> 'cpu' if we want
        # But for UI consistency, better to map:
        category_map = {
            'cpus': 'cpu',
            'gpus': 'gpu',
            'motherboards': 'motherboard',
            'ram': 'ram',
            'storage': 'storage',
            'psu': 'psu',
            'cases': 'case',
            'coolers': 'cooler',
            'monitors': 'monitor',
            'os': 'os',
            'peripherals': 'peripherals',
            'fans': 'fans'
        }
        
        req_cat = request.args.get('category', 'cpus').lower()
        search = request.args.get('search', '').strip()
        
        global db
        if db is None:
            db = get_db()
        
        if db is None:
            app.logger.error("Hardware Encyclopedia requested but DB is None")
            return render_template('error.html', message="Database connection unavailable."), 503
        
        valid_categories = {
            'cpus': 'Processors',
            'gpus': 'Graphics Cards',
            'motherboards': 'Motherboards',
            'ram': 'Memory',
            'storage': 'Storage',
            'psu': 'Power Supplies',
            'cases': 'Cases',
            'coolers': 'Coolers',
            'monitors': 'Monitors',
            'os': 'Operating Systems',
            'fans': 'Case Fans',
            'keyboards': 'Keyboards',
            'mice': 'Mice',
            'headsets': 'Headsets',
            'webcams': 'Webcams',
            'peripherals': 'All Peripherals',
            'thermal_paste': 'Thermal Paste',
            'wifi_adapters': 'Network Adapters',
            'speakers': 'Speakers',
            'microphones': 'Microphones',
            'ups': 'UPS / Power Protection',
            'tools': 'Assembly Tools'
        }
        
        category_map = {
            'cpus': 'cpu', 'gpus': 'gpu', 'motherboards': 'motherboard',
            'ram': 'ram', 'storage': 'storage', 'psu': 'psu',
            'cases': 'case', 'coolers': 'cooler', 'monitors': 'monitor',
            'os': 'os', 'peripherals': 'peripherals', 'fans': 'fans',
            'keyboards': 'peripherals', 'mice': 'peripherals',
            'headsets': 'peripherals', 'webcams': 'peripherals',
            'thermal_paste': 'thermal_paste', 'wifi_adapters': 'wifi_adapters',
            'speakers': 'speakers', 'microphones': 'microphones',
            'ups': 'ups', 'tools': 'tools'
        }
        if req_cat not in valid_categories:
            req_cat = 'cpus'
            
        db_cat = category_map.get(req_cat, 'cpu')
        # Use regex to be robust against trailing spaces or case differences in DB
        query = {'category': {'$regex': f'^{re.escape(db_cat.strip())}$', '$options': 'i'}}
        
        # Mapping for sub-category routing
        subcat_map = {
            'keyboards': 'keyboard',
            'mice': 'mouse',
            'headsets': 'headset',
            'webcams': 'webcam'
        }
        
        if req_cat in subcat_map:
            query['sub_category'] = {'$regex': f'^{re.escape(subcat_map[req_cat])}$', '$options': 'i'}

        if search:
            query['name'] = {'$regex': search, '$options': 'i'}
            
        # Generic query to components table
        items = list(db.components.find(query).sort('name', 1))
        for item in items:
            item['_id'] = str(item['_id'])
            formatted_fields = {}
            for price_key in ('price', 'msrp', 'cost'):
                raw_price = item.get(price_key)
                if raw_price in (None, ''):
                    continue
                try:
                    normalized_price = float(str(raw_price).replace('$', '').replace(',', '').strip())
                    formatted_fields[price_key] = format_price(normalized_price)
                except (TypeError, ValueError):
                    formatted_fields[price_key] = raw_price
            item['_formatted_fields'] = formatted_fields
            
        return render_template('hardware.html', 
                               items=items, 
                               current_cat=req_cat, 
                               categories=valid_categories,
                               search=search)
    except Exception as e:
        app.logger.error(f"Hardware Error: {e}")
        flash("Could not load hardware database.")
        return redirect(url_for('home'))



@app.route('/builder')
@login_required
def builder():
    return render_template('builder.html')

@app.route('/api/my_builds')
@login_required
def api_my_builds():
    """Return a lightweight list of the current user's saved builds for dropdown selectors."""
    try:
        if db is None:
            return jsonify([])
        user_id = session.get('user_id')
        user_ids = [user_id]
        try:
            user_ids.append(ObjectId(user_id))
        except:
            pass
        builds = list(db.saved_builds.find(
            {'user_id': {'$in': user_ids}},
            {'name': 1, 'created_at': 1,
             'cpu_id': 1, 'gpu_id': 1, 'motherboard_id': 1, 'ram_id': 1,
             'storage_id': 1, 'psu_id': 1, 'case_id': 1, 'cooler_id': 1,
             'monitor_id': 1, 'os_id': 1, 'fans_id': 1,
             'keyboard_id': 1, 'mouse_id': 1, 'headset_id': 1,
             'webcam_id': 1, 'peripherals_id': 1,
             'thermal_paste_id': 1, 'wifi_id': 1, 'speakers_id': 1,
             'microphone_id': 1, 'ups_id': 1, 'tool_id': 1}
        ).sort('created_at', -1))
        result = []
        for b in builds:
            result.append({
                'id': str(b['_id']),
                'name': b.get('name') or 'Custom Rig',
                'date': b.get('created_at', '').strftime('%Y-%m-%d') if hasattr(b.get('created_at', ''), 'strftime') else '',
                'cpu_id': b.get('cpu_id') or '',
                'gpu_id': b.get('gpu_id') or '',
                'motherboard_id': b.get('motherboard_id') or '',
                'ram_id': b.get('ram_id') or '',
                'storage_id': b.get('storage_id') or '',
                'psu_id': b.get('psu_id') or '',
                'case_id': b.get('case_id') or '',
                'cooler_id': b.get('cooler_id') or '',
                'monitor_id': b.get('monitor_id') or '',
                'os_id': b.get('os_id') or '',
                'fans_id': b.get('fans_id') or '',
                'keyboard_id': b.get('keyboard_id') or '',
                'mouse_id': b.get('mouse_id') or '',
                'headset_id': b.get('headset_id') or '',
                'webcam_id': b.get('webcam_id') or '',
                'peripherals_id': b.get('peripherals_id') or '',
                'thermal_paste_id': b.get('thermal_paste_id') or '',
                'wifi_id': b.get('wifi_id') or '',
                'speakers_id': b.get('speakers_id') or '',
                'microphone_id': b.get('microphone_id') or '',
                'ups_id': b.get('ups_id') or '',
                'tool_id': b.get('tool_id') or '',
            })
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching user builds: {e}")
        return jsonify([])

@app.route('/analysis')
@login_required
def analysis():
    return render_template('analysis.html')

@app.route('/ai-recommendation')
@login_required
def ai_recommendation():
    return render_template('recommendation.html')

@app.route('/ai-demo')
@login_required
def ai_demo():
    return render_template('ai_demo.html')

@app.route('/support', methods=['GET', 'POST'])
@login_required
def support_page():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        user_email = request.form.get('user_email')
        request_type = request.form.get('request_type', 'General Feedback')
        user_message = request.form.get('user_message')
        
        # Save to database
        try:
            db = get_db()
            complaint_data = {
                'user_name': user_name,
                'user_email': user_email,
                'type': request_type,
                'message': user_message,
                'status': 'Pending',
                'created_at': datetime.now()
            }
            db.complaints.insert_one(complaint_data)
        except Exception as e:
            app.logger.error(f"Failed to save complaint to DB: {e}")

        success = send_contact_email(user_name, user_email, request_type, user_message)
        
        if success:
            flash(f'Thank you {user_name}! Your {request_type} message has been sent successfully.')
        else:
            flash('Message received and saved, but email notification failed.')
            
        return redirect(url_for('support_page'))
    return render_template('support.html')





def send_contact_email(name, email, req_type, message):
    """Send contact form details via email using SMTP settings from DB (fallback to .env)"""
    smtp_server = get_site_setting('SMTP_SERVER', os.getenv('SMTP_SERVER'))
    smtp_port = get_site_setting('SMTP_PORT', os.getenv('SMTP_PORT'))
    smtp_email = get_site_setting('SMTP_EMAIL', os.getenv('SMTP_EMAIL'))
    smtp_password = get_site_setting('SMTP_PASSWORD', os.getenv('SMTP_PASSWORD'))


    if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
        print(f"[MOCK CONTACT EMAIL] SMTP not configured. From: {name} ({email}) - Type: {req_type}")
        print(f"Message: {message}")
        return True

    try:
        # Create message for Admin/Support Team
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = smtp_email # Send to our own support email
        msg['Subject'] = f"RigMaster Support: {req_type} from {name}"

        body = f"New support request from RigMaster AI Contact Form:\n\n"
        body += f"Name: {name}\n"
        body += f"Email: {email}\n"
        body += f"Type: {req_type}\n\n"
        body += f"Message:\n{message}"
        
        msg.attach(MIMEText(body, 'plain'))

        # Add Reply-To so support can reply directly to the user
        msg.add_header('reply-to', email)

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, smtp_email, msg.as_string())
        
        # Optionally send a confirmation to the user
        confirm_msg = MIMEMultipart()
        confirm_msg['From'] = smtp_email
        confirm_msg['To'] = email
        confirm_msg['Subject'] = "RigMaster AI - We've received your message"
        
        confirm_body = f"Hi {name},\n\nWe've received your {req_type} request and our team will get back to you as soon as possible.\n\nYour message:\n\"{message}\"\n\nBest regards,\nThe RigMaster AI Team"
        confirm_msg.attach(MIMEText(confirm_body, 'plain'))
        
        server.sendmail(smtp_email, email, confirm_msg.as_string())
        
        server.quit()
        return True
    except Exception as e:
        app.logger.error(f"[EMAIL ERROR] Failed to send contact email: {e}")
        return False


@app.route('/vault')
@login_required
def vault():
    build_id = request.args.get('build_id')
    return redirect(url_for('insights_vault', build_id=build_id))


@app.route('/resources')
@login_required
def resources():
    return redirect(url_for('support_page'))

@app.route('/help')
@login_required
def help_center():
    return redirect(url_for('support_page', _anchor='help-center'))

@app.route('/contact')
@login_required
def contact():
    return redirect(url_for('support_page', _anchor='contact'))

@app.route('/feedback')
@login_required
def feedback():
    return redirect(url_for('support_page', _anchor='contact'))

@app.route('/admin/complaints')
@admin_required
def admin_complaints():
    try:
        db = get_db()
        if db is None:
            flash("Database connection unavailable.")
            return redirect(url_for('admin_dashboard'))
            
        complaints_list = list(db.complaints.find().sort('created_at', -1))
        # Convert ObjectId and datetime for template
        for c in complaints_list:
            c['_id'] = str(c['_id'])
            if 'created_at' in c:
                c['date'] = c['created_at'].strftime('%Y-%m-%d %H:%M')
        return render_template('admin/complaints.html', complaints=complaints_list)
    except Exception as e:
        app.logger.error(f"Admin Complaints Error: {e}")
        flash("Could not load complaints.")
        return redirect(url_for('admin_dashboard'))

@app.route('/api/admin/complaints/<complaint_id>', methods=['DELETE'])
@admin_required
def delete_complaint(complaint_id):
    try:
        db = get_db()
        db.complaints.delete_one({'_id': ObjectId(complaint_id)})
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/admin/complaints/<complaint_id>/status', methods=['POST'])
@admin_required
def update_complaint_status(complaint_id):
    try:
        db = get_db()
        data = request.json
        new_status = data.get('status', 'Pending')
        reply_message = data.get('reply_message', '').strip()
        
        # Get complaint info
        complaint = db.complaints.find_one({'_id': ObjectId(complaint_id)})
        if not complaint:
            return jsonify({'status': 'error', 'message': 'Complaint not found'}), 404

        db.complaints.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$set': {'status': new_status}}
        )

        # If a reply message was provided, send an email to the user
        if reply_message and complaint.get('user_email'):
            subject = f"Re: Your Support Request - RigMaster AI Admin"
            body = f"Hello {complaint.get('user_name', 'User')},\n\n" \
                   f"Regarding your query:\n\"{complaint.get('message', '')}\"\n\n" \
                   f"Admin Reply:\n{reply_message}\n\n" \
                   f"Status explicitly set to: {new_status}\n\n" \
                   f"Best regards,\nRigMaster AI Admin Team"
            
            send_generic_email(complaint['user_email'], subject, body)

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def send_generic_email(to_email, subject, body):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    smtp_server = get_site_setting('SMTP_SERVER', os.getenv('SMTP_SERVER'))
    smtp_port = get_site_setting('SMTP_PORT', os.getenv('SMTP_PORT'))
    smtp_email = get_site_setting('SMTP_EMAIL', os.getenv('SMTP_EMAIL'))
    smtp_password = get_site_setting('SMTP_PASSWORD', os.getenv('SMTP_PASSWORD'))


    if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
        print(f"[MOCK EMAIL] To: {to_email} | Subject: {subject} | Body: {body}")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_email, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
        return False

@app.route('/admin/broadcast', methods=['GET'])
@admin_required
def admin_broadcast():
    db = get_db()
    if db is None:
        flash("Database unavailable.")
        return redirect(url_for('admin_dashboard'))
    user_count = db.users.count_documents({})
    current_announcement = get_site_setting('global_announcement', '')
    maintenance_mode = get_site_setting('maintenance_mode', False)
    return render_template('admin/broadcast.html', 
                         user_count=user_count, 
                         global_announcement=current_announcement,
                         maintenance_mode=maintenance_mode)

@app.route('/api/admin/broadcast', methods=['POST'])
@admin_required
def api_admin_broadcast():
    try:
        data = request.json
        subject = data.get('subject')
        body = data.get('body')
        
        if not subject or not body:
            return jsonify({'status': 'error', 'message': 'Missing subject or body'}), 400
            
        db = get_db()
        # Find all users that have an email
        users = list(db.users.find({'email': {'$exists': True, '$ne': ''}}))
        
        # Send immediately to all in this thread (This could be optimized with Celery, but works for now)
        success_count = 0
        for user in users:
            personal_body = f"Hi {user.get('username', 'User')},\n\n{body}\n\n- RigMaster AI Team"
            if send_generic_email(user['email'], subject, personal_body):
                success_count += 1
                
        return jsonify({'status': 'success', 'sent_count': success_count})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/user-analytics', methods=['GET'])
@admin_required
def admin_user_analytics():
    db = get_db()
    if db is None:
        flash("Database connection unavailable. Please check your internet or MONGO_URI.")
        return redirect(url_for('admin_dashboard'))
    
    # Calculate simple DAU approximation
    metrics = {
        'dau': db.users.count_documents({}),
        'bpu': 0,
        'recent_signups': db.users.count_documents({}),
        'top_cpu': [],
        'top_gpu': []
    }
    
    # Approx BPU (Builds per User)
    total_users = db.users.count_documents({})
    total_builds = db.saved_builds.count_documents({})
    if total_users > 0:
        metrics['bpu'] = round(total_builds / total_users, 2)
        
    # Top CPUs
    pipeline_cpu = [
        {'$match': {'cpu_id': {'$exists': True, '$ne': None}}},
        {'$group': {'_id': '$cpu_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    top_cpu_res = list(db.saved_builds.aggregate(pipeline_cpu))
    
    cpu_list = []
    for c in top_cpu_res:
        comp = None
        try:
            comp = db.components.find_one({'_id': ObjectId(c['_id'])}, {'name': 1})
        except:
            pass
        cpu_list.append({'name': comp['name'] if comp else 'Unknown CPU', 'count': c['count']})
    metrics['top_cpu'] = cpu_list
    
    # Top GPUs
    pipeline_gpu = [
        {'$match': {'gpu_id': {'$exists': True, '$ne': None}}},
        {'$group': {'_id': '$gpu_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    top_gpu_res = list(db.saved_builds.aggregate(pipeline_gpu))
    
    gpu_list = []
    for g in top_gpu_res:
        comp = None
        try:
            comp = db.components.find_one({'_id': ObjectId(g['_id'])}, {'name': 1})
        except:
            pass
        gpu_list.append({'name': comp['name'] if comp else 'Unknown GPU', 'count': g['count']})
    metrics['top_gpu'] = gpu_list
    
    return render_template('admin/user_analytics.html', metrics=metrics)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not email or not username or not password:
            flash('All fields are required')
            return render_template('signup.html'), 400
            
        if len(password) < 6:
            flash('Password must be at least 6 characters')
            return render_template('signup.html'), 400
            
        if db is not None:
            # Check if user already exists
            if db.users.find_one({'$or': [{'email': email}, {'username': username}]}):
                flash('Email or username already exists')
                return render_template('signup.html'), 400
            
            hashed_password = generate_password_hash(password)
            db.users.insert_one({
                'email': email,
                'username': username,
                'password': hashed_password,
                'is_admin': False,
                'is_active': True,
                'created_at': datetime.now(timezone.utc)
            })
            flash('Account created! Please log in.')
            return redirect(url_for('login'))
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if db is not None:
            user = db.users.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                if not user.get('is_active', True):
                    flash('This account has been disabled. Please contact support.')
                    return render_template('login.html'), 401
                    
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                session['is_admin'] = user.get('is_admin', False)
                
                # Restore user's saved currency preference into session
                preferred_currency = user.get('preferred_currency', 'USD')
                if preferred_currency in EXCHANGE_RATES:
                    session['currency'] = preferred_currency
                    session['currency_symbol'] = CURRENCY_SYMBOLS.get(preferred_currency, '$')
                else:
                    session['currency'] = 'USD'
                    session['currency_symbol'] = '$'
                
                # Restore units preference
                session['units'] = user.get('preferred_units', 'Metric')
                
                if session['is_admin']:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('home'))
            
        flash('Invalid username or password')
        return render_template('login.html'), 401
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/saved-builds')
@login_required
def saved_builds():
    global db
    if db is None:
        db = get_db()
        
    if db is None:
        return render_template('saved_builds.html', builds=[])
        
    user_id = session.get('user_id')
    user_ids = [user_id]
    try:
        from bson.objectid import ObjectId
        user_ids.append(ObjectId(user_id))
    except:
        pass
        
    user_builds = list(db.saved_builds.find({'user_id': {'$in': user_ids}}).sort('created_at', -1))
    
    # Resolve IDs to names for display
    resolved_builds = []
    # Ordered slot rendering ensures all categories are always shown in a stable order
    slot_order = [
        ('cpu_id', 'CPU'),
        ('gpu_id', 'GPU'),
        ('motherboard_id', 'MOTHERBOARD'),
        ('ram_id', 'RAM'),
        ('storage_id', 'STORAGE'),
        ('psu_id', 'PSU'),
        ('case_id', 'CASE'),
        ('cooler_id', 'COOLER'),
        ('monitor_id', 'MONITOR'),
        ('os_id', 'OS'),
        ('fans_id', 'FANS'),
        ('peripherals_id', 'PERIPHERALS'),
        ('keyboard_id', 'KEYBOARD'),
        ('mouse_id', 'MOUSE'),
        ('headset_id', 'HEADSET'),
        ('webcam_id', 'WEBCAM'),
        ('thermal_paste_id', 'THERMAL PASTE'),
        ('wifi_id', 'WIFI ADAPTER'),
        ('speakers_id', 'SPEAKERS'),
        ('microphone_id', 'MICROPHONE'),
        ('ups_id', 'UPS/SURGE'),
        ('tool_id', 'ASSEMBLY TOOLS')
    ]
    
    for build in user_builds:
        # Get name with fallback and ensure it's a string
        db_name = build.get('name')
        if db_name is None or str(db_name).strip() == "":
            display_name = "Custom Rig"
        else:
            display_name = str(db_name).strip()
            
        qty = int(build.get('quantity', 1))
        build_details = {
            'id': str(build['_id']),
            'name': str(display_name or "Custom Rig").strip() or "Custom Rig",
            'date': build.get('created_at', datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M'),
            'is_public': build.get('is_public', False),
            'quantity': qty,
            'components': {}
        }
        
        EMOJI_MAP = {
            'CPU': '🧠', 'GPU': '🎮', 'MOTHERBOARD': '📟', 'RAM': '💾', 'STORAGE': '🗄️',
            'PSU': '⚡', 'CASE': '📦', 'COOLER': '❄️', 'MONITOR': '🖥️', 'OS': '🪟',
            'FANS': '🌪️', 'PERIPHERALS': '🔌', 'KEYBOARD': '⌨️', 'MOUSE': '🖱️',
            'HEADSET': '🎧', 'WEBCAM': '📷',
            'THERMAL PASTE': '🌡️', 'WIFI ADAPTER': '📶', 'SPEAKERS': '🔊', 
            'MICROPHONE': '🎙️', 'UPS/SURGE': '🔋', 'ASSEMBLY TOOLS': '🔧'
        }
        
        total_unit_cost = 0

        for key, raw_key in slot_order:
            comp_id = build.get(key)
            display_key = f"{EMOJI_MAP.get(raw_key, '')} {raw_key}".strip()
            if comp_id:
                try:
                    comp = db.components.find_one({'_id': ObjectId(comp_id)})
                    if comp:
                        cname = comp.get('name', 'Unknown')
                        build_details['components'][display_key] = cname
                        total_unit_cost += get_comp_price_usd(comp, id_key=key)
                    else:
                        build_details['components'][display_key] = "Unknown Component (ID: " + str(comp_id) + ")"
                except Exception:
                    build_details['components'][display_key] = "Invalid Component Reference"
            else:
                # Only show essential components if none selected, hide others to avoid clutter
                essentials = ['cpu_id', 'gpu_id', 'motherboard_id', 'ram_id', 'storage_id', 'psu_id']
                if key in essentials:
                    build_details['components'][display_key] = "None Selected"
                elif raw_key != 'PERIPHERALS':
                    build_details['components'][display_key] = "None"

        build_details['project_total'] = format_price(total_unit_cost)
        
        diff_info = calculate_build_difficulty(build)
        build_details['difficulty'] = diff_info['level']
        build_details['difficulty_explanation'] = diff_info['explanation']
        
        resolved_builds.append(build_details)
        
    return render_template('saved_builds.html', builds=resolved_builds)

@app.route('/api/delete_build/<build_id>', methods=['DELETE'])
@login_required
def delete_build(build_id):
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
            
        res = db.saved_builds.delete_one({
            '_id': ObjectId(build_id),
            'user_id': session.get('user_id')
        })
        
        if res.deleted_count > 0:
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Build not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# API Endpoints
def get_component_list(category_name):
    """Helper to fetch simplified component list from unified components table"""
    global db
    try:
        if db is None:
            db = get_db()
        if db is None:
            return []
            
        # category_name should be singular 'cpu', 'gpu' etc.
        # But our API routes usage below calls with 'cpus', 'gpus'...
        # Map them here
        cat_map = {
            'cpus': 'cpu',
            'gpus': 'gpu',
            'motherboards': 'motherboard',
            'ram': 'ram',
            'storage': 'storage',
            'psu': 'psu',
            'cases': 'case',
            'coolers': 'cooler',
            'monitors': 'monitor',
            'os': 'os',
            'peripherals': 'peripherals',
            'fans': 'fans'
        }
        target_cat = cat_map.get(category_name, category_name) # Fallback to input if not in map
        
        # Search for both 'ram' and 'memory' if RAM is requested due to DB inconsistency
        query = {'category': target_cat}
        if category_name == 'ram':
            query = {'category': {'$in': ['ram', 'memory']}}

        # sort by name, include status and brand for builder logic
        items = list(db.components.find(query, {'name': 1, 'status': 1, 'brand': 1}).sort('name', 1))
        return [{
            'id': str(item['_id']), 
            'name': item.get('name', 'Unknown'),
            'status': item.get('status', 'Active'),
            'brand': item.get('brand', 'Unknown')
        } for item in items]
    except Exception as e:
        app.logger.error(f"Error fetching {category_name}: {e}")
        return []

@app.route('/api/cpus')
@login_required
def api_cpus():
    return jsonify(get_component_list('cpus'))

@app.route('/api/gpus')
@login_required
def api_gpus():
    return jsonify(get_component_list('gpus'))

@app.route('/api/motherboards')
@login_required
def api_motherboards():
    return jsonify(get_component_list('motherboards'))

@app.route('/api/ram')
@login_required
def api_ram():
    return jsonify(get_component_list('ram'))

@app.route('/api/psu')
@login_required
def api_psu():
    return jsonify(get_component_list('psu'))

@app.route('/api/storage')
@login_required
def api_storage():
    return jsonify(get_component_list('storage'))

@app.route('/api/cases')
@login_required
def api_cases():
    return jsonify(get_component_list('cases'))

@app.route('/api/coolers')
@login_required
def api_coolers():
    return jsonify(get_component_list('coolers'))

@app.route('/api/monitors')
@login_required
def api_monitors():
    return jsonify(get_component_list('monitors'))

@app.route('/api/os')
@login_required
def api_os():
    return jsonify(get_component_list('os'))

@app.route('/api/peripherals')
@login_required
def api_peripherals():
    sub_cat = request.args.get('sub_category')
    if sub_cat:
        # Filter by sub_category
        try:
            items = list(db.components.find(
                {'category': 'peripherals', 'sub_category': sub_cat},
                {'name': 1, 'status': 1, 'brand': 1}
            ).sort('name', 1))
            return jsonify([{
                'id': str(item['_id']),
                'name': item.get('name', 'Unknown'),
                'status': item.get('status', 'Active'),
                'brand': item.get('brand', 'Unknown')
            } for item in items])
        except Exception as e:
            app.logger.error(f"Error fetching peripherals sub_category {sub_cat}: {e}")
            return jsonify([])
    return jsonify(get_component_list('peripherals'))

@app.route('/api/fans')
@login_required
def api_fans():
    return jsonify(get_component_list('fans'))
@app.route('/api/thermal_paste')
@login_required
def api_thermal_paste():
    return jsonify(get_component_list('thermal_paste'))

@app.route('/api/wifi_adapters')
@login_required
def api_wifi():
    return jsonify(get_component_list('wifi_adapters'))

@app.route('/api/speakers')
@login_required
def api_speakers():
    return jsonify(get_component_list('speakers'))

@app.route('/api/microphones')
@login_required
def api_microphones():
    return jsonify(get_component_list('microphones'))

@app.route('/api/ups')
@login_required
def api_ups():
    return jsonify(get_component_list('ups'))

@app.route('/api/tools')
@login_required
def api_tools():
    return jsonify(get_component_list('tools'))



# Test route to verify MongoDB connection
@app.route('/db-status')
@login_required
def db_status():
    try:
        global db
        if db is not None:
            db.client.admin.command('ping')
            return jsonify({'status': 'ok', 'message': 'MongoDB connection successful'})
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/save_build', methods=['POST'])
@login_required
def save_build():
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
            
        data = request.json
        app.logger.info(f"Incoming save_build request. Payload keys: {list(data.keys()) if data else 'None'}")
        
        build_id = data.get('build_id')
        quantity_raw = data.get('quantity', 1)
        try:
            quantity = int(quantity_raw) if quantity_raw is not None else 1
        except (ValueError, TypeError):
            quantity = 1
        if quantity < 1: quantity = 1
        
        # Establish user identity for both string and ObjectId formats
        user_id = session.get('user_id')
        user_ids_list = [user_id]
        try:
            from bson.objectid import ObjectId
            user_ids_list.append(ObjectId(user_id))
        except:
            pass

        raw_name = data.get('name')
        if raw_name and str(raw_name).strip():
            build_name = str(raw_name).strip()
        elif build_id:
            # Keep existing name if updating and no new name provided
            existing = db.saved_builds.find_one({'_id': ObjectId(build_id), 'user_id': {'$in': user_ids_list}})
            build_name = existing.get('name', 'Custom Rig') if existing else 'Custom Rig'
        else:
            count = db.saved_builds.count_documents({'user_id': {'$in': user_ids_list}})
            build_name = f"Custom Rig #{count + 1}"
            
        if not build_name or str(build_name).strip() == "":
            build_name = "Custom Rig"
        else:
            build_name = str(build_name).strip()[:100] # Cap length
            
        app.logger.info(f"Saving build '{build_name}' for user {user_id}")

        build_doc = {
            'user_id': user_id,
            'name': build_name,
            'cpu_id': data.get('cpu_id'),
            'gpu_id': data.get('gpu_id'),
            'motherboard_id': data.get('motherboard_id'),
            'ram_id': data.get('ram_id'),
            'storage_id': data.get('storage_id'),
            'psu_id': data.get('psu_id'),
            'case_id': data.get('case_id'),
            'cooler_id': data.get('cooler_id'),
            'monitor_id': data.get('monitor_id'),
            'os_id': data.get('os_id'),
            'peripherals_id': data.get('peripherals_id'),
            'keyboard_id': data.get('keyboard_id'),
            'mouse_id': data.get('mouse_id'),
            'headset_id': data.get('headset_id'),
            'webcam_id': data.get('webcam_id'),
            'fans_id': data.get('fans_id'),
            'thermal_paste_id': data.get('thermal_paste_id'),
            'wifi_id': data.get('wifi_id'),
            'speakers_id': data.get('speakers_id'),
            'microphone_id': data.get('microphone_id'),
            'ups_id': data.get('ups_id'),
            'tool_id': data.get('tool_id'),
            'quantity': quantity
        }
        
        if build_id:
            db.saved_builds.update_one(
                {'_id': ObjectId(build_id), 'user_id': {'$in': user_ids_list}},
                {'$set': build_doc}
            )
            inserted_id = build_id
        else:
            build_doc['created_at'] = datetime.now(timezone.utc)
            result = db.saved_builds.insert_one(build_doc)
            inserted_id = str(result.inserted_id)
        
        return jsonify({
            'status': 'success', 
            'message': 'Build saved successfully', 
            'id': inserted_id,
            'name': build_name
        })
    except Exception as e:
        app.logger.error(f"Error saving build: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/api/get_build/<build_id>')
@login_required
def api_get_build(build_id):
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
            
        build = db.saved_builds.find_one({
            '_id': ObjectId(build_id),
            'user_id': session.get('user_id')
        })
        
        if not build:
            return jsonify({'status': 'error', 'message': 'Build not found'}), 404
            
        # Convert ObjectId and datetime for JSON
        build['_id'] = str(build['_id'])
        if 'created_at' in build:
            build['created_at'] = build['created_at'].isoformat()
            
        return jsonify({
            'status': 'success',
            'build': build
        })
    except Exception as e:
        app.logger.error(f"Error getting build: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/validate_build', methods=['POST'])
@login_required
def api_validate_build():
    data = request.json
    return jsonify(run_validation_logic(data))

@app.route('/api/fix-compatibility', methods=['POST'])
@login_required
def api_fix_compatibility():
    """
    Identifies incompatibilities and suggests real parts from the database to fix them.
    """
    try:
        if db is None:
            return jsonify({'suggestions': [], 'status': 'Database Error'})
        data = request.json
        
        # Helper to get component safely
        def get_comp(comp_id):
            if not comp_id or comp_id == "None Selected": return None
            try: 
                from bson.objectid import ObjectId
                return db.components.find_one({'_id': ObjectId(comp_id)})
            except: return None

        cpu = get_comp(data.get('cpu_id'))
        mobo = get_comp(data.get('motherboard_id'))
        ram = get_comp(data.get('ram_id'))
        case = get_comp(data.get('case_id'))
        psu = get_comp(data.get('psu_id'))
        gpu = get_comp(data.get('gpu_id'))
        cooler = get_comp(data.get('cooler_id'))
        storage = get_comp(data.get('storage_id'))
        
        if not cpu or not mobo or not ram:
            return jsonify({'suggestions': [], 'status': 'Incomplete Selection'})
        
        suggestions = []
        
        # --- 1. Basic Constraints & Tiering ---
        cpu_sock = infer_cpu_socket(cpu)
        mobo_sock = infer_mobo_socket(mobo)
        mobo_ff = infer_mobo_form_factor(mobo)
        case_ffs = infer_case_supported_form_factors(case) if case else []
        ram_gen = infer_ram_generation(ram, is_mobo=False)
        mobo_ram_gen = infer_ram_generation(mobo, is_mobo=True)
        
        system_tier = max(get_comp_tier(cpu), get_comp_tier(gpu) if gpu else 1)
        
        socket_mismatch = cpu_sock and mobo_sock and cpu_sock not in [s.strip() for s in mobo_sock.split('/')]
        ff_mismatch = mobo_ff and case_ffs and mobo_ff not in case_ffs
        ram_gen_mismatch = ram_gen and mobo_ram_gen and ram_gen != mobo_ram_gen
        
        # --- 2. Motherboard / Case / RAM Generation Fixes ---
        if socket_mismatch or ram_gen_mismatch or ff_mismatch:
            # Suggest Motherboard swap that fixes multiple issues
            all_mobos = list(db.components.find({'category': 'motherboard'}).limit(300))
            mobo_matches = []
            for m in all_mobos:
                ms = infer_mobo_socket(m)
                mf = infer_mobo_form_factor(m)
                mrg = infer_ram_generation(m, is_mobo=True)
                
                # Must match CPU socket AND Case size AND RAM generation
                if ms and cpu_sock in [s.strip() for s in ms.split('/')]:
                    if (not case_ffs or mf in case_ffs) and (not ram_gen or mrg == ram_gen):
                        mobo_matches.append({'id': str(m['_id']), 'name': m.get('name'), 'dist': abs(get_comp_tier(m) - system_tier)})
            
            if mobo_matches:
                mobo_matches.sort(key=lambda x: x['dist'])
                suggestions.append({
                    'category': 'motherboard',
                    'title': f'Compatible {cpu_sock} Motherboard',
                    'reason': 'Resolves identified socket, form factor, or memory generation mismatches.',
                    'options': [{'id': m['id'], 'name': m['name']} for m in mobo_matches[:3]]
                })

            if socket_mismatch:
                all_cpus = list(db.components.find({'category': 'cpu'}).limit(200))
                cpu_matches = []
                for c in all_cpus:
                    cs = infer_cpu_socket(c)
                    if cs and mobo_sock and cs in [s.strip() for s in mobo_sock.split('/')]:
                        cpu_matches.append({'id': str(c['_id']), 'name': c.get('name'), 'dist': abs(get_comp_tier(c) - system_tier)})
                
                if cpu_matches:
                    cpu_matches.sort(key=lambda x: x['dist'])
                    suggestions.append({
                        'category': 'cpu',
                        'title': f'Compatible {mobo_sock} CPU',
                        'reason': f'Fits your selected {mobo.get("name")} ({mobo_sock}).',
                        'options': [{'id': c['id'], 'name': c['name']} for c in cpu_matches[:3]]
                    })

        if ff_mismatch:
            all_cases = list(db.components.find({'category': 'case'}).limit(300))
            roomy_cases = []
            for c in all_cases:
                if mobo_ff in infer_case_supported_form_factors(c):
                    roomy_cases.append({'id': str(c['_id']), 'name': c.get('name'), 'dist': abs(get_comp_tier(c) - system_tier)})
            if roomy_cases:
                roomy_cases.sort(key=lambda x: x['dist'])
                suggestions.append({
                    'category': 'case',
                    'title': f'Case supporting {mobo_ff}',
                    'reason': f'Your motherboard requires a case with {mobo_ff} support.',
                    'options': [{'id': c['id'], 'name': c['name']} for c in roomy_cases[:3]]
                })

        # --- 3. Physical Clearances (GPU / Cooler / PSU) ---
        if case:
            c_g_max = parse_dimension_mm(case, ['max_video_card_length', 'gpu_clearance'])
            c_c_max = parse_dimension_mm(case, ['max_cpucooler_height', 'cooler_clearance'])
            c_p_max = parse_dimension_mm(case, ['max_psu_length', 'psu_clearance'])
            
            if gpu:
                g_len = parse_dimension_mm(gpu, ['length', 'gpu_length'])
                if g_len > 0 and c_g_max > 0 and g_len > c_g_max:
                    fitting_cases = []
                    all_c = list(db.components.find({'category': 'case'}).limit(300))
                    for c in all_c:
                        if parse_dimension_mm(c, ['max_video_card_length', 'gpu_clearance']) >= g_len:
                            fitting_cases.append({'id': str(c['_id']), 'name': c.get('name'), 'dist': abs(get_comp_tier(c) - system_tier)})
                    if fitting_cases:
                        fitting_cases.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'case',
                            'title': 'Case with Better GPU Clearance',
                            'reason': f'The {gpu.get("name")} ({int(g_len)}mm) is too long for the current case.',
                            'options': [{'id': c['id'], 'name': c['name']} for c in fitting_cases[:3]]
                        })

            if cooler and cooler != "None Selected":
                c_h = parse_dimension_mm(cooler, ['height', 'cooler_height'])
                if c_h > 0 and c_c_max > 0 and c_h > c_c_max:
                    fitting_coolers = []
                    all_l = list(db.components.find({'category': 'cooler'}).limit(300))
                    for co in all_l:
                        h = parse_dimension_mm(co, ['height'])
                        if 0 < h <= c_c_max:
                            fitting_coolers.append({'id': str(co['_id']), 'name': co.get('name'), 'dist': abs(get_comp_tier(co) - system_tier)})
                    if fitting_coolers:
                        fitting_coolers.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'cooler',
                            'title': 'Lower Profile Cooler',
                            'reason': f'Cooler ({int(c_h)}mm) exceeds case height limit ({int(c_c_max)}mm).',
                            'options': [{'id': c['id'], 'name': c['name']} for c in fitting_coolers[:3]]
                        })

            if psu:
                p_len = parse_dimension_mm(psu, ['length', 'psu_length'])
                if p_len > 0 and c_p_max > 0 and p_len > c_p_max:
                    # Suggest cases with better PSU clearance
                    fitting_p_cases = []
                    all_c = list(db.components.find({'category': 'case'}).limit(300))
                    for c in all_c:
                        if parse_dimension_mm(c, ['max_psu_length', 'psu_clearance']) >= p_len:
                            fitting_p_cases.append({'id': str(c['_id']), 'name': c.get('name'), 'dist': abs(get_comp_tier(c) - system_tier)})
                    if fitting_p_cases:
                        fitting_p_cases.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'case',
                            'title': 'Case with Better PSU Room',
                            'reason': f'The selected PSU ({int(p_len)}mm) is too long for this case.',
                            'options': [{'id': c['id'], 'name': c['name']} for c in fitting_p_cases[:3]]
                        })

        # --- 4. PSU Wattage & Radiator Support ---
        power_analysis = run_power_analysis(data)
        if power_analysis.get('adequacy_status') == 'Insufficient':
            target_w = power_analysis.get('recommended_wattage', 600) + 100
            c_name = normalize(case.get('name')) if case else ""
            needs_sfx = any(x in c_name for x in ['SFX', 'MINI', 'ITX'])
            psus = list(db.components.find({'category': 'psu'}).limit(300))
            beefy_psus = []
            for p in psus:
                w = int(re.findall(r'\d+', str(p.get('wattage') or '0'))[0] or 0)
                if w >= target_w:
                    if not needs_sfx or 'SFX' in normalize(p.get('name')):
                        beefy_psus.append({'id': str(p['_id']), 'name': p.get('name'), 'dist': abs(get_comp_tier(p) - system_tier)})
            if beefy_psus:
                beefy_psus.sort(key=lambda x: x['dist'])
                suggestions.append({
                    'category': 'psu',
                    'title': f'High-Wattage PSU ({target_w}W+)',
                    'reason': f'System requires at least {power_analysis.get("recommended_wattage")}W.',
                    'options': [{'id': p['id'], 'name': p['name']} for p in beefy_psus[:3]]
                })

        # --- 5. Memory Slots & Capacity ---
        if ram and mobo:
            sticks = parse_ram_stick_count(ram)
            slots = infer_mobo_ram_slots(mobo)
            if sticks > slots:
                all_mobos = list(db.components.find({'category': 'motherboard'}).limit(300))
                slot_mobos = []
                for m in all_mobos:
                    if infer_mobo_ram_slots(m) >= sticks and (not cpu_sock or cpu_sock in [s.strip() for s in infer_mobo_socket(m).split('/')]):
                        slot_mobos.append({'id': str(m['_id']), 'name': m.get('name'), 'dist': abs(get_comp_tier(m) - system_tier)})
                if slot_mobos:
                    slot_mobos.sort(key=lambda x: x['dist'])
                    suggestions.append({
                        'category': 'motherboard',
                        'title': f'{sticks}-Slot Motherboard',
                        'reason': f'Selected RAM kit ({sticks} sticks) requires more slots than available ({slots}).',
                        'options': [{'id': m['id'], 'name': m['name']} for m in slot_mobos[:3]]
                    })

            ram_cap = parse_ram_capacity(ram)
            mobo_max_ram_f = mobo.get('max_ram') or mobo.get('max_memory')
            if ram_cap and mobo_max_ram_f:
                m_v = int(re.findall(r'\d+', str(mobo_max_ram_f))[0] if re.findall(r'\d+', str(mobo_max_ram_f)) else 0)
                if m_v > 0 and ram_cap > m_v:
                    all_mobos_cap = list(db.components.find({'category': 'motherboard'}).limit(300))
                    fitting_cap_mobos = []
                    for m in all_mobos_cap:
                        m_cap = int(re.findall(r'\d+', str(m.get('max_ram') or m.get('max_memory') or '0'))[0] or 0)
                        if m_cap >= ram_cap and (not cpu_sock or cpu_sock in [s.strip() for s in infer_mobo_socket(m).split('/')]):
                            fitting_cap_mobos.append({'id': str(m['_id']), 'name': m.get('name'), 'dist': abs(get_comp_tier(m) - system_tier)})
                    if fitting_cap_mobos:
                        fitting_cap_mobos.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'motherboard',
                            'title': f'Motherboard supporting {int(ram_cap)}GB',
                            'reason': f'RAM ({int(ram_cap)}GB) exceeds motherboard limit ({m_v}GB).',
                            'options': [{'id': m['id'], 'name': m['name']} for m in fitting_cap_mobos[:3]]
                        })

        # --- 6. Storage & M.2 Support ---
        if storage and mobo:
            s_t = normalize(storage.get('type') or storage.get('form_factor') or "")
            is_m2 = 'M.2' in s_t or 'NVME' in s_t
            m_slots = infer_mobo_storage_slots(mobo)
            if is_m2 and m_slots['m2'] == 0:
                # Suggest mobo with M.2
                all_mobos_m2 = list(db.components.find({'category': 'motherboard'}).limit(300))
                m2_mobos = []
                for m in all_mobos_m2:
                    if infer_mobo_storage_slots(m)['m2'] > 0 and (not cpu_sock or cpu_sock in [s.strip() for s in infer_mobo_socket(m).split('/')]):
                        m2_mobos.append({'id': str(m['_id']), 'name': m.get('name'), 'dist': abs(get_comp_tier(m) - system_tier)})
                if m2_mobos:
                    m2_mobos.sort(key=lambda x: x['dist'])
                    suggestions.append({
                        'category': 'motherboard',
                        'title': 'Motherboard with M.2 Support',
                        'reason': 'Selected M.2 storage is not supported by current board.',
                        'options': [{'id': m['id'], 'name': m['name']} for m in m2_mobos[:3]]
                    })
                # Or suggest SATA storage
                all_sata = list(db.components.find({'category': 'storage'}).limit(300))
                sata_options = []
                for s in all_sata:
                    if 'M.2' not in normalize(s.get('type') or '') and 'NVME' not in normalize(s.get('type') or ''):
                        sata_options.append({'id': str(s['_id']), 'name': s.get('name'), 'dist': abs(get_comp_tier(s) - system_tier)})
                if sata_options:
                    sata_options.sort(key=lambda x: x['dist'])
                    suggestions.append({
                        'category': 'storage',
                        'title': 'SATA SSD Alternative',
                        'reason': 'Current board lacks M.2 slots; suggest switching to a standard SATA drive.',
                        'options': [{'id': s['id'], 'name': s['name']} for s in sata_options[:3]]
                    })

        # --- 7. Cooler Socket & TDP Fix ---
        if cpu:
            tdp_v = int(re.findall(r'\d+', str(cpu.get('tdp', '0')))[0] or 0)
            if cooler and cooler != "None Selected":
                c_supp = infer_cooler_socket_support(cooler)
                if cpu_sock and c_supp and cpu_sock not in c_supp:
                    all_coolers = list(db.components.find({'category': 'cooler'}).limit(300))
                    fitting_coolers = []
                    for c in all_coolers:
                        if cpu_sock in infer_cooler_socket_support(c):
                            fitting_coolers.append({'id': str(c['_id']), 'name': c.get('name'), 'dist': abs(get_comp_tier(c) - system_tier)})
                    if fitting_coolers:
                        fitting_coolers.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'cooler',
                            'title': f'Cooler supporting {cpu_sock}',
                            'reason': f'Selected cooler does not officially support the {cpu_sock} socket.',
                            'options': [{'id': c['id'], 'name': c['name']} for c in fitting_coolers[:3]]
                        })
            elif tdp_v > 105:
                # Suggest a cooler for high TDP
                all_at = list(db.components.find({'category': 'cooler'}).limit(300))
                high_coolers = []
                for c in all_at:
                    if cpu_sock and cpu_sock in infer_cooler_socket_support(c):
                        high_coolers.append({'id': str(c['_id']), 'name': c.get('name'), 'dist': abs(get_comp_tier(c) - system_tier)})
                if high_coolers:
                    high_coolers.sort(key=lambda x: x['dist'])
                    suggestions.append({
                        'category': 'cooler',
                        'title': 'High-Performance Cooling',
                        'reason': 'High-TDP processor requires substantial thermal solution.',
                        'options': [{'id': c['id'], 'name': c['name']} for c in high_coolers[:3]]
                    })

        # --- 8. Missing Components ---
        critical = {'cpu_id': 'cpu', 'motherboard_id': 'motherboard', 'ram_id': 'ram', 'psu_id': 'psu', 'case_id': 'case', 'storage_id': 'storage'}
        for key, cat in critical.items():
            if not data.get(key) or data.get(key) == "None Selected":
                items = list(db.components.find({'category': cat if cat != 'ram' else {'$in': ['ram', 'memory']}}).limit(300))
                matches = [{'id': str(i['_id']), 'name': i.get('name'), 'dist': abs(get_comp_tier(i) - system_tier)} for i in items]
                if matches:
                    matches.sort(key=lambda x: x['dist'])
                    suggestions.append({
                        'category': cat,
                        'title': f'Essential {cat.upper()}',
                        'reason': f'Your build is missing a {cat}.',
                        'options': [{'id': m['id'], 'name': m['name']} for m in matches[:3]]
                    })

        # Discrete GPU Necessity
        has_igpu = False
        if cpu:
            cn = normalize(cpu.get('name'))
            if 'INTEL' in cn and '-F' not in cn: has_igpu = True
            elif 'RYZEN' in cn and ('G' in cn or '7000' in cn or '9000' in cn): has_igpu = True
        
        if not has_igpu and (not data.get('gpu_id') or data.get('gpu_id') == "None Selected"):
            gpus = list(db.components.find({'category': 'gpu'}).limit(200))
            gpu_matches = [{'id': str(i['_id']), 'name': i.get('name'), 'dist': abs(get_comp_tier(i) - system_tier)} for i in gpus]
            if gpu_matches:
                gpu_matches.sort(key=lambda x: x['dist'])
                suggestions.append({
                    'category': 'gpu',
                    'title': 'Discrete GPU Required',
                    'reason': 'Your CPU lacks integrated graphics; a dedicated GPU is necessary for display output.',
                    'options': [{'id': g['id'], 'name': g['name']} for g in gpu_matches[:3]]
                })

        # --- 9. Thermal Paste & Essentials ---
        if cpu and (not data.get('thermal_paste_id') or data.get('thermal_paste_id') == "None Selected"):
            tdp_val = int(re.findall(r'\d+', str(cpu.get('tdp', '0')))[0] or 0)
            if tdp_val > 100:
                pastes = list(db.components.find({'category': 'thermal_paste'}).limit(10))
                if pastes:
                    suggestions.append({
                        'category': 'thermal_paste',
                        'title': 'Performance Thermal Paste',
                        'reason': 'Recommended for stable thermals on high-output CPUs.',
                        'options': [{'id': str(p['_id']), 'name': p.get('name')} for p in pastes[:3]]
                    })

        # ===== ADVANCED SUGGESTION TIER =====
        
        # --- 10. CPU Power Delivery & Voltage Optimization ---
        if cpu and mobo:
            cpu_tdp = infer_cpu_tdp(cpu)
            cpu_voltage = infer_cpu_voltage(cpu)
            mobo_vrm = infer_mobo_vrm_phases(mobo)
            
            if cpu_tdp > 140 and mobo_vrm < 16:
                # Suggest high-end motherboards with better VRM
                try:
                    cpu_socket = infer_cpu_socket(cpu)
                    high_vrm_mobos = list(db.components.find({'category': 'motherboard'}).limit(300))
                    vrm_matches = []
                    for m in high_vrm_mobos:
                        if cpu_socket and cpu_socket in [s.strip() for s in (infer_mobo_socket(m) or '').split('/')]:
                            mobo_vrm_check = infer_mobo_vrm_phases(m)
                            if mobo_vrm_check >= 16:
                                vrm_matches.append({'id': str(m['_id']), 'name': m.get('name'), 'dist': abs(get_comp_tier(m) - system_tier)})
                    if vrm_matches:
                        vrm_matches.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'motherboard',
                            'title': f'High-Power-Delivery Motherboard (16+ Phase VRM)',
                            'reason': f'Your {int(cpu_tdp)}W CPU benefits from robust VRM; current board has only {mobo_vrm} phases.',
                            'options': [{'id': m['id'], 'name': m['name']} for m in vrm_matches[:3]]
                        })
                except Exception:
                    pass
        
        # --- 11. GPU Performance & Power Optimization ---
        if gpu and psu:
            gpu_vram = infer_gpu_vram(gpu)
            gpu_tdp = infer_gpu_tdp(gpu)
            psu_wattage = extract_numeric_value(psu.get('wattage') or psu.get('power'))
            gpu_bus = infer_gpu_bus_width(gpu)
            
            # Suggest better GPUs with more VRAM
            if gpu_vram > 0 and gpu_vram <= 8:
                try:
                    all_gpus = list(db.components.find({'category': 'gpu'}).limit(300))
                    better_gpus = []
                    for g in all_gpus:
                        g_vram = infer_gpu_vram(g)
                        if g_vram > gpu_vram and psu_wattage > infer_gpu_tdp(g) * 1.5:
                            better_gpus.append({'id': str(g['_id']), 'name': g.get('name'), 'dist': abs(get_comp_tier(g) - system_tier)})
                    if better_gpus:
                        better_gpus.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'gpu',
                            'title': f'Upgrade GPU: {int(gpu_vram)}GB → {int(infer_gpu_vram(better_gpus[0]['name']))}GB+',
                            'reason': f'Current GPU has {int(gpu_vram)}GB VRAM; system has power headroom for higher VRAM models.',
                            'options': [{'id': g['id'], 'name': g['name']} for g in better_gpus[:3]]
                        })
                except Exception:
                    pass
            
            # Suggest wider memory bus GPUs
            if gpu_bus > 0 and gpu_bus < 256:
                try:
                    all_gpus = list(db.components.find({'category': 'gpu'}).limit(300))
                    better_bus = []
                    for g in all_gpus:
                        g_bus = infer_gpu_bus_width(g)
                        if g_bus >= 256 and get_comp_tier(g) <= get_comp_tier(gpu) + 1:
                            better_bus.append({'id': str(g['_id']), 'name': g.get('name'), 'dist': abs(infer_gpu_bus_width(g) - 256)})
                    if better_bus:
                        better_bus.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'gpu',
                            'title': f'Enhance GPU Memory Bus: {int(gpu_bus)}-bit → 256-bit+',
                            'reason': f'Current GPU has {int(gpu_bus)}-bit bus; wider bus improves bandwidth and stability.',
                            'options': [{'id': g['id'], 'name': g['name']} for g in better_bus[:3]]
                        })
                except Exception:
                    pass
        
        # --- 12. RAM Performance Optimization ---
        if ram and mobo:
            ram_speed = infer_ram_speed(ram)
            ram_timing = infer_ram_timing(ram)
            ram_voltage = infer_ram_voltage(ram)
            ram_gen = infer_ram_generation(ram, is_mobo=False)
            mobo_gen = infer_ram_generation(mobo, is_mobo=True)
            
            # Suggest faster RAM for same generation
            if ram_speed > 0 and ram_speed < 5400 and ram_gen == mobo_gen:
                try:
                    all_ram = list(db.components.find({'category': 'ram'}).limit(300))
                    faster_ram = []
                    for r in all_ram:
                        if infer_ram_generation(r, is_mobo=False) == ram_gen and infer_ram_speed(r) > ram_speed:
                            faster_ram.append({'id': str(r['_id']), 'name': r.get('name'), 'dist': abs(get_comp_tier(r) - system_tier)})
                    if faster_ram:
                        faster_ram.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'ram',
                            'title': f'Faster RAM: {int(ram_speed)}MHz → 5600MHz+',
                            'reason': f'Upgrading RAM speed improves system responsiveness and gaming FPS. Current: {int(ram_speed)}MHz.',
                            'options': [{'id': r['id'], 'name': r['name']} for r in faster_ram[:3]]
                        })
                except Exception:
                    pass
            
            # Suggest lower-latency RAM
            if ram_timing > 20 and ram_gen == 'DDR5':
                try:
                    all_ram = list(db.components.find({'category': 'ram'}).limit(250))
                    tight_ram = []
                    for r in all_ram:
                        if infer_ram_generation(r, is_mobo=False) == 'DDR5' and infer_ram_timing(r) < ram_timing and infer_ram_timing(r) > 0:
                            tight_ram.append({'id': str(r['_id']), 'name': r.get('name'), 'dist': abs(get_comp_tier(r) - system_tier)})
                    if tight_ram:
                        tight_ram.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'ram',
                            'title': f'Tighter Timings: CL{int(ram_timing)} → CL16-18',
                            'reason': f'Tighter CAS latency (CL{int(ram_timing)} → CL16-18) improves latency-sensitive workloads.',
                            'options': [{'id': r['id'], 'name': r['name']} for r in tight_ram[:3]]
                        })
                except Exception:
                    pass
        
        # --- 13. Motherboard Connectivity & Feature Upgrades ---
        if mobo:
            mobo_usb = extract_usb_ports(mobo)
            mobo_audio = infer_audio_codec(mobo)
            mobo_pcie = infer_mobo_pcie_lanes(mobo)
            
            # Suggest boards with more USB ports
            if mobo_usb['usb3'] < 4 or mobo_usb['type_c'] == 0:
                try:
                    mobo_socket = infer_mobo_socket(mobo)
                    cpu_sock_match = infer_cpu_socket(cpu) if cpu else None
                    upgraded_mobos = list(db.components.find({'category': 'motherboard'}).limit(300))
                    better_usb = []
                    for m in upgraded_mobos:
                        if (not cpu_sock_match or cpu_sock_match in [s.strip() for s in (infer_mobo_socket(m) or '').split('/')]):
                            m_usb = extract_usb_ports(m)
                            if m_usb['usb3'] >= 6 or m_usb['type_c'] >= 2:
                                better_usb.append({'id': str(m['_id']), 'name': m.get('name'), 'dist': abs(get_comp_tier(m) - system_tier)})
                    if better_usb:
                        better_usb.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'motherboard',
                            'title': 'Enhanced Connectivity: USB 3.x + Type-C',
                            'reason': f'Current board has {mobo_usb["usb3"]} USB 3.x + {mobo_usb["type_c"]} Type-C; upgrade for modern peripherals.',
                            'options': [{'id': m['id'], 'name': m['name']} for m in better_usb[:3]]
                        })
                except Exception:
                    pass
            
            # Suggest boards with better audio
            if mobo_audio != 'High-End':
                try:
                    mobo_socket = infer_mobo_socket(mobo)
                    cpu_sock_match = infer_cpu_socket(cpu) if cpu else None
                    audio_upgrade = list(db.components.find({'category': 'motherboard'}).limit(300))
                    better_audio = []
                    for m in audio_upgrade:
                        if (not cpu_sock_match or cpu_sock_match in [s.strip() for s in (infer_mobo_socket(m) or '').split('/')]):
                            if infer_audio_codec(m) == 'High-End' and get_comp_tier(m) <= system_tier + 1:
                                better_audio.append({'id': str(m['_id']), 'name': m.get('name'), 'dist': abs(get_comp_tier(m) - system_tier)})
                    if better_audio:
                        better_audio.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'motherboard',
                            'title': 'High-End Audio Codec Upgrade',
                            'reason': f'Current board: {mobo_audio}; upgrade to High-End codec for audiophile-grade sound.',
                            'options': [{'id': m['id'], 'name': m['name']} for m in better_audio[:3]]
                        })
                except Exception:
                    pass
        
        # --- 14. Storage – NVMe Optimization ---
        if storage:
            storage_protocol = infer_storage_protocol(storage)
            storage_interface = infer_storage_interface(storage)
            
            # Suggest PCIe 5.0 storage if on compatible system
            if storage_interface == 'NVMe' and 'PCIe 4' in str(storage_protocol):
                if mobo and mobo_pcie >= 20:
                    try:
                        all_storage = list(db.components.find({'category': 'storage'}).limit(200))
                        pcie5_storage = []
                        for s in all_storage:
                            if 'PCIe 5' in infer_storage_protocol(s):
                                pcie5_storage.append({'id': str(s['_id']), 'name': s.get('name'), 'dist': abs(get_comp_tier(s) - system_tier)})
                        if pcie5_storage:
                            pcie5_storage.sort(key=lambda x: x['dist'])
                            suggestions.append({
                                'category': 'storage',
                                'title': 'PCIe 5.0 NVMe Storage Upgrade',
                                'reason': 'Your system supports PCIe 5.0; upgrade to newest gen for future-proofing.',
                                'options': [{'id': s['id'], 'name': s['name']} for s in pcie5_storage[:3]]
                            })
                    except Exception:
                        pass
        
        # --- 15. Cooler TDP Rating & Performance ---
        if cpu and cooler:
            cpu_tdp = infer_cpu_tdp(cpu)
            if cpu_tdp > 100:
                try:
                    cpu_sock_check = infer_cpu_socket(cpu)
                    all_coolers = list(db.components.find({'category': 'cooler'}).limit(300))
                    premium_coolers = []
                    for c in all_coolers:
                        c_sock = infer_cooler_socket_support(c)
                        if cpu_sock_check and cpu_sock_check in c_sock:
                            c_name = normalize(c.get('name', ''))
                            if any(x in c_name for x in ['AIO', 'LIQUID', 'ELITE', 'DARK', 'NOCTUA']):
                                premium_coolers.append({'id': str(c['_id']), 'name': c.get('name'), 'dist': abs(get_comp_tier(c) - system_tier)})
                    if premium_coolers:
                        premium_coolers.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'cooler',
                            'title': f'Premium Cooling for {int(cpu_tdp)}W CPU',
                            'reason': f'High-performance CPU ({int(cpu_tdp)}W) benefits from top-tier cooling solution.',
                            'options': [{'id': c['id'], 'name': c['name']} for c in premium_coolers[:3]]
                        })
                except Exception:
                    pass
        
        # --- 16. PSU Efficiency & Modularity ---
        if psu:
            psu_efficiency = infer_psu_efficiency_rating(psu)
            psu_modularity = infer_psu_modularity(psu)
            psu_wattage = extract_numeric_value(psu.get('wattage') or psu.get('power'))
            
            # Suggest higher efficiency
            if psu_efficiency not in ['Platinum', 'Titanium'] and psu_wattage > 650:
                try:
                    all_psus = list(db.components.find({'category': 'psu'}).limit(200))
                    efficient_psus = []
                    for p in all_psus:
                        p_watt = extract_numeric_value(p.get('wattage') or p.get('power'))
                        if p_watt >= psu_wattage * 0.9 and infer_psu_efficiency_rating(p) in ['Platinum', 'Titanium']:
                            efficient_psus.append({'id': str(p['_id']), 'name': p.get('name'), 'dist': abs(get_comp_tier(p) - system_tier)})
                    if efficient_psus:
                        efficient_psus.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'psu',
                            'title': f'Upgrade to {infer_psu_efficiency_rating(efficient_psus[0]["name"])} Rated PSU',
                            'reason': f'Platinum/Titanium PSU reduces power loss, heat, and electricity costs over time.',
                            'options': [{'id': p['id'], 'name': p['name']} for p in efficient_psus[:3]]
                        })
                except Exception:
                    pass
            
            # Suggest modular PSU
            if psu_modularity == 'Non-Modular':
                try:
                    all_psus = list(db.components.find({'category': 'psu'}).limit(200))
                    modular_psus = []
                    for p in all_psus:
                        p_watt = extract_numeric_value(p.get('wattage') or p.get('power'))
                        if p_watt >= psu_wattage * 0.9 and infer_psu_modularity(p) in ['Fully Modular', 'Semi-Modular']:
                            modular_psus.append({'id': str(p['_id']), 'name': p.get('name'), 'dist': abs(get_comp_tier(p) - system_tier)})
                    if modular_psus:
                        modular_psus.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'psu',
                            'title': 'Modular/Semi-Modular PSU for Better Cable Management',
                            'reason': 'Modular cables reduce clutter, improve airflow, and simplify future upgrades.',
                            'options': [{'id': p['id'], 'name': p['name']} for p in modular_psus[:3]]
                        })
                except Exception:
                    pass
        
        # --- 17. Case Airflow & Thermal Optimization ---
        if case and cpu:
            cpu_tdp = infer_cpu_tdp(cpu)
            case_airflow = infer_case_airflow_design(case)
            if cpu_tdp > 100 and case_airflow == 'Standard':
                try:
                    all_cases = list(db.components.find({'category': 'case'}).limit(250))
                    airflow_cases = []
                    for c in all_cases:
                        if infer_case_airflow_design(c) in ['Optimized Flow', 'Open-Frame']:
                            airflow_cases.append({'id': str(c['_id']), 'name': c.get('name'), 'dist': abs(get_comp_tier(c) - system_tier)})
                    if airflow_cases:
                        airflow_cases.sort(key=lambda x: x['dist'])
                        suggestions.append({
                            'category': 'case',
                            'title': 'Optimized Airflow Case for High-Performance System',
                            'reason': f'Your {int(cpu_tdp)}W system benefits from case with optimized airflow design.',
                            'options': [{'id': c['id'], 'name': c['name']} for c in airflow_cases[:3]]
                        })
                except Exception:
                    pass
        
        # --- 18. Premium Thermal Paste for High-End Builds ---
        if cpu and (not data.get('thermal_paste_id') or data.get('thermal_paste_id') == "None Selected"):
            cpu_tdp = infer_cpu_tdp(cpu)
            if cpu_tdp > 140:
                try:
                    premium_pastes = list(db.components.find({'category': 'thermal_paste'}).limit(15))
                    if premium_pastes:
                        paste_options = [{'id': str(p['_id']), 'name': p.get('name')} for p in premium_pastes]
                        suggestions.append({
                            'category': 'thermal_paste',
                            'title': 'Ultra-Premium Thermal Paste (High-TDP System)',
                            'reason': f'Your {int(cpu_tdp)}W CPU requires premium thermal interface for optimal heat transfer.',
                            'options': paste_options[:3]
                        })
                except Exception:
                    pass

        return jsonify({'status': 'success', 'suggestions': suggestions})
    except Exception as e:
        app.logger.error(f"Fix Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/simulate-upgrade', methods=['POST'])
@login_required
def api_simulate_upgrade():
    """
    Analyzes an upgrade path using the upgraded AI Engine.
    """
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database connection unavailable.'}), 503
        data = request.json
        original_id = data.get('original_build_id')
        upgrades = data.get('upgraded_components', {})

        if not upgrades:
            return jsonify({'status': 'error', 'message': 'No upgrade components provided'}), 400

        # Helper to resolve IDs to names from unified components collection
        def get_name(comp_id):
            if not comp_id or comp_id == "None Selected":
                return "None"
            try:
                from bson.objectid import ObjectId
                comp = db.components.find_one({'_id': ObjectId(comp_id)})
                return comp.get('name', 'Unknown') if comp else "Unknown"
            except:
                return "Unknown"

        # 1. Resolve original configuration
        original_resolved = {}
        if original_id:
            try:
                build = db.saved_builds.find_one({'_id': ObjectId(original_id)})
                if build:
                    original_resolved = {
                        'CPU': get_name(build.get('cpu_id')),
                        'MOTHERBOARD': get_name(build.get('motherboard_id')),
                        'RAM': get_name(build.get('ram_id')),
                        'GPU': get_name(build.get('gpu_id')),
                        'STORAGE': get_name(build.get('storage_id')),
                        'PSU': get_name(build.get('psu_id')),
                        'CASE': get_name(build.get('case_id')),
                        'COOLER': get_name(build.get('cooler_id')),
                        'MONITOR': get_name(build.get('monitor_id')),
                        'OS': get_name(build.get('os_id')),
                        'PERIPHERALS': get_name(build.get('peripherals_id')),
                        'KEYBOARD': get_name(build.get('keyboard_id')),
                        'MOUSE': get_name(build.get('mouse_id')),
                        'HEADSET': get_name(build.get('headset_id')),
                        'WEBCAM': get_name(build.get('webcam_id')),
                        'FANS': get_name(build.get('fans_id')),
                        'THERMAL_PASTE': get_name(build.get('thermal_paste_id')),
                        'WIFI': get_name(build.get('wifi_id')),
                        'SPEAKERS': get_name(build.get('speakers_id')),
                        'MICROPHONE': get_name(build.get('microphone_id')),
                        'UPS': get_name(build.get('ups_id')),
                        'TOOLS': get_name(build.get('tool_id'))
                    }
            except:
                pass
        
        # Fallback: Resolve from original_components if provided (for unsaved builds)
        if not original_resolved and data.get('original_components'):
            orig = data.get('original_components')
            original_resolved = {
                'CPU': get_name(orig.get('cpu_id')),
                'MOTHERBOARD': get_name(orig.get('motherboard_id')),
                'RAM': get_name(orig.get('ram_id')),
                'GPU': get_name(orig.get('gpu_id')),
                'STORAGE': get_name(orig.get('storage_id')),
                'PSU': get_name(orig.get('psu_id')),
                'CASE': get_name(orig.get('case_id')),
                'COOLER': get_name(orig.get('cooler_id')),
                'MONITOR': get_name(orig.get('monitor_id')),
                'OS': get_name(orig.get('os_id')),
                'PERIPHERALS': get_name(orig.get('peripherals_id')),
                'KEYBOARD': get_name(orig.get('keyboard_id')),
                'MOUSE': get_name(orig.get('mouse_id')),
                'HEADSET': get_name(orig.get('headset_id')),
                'WEBCAM': get_name(orig.get('webcam_id')),
                'FANS': get_name(orig.get('fans_id')),
                'THERMAL_PASTE': get_name(orig.get('thermal_paste_id')),
                'WIFI': get_name(orig.get('wifi_id')),
                'SPEAKERS': get_name(orig.get('speakers_id')),
                'MICROPHONE': get_name(orig.get('microphone_id')),
                'UPS': get_name(orig.get('ups_id')),
                'TOOLS': get_name(orig.get('tool_id'))
            }

        # 2. Resolve upgraded configuration
        sim_resolved = {
            'CPU': get_name(upgrades.get('cpu_id')),
            'GPU': get_name(upgrades.get('gpu_id')),
            'MOTHERBOARD': get_name(upgrades.get('motherboard_id')),
            'RAM': get_name(upgrades.get('ram_id')),
            'STORAGE': get_name(upgrades.get('storage_id')),
            'PSU': get_name(upgrades.get('psu_id')),
            'CASE': get_name(upgrades.get('case_id')),
            'COOLER': get_name(upgrades.get('cooler_id')),
            'MONITOR': get_name(upgrades.get('monitor_id')),
            'OS': get_name(upgrades.get('os_id')),
            'PERIPHERALS': get_name(upgrades.get('peripherals_id')),
            'KEYBOARD': get_name(upgrades.get('keyboard_id')),
            'MOUSE': get_name(upgrades.get('mouse_id')),
            'HEADSET': get_name(upgrades.get('headset_id')),
            'WEBCAM': get_name(upgrades.get('webcam_id')),
            'FANS': get_name(upgrades.get('fans_id')),
            'THERMAL_PASTE': get_name(upgrades.get('thermal_paste_id')),
            'WIFI': get_name(upgrades.get('wifi_id')),
            'SPEAKERS': get_name(upgrades.get('speakers_id')),
            'MICROPHONE': get_name(upgrades.get('microphone_id')),
            'UPS': get_name(upgrades.get('ups_id')),
            'TOOLS': get_name(upgrades.get('tool_id'))
        }

        # 3. Get AI Analysis from upgraded Engine
        ai_engine = get_ai_engine()
        explanation = ai_engine.simulate_upgrade(original_resolved, sim_resolved)

        # 4. Run standard validation for badges
        validation = run_validation_logic(upgrades)
        power = run_power_analysis(upgrades)

        return jsonify({
            'status': 'success',
            'explanation': explanation,
            'validation': validation,
            'power': power,
            'original': original_resolved,
            'simulated': sim_resolved
        })

    except Exception as e:
        app.logger.error(f"Simulate upgrade error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analyze_upgrade', methods=['POST'])
@login_required
def api_analyze_upgrade():
    """
    Analyzes the upgrade potential of a build.
    Used by the main Analysis dashboard.
    """
    try:
        data = request.json
        # Helper to get component safely
        def get_comp(col, comp_id):
            if db is None: return None
            if not comp_id: return None
            try: return db[col].find_one({'_id': ObjectId(comp_id)})
            except: return None

        # Initialize ALL categories with defaults so the frontend never gets undefined
        results = {
            'ram':     {'status': 'Ready', 'message': 'Memory slots available for expansion.'},
            'storage': {'status': 'Ready', 'message': 'Multiple expansion slots available for high-speed storage.'},
            'gpu':     {'status': 'Ready', 'message': 'GPU slot clear for current and next-gen cards.'},
            'cpu':     {'status': 'Ready', 'message': 'Platform supports current-generation processors.'},
            'psu':     {'status': 'Ready', 'message': 'Power supply provides growth capacity.'},
            'case':    {'status': 'Ready', 'message': 'Standard ATX case clearance expected.'},
            'cooling': {'status': 'Ready', 'message': 'Mounting patterns support standard AIO and high-end air cooling.'},
        }
        
        cpu = get_comp('components', data.get('cpu_id'))
        mobo = get_comp('components', data.get('motherboard_id'))
        psu = get_comp('components', data.get('psu_id'))
        gpu = get_comp('components', data.get('gpu_id'))
        ram = get_comp('components', data.get('ram_id'))
        storage = get_comp('components', data.get('storage_id'))
        case = get_comp('components', data.get('case_id'))
        cooler = get_comp('components', data.get('cooler_id'))

        # 1. RAM & Storage Readiness
        if mobo and ram:
            max_slots = 4
            if 'ITX' in str(mobo.get('name', '')).upper(): max_slots = 2
            ram_name = str(ram.get('name', '')).upper()
            if f'{max_slots}X' in ram_name:
                results['ram'] = {'status': 'Limited', 'message': 'All memory slots occupied. Requires full replacement to upgrade.'}
        
        # 2. GPU / PSU Readiness
        power = run_power_analysis(data)
        if power.get('adequacy_status') != 'Safe':
            results['gpu'] = {'status': 'Limited', 'message': 'Estimated power draw is near PSU limits. PSU upgrade recommended for higher-tier GPUs.'}
            results['psu'] = {'status': 'Limited', 'message': 'Current PSU has low headroom for high-power modern components.'}
        else:
             results['psu'] = {'status': 'Ready', 'message': 'Power supply provides significant growth capacity.'}

        # 3. CPU / Platform Readiness
        if cpu:
            name = str(cpu.get('name', '')).upper()
            if 'AM4' in name or 'LGA1200' in name or 'LGA1151' in name:
                results['cpu'] = {'status': 'Limited', 'message': 'End-of-life socket. Significant upgrades require a new motherboard.'}
            elif 'AM5' in name or 'LGA1700' in name:
                results['cpu'] = {'status': 'Ready', 'message': 'Active socket. Supports latest and upcoming processor generations.'}

        # 4. Cooling & Case Readiness
        if cooler and cpu:
            try:
                tdp_raw = cpu.get('tdp', 65)
                if isinstance(tdp_raw, str):
                    import re as _re
                    nums = _re.findall(r'\d+', tdp_raw)
                    tdp = int(nums[0]) if nums else 65
                elif isinstance(tdp_raw, (int, float)):
                    tdp = int(tdp_raw)
                else:
                    tdp = 65
            except:
                tdp = 65
            c_type = str(cooler.get('type' if 'type' in cooler else 'name', '')).upper()
            if 'LIQUID' in c_type or 'AIO' in c_type:
                results['cooling'] = {'status': 'Ready', 'message': 'Liquid cooling provided massive thermal headroom for overclocking.'}
            elif tdp > 125:
                 results['cooling'] = {'status': 'Limited', 'message': 'High TDP CPU may benefit from a more robust cooling solution.'}
            else:
                 results['cooling'] = {'status': 'Ready', 'message': 'Cooling solution is well-matched for this processor.'}
        else:
            results['cooling'] = {'status': 'Ready', 'message': 'Mounting patterns support standard AIO and high-end air cooling.'}
            
        if case:
            results['case'] = {'status': 'Ready', 'message': 'Chassis internal volume supports top-tier GPU sizes.'}
        else:
            results['case'] = {'status': 'Ready', 'message': 'Standard ATX case clearance expected.'}

        # 5. Storage Analysis
        if storage:
            s_type = str(storage.get('type', '')).upper()
            if 'NVME' in s_type:
                 results['storage'] = {'status': 'Ready', 'message': 'High-speed NVMe storage detected. Rapid boot and load times.'}
            else:
                 results['storage'] = {'status': 'Limited', 'message': 'SATA storage detected. Upgrade to NVMe for significantly faster performance.'}
        else:
             results['storage'] = {'status': 'Ready', 'message': 'Multiple expansion slots available for high-speed storage.'}

        return jsonify(results)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- Helpers for Robust Inference (Top Level) ---
def normalize(s):
    return str(s).strip().upper() if s else ""

def infer_cpu_socket(doc):
        # 1. Check explicit fields
        s = normalize(doc.get('socket') or doc.get('socket_cpu') or doc.get('socket_type'))
        if s: return s
        
        # 2. Infer from Microarchitecture
        micro = normalize(doc.get('microarchitecture'))
        if micro:
            if 'ZEN 5' in micro or 'ZEN 4' in micro: return 'AM5'
            if 'ZEN' in micro: return 'AM4'
            if 'BULLDOZER' in micro or 'PILEDRIVER' in micro or 'STEAMROLLER' in micro: return 'AM3+'
            if 'EXCAVATOR' in micro: return 'FM2+'
            if 'K10' in micro or 'STARS' in micro or 'K8' in micro: return 'AM3'
            
            # Intel Micros
            if 'METEOR' in micro or 'ARROW' in micro or 'LUNAR' in micro: return 'LGA1851'
            if 'RAPTOR' in micro or 'ALDER' in micro: return 'LGA1700'
            if 'ROCKET' in micro or 'COMET' in micro: return 'LGA1200'
            if 'LAKE' in micro: # Fallback for other Lake archs
                if 'COFFEE' in micro or 'KABY' in micro or 'SKY' in micro: return 'LGA1151'
                if 'BROADWELL' in micro or 'HASWELL' in micro: return 'LGA1150'
                if 'IVY' in micro or 'SANDY' in micro: return 'LGA1155'
        
        # 3. Name Heuristics
        name = normalize(doc.get('name'))
        
        # AMD Heuristics
        if 'RYZEN' in name:
            if any(x in name for x in ['7600', '7700', '7800', '7900', '7950', '9600', '9700', '9800', '9900', '9950']): return 'AM5'
            if 'THREADRIPPER' in name:
                if any(x in name for x in ['79', '78']): return 'STR5'
                if any(x in name for x in ['39', '29']): return 'STRX4'
                return 'TR4'
            return 'AM4'
        
        if 'ATHLON' in name or 'SEMPRON' in name:
            if any(x in name for x in ['5350', '5150', '3850', '2650']): return 'AM1'
            if 'X4' in name:
                if any(x in name for x in ['950', '970']): return 'AM4'
                if any(x in name for x in ['845', '860K', '870K', '880K']): return 'FM2+'
            if 'II' in name: return 'AM3'
            return 'AM1' if 'AM1' in name else None

        if 'FX-' in name: return 'AM3+'
        if 'A10-' in name or 'A8-' in name or 'A6-' in name or 'A4-' in name:
            if any(x in name for x in ['7', '6', '5']): return 'FM2+'
            return 'FM2'

        # Intel Heuristics
        if 'CORE ULTRA' in name:
            return 'LGA1851'
        if any(x in name for x in ['I9-', 'I7-', 'I5-', 'I3-', 'PENTIUM', 'CELERON']):
            # A. Pentium/Celeron G-series specific (overrides general numbering)
            g_match = re.search(r'[GC](\d{3,5})', name)
            if g_match:
                model = int(g_match.group(1))
                if model >= 7000: return 'LGA1700'
                if model >= 6000: return 'LGA1200'
                if model >= 5000: return 'LGA1151' # Coffee Lake
                if model >= 4400: return 'LGA1151' # Kaby Lake/Skylake (mostly)
                if model >= 3000: return 'LGA1150' # Haswell
                if model >= 2000: return 'LGA1155' # Ivy Bridge
                if model >= 1800: return 'LGA1150' # Haswell Celeron
                if model >= 1600: return 'LGA1155' # Ivy Bridge Celeron
                if model >= 500: return 'LGA1155'  # Sandy Bridge Pentiums (G600-G800)

            # B. Search for 4-5 digit model numbers (Core iX)
            num_match = re.search(r'(\d{4,5})', name)
            if num_match:
                model = int(num_match.group(1))
                if model >= 12000: return 'LGA1700'
                if model >= 10000: return 'LGA1200'
                if model >= 8000: return 'LGA1151' # 8th/9th Gen
                if model >= 6000: return 'LGA1151' # 6th/7th Gen
                if model >= 4000: return 'LGA1150'
                if model >= 2000: return 'LGA1155'
            
            # C. Generation specific tags
            if '-14' in name or '-13' in name or '-12' in name: return 'LGA1700'
            if '-11' in name or '-10' in name: return 'LGA1200'
            if '-9' in name or '-8' in name: return 'LGA1151'
            if '-7' in name or '-6' in name: return 'LGA1151'
            if '-4' in name: return 'LGA1150'
            if '-3' in name or '-2' in name: return 'LGA1155'
            
        return None


def infer_mobo_socket(doc):
    # 1. Explicit field
    s = normalize(doc.get('socket_cpu') or doc.get('socket') or doc.get('socket_type') or doc.get('chipset'))
    if s:
        if 'AM5' in s: return 'AM5'
        if 'AM4' in s: return 'AM4'
        if 'LGA1700' in s: return 'LGA1700'
        if 'LGA1200' in s: return 'LGA1200'
        if 'AM1' in s: return 'AM1'
        if 'FM2+' in s: return 'FM2+'
        return s
    
    # 2. Heuristic from Chipset/Name
    name = normalize(doc.get('name'))
    chipset = normalize(doc.get('chipset') or doc.get('specs', ''))
    combined = name + " " + chipset
    
    # AMD
    if any(x in combined for x in ['X870', 'X670', 'B650', 'A620']): return 'AM5'
    if any(x in combined for x in ['X570', 'B550', 'A520', 'X470', 'B450', 'B350', 'A320']): return 'AM4'
    if any(x in combined for x in ['A88X', 'A78', 'A68H', 'A58']): return 'FM2+'
    if 'AM1' in combined: return 'AM1'
    
    # Intel
    if any(x in combined for x in ['Z890', 'B860']): return 'LGA1851'
    if any(x in combined for x in ['Z790', 'B760', 'H770', 'Z690', 'B660', 'H610']): return 'LGA1700'
    if any(x in combined for x in ['Z590', 'B560', 'H510', 'Z490', 'B460', 'H410']): return 'LGA1200'
    if any(x in combined for x in ['Z390', 'Z370', 'B365', 'B360', 'H370', 'H310', 'Z270', 'Z170', 'B250', 'B150']): return 'LGA1151'
    if any(x in combined for x in ['Z97', 'H97', 'Z87', 'H87', 'B85', 'H81']): return 'LGA1150'
    if any(x in combined for x in ['Z77', 'H77', 'B75', 'Z68', 'P67', 'H67', 'H61']): return 'LGA1155'
    if any(x in combined for x in ['P55', 'H55']): return 'LGA1156'
    if 'X58' in combined: return 'LGA1366'
    if 'X79' in combined: return 'LGA2011'
    if 'X99' in combined: return 'LGA2011-3'
    if 'X299' in combined: return 'LGA2066'
    
    return None

def infer_ram_generation(doc, is_mobo=False):
    import re
    search_fields = []
    if is_mobo:
        search_fields = [doc.get('ram_type'), doc.get('memory_type'), doc.get('memory_speed'), doc.get('name')]
    else:
        search_fields = [doc.get('type'), doc.get('ram_type'), doc.get('memory_type'), doc.get('name')]
    
    for field in search_fields:
        val = normalize(field)
        if not val: continue
        match = re.search(r'DDR(\d)', val)
        if match: return f"DDR{match.group(1)}"
        if 'D5' in val or 'RAM5' in val: return 'DDR5'
        if 'D4' in val or 'RAM4' in val: return 'DDR4'
    
    if is_mobo:
        sock = infer_mobo_socket(doc)
        if sock:
            if 'AM5' in sock: return 'DDR5'
            if 'LGA1700' in sock:
                # Hardened LGA1700 check: could be DDR4 or DDR5
                name = normalize(doc.get('name'))
                specs = normalize(str(doc.get('specs', '')) + " " + str(doc.get('memory_type', '')) + " " + str(doc.get('memory_speed', '')))
                # Heuristics for DDR5
                if any(x in name or x in specs for x in ['DDR5', 'D5', '6000', '5200', '4800', '5600', '6400']): 
                    return 'DDR5'
                # Default to DDR4 for older/budget LGA1700 boards
                return 'DDR4'
            if 'AM1' in sock or 'FM2+' in sock or 'FM2' in sock or 'AM3+' in sock or 'AM3' in sock or 'LGA1150' in sock or 'LGA1155' in sock:
                return 'DDR3'
            if 'AM4' in sock or 'LGA1200' in sock or 'LGA1151' in sock: return 'DDR4'
    return None

def infer_mobo_storage_slots(doc):
    import re
    slots = {'m2': 0, 'sata': 0}
    
    # Infer from name and specs
    name = normalize(doc.get('name'))
    specs = normalize(str(doc.get('specs', '')))
    
    # M.2 slots
    m2_matches = re.findall(r'(\d+)\s*X\s*M\.2', name + specs)
    if m2_matches:
        slots['m2'] = sum(int(m) for m in m2_matches)
    elif 'M.2' in name or 'NVME' in specs:
        slots['m2'] = 1 # Assume at least one if mentioned

    # SATA ports
    sata_matches = re.findall(r'(\d+)\s*X\s*SATA', name + specs)
    if sata_matches:
        slots['sata'] = sum(int(m) for m in sata_matches)
    elif 'SATA' in name or 'SATA' in specs:
        slots['sata'] = 4 # Assume at least 4 if mentioned

    return slots

def infer_mobo_form_factor(doc):
    """Infers motherboard form factor (ATX, Micro ATX, Mini ITX)."""
    # 1. Check explicit fields
    val = normalize(doc.get('form_factor') or doc.get('type') or doc.get('motherboard_form_factor'))
    if 'MINI' in val and 'ITX' in val: return 'Mini ITX'
    if 'MICRO' in val and 'ATX' in val: return 'Micro ATX'
    if 'E-ATX' in val or 'EATX' in val: return 'E-ATX'
    if 'ATX' in val: return 'ATX'
    
    # 2. Infer from Name
    name = normalize(doc.get('name'))
    if 'MINI-ITX' in name or 'MINI ITX' in name or (re.search(r'\bI\b', name) and 'WIFI' in name): return 'Mini ITX'
    if 'MICRO-ATX' in name or 'MICRO ATX' in name or re.search(r'\bM\b', name) or '-M ' in name or ' M ' in name: return 'Micro ATX'
    
    # 3. Default heuristics based on chipset/series if everything else fails
    # Tomahawk, Maximus, Strix (non-I/M) are almost always ATX
    if any(x in name for x in ['TOMAHAWK', 'MAXIMUS', 'STRIX', 'AORUS ELITE', 'PRO RS']):
        return 'ATX'
    
    return 'ATX' # Most common default if we can't tell

def infer_case_supported_form_factors(doc):
    """Determines which motherboard sizes a case can accommodate."""
    val = normalize(doc.get('type') or doc.get('form_factor') or doc.get('motherboard_support') or doc.get('name'))
    
    # Check for E-ATX first (Largest)
    if 'FULL' in val or 'E-ATX' in val or 'EATX' in val:
        return ['E-ATX', 'ATX', 'Micro ATX', 'Mini ITX']
    
    # Check for ATX (Mid Tower)
    # Be careful not to match MICROATX as ATX here
    if 'MID' in val or ('ATX' in val and 'MICRO' not in val and 'MINI' not in val):
        return ['ATX', 'Micro ATX', 'Mini ITX']
    
    # Check for Micro ATX
    if 'MICRO' in val or 'MINI TOWER' in val:
        return ['Micro ATX', 'Mini ITX']
    
    # Check for Mini ITX
    if 'MINI' in val or 'ITX' in val:
        return ['Mini ITX']
    
    return ['ATX', 'Micro ATX', 'Mini ITX'] # Default to common Mid Tower

def infer_cooler_socket_support(doc):
    """Parses supported sockets for a cooler from various fields."""
    import re
    val = normalize(doc.get('sockets') or doc.get('socket_support') or doc.get('socket') or doc.get('name'))
    
    # Common socket patterns
    sockets = []
    if 'AM5' in val: sockets.append('AM5')
    if 'AM4' in val: sockets.append('AM4')
    if 'LGA1700' in val or '1700' in val: sockets.append('LGA1700')
    if 'LGA1200' in val or '1200' in val: sockets.append('LGA1200')
    if '1151' in val or '1150' in val or '1155' in val: sockets.append('LGA1151'); sockets.append('LGA1150'); sockets.append('LGA1155')
    if 'AM1' in val: sockets.append('AM1')
    if 'FM2' in val: sockets.append('FM2'); sockets.append('FM2+')
    if 'TR4' in val or 'STR4' in val: sockets.append('TR4'); sockets.append('STRX4')
    
    # If no sockets found but it's a "Universal" cooler
    if not sockets and any(x in val for x in ['UNIVERSAL', 'MULTI-SOCKET', 'ALL-IN-ONE']):
        return ['AM4', 'AM5', 'LGA1700', 'LGA1200']
        
    return sockets

def parse_ram_stick_count(doc):
    """Infers the number of sticks in a memory kit."""
    import re
    val = normalize(doc.get('name') or doc.get('capacity') or doc.get('modules') or "")
    # Match "2 x 16GB", "Kit of 2", "2 sticks"
    match = re.search(r'(\d+)\s*x\s*', val)
    if match: return int(match.group(1))
    match = re.search(r'kit of (\d+)', val)
    if match: return int(match.group(1))
    
    # Heuristic: Dual channel kits often have even capacities
    cap = parse_ram_capacity(doc)
    if cap in [16, 32, 64, 128]: return 2 # Common safe assumption for kits
    return 1

def infer_mobo_ram_slots(doc):
    """Infers the number of RAM slots on a motherboard."""
    val = normalize(doc.get('memory_slots') or doc.get('ram_slots') or doc.get('name') or "")
    if '4' in val: return 4
    if '2' in val: return 2
    if '8' in val: return 8
    
    # Form factor heuristic
    ff = infer_mobo_form_factor(doc)
    if ff == 'Mini ITX': return 2
    return 4 # Default for ATX/mATX

def infer_mobo_storage_slots(doc):
    """Infers M.2 and SATA slot counts from motherboard data."""
    val = normalize(doc.get('storage_slots') or doc.get('m2_slots') or doc.get('sata_slots') or doc.get('name') or "")
    m2_count = 0
    # Match "2x M.2" or "2 x M.2"
    m2_match = re.search(r'(\d+)\s*x\s*m\.2', val)
    if m2_match: m2_count = int(m2_match.group(1))
    elif 'M.2' in val: m2_count = 1
    
    sata_count = 4 # Default
    sata_match = re.search(r'(\d+)\s*x\s*sata', val)
    if sata_match: sata_count = int(sata_match.group(1))
    
    return {'m2': m2_count, 'sata': sata_count}

def get_comp_tier(doc):
    """Estimates the 'Tier' of a component (1=Budget, 2=Mid, 3=Enthusiast)."""
    if not doc: return 1
    price = get_comp_price_usd(doc)
    cat = normalize(doc.get('category'))
    
    if cat == 'CPU':
        if price > 450: return 3
        if price > 200: return 2
        return 1
    if cat == 'GPU':
        if price > 700: return 3
        if price > 350: return 2
        return 1
    if price > 200: return 3
    if price > 100: return 2
    return 1

def parse_dimension_mm(doc, fields):
    """Parses a millimeter dimension from a list of possible fields."""
    import re
    for field in fields:
        val = doc.get(field)
        if val is None: continue
        val_str = str(val)
        # Match '330mm', '330 mm', '330.5mm'
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:mm|millimeters)', val_str, re.I)
        if match:
            return float(match.group(1))
        # If it's a pure number, assume mm
        try:
            num = float(val_str)
            if num > 0: return num
        except: pass
    
    # Try searching the name as fallback
    name = doc.get('name', '')
    match = re.search(r'(\d+(?:\.\d+)?)\s*mm', name, re.I)
    if match: return float(match.group(1))
    
    return 0.0

def parse_ram_capacity(doc):
    """Parses total RAM capacity (in GB) from name or capacity field."""
    # 1. Check explicit capacity field
    cap = doc.get('capacity')
    if isinstance(cap, (int, float)): return float(cap)
    
    val = normalize(cap or doc.get('name'))
    # Look for "64GB" or "2x32GB" patterns
    import re
    # Match "2x32GB" or "2 x 32 GB"
    mult_match = re.search(r'(\d+)\s*[xX]\s*(\d+)\s*GB', val)
    if mult_match:
        return float(mult_match.group(1)) * float(mult_match.group(2))
    
    # Match "64GB"
    gb_match = re.search(r'(\d+)\s*GB', val)
    if gb_match:
        return float(gb_match.group(1))
    
    return 0.0

# ============================================================================
# ADVANCED COMPATIBILITY HELPERS (CPU, GPU, RAM, Mobo, Storage, PSU, Thermal)
# ============================================================================

def extract_numeric_value(text, pattern=r'(\d+(?:\.\d+)?)'):
    """Extract the first numeric value from text."""
    import re
    if not text: return 0
    match = re.search(pattern, str(text))
    return float(match.group(1)) if match else 0

def infer_cpu_tdp(doc):
    """Extracts CPU TDP in watts."""
    if not doc: return 0
    for field in ['tdp', 'thermal_design_power', 'power_consumption', 'max_power']:
        val = extract_numeric_value(doc.get(field))
        if val > 0: return val
    # Heuristic from name
    name = normalize(doc.get('name', ''))
    if 'HX' in name or 'KS' in name: return 140
    if 'K' in name or 'X' in name: return 125
    return 65

def infer_cpu_voltage(doc):
    """Extracts CPU core voltage specification."""
    if not doc: return None
    for field in ['voltage', 'core_voltage', 'vcore', 'default_voltage']:
        val = doc.get(field)
        if val:
            val_str = str(val).strip()
            if 'V' in val_str.upper():
                try:
                    return float(val_str.replace('V', '').strip())
                except: pass
    # Standard fallback based on socket
    sock = infer_cpu_socket(doc)
    if sock in ['LGA1700', 'AM5']: return 1.35
    if sock in ['LGA1200', 'AM4']: return 1.20
    return 1.10

def infer_cpu_base_clock(doc):
    """Extracts CPU base frequency in GHz."""
    if not doc: return 0
    for field in ['base_frequency', 'base_clock', 'clock_speed', 'frequency']:
        val = extract_numeric_value(doc.get(field))
        if val > 0:
            return val / 1000 if val > 10 else val  # Handle MHz vs GHz
    return 0

def infer_cpu_boost_clock(doc):
    """Extracts CPU max turbo frequency in GHz."""
    if not doc: return 0
    for field in ['boost_frequency', 'turbo_frequency', 'max_frequency', 'max_clock']:
        val = extract_numeric_value(doc.get(field))
        if val > 0:
            return val / 1000 if val > 10 else val
    return 0

def infer_cpu_core_count(doc):
    """Extracts number of CPU cores."""
    if not doc: return 0
    for field in ['cores', 'core_count', 'num_cores']:
        val = extract_numeric_value(doc.get(field))
        if val > 0: return int(val)
    # Heuristic from name
    name = normalize(doc.get('name', ''))
    if 'HX45' in name: return 12
    if 'HX' in name: return 8
    return 0

def infer_gpu_vram(doc):
    """Extracts dedicated GPU VRAM in GB."""
    if not doc: return 0
    for field in ['vram', 'memory', 'memory_size', 'memory_gb']:
        val = extract_numeric_value(doc.get(field))
        if val > 0: return val
    # Fallback to name parsing
    name = normalize(doc.get('name', ''))
    for size in [24, 12, 8, 6, 4, 3, 2, 1]:
        if f'{size}GB' in name or f'{size}G ' in name:
            return size
    return 0

def infer_gpu_bus_width(doc):
    """Extracts GPU memory bus width in bits."""
    if not doc: return 0
    for field in ['bus_width', 'memory_bus', 'memory_interface', 'interface']:
        val = extract_numeric_value(doc.get(field))
        if val > 0: return int(val)
    # Common patterns in name
    name = str(doc.get('name', '')).upper()
    if '384-bit' in name: return 384
    if '256-bit' in name: return 256
    if '192-bit' in name: return 192
    if '128-bit' in name: return 128
    return 0

def infer_gpu_tdp(doc):
    """Extracts GPU power consumption in watts."""
    if not doc: return 0
    for field in ['tdp', 'power_consumption', 'max_power', 'tgp']:
        val = extract_numeric_value(doc.get(field))
        if val > 0: return val
    # Heuristic from VRAM and name
    vram = infer_gpu_vram(doc)
    name = normalize(doc.get('name', ''))
    if 'RTX 4090' in name: return 450
    if 'RTX 4080' in name: return 320
    if 'RTX 4070' in name: return 200
    if 'RTX 3080' in name: return 320
    if any(x in name for x in ['RTX', 'RTX 4']): return max(min(vram * 20, 400), 100)
    return 0

def infer_ram_voltage(doc):
    """Extracts RAM operating voltage."""
    if not doc: return None
    for field in ['voltage', 'operating_voltage', 'vram', 'default_voltage']:
        val = doc.get(field)
        if val:
            val_str = str(val).strip()
            if 'V' in val_str.upper():
                try:
                    return float(val_str.replace('V', '').strip())
                except: pass
    # Standard fallbacks
    ram_type = infer_ram_generation(doc, is_mobo=False)
    if ram_type == 'DDR5': return 1.25
    if ram_type == 'DDR4': return 1.20
    if ram_type == 'DDR3': return 1.50
    return None

def infer_ram_speed(doc):
    """Extracts RAM speed in MHz."""
    if not doc: return 0
    for field in ['speed', 'frequency', 'mhz', 'clock_speed']:
        val = extract_numeric_value(doc.get(field))
        if val > 0: return val
    # Parse from name patterns like "DDR5-6000"
    name = normalize(doc.get('name', ''))
    for pattern in ['DDR5-', 'DDR4-', 'DDR3-']:
        if pattern in name:
            idx = name.index(pattern) + len(pattern)
            speed = extract_numeric_value(name[idx:idx+5])
            if speed > 0: return speed
    return 0

def infer_ram_timing(doc):
    """Extracts RAM CAS latency timing (CL value)."""
    if not doc: return 0
    for field in ['cas_latency', 'cl', 'latency', 'timing']:
        val = extract_numeric_value(doc.get(field))
        if val > 0: return int(val)
    # Parse "CL20" or "20-26-26-46" patterns from name
    name = str(doc.get('name', '')).upper()
    if 'CL' in name:
        cl_idx = name.index('CL') + 2
        val = extract_numeric_value(name[cl_idx:cl_idx+3])
        if val > 0: return int(val)
    # Parse timing string like "20-26-26-46"
    import re
    timing_match = re.search(r'(\d+)-(\d+)-(\d+)-(\d+)', name)
    if timing_match:
        return int(timing_match.group(1))
    return 0

def infer_mobo_vrm_phases(doc):
    """Estimates motherboard VRM phase count."""
    if not doc: return 0
    for field in ['vrm_phases', 'phases', 'power_phases', 'vrm']:
        val = extract_numeric_value(doc.get(field))
        if val > 0: return int(val)
    # Heuristic from chipset/form factor
    chipset = normalize(doc.get('chipset', ''))
    name = normalize(doc.get('name', ''))
    ff = infer_mobo_form_factor(doc)
    
    if 'X870' in chipset or 'X870' in name: return 18
    if 'X870-E' in name: return 24
    if 'X870-F' in name: return 20
    if 'X670' in chipset or 'X670' in name:
        return 16 if 'E' in name else 14
    if 'B650' in chipset or 'B650' in name: return 12
    if ff == 'Mini ITX': return 8
    return 10

def infer_mobo_pcie_lanes(doc):
    """Estimates available PCIe lanes."""
    if not doc: return 0
    for field in ['pcie_lanes', 'lanes', 'pcie_gen4_lanes']:
        val = extract_numeric_value(doc.get(field))
        if val > 0: return int(val)
    # Heuristic from chipset
    chipset = normalize(doc.get('chipset', ''))
    if 'AM5' in infer_mobo_socket(doc):
        if 'X870' in chipset: return 24
        if 'X670' in chipset: return 20
        if 'B650' in chipset: return 18
        return 16
    if 'LGA1700' in infer_mobo_socket(doc):
        if 'Z890' in chipset: return 28
        if 'Z790' in chipset: return 28
        return 20
    return 16

def infer_storage_interface(doc):
    """Determines storage interface type."""
    if not doc: return 'UNKNOWN'
    val = normalize(doc.get('interface') or doc.get('type') or doc.get('name'))
    if 'NVME' in val or 'M.2' in val: return 'NVMe'
    if 'SATA' in val or 'SSD' in val: return 'SATA'
    if 'HDD' in val: return 'HDD'
    return 'UNKNOWN'

def infer_storage_protocol(doc):
    """Determines NVMe protocol (PCIe Gen, AHCI)."""
    if not doc: return None
    val = normalize(doc.get('protocol') or doc.get('interface') or doc.get('name'))
    if 'PCIE 5' in val or 'PCIE5' in val or 'GEN5' in val: return 'NVMe PCIe 5.0'
    if 'PCIE 4' in val or 'PCIE4' in val or 'GEN4' in val: return 'NVMe PCIe 4.0'
    if 'PCIE 3' in val or 'PCIE3' in val or 'GEN3' in val: return 'NVMe PCIe 3.0'
    if 'NVME' in val: return 'NVMe'
    if 'SATA' in val: return 'SATA'
    return None

def infer_storage_raid_support(doc):
    """Checks if storage device supports RAID configurations."""
    if not doc: return False
    val = normalize(doc.get('name') or doc.get('specs') or '')
    interface = infer_storage_interface(doc)
    # RAID primarily relevant for SATA
    return 'ENTERPRISE' in val or 'RAID' in val or interface == 'HDD'

def infer_psu_efficiency_rating(doc):
    """Extracts PSU efficiency rating (80+, Gold, Platinum, etc)."""
    if not doc: return '80+'
    val = normalize(doc.get('efficiency') or doc.get('rating') or doc.get('name'))
    if 'TITANIUM' in val: return 'Titanium'
    if 'PLATINUM' in val: return 'Platinum'
    if 'GOLD' in val: return 'Gold'
    if 'SILVER' in val: return 'Silver'
    return '80+'

def infer_psu_modularity(doc):
    """Determines PSU cable modularity."""
    if not doc: return 'Non-Modular'
    val = normalize(doc.get('modularity') or doc.get('type') or doc.get('name'))
    if 'FULLY MODULAR' in val or 'FULL MODULAR' in val: return 'Fully Modular'
    if 'SEMI MODULAR' in val: return 'Semi-Modular'
    return 'Non-Modular'

def infer_psu_connector_support(doc):
    """Checks for PCIE 12V-2x6 (Gen5) support."""
    if not doc: return 'ATX 3.0 Ready'
    val = normalize(doc.get('pcie_connector') or doc.get('connectors') or doc.get('name'))
    if '12V-2X6' in val or '12VHPWR' in val or 'ATX 3.0' in val:
        return 'ATX 3.0 Ready (12V-2x6)'
    return '12VAUX'

def infer_case_airflow_design(doc):
    """Determines case cooling design (ITX, ATX, Open, etc)."""
    if not doc: return 'Standard'
    val = normalize(doc.get('design') or doc.get('type') or doc.get('name'))
    if 'OPEN' in val or 'OPEN-AIR' in val or 'BENCH' in val: return 'Open-Frame'
    if 'OPTIMIZED' in val or 'FLOW' in val: return 'Optimized Flow'
    return 'Standard'

def extract_usb_ports(doc):
    """Parses USB port configuration from motherboard."""
    if not doc: return {'usb2': 0, 'usb3': 0, 'usb3_1': 0, 'usb3_2': 0, 'type_c': 0}
    
    ports = {'usb2': 0, 'usb3': 0, 'usb3_1': 0, 'usb3_2': 0, 'type_c': 0}
    name = normalize(doc.get('name', ''))
    specs = normalize(doc.get('specs', ''))
    
    # Try to extract counts from specs or structured fields
    for usb_type in ['USB 3.2', 'USB 3.1', 'USB 3.0', 'USB 2.0']:
        key = usb_type.lower().replace('.','_')
        count = extract_numeric_value(doc.get(key + '_count'))
        if count > 0:
            ports[key] = int(count)
    
    # Fallback name parsing
    import re
    if re.search(r'4x.*USB.*3', name): ports['usb3'] = 4
    if re.search(r'6x.*USB', name): ports['usb3'] = 6
    if re.search(r'2x.*TYPE.*C', name): ports['type_c'] = 2
    
    # Typical defaults if nothing found
    if sum(ports.values()) == 0:
        ports['usb3'] = 4
        ports['usb2'] = 2
    
    return ports

def infer_audio_codec(doc):
    """Extracts supported audio codec."""
    if not doc: return 'Standard'
    val = normalize(doc.get('audio_codec') or doc.get('audio') or doc.get('name'))
    if 'ALC1220' in val or 'ALC1150' in val or 'SUPREME' in val: return 'High-End'
    if 'REALTEK' in val or 'ALC' in val: return 'Realtek Standard'
    return 'Standard'

def infer_os_compatibility(cpu_doc, mobo_doc, ram_doc):
    """Determines OS compatibility."""
    issues = []
    
    if not cpu_doc or not mobo_doc: return issues
    
    cpu_name = normalize(cpu_doc.get('name', ''))
    mobo_socket = infer_mobo_socket(mobo_doc)
    
    # Very old systems warn for Windows 11/12
    if 'AM1' in mobo_socket or 'FM2' in mobo_socket or 'LGA1156' in mobo_socket:
        issues.append("OS Compat: Very old socket; Windows 11/12 support uncertain.")
    
    # Ryzen with AM4 socket has Windows 11 support issues on older BIOSes
    if 'RYZEN' in cpu_name and 'AM4' in mobo_socket:
        issues.append("OS Compat: AM4 Ryzen may need BIOS update for Win11 TPM support.")
    
    return issues

def run_validation_logic(data):
    try:
        if db is None:
            return {'status': 'Database Error', 'messages': ['The compatibility engine is currently offline due to a database issue.']}
        
        # 1. Resolve Components
        def get_doc(oid):
            if not oid: return None
            try:
                return db.components.find_one({'_id': ObjectId(oid)})
            except: return None

        cpu = get_doc(data.get('cpu_id'))
        mobo = get_doc(data.get('motherboard_id'))
        ram = get_doc(data.get('ram_id'))
        gpu = get_doc(data.get('gpu_id'))
        storage = get_doc(data.get('storage_id'))
        psu = get_doc(data.get('psu_id'))
        case = get_doc(data.get('case_id'))
        cooler = get_doc(data.get('cooler_id'))
        fans_doc = get_doc(data.get('fans_id'))

        messages = []
        status = "Compatible"

        if not cpu or not mobo or not ram:
             return {'status': 'Incomplete Selection', 'messages': ['Please select CPU, Motherboard, and RAM to perform validation.']}

        # 2. CPU Socket & BIOS advisory
        cpu_sock = infer_cpu_socket(cpu)
        mobo_sock = infer_mobo_socket(mobo)
        if cpu_sock and mobo_sock:
            mobo_sockets = [s.strip() for s in mobo_sock.split('/')]
            if cpu_sock not in mobo_sockets:
                status = "Not Compatible"
                messages.append(f"Socket Mismatch: {cpu.get('name')} ({cpu_sock}) does not fit {mobo.get('name')} ({mobo_sock}).")
            else:
                m_name = normalize(mobo.get('name'))
                c_name = normalize(cpu.get('name'))
                if 'B450' in m_name and '5000' in c_name:
                    messages.append("BIOS Advisory: Ryzen 5000 CPUs may require a BIOS update on B450 motherboards.")
                if 'A320' in m_name and '3000' in c_name:
                    messages.append("BIOS Advisory: Ryzen 3000 CPUs may require a BIOS update on A320 motherboards.")
        
        # 2.1 Physical Clearances
        if case:
            if gpu:
                g_len = parse_dimension_mm(gpu, ['length', 'video_card_length', 'gpu_length'])
                c_g_max = parse_dimension_mm(case, ['max_video_card_length', 'video_card_max_length', 'gpu_clearance'])
                if g_len > 0 and c_g_max > 0 and g_len > c_g_max:
                    status = "Not Compatible"
                    messages.append(f"Physical Clearance: {gpu.get('name')} ({int(g_len)}mm) is too long for the selected case (Max: {int(c_g_max)}mm).")
            
            if cooler and cooler != "None Selected":
                c_height = parse_dimension_mm(cooler, ['height', 'cooler_height'])
                c_c_max = parse_dimension_mm(case, ['max_cpucooler_height', 'cpu_cooler_clearance', 'cooler_clearance'])
                if c_height > 0 and c_c_max > 0 and c_height > c_c_max:
                    status = "Not Compatible"
                    messages.append(f"Physical Clearance: {cooler.get('name')} ({int(c_height)}mm) is too tall for the selected case (Max: {int(c_c_max)}mm).")
            
            if psu:
                p_len = parse_dimension_mm(psu, ['length', 'psu_length'])
                c_p_max = parse_dimension_mm(case, ['max_psu_length', 'psu_clearance'])
                if p_len > 0 and c_p_max > 0 and p_len > c_p_max:
                    messages.append(f"Advisory: {psu.get('name')} ({int(p_len)}mm) exceeds recommended PSU length for this case.")
                    if status == "Compatible": status = "Borderline"

            # 2.2 RAM capacity and slot checks
            try:
                # motherboard max RAM (in GB)
                mobo_max_ram = None
                if mobo:
                    mobo_max_ram = parse_ram_capacity(mobo) or mobo.get('max_memory') or mobo.get('max_ram')
                ram_capacity = None
                if ram:
                    ram_capacity = parse_ram_capacity(ram)

                # If motherboard exposes max RAM and RAM per-stick capacity, check totals
                if mobo_max_ram and ram_capacity:
                    import re
                    sticks = 1
                    rname = str(ram.get('name') or '')
                    m = re.search(r"(\d+)\s*[xX]", rname)
                    if m:
                        sticks = int(m.group(1))
                    total_ram = ram_capacity * sticks
                    # try to get motherboard slot count
                    mobo_slots = None
                    try:
                        mobo_slots = int(mobo.get('memory_slots') or mobo.get('ram_slots') or 0)
                    except:
                        mobo_slots = None
                    if mobo_slots and sticks > mobo_slots:
                        status = "Not Compatible"
                        messages.append(f"RAM Slots: Selected RAM uses {sticks} sticks but the motherboard only has {mobo_slots} slots.")
                    try:
                        if isinstance(float(mobo_max_ram), float) and total_ram > float(mobo_max_ram):
                            status = "Not Compatible"
                            messages.append(f"RAM Capacity: Selected RAM total ({int(total_ram)}GB) exceeds motherboard maximum ({int(mobo_max_ram)}GB).")
                    except Exception:
                        pass
            except Exception:
                pass

            # 2.3 Storage: M.2 / SATA port availability
            try:
                # count NVMe/M.2 drives selected
                m2_needed = 0
                sname = ''
                if storage:
                    sname = str(storage.get('name') or '').lower()
                    if 'nvme' in sname or 'm.2' in sname or 'm2' in sname:
                        m2_needed = 1
                # motherboard M.2 slot count
                mobo_m2 = 0
                try:
                    mobo_m2 = int(mobo.get('m2_slots') or mobo.get('m.2_slots') or mobo.get('m2_count') or 0)
                except:
                    mobo_m2 = 0
                if m2_needed > 0 and m2_needed > mobo_m2:
                    status = "Not Compatible"
                    messages.append(f"Storage: Selected NVMe drive requires {m2_needed} M.2 slot(s) but motherboard has {mobo_m2}.")

                # SATA ports check for SATA drives
                sata_needed = 0
                if storage and ('ssd' in sname or 'hdd' in sname) and 'nvme' not in sname:
                    sata_needed = 1
                mobo_sata = 0
                try:
                    mobo_sata = int(mobo.get('sata_ports') or mobo.get('sata_count') or 0)
                except:
                    mobo_sata = 0
                if sata_needed > mobo_sata:
                    status = "Not Compatible"
                    messages.append(f"Storage: Selected SATA drive requires {sata_needed} SATA port(s) but motherboard has {mobo_sata}.")
            except Exception:
                pass

            # 2.4 PCIe version and lane advisory
            try:
                if gpu and mobo:
                    # warn if motherboard PCIe version is older than GPU's advertised PCIe
                    def detect_pcie(doc):
                        if not doc: return 0
                        for key in ['pcie_version','pcie','pcie_slot','pcie_rev']:
                            if key in doc and doc.get(key):
                                try:
                                    v = int(str(doc.get(key)).strip().lower().replace('pcie','').replace('pci-e','').replace('v',''))
                                    return v
                                except:
                                    pass
                        s = str(doc.get('name') or '').lower()
                        if 'pcie5' in s or 'pcie 5' in s or 'pci express 5' in s: return 5
                        if 'pcie4' in s or 'pcie 4' in s or 'pci express 4' in s: return 4
                        if 'pcie3' in s or 'pcie 3' in s or 'pci express 3' in s: return 3
                        return 0
                    g_pcie = detect_pcie(gpu)
                    m_pcie = detect_pcie(mobo)
                    if g_pcie and m_pcie and g_pcie > m_pcie:
                        messages.append(f"PCIe Advisory: GPU appears to support PCIe {g_pcie} but motherboard is PCIe {m_pcie}. This is backward-compatible but may limit peak bandwidth.")
            except Exception:
                pass
            
            # Cable management check (outside of PCIe exception block)
            c_name = normalize(case.get('name'))
            if any(x in c_name for x in ['MINI', 'ITX', 'SMALL', 'SFF']):
                p_name = normalize(psu.get('name')) if psu else ''
                if 'MODULAR' not in p_name and 'SEMI' not in p_name:
                    messages.append("Cable Management: Non-modular PSU in small case.")
                    if status == "Compatible": status = "Borderline"

            if fans_doc:
                f_slots = infer_case_fan_slots(case)
                f_count = parse_ram_stick_count(fans_doc)
                if f_count > f_slots:
                    messages.append(f"Fan Configuration: Selected {f_count} fans, but case only has approx {f_slots} slots.")
                    if status == "Compatible": status = "Borderline"

        # 3. RAM Generation, Capacity, & Slot Check
        cpu_ram_gen = infer_ram_generation(ram, is_mobo=False)
        mobo_ram_gen = infer_ram_generation(mobo, is_mobo=True)

        if cpu_ram_gen and mobo_ram_gen and cpu_ram_gen != mobo_ram_gen:
            status = "Not Compatible"
            messages.append(f"RAM Type Mismatch: Motherboard requires {mobo_ram_gen} but selected RAM is {cpu_ram_gen}.")
        
        if ram and mobo:
            sticks = parse_ram_stick_count(ram)
            slots = infer_mobo_ram_slots(mobo)
            if sticks > slots:
                status = "Not Compatible"
                messages.append(f"Memory Slot Conflict: {sticks} sticks vs {slots} slots.")

        ram_cap = parse_ram_capacity(ram)
        mobo_max_ram = mobo.get('max_ram') or mobo.get('max_memory')
        if ram_cap and mobo_max_ram:
            import re
            m = re.search(r'(\d+)', str(mobo_max_ram))
            max_gb = float(m.group(1)) if m else 0
            if max_gb and ram_cap > max_gb:
                status = "Not Compatible"
                messages.append(f"Memory Overload: Max {int(max_gb)}GB supported.")

        # 4. Form Factor Check (Mobo vs Case)
        if mobo and case:
            m_ff = infer_mobo_form_factor(mobo)
            c_ffs = infer_case_supported_form_factors(case)
            if m_ff and c_ffs and m_ff not in c_ffs:
                status = "Not Compatible"
                messages.append(f"Physical Incompatibility: {m_ff} is too large for case.")

        # 5. PSU Adequacy
        if cpu or gpu:
            p_res = run_power_analysis(data)
            if p_res.get('status') == 'success':
                psu_status = p_res.get('adequacy_status')
                rec_w = p_res.get('recommended_wattage')
                sel_w = p_res.get('selected_psu_wattage')
                if psu_status == "Insufficient":
                    status = "Not Compatible"
                    messages.append(f"Power Deficit: {rec_w}W required, but only {sel_w}W selected.")
                elif psu_status == "Borderline":
                    if status == "Compatible": status = "Borderline"
                    messages.append(f"Power Alert: {sel_w}W PSU is near the limit.")

        # 6. Storage & Resource Sharing
        if storage and mobo:
            s_type = normalize(storage.get('type') or storage.get('form_factor') or storage.get('interface'))
            is_m2 = 'M.2' in s_type or 'NVME' in s_type
            mobo_slots = infer_mobo_storage_slots(mobo)
            if is_m2 and mobo_slots['m2'] == 0:
                status = "Not Compatible"
                messages.append("Storage Mismatch: No M.2 slots available.")

        # 7. Cooler Compatibility & TDP
        if cpu:
            tdp = cpu.get('tdp', 0)
            if isinstance(tdp, str):
                import re
                nums = re.findall(r'\d+', tdp)
                tdp = int(nums[0]) if nums else 0

            if cooler and cooler != "None Selected":
                c_sock_support = infer_cooler_socket_support(cooler)
                if cpu_sock and c_sock_support and cpu_sock not in c_sock_support:
                    status = "Not Compatible"
                    messages.append(f"Cooling Mismatch: {cooler.get('name')} does not support {cpu_sock}.")
            elif tdp > 105 and (not cooler or cooler == "None Selected"):
                status = "Not Compatible"
                messages.append("Cooling Missing: High-TDP processor requires aftermarket cooling.")

        # 8. Component Completion Check
        critical_slots = ['cpu_id', 'motherboard_id', 'ram_id', 'psu_id', 'case_id', 'storage_id']
        missing_crit = [s.replace('_id','').upper() for s in critical_slots if not data.get(s) or data.get(s) == "None Selected"]
        
        has_igpu = False
        if cpu:
            c_name = normalize(cpu.get('name'))
            if 'INTEL' in c_name and '-F' in c_name: has_igpu = False
            elif 'RYZEN' in c_name and 'G' not in c_name and '7000' not in c_name and '9000' not in c_name: has_igpu = False
            else: has_igpu = True
            
        if not has_igpu and (not data.get('gpu_id') or data.get('gpu_id') == "None Selected"):
            missing_crit.append("GPU")

        if missing_crit:
             messages.append(f"Incomplete Build: Missing {', '.join(missing_crit)}.")
             if status == "Compatible": status = "Borderline"

        # 9. Eco & Utility
        wifi_id = data.get('wifi_id')
        if wifi_id and wifi_id != "None Selected" and mobo:
            m_name = normalize(mobo.get('name'))
            if 'WIFI' in m_name:
                messages.append(f"Advisory: {mobo.get('name')} already has built-in WiFi.")
        
        ups_id = data.get('ups_id')
        if ups_id and ups_id != "None Selected":
             ups = get_doc(ups_id)
             if ups:
                ups_w = ups.get('wattage') or ups.get('power') or 0
                if isinstance(ups_w, str):
                    try: ups_w = int(re.findall(r'\d+', ups_w)[0])
                    except: ups_w = 0
                p_res = run_power_analysis(data)
                draw = p_res.get('total_base_wattage', 0)
                if ups_w > 0 and ups_w < draw:
                    messages.append(f"UPS Alert: UPS capacity too low ({ups_w}W vs {draw}W).")
                    if status == "Compatible": status = "Borderline"

        # 10. Assembly Preparation
        if not data.get('thermal_paste_id') or data.get('thermal_paste_id') == "None Selected":
            if cpu and cpu.get('tdp', 0):
                try:
                    import re as _re
                    tdp_v = int(_re.findall(r'\d+', str(cpu.get('tdp', 0)))[0]) if _re.findall(r'\d+', str(cpu.get('tdp', 0))) else 0
                    if tdp_v > 100:
                        messages.append("Assembly Note: High-performance thermal paste recommended.")
                except: pass
        
        # ===== ADVANCED COMPATIBILITY CHECKS =====
        
        # Initialize advanced metrics
        cpu_tdp = infer_cpu_tdp(cpu) if cpu else 0
        cpu_voltage = infer_cpu_voltage(cpu) if cpu else None
        cpu_cores = infer_cpu_core_count(cpu) if cpu else 0
        cpu_base_clock = infer_cpu_base_clock(cpu) if cpu else 0
        cpu_boost_clock = infer_cpu_boost_clock(cpu) if cpu else 0
        
        gpu_vram = infer_gpu_vram(gpu) if gpu else 0
        gpu_tdp = infer_gpu_tdp(gpu) if gpu else 0
        gpu_bus_width = infer_gpu_bus_width(gpu) if gpu else 0
        
        mobo_vrm = infer_mobo_vrm_phases(mobo) if mobo else 0
        mobo_pcie_lanes = infer_mobo_pcie_lanes(mobo) if mobo else 0
        
        # 11. CPU-Specific Advanced Checks
        if cpu:
            # TDP and VRM Power Delivery
            if mobo and cpu_tdp > 120:
                if mobo_vrm < 14:
                    if status == "Compatible": status = "Borderline"
                    messages.append(f"VRM Warning: {mobo_vrm}-phase VRM may be marginal for {cpu_tdp}W TDP CPU. Consider higher-end boards for stability.")
            
            # CPU Voltage compatibility check
            if cpu_voltage and mobo:
                mobo_name = normalize(mobo.get('name', ''))
                if cpu_voltage > 1.35 and any(x in mobo_name for x in ['BUDGET', 'PRO', 'PRIME']):
                    messages.append(f"CPU Voltage: This CPU may require {cpu_voltage}V; verify motherboard supports this voltage range.")
            
            # Boost clock advisory
            if cpu_boost_clock > 6.0:
                messages.append(f"High Clock Advisory: {cpu_boost_clock:.1f}GHz boost detected; ensure adequate cooling and power delivery.")
        
        # 12. GPU-Specific Advanced Checks
        if gpu:
            # VRAM Generation Compatibility
            if gpu_vram > 0 and mobo:
                m_ff = infer_mobo_form_factor(mobo)
                if m_ff == 'Mini ITX' and gpu_vram > 12:
                    messages.append(f"GPU VRAM Note: {int(gpu_vram)}GB GPU on Mini-ITX may have thermal/power challenges.")
            
            # GPU Memory Bus and Bandwidth
            if gpu_bus_width > 0 and gpu_bus_width < 192:
                messages.append(f"GPU Memory Bus: {int(gpu_bus_width)}-bit bus may limit memory bandwidth (consider 256-bit or wider).")
            
            # External power connectors
            if gpu_tdp > 300 and psu:
                psu_rating = extract_numeric_value(psu.get('wattage') or psu.get('power'))
                if psu_rating > 0 and psu_rating < gpu_tdp * 1.6:
                    if status == "Compatible": status = "Borderline"
                    messages.append(f"GPU Power Alert: {int(gpu_tdp)}W GPU with {int(psu_rating)}W PSU is tight; recommend higher capacity.")
        
        # 13. RAM-Specific Advanced Checks
        if ram:
            ram_voltage = infer_ram_voltage(ram)
            ram_speed = infer_ram_speed(ram)
            ram_timing = infer_ram_timing(ram)
            ram_gen = infer_ram_generation(ram, is_mobo=False)
            
            # RAM Voltage Stability
            if ram_voltage and ram_voltage > 1.25:
                messages.append(f"RAM Voltage: {ram_voltage}V operation detected; ensure motherboard supports XMP/DOCP stability.")
            
            # RAM Speed with Motherboard
            if mobo and ram_speed > 0:
                mobo_gen = infer_ram_generation(mobo, is_mobo=True)
                if ram_gen and mobo_gen and ram_gen == mobo_gen:
                    if ram_speed > 6000 and ram_gen == 'DDR5':
                        messages.append(f"DDR5 Speed: {int(ram_speed)}MHz requires manual BIOS tuning; default profiles may be lower.")
                    if ram_speed > 4000 and ram_gen == 'DDR4':
                        messages.append(f"DDR4 Speed: {int(ram_speed)}MHz typically requires XMP profile in BIOS.")
            
            # CAS Latency Advisory
            if ram_timing > 20 and ram_gen == 'DDR5':
                messages.append(f"DDR5 Timing: CL{int(ram_timing)} is average; tighter timings improve performance.")
        
        # 14. Motherboard Advanced Checks
        if mobo:
            mobo_usb = extract_usb_ports(mobo)
            mobo_audio = infer_audio_codec(mobo)
            
            # PCIe Lane Allocation
            if gpu and mobo_pcie_lanes > 0:
                if mobo_pcie_lanes < 16 and gpu_vram and gpu_vram > 8:
                    messages.append(f"PCIe Lanes: Only {int(mobo_pcie_lanes)} lanes detected; high-VRAM GPU may experience x8 mode performance impact.")
            
            # USB Port Count
            if mobo_usb['usb3'] < 4 and mobo_usb['type_c'] == 0:
                messages.append(f"USB Ports: Limited USB 3.x ports ({mobo_usb['usb3']} + {mobo_usb['type_c']} Type-C); many peripherals may require hubs.")
            
            # Audio Quality  
            audio_quality = infer_audio_codec(mobo)
            if audio_quality == 'Standard':
                messages.append(f"Audio Codec: Standard codec; if using high-end headphones/speakers, consider dedicated DAC.")
        
        # 15. Storage Advanced Checks
        if storage:
            storage_interface = infer_storage_interface(storage)
            storage_protocol = infer_storage_protocol(storage)
            raid_support = infer_storage_raid_support(storage)
            
            # NVMe Gen Mismatch
            if mobo and storage_protocol:
                if 'PCIe 5' in storage_protocol and mobo_pcie_lanes < 20:
                    messages.append(f"Storage Gen: PCIe 5.0 NVMe on platform with limited lanes; PCIe 4.0 may be more practical.")
            
            # RAID Configuration hint
            if raid_support and mobo:
                messages.append(f"Storage Note: Drive supports RAID; motherboard has {infer_mobo_storage_slots(mobo)['sata']} SATA ports for RAID setup.")
        
        # 16. Power Supply Advanced Checks
        if psu and (cpu or gpu):
            psu_efficiency = infer_psu_efficiency_rating(psu)
            psu_modularity = infer_psu_modularity(psu)
            psu_connectors = infer_psu_connector_support(psu)
            psu_wattage = extract_numeric_value(psu.get('wattage') or psu.get('power'))
            
            # Efficiency and heat
            if psu_efficiency in ['80+', 'Silver'] and psu_wattage > 750:
                messages.append(f"PSU Efficiency: {psu_efficiency} rated; higher efficiency (Gold/Platinum) reduces heat/noise in high-wattage systems.")
            
            # ATX 3.0 Connector Support (for modern high-end GPUs)
            if gpu and gpu_tdp > 300:
                mobo_audio_check = infer_audio_codec(mobo) if mobo else 'Standard'
                if 'ATX 3.0' not in psu_connectors and 'High-End' not in mobo_audio_check:
                    messages.append(f"ATX 3.0 Readiness: {psu_connectors}; newer GPUs prefer 12V-2x6 (ATX 3.0) connectors for stability.")
            
            # Cable Capacity vs System
            total_draw = extract_numeric_value(psu.get('total_base_wattage') or 0)
            if psu_wattage > 0 and psu_modularity == 'Fully Modular' and case:
                messages.append(f"Cable Management: Fully modular PSU ({int(psu_wattage)}W) allows clean builds; ideal for visibility and airflow.")
        
        # 17. Thermal Management Analysis
        if cpu and cooler and case:
            case_airflow = infer_case_airflow_design(case)
            cooler_height = parse_dimension_mm(cooler, ['height', 'cooler_height'])
            case_cooler_max = parse_dimension_mm(case, ['max_cpucooler_height', 'cooler_clearance'])
            
            if cooler_height > 0 and case_cooler_max > 0:
                clearance_pct = ((case_cooler_max - cooler_height) / case_cooler_max) * 100
                if clearance_pct < 20:
                    messages.append(f"Thermal Clearance: Only {clearance_pct:.0f}% headroom for cooler; consider downsizing cooler for safety.")
            
            # Case airflow design
            if ('ITX' in normalize(case.get('name')) or case_airflow == 'Open-Frame') and cpu_tdp and cpu_tdp > 100:
                messages.append(f"Airflow Design: {case_airflow} case with {cpu_tdp}W CPU may struggle; ensure adequate intake fans.")
        
        # 18. Peripheral & Connectivity Checks
        if mobo:
            mobo_usb = extract_usb_ports(mobo)
            usb_deficiency = []
            
            if mobo_usb['type_c'] == 0:
                usb_deficiency.append("no USB Type-C ports")
            if mobo_usb['usb3'] < 2:
                usb_deficiency.append(f"only {mobo_usb['usb3']} USB 3.x ports")
            
            if usb_deficiency:
                messages.append(f"Connectivity: Motherboard has {', '.join(usb_deficiency)}; many modern peripherals require these.")
        
        # 19. OS Compatibility Warnings
        os_compat_issues = infer_os_compatibility(cpu, mobo, ram)
        for issue in os_compat_issues:
            messages.append(issue)
        
        # 20. Final Summary Check
        if not messages and status == "Compatible":
            messages.append("Systems check: All selected components are compatible!")

        return {'status': status, 'messages': messages}

    except Exception as e:
        app.logger.error(f"Validation internal error: {e}")
        return {'status': 'Error', 'messages': [str(e)]}

def infer_case_fan_slots(doc):
    """Infers the number of fan mounting positions in a case."""
    if not doc: return 3
    val = normalize(doc.get('name') or doc.get('specs') or doc.get('type') or "")
    if 'MINI' in val or 'ITX' in val: return 2
    if 'MICRO' in val or 'MINI TOWER' in val: return 4
    if 'FULL' in val or 'XL' in val: return 8
    return 6

# ============================================================================
# NEW AI ENGINE ENDPOINTS (Multi-Provider: Groq, Mistral, Gemini, Ollama)
# ============================================================================

@app.route('/api/ai-engine/recommend', methods=['POST'])
@login_required
def api_ai_engine_recommend():
    """
    NEW: AI-Powered PC Build Recommendation using multi-provider AI engine
    Uses Groq, Mistral, Gemini, and Ollama with automatic rotation
    """
    try:
        data = request.json
        budget = data.get('budget', '$1000')
        use_case = data.get('use_case', 'General Use')
        preferences = data.get('preferences', {})
        user_currency = session.get('currency', 'USD')

        # AI Cache Check
        cache_key = f"rec_{budget}_{use_case}_{str(preferences)}_{user_currency}"
        if 'ai_cache' in db.list_collection_names():
            cached_res = db.ai_cache.find_one({'cache_key': cache_key})
            if cached_res:
                log_ai_request('recommendation', cached_res.get('provider'), cached=True)
                return jsonify({
                    'status': 'success',
                    'recommendation': cached_res.get('recommendation'),
                    'matched_components': cached_res.get('matched_components'),
                    'cached': True
                })
        
        # RAG Strategy: Get available components from database components table
        component_pool = {}
        try:
            # Helper to format component list with IDs
            def get_pool(query, limit=15):
                components = []
                # Fetch only ID and Name - NO PRICES for the AI Engine
                # This prevents the AI from "hallucinating" or prioritizing based on outdated prices
                for c in db.components.find(query, {'_id': 1, 'name': 1}).limit(limit):
                    components.append(f"ID:{str(c['_id'])}|{c['name']}")
                return components

            component_pool['cpus'] = get_pool({'category': 'cpu'}, 20)
            component_pool['gpus'] = get_pool({'category': 'gpu'}, 20)
            component_pool['motherboards'] = get_pool({'category': 'motherboard'}, 15)
            component_pool['ram'] = get_pool({'category': 'ram'}, 15)
            component_pool['storage'] = get_pool({'category': 'storage'}, 15)
            component_pool['psu'] = get_pool({'category': 'psu'}, 15)
            component_pool['cases'] = get_pool({'category': 'case'}, 15)
            component_pool['coolers'] = get_pool({'category': 'cooler'}, 15)
            component_pool['monitors'] = get_pool({'category': 'monitor'}, 10)
            component_pool['os'] = get_pool({'category': 'os'}, 5)
            component_pool['fans'] = get_pool({'category': 'fans'}, 10)
            
            # Peripherals
            component_pool['keyboards'] = get_pool({'category': 'peripherals', 'sub_category': 'keyboard'}, 10)
            component_pool['mice'] = get_pool({'category': 'peripherals', 'sub_category': 'mouse'}, 10)
            component_pool['headsets'] = get_pool({'category': 'peripherals', 'sub_category': 'headset'}, 10)
            component_pool['webcams'] = get_pool({'category': 'peripherals', 'sub_category': 'webcam'}, 10)
            component_pool['peripherals'] = get_pool({'category': 'peripherals', 'sub_category': 'other'}, 10)
            
            # PC Build Essentials (Requested by user)
            component_pool['thermal_paste'] = get_pool({'category': 'thermal_paste'}, 10)
            component_pool['wifi_adapters'] = get_pool({'category': 'wifi_adapters'}, 10)
            component_pool['speakers'] = get_pool({'category': 'speakers'}, 10)
            component_pool['microphones'] = get_pool({'category': 'microphones'}, 10)
            component_pool['ups'] = get_pool({'category': 'ups'}, 10)
            component_pool['tools'] = get_pool({'category': 'tools'}, 10)
        except Exception as e:
            app.logger.warning(f"Could not fetch component pool: {e}")
            component_pool = None
        
        # Get AI recommendation
        user_currency = session.get('currency', 'USD')
        ai_engine = get_ai_engine()
        recommendation = ai_engine.get_pc_recommendation(
            budget=budget,
            use_case=use_case,
            preferences=preferences,
            component_pool=component_pool,
            user_currency=user_currency
        )
        
        # Log request
        log_ai_request('recommendation', recommendation.get('provider_used') if recommendation else 'failed')
        
        # Try to match AI recommendations to actual database components
        matched_components = {}
        if recommendation and not recommendation.get('fallback', False):
            # Categories to match (All 22)
            # aligned with ai_engine keys
            cats = [
                'cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooler', 
                'monitor', 'os', 'fans', 'keyboard', 'mouse', 'headset', 'webcam', 'peripherals', 
                'thermal_paste', 'wifi', 'speakers', 'microphone', 'ups', 'tools'
            ]
            
            for comp_type in cats:
                ai_suggestion = recommendation.get(comp_type, '')
                if ai_suggestion:
                    # 1. Try to extract ID from "ID:xxx|Name"
                    match = None
                    if "ID:" in ai_suggestion and "|" in ai_suggestion:
                        try:
                            cid = ai_suggestion.split('|')[0].replace('ID:', '').strip()
                            match = db.components.find_one({'_id': ObjectId(cid)})
                        except:
                            pass
                    
                    # 2. Fallback to name-based regex matching if ID match failed
                    if not match:
                        # Clean name from ID:...| if present
                        clean_name = ai_suggestion
                        if "|" in clean_name: clean_name = clean_name.split('|')[-1].strip()
                        elif "ID:" in clean_name: clean_name = clean_name.split(':')[-1].strip()
                        
                        search_term = clean_name.split()[0] if clean_name else ""
                        if search_term:
                            query = {'name': {'$regex': re.escape(search_term), '$options': 'i'}}
                            
                            # Apply Category Filters
                            subcat_map = {'keyboard': 'keyboard', 'mouse': 'mouse', 'headset': 'headset', 'webcam': 'webcam'}
                            if comp_type in subcat_map:
                                query['category'] = 'peripherals'
                                query['sub_category'] = subcat_map[comp_type]
                            else:
                                cat_map = {
                                    'cpu':'cpu', 'gpu':'gpu', 'motherboard':'motherboard', 'ram':'ram', 
                                    'storage':'storage', 'psu':'psu', 'case':'case', 'cooler':'cooler', 
                                    'fans':'fans', 'wifi': 'wifi_adapters', 'microphone': 'microphones'
                                }
                                query['category'] = cat_map.get(comp_type, comp_type)

                            try:
                                match = db.components.find_one(query)
                            except:
                                pass
                    
                    if match:
                        # Map internal key names to UI/Database keys if different
                        # (The UI uses some singular keys or shorthand like 'wifi')
                        ui_key = comp_type
                        if ui_key == 'wifi_adapters': ui_key = 'wifi'
                        if ui_key == 'microphones': ui_key = 'microphone'
                        
                        matched_components[ui_key + '_id'] = str(match['_id'])
                        matched_components[ui_key + '_name'] = match['name']
                        
                        # FETCH REAL-TIME PRICE VIA SERPAPI (favored over DB)
                        fetcher = get_price_fetcher(db=db)
                        live_data = fetcher.fetch_component_price(match['name'], comp_type)
                        
                        if live_data and live_data.get('price_usd'):
                            matched_components[ui_key + '_price'] = live_data['price_usd']
                            matched_components[ui_key + '_source'] = live_data.get('source')
                            matched_components[ui_key + '_link'] = live_data.get('link')
                        else:
                            # Fallback to normalized database price if live search fails
                            matched_components[ui_key + '_price'] = get_comp_price_usd(match)
                            matched_components[ui_key + '_source'] = "Database"

            # Recalculate total build cost based on LIVE prices
            total_cost_usd = sum(v for k, v in matched_components.items() if k.endswith('_price'))
            recommendation['calculated_total_usd'] = total_cost_usd
            recommendation['calculated_total'] = total_cost_usd * EXCHANGE_RATES.get(user_currency, 1.0)
            recommendation['estimated_total'] = recommendation['calculated_total']

        
        
        # Save to AI cache for metrics and performance
        try:
            db.ai_cache.update_one(
                {'cache_key': cache_key},
                {'$set': {
                    'recommendation': recommendation,
                    'matched_components': matched_components,
                    'provider': recommendation.get('provider_used'),
                    'created_at': datetime.now(timezone.utc)
                }},
                upsert=True
            )
        except Exception:
            pass

        return jsonify({
            'status': 'success',
            'recommendation': recommendation,
            'matched_components': matched_components
        })
        
    except Exception as e:
        app.logger.error(f"AI engine recommendation error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/ai-engine/compatibility', methods=['POST'])
@login_required
def api_ai_engine_compatibility():
    """
    NEW: AI-powered compatibility analysis using multi-provider AI
    """
    try:
        data = request.json
        
        def get_name(category, comp_id):
            if not comp_id:
                return None
            try:
                # Try components table first
                comp = db.components.find_one({'_id': ObjectId(comp_id)})
                if comp: return comp.get('name')
                
                # Fallback to separate tables
                col_map = {
                    'cpu': 'cpus', 'gpu': 'gpus', 'motherboard': 'motherboards', 
                    'ram': 'ram', 'storage': 'storage', 'psu': 'psu', 
                    'case': 'cases', 'cooler': 'coolers', 'monitor': 'monitors', 
                    'os': 'os', 'peripherals': 'peripherals', 'fans': 'fans'
                }
                col = col_map.get(category, category)
                comp = db[col].find_one({'_id': ObjectId(comp_id)})
                return comp.get('name') if comp else None
            except:
                return None
        
        cpu_name = get_name('cpu', data.get('cpu_id'))
        mobo_name = get_name('motherboard', data.get('motherboard_id'))
        ram_name = get_name('ram', data.get('ram_id'))
        
        if not all([cpu_name, mobo_name, ram_name]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required components'
            }), 400
        
        other_components = {}
        if data.get('gpu_id'):
            gpu_name = get_name('gpus', data.get('gpu_id'))
            if gpu_name:
                other_components['GPU'] = gpu_name
        
        if data.get('psu_id'):
            psu_name = get_name('psu', data.get('psu_id'))
            if psu_name:
                other_components['PSU'] = psu_name

        cols = {
            'storage_id': 'STORAGE', 'case_id': 'CASE', 'cooler_id': 'COOLER',
            'monitor_id': 'MONITOR', 'os_id': 'OS', 'peripherals_id': 'PERIPHERALS', 
            'keyboard_id': 'KEYBOARD', 'mouse_id': 'MOUSE', 'headset_id': 'HEADSET', 'webcam_id': 'WEBCAM',
            'fans_id': 'FANS', 'thermal_paste_id': 'THERMAL_PASTE', 'wifi_id': 'WIFI', 'speakers_id': 'SPEAKERS',
            'microphone_id': 'MICROPHONE', 'ups_id': 'UPS', 'tool_id': 'TOOLS'
        }
        for key, label in cols.items():
            cid = data.get(key)
            if cid:
                cname = get_name(key.replace('_id',''), cid)
                if cname: other_components[label] = cname
        
        ai_engine = get_ai_engine()
        analysis = ai_engine.analyze_compatibility(
            cpu_name=cpu_name,
            motherboard_name=mobo_name,
            ram_name=ram_name,
            other_components=other_components
        )
        
        # Log request
        log_ai_request('compatibility', analysis.get('provider_used') if analysis else 'failed')
        
        return jsonify({
            'status': 'success',
            'analysis': analysis
        })
        
    except Exception as e:
        app.logger.error(f"AI engine compatibility error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/ai-engine/performance', methods=['POST'])
@login_required
def api_ai_engine_performance():
    """
    NEW: AI-powered performance estimation using multi-provider AI
    """
    try:
        data = request.json
        
        def get_name(category, comp_id):
            if not comp_id:
                return "Unknown"
            try:
                # Try components table first
                comp = db.components.find_one({'_id': ObjectId(comp_id)})
                if comp: return comp.get('name', 'Unknown')
                
                # Fallback to separate tables
                col_map = {'cpu': 'cpus', 'gpu': 'gpus', 'motherboard': 'motherboards', 'ram': 'ram', 'storage': 'storage', 'psu': 'psu', 'case': 'cases', 'cooler': 'coolers'}
                col = col_map.get(category, category)
                comp = db[col].find_one({'_id': ObjectId(comp_id)})
                return comp.get('name', 'Unknown') if comp else "Unknown"
            except:
                return "Unknown"
        
        cpu_name = get_name('cpu', data.get('cpu_id'))
        gpu_name = get_name('gpu', data.get('gpu_id'))
        ram_name = get_name('ram', data.get('ram_id'))
        games = data.get('games', None)
        
        ai_engine = get_ai_engine()
        performance = ai_engine.estimate_performance(
            cpu_name=cpu_name,
            gpu_name=gpu_name,
            ram_name=ram_name,
            games=games
        )
        
        # Log request
        log_ai_request('performance', performance.get('provider_used') if performance else 'failed')
        
        return jsonify({
            'status': 'success',
            'performance': performance
        })
        
    except Exception as e:
        app.logger.error(f"AI engine performance error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500



@app.route('/api/get-price', methods=['GET'])
@login_required
def api_get_price():
    """
    NEW: Fetch real-time price for a component name
    Requirement: AI generates names, backend fetches real prices
    """
    name = request.args.get('name')
    category = request.args.get('category', '')
    if not name:
        return jsonify({'status': 'error', 'message': 'Missing component name'}), 400
        
    fetcher = get_price_fetcher(db=db)
    price_data = fetcher.fetch_component_price(name, category)
    
    if price_data:
        # Convert to user's currency
        currency = session.get('currency', 'USD')
        rate = EXCHANGE_RATES.get(currency, 1.0)
        local_price = price_data['price_usd'] * rate
        
        return jsonify({
            'status': 'success',
            'name': name,
            'price_usd': price_data['price_usd'],
            'local_price': local_price,
            'formatted_price': format_price(price_data['price_usd']),
            'source': price_data.get('source'),
            'link': price_data.get('link')
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Price not found'
        }), 404


@app.route('/api/analyze_power', methods=['POST'])
@login_required
def api_analyze_power():
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    return jsonify(run_power_analysis(data))

def run_power_analysis(data):
    try:
        # Fetch components using our unified helper
        cpu = get_component_by_id(data.get('cpu_id'))
        gpu = get_component_by_id(data.get('gpu_id'))
        ram = get_component_by_id(data.get('ram_id'))
        storage = get_component_by_id(data.get('storage_id'))
        psu = get_component_by_id(data.get('psu_id'))

        # Calculate Power (Rule Based)
        power_breakdown = {}
        total_base_watts = 0

        # 1. CPU Power
        if cpu:
            cpu_tdp = cpu.get('tdp') or cpu.get('power')
            if isinstance(cpu_tdp, str):
                import re
                nums = re.findall(r'\d+', cpu_tdp)
                cpu_tdp = int(nums[0]) if nums else 105
            elif not isinstance(cpu_tdp, (int, float)):
                name = str(cpu.get('name', '')).upper()
                if 'I9' in name or 'R9' in name or 'RYZEN 9' in name: cpu_tdp = 125
                elif 'I7' in name or 'R7' in name or 'RYZEN 7' in name: cpu_tdp = 105
                elif 'I5' in name or 'R5' in name or 'RYZEN 5' in name: cpu_tdp = 65
                else: cpu_tdp = 65
            
            power_breakdown['cpu'] = cpu_tdp
            total_base_watts += cpu_tdp
        else:
            power_breakdown['cpu'] = 0

        # 2. GPU Power
        if gpu:
            gpu_tdp = gpu.get('tdp') or gpu.get('power')
            if isinstance(gpu_tdp, str):
                import re
                nums = re.findall(r'\d+', gpu_tdp)
                gpu_tdp = int(nums[0]) if nums else 200
            elif not isinstance(gpu_tdp, (int, float)):
                name = str(gpu.get('chipset', gpu.get('name', ''))).upper()
                if '5090' in name: gpu_tdp = 600 # Estimated for Blackwell
                elif '4090' in name or '7900 XTX' in name: gpu_tdp = 450
                elif '5080' in name: gpu_tdp = 400
                elif '4080' in name or '7900 XT' in name: gpu_tdp = 320
                elif '4070' in name or '3080' in name or '7800' in name: gpu_tdp = 250
                elif '5070' in name: gpu_tdp = 250
                elif '3070' in name or '4060 TI' in name or '7700' in name: gpu_tdp = 200
                elif '3060' in name or '4060' in name or '7600' in name: gpu_tdp = 150
                elif '50' in name or '60' in name: gpu_tdp = 120
                else: gpu_tdp = 200
            
            power_breakdown['gpu'] = gpu_tdp
            total_base_watts += gpu_tdp
        else:
            power_breakdown['gpu'] = 0

        # 3. RAM Power
        # Estimate: ~3-5W per module.
        # DB might have 'modules' like "2 x 8GB".
        if ram:
            # Try to parse number of modules
            # Common fields: 'modules' (list or string)
            # Default to 2 modules (10W total) if unknown
            ram_power = 10 
            # If we had detailed voltage/module count logic, we'd apply it here.
            power_breakdown['ram'] = ram_power
            total_base_watts += ram_power
        else:
            power_breakdown['ram'] = 0
        
        # 4. Storage Power
        # Estimate ~5-10W
        if storage:
            storage_power = 10
            power_breakdown['storage'] = storage_power
            total_base_watts += storage_power
        else:
            power_breakdown['storage'] = 0

        # 5. Fans & Cooler Power
        fans = get_component_by_id(data.get('fans_id'))
        cooler = get_component_by_id(data.get('cooler_id'))
        
        fans_power = 0
        if fans:
            fans_power = 15 if 'KIT' in str(fans.get('name', '')).upper() or '3-PACK' in str(fans.get('name', '')).upper() else 5
        
        cooler_power = 0
        if cooler:
            c_name = str(cooler.get('name', '')).upper()
            c_type = str(cooler.get('type', '')).upper()
            if 'LIQUID' in c_name or 'AIO' in c_name or 'LIQUID' in c_type:
                cooler_power = 15 # Pump draw
            else:
                cooler_power = 5 # Fan draw
            
        power_breakdown['fans'] = fans_power
        power_breakdown['cooler'] = cooler_power
        total_base_watts += (fans_power + cooler_power)

        # 6. Peripherals Power (External Draw awareness)
        # Often negligible for PSU but good for total system context
        periph_power = 0
        periph_keys = ['keyboard_id', 'mouse_id', 'headset_id', 'webcam_id', 'peripherals_id', 'thermal_paste_id', 'wifi_id', 'speakers_id', 'microphone_id', 'ups_id', 'tool_id']
        for pk in periph_keys:
            if data.get(pk): periph_power += 3 # Nominal 3W (Average)
        
        power_breakdown['peripherals'] = periph_power
        total_base_watts += periph_power

        # 7. Motherboard (Base Overhead)
        base_overhead = 40 # 40W for modern mobo
        power_breakdown['other'] = base_overhead
        total_base_watts += base_overhead

        # Calculations
        safety_margin = 1.3 # 30% overhead
        recommended_watts = int(total_base_watts * safety_margin)

        # Round up to nearest 50
        recommended_watts = ((recommended_watts + 49) // 50) * 50

        # Prepare PSU Comparison
        psu_status = "Incomplete Selection"
        psu_wattage = 0
        
        if psu:
            w = psu.get('wattage') or psu.get('watts') or psu.get('power')
            if w:
                if isinstance(w, str):
                   import re
                   nums = re.findall(r'\d+', w)
                   psu_wattage = int(nums[0]) if nums else 0
                elif isinstance(w, (int, float)):
                   psu_wattage = int(w)
            
            if not psu_wattage and 'name' in psu:
                import re
                nums = re.findall(r'\d{3,4}', str(psu.get('name')))
                if nums:
                    valid_nums = [int(n) for n in nums if 300 <= int(n) <= 2000]
                    if valid_nums:
                        psu_wattage = valid_nums[0]
            
            if psu_wattage > 0:
                if psu_wattage >= recommended_watts:
                    psu_status = "Safe"
                elif psu_wattage >= total_base_watts:
                    psu_status = "Borderline"
                else:
                    psu_status = "Insufficient"
            else:
                psu_status = "Unknown PSU Wattage"
        elif total_base_watts > base_overhead: # Components selected but no PSU
             psu_status = "No PSU Selected"

        return {
            'status': 'success',
            'breakdown': power_breakdown,
            'total_base_wattage': total_base_watts,
            'recommended_wattage': recommended_watts,
            'selected_psu_wattage': psu_wattage,
            'adequacy_status': psu_status
        }

    except Exception as e:
        app.logger.error(f"Power analysis internal error: {e}")
        return {'status': 'error', 'message': str(e)}

def calculate_build_difficulty(build):
    try:
        score = 0
        reasons = []
        
        cpu = get_component_by_id(build.get('cpu_id'))
        gpu = get_component_by_id(build.get('gpu_id'))
        cooler = get_component_by_id(build.get('cooler_id'))
        case = get_component_by_id(build.get('case_id'))
        storage = get_component_by_id(build.get('storage_id'))
        psu = get_component_by_id(build.get('psu_id'))

        # 1. GPU Complexity
        if gpu:
            score += 2
            reasons.append("GPU installation")
            gpu_name = gpu.get('name', '').upper()
            if any(x in gpu_name for x in ['4090', '4080', '7900 XTX', '3090']):
                score += 1
                reasons.append("Large-format GPU handling")
        
        # 2. Storage Count & Type
        if storage:
            score += 1
            interface = storage.get('interface', '').upper()
            if 'SATA' in interface:
                score += 1
                reasons.append("SATA cabling")

        # 3. Cooler Type
        if cooler:
            cooler_type = cooler.get('type', '').lower()
            if 'liquid' in cooler_type or 'aio' in cooler_type:
                score += 3
                reasons.append("Liquid cooling mounting")
            else:
                score += 1
                reasons.append("Aftermarket cooling")

        # 4. Case Size
        if case:
            case_type = case.get('type', '').lower()
            if 'mini' in case_type or 'itx' in case_type or 'small' in case_type:
                score += 4
                reasons.append("High-density ITX assembly")
            elif 'micro' in case_type:
                score += 1
                reasons.append("Micro-ATX space management")

        # 5. PSU Complexity
        if psu:
            wattage = psu.get('wattage') or psu.get('watts') or 0
            if isinstance(wattage, str):
                import re
                nums = re.findall(r'\d+', wattage)
                wattage = int(nums[0]) if nums else 0
            if wattage >= 850:
                score += 1
                reasons.append("High-wattage cable management")

        # Total components check (Total 22 slots)
        required_keys = [
            'cpu_id', 'gpu_id', 'motherboard_id', 'ram_id', 'storage_id', 'psu_id', 'case_id', 'cooler_id', 'fans_id', 
            'thermal_paste_id', 'wifi_id', 'speakers_id', 'microphone_id', 'ups_id', 'tool_id', 'monitor_id', 'os_id',
            'keyboard_id', 'mouse_id', 'headset_id', 'webcam_id', 'peripherals_id'
        ]
        comp_count = sum(1 for k in required_keys if build.get(k) and build.get(k) != "None Selected")
        
        if comp_count >= 18:
            score += 3
        elif comp_count >= 12:
            score += 2
        elif comp_count >= 7:
            score += 1

        # Complexity mapping
        if score <= 2:
            level = "Beginner"
            explanation = "Straightforward build with minimal cable management and standard components."
        elif score <= 6:
            level = "Intermediate"
            # Deduplicate reasons
            reasons = list(dict.fromkeys(reasons))
            explanation = f"Requires careful handling of {', '.join(reasons).lower() if reasons else 'all components'}."
        else:
            level = "Advanced"
            reasons = list(dict.fromkeys(reasons))
            explanation = f"Challenging build due to {', '.join(reasons).lower() if reasons else 'high component density'}. Recommended for experienced builders."

        return {
            'level': level,
            'explanation': explanation,
            'score': score
        }
    except Exception as e:
        app.logger.error(f"Difficulty calculation error: {e}")
        return {
            'level': "Intermediate",
            'explanation': "Standard PC assembly requirements.",
            'score': 4
        }

def get_build_insights_data(build):
    """
    Generates dynamic build insights, assembly steps, and setup checklists.
    Ensures that data is returned even if some components are missing.
    """
    try:
        # Resolve components safely
        cpu = get_component_by_id(build.get('cpu_id'))
        gpu = get_component_by_id(build.get('gpu_id'))
        mobo = get_component_by_id(build.get('motherboard_id'))
        ram = get_component_by_id(build.get('ram_id'))
        storage = get_component_by_id(build.get('storage_id'))
        psu = get_component_by_id(build.get('psu_id'))
        case = get_component_by_id(build.get('case_id'))
        cooler = get_component_by_id(build.get('cooler_id'))
        keyboard = get_component_by_id(build.get('keyboard_id'))
        mouse = get_component_by_id(build.get('mouse_id'))
        headset = get_component_by_id(build.get('headset_id'))
        webcam = get_component_by_id(build.get('webcam_id'))
        fans = get_component_by_id(build.get('fans_id'))
        thermal_paste = get_component_by_id(build.get('thermal_paste_id'))
        wifi = get_component_by_id(build.get('wifi_id'))
        speakers = get_component_by_id(build.get('speakers_id'))
        microphone = get_component_by_id(build.get('microphone_id'))
        ups = get_component_by_id(build.get('ups_id'))
        tools = get_component_by_id(build.get('tool_id'))

        # 1. Overview & Difficulty
        comp_keys = [
            'cpu_id', 'gpu_id', 'motherboard_id', 'ram_id', 'storage_id', 'psu_id', 
            'case_id', 'cooler_id', 'keyboard_id', 'mouse_id', 'headset_id', 'webcam_id',
            'fans_id', 'peripherals_id', 'monitor_id', 'os_id', 'thermal_paste_id',
            'wifi_id', 'speakers_id', 'microphone_id', 'ups_id', 'tool_id'
        ]
        comp_count = sum(1 for k in comp_keys if build.get(k) and build.get(k) != "None Selected")
        
        difficulty = calculate_build_difficulty(build)
        
        # Calculate Cost
        total_cost = 0
        cat_map = {
            'cpu': ('cpu_id', 'cpus'), 'gpu': ('gpu_id', 'gpus'), 'motherboard': ('motherboard_id', 'motherboards'),
            'ram': ('ram_id', 'ram'), 'storage': ('storage_id', 'storage'), 'psu': ('psu_id', 'psu'),
            'case': ('case_id', 'cases'), 'cooler': ('cooler_id', 'coolers'),
            'keyboard': ('keyboard_id', 'keyboards'), 'mouse': ('mouse_id', 'mice'),
            'headset': ('headset_id', 'headsets'), 'webcam': ('webcam_id', 'webcams'),
            'fans': ('fans_id', 'fans'), 'peripherals': ('peripherals_id', 'peripherals'),
            'monitor': ('monitor_id', 'monitors'), 'os': ('os_id', 'os'),
            'thermal_paste': ('thermal_paste_id', 'thermal_paste'),
            'wifi': ('wifi_id', 'wifi_adapters'),
            'speakers': ('speakers_id', 'speakers'),
            'microphone': ('microphone_id', 'microphones'),
            'ups': ('ups_id', 'ups'),
            'tools': ('tool_id', 'tools')
        }
        
        for cat, (key, est_cat) in cat_map.items():
            cid = build.get(key)
            if cid and cid != "None Selected":
                comp = get_component_by_id(cid)
                if comp:
                    total_cost += get_comp_price_usd(comp, est_cat=est_cat)

        quantity = int(build.get('quantity', 1))
        overview = {
            'name': build.get('name', 'Custom Rig'),
            'total_cost': format_price(total_cost),
            'unit_cost': total_cost,
            'quantity': quantity,
            'project_total': format_price(total_cost * quantity),
            'comp_count': comp_count,
            'difficulty': difficulty['level']
        }

        # 2. Time Estimator
        base_install = 30
        cable_mgmt = 20
        bios_os = 20
        
        if cooler and ('liquid' in str(cooler.get('type', '')).lower() or 'aio' in str(cooler.get('name', '')).lower()):
            base_install += 20
        if gpu:
            base_install += 10
        if case and 'small' in str(case.get('type', '')).lower():
            base_install += 15
            cable_mgmt += 25
            
        time_estimator = {
            'total_minutes': base_install + cable_mgmt + bios_os,
            'breakdown': [
                {'task': 'Hardware Installation', 'time': f"{base_install}m"},
                {'task': 'Cable Management', 'time': f"{cable_mgmt}m"},
                {'task': 'BIOS & OS Setup', 'time': f"{bios_os}m"}
            ]
        }

        # 3. Safety Warnings
        warnings = [
            {'title': 'Anti-Static Protocol', 'text': 'Ground yourself by touching the case frame or using an ESD strap before handling the motherboard or CPU.'}
        ]
        if psu:
            warnings.append({'title': 'PSU Safety', 'text': 'Never disassemble a power supply casing. Internal capacitors hold lethal voltage regardless of power status.'})
        if gpu and ('4090' in str(gpu.get('name', '')).upper() or '4080' in str(gpu.get('name', '')).upper()):
             warnings.append({'title': '12VHPWR Integrity', 'text': 'Ensure the 16-pin power connector is pushed in until it clicks. A loose connection can cause high-temperature damage.'})

        # 4. Upgrade Readiness
        power_data = run_power_analysis(build)
        psu_wattage = power_data.get('selected_psu_wattage', 600) or 600
        total_draw = power_data.get('total_base_wattage', 300)
        headroom = psu_wattage - total_draw
        
        upgrade = {
            'ram_slots': {'status': 'Available' if 'ITX' not in str(mobo.get('name', '') if mobo else '').upper() else 'Limited', 'icon': 'memory'},
            'storage_expansion': {'status': 'Ready (M.2/SATA)', 'icon': 'storage'},
            'psu_headroom': {
                'status': 'Safe' if headroom > 150 else 'Limited',
                'icon': 'bolt',
                'value': f"{headroom}W"
            }
        }

        # 5. Assembly Guidance Steps (CORE FIX: Ensure these are always returned)
        steps = [
            {'step': 1, 'title': 'Preparation', 'text': 'Clear a clean work surface. Gather your screwdrivers and thermal paste. Remove the side panels from your case.'},
            {'step': 2, 'title': 'CPU & RAM Installation', 'text': f"Place the {cpu.get('name', 'CPU') if cpu else 'CPU'} into the motherboard socket. Install the {ram.get('name', 'RAM') if ram else 'RAM'} into the DIMM slots (check manual for dual-channel slots)."}
        ]
        
        current_step = 3
        if cooler:
            steps.append({'step': current_step, 'title': 'Cooler Mounting', 'text': f"Mount the {cooler.get('name', 'Cooler')} onto the CPU. Ensure thermal paste coverage is even."})
            current_step += 1
            
        steps.extend([
            {'step': current_step, 'title': 'Case & I/O Setup', 'text': 'Install the I/O shield into the back of the case. Ensure motherboard standoffs are correctly positioned for your board size.'},
            {'step': current_step + 1, 'title': 'Motherboard Mounting', 'text': 'Carefully lower the motherboard onto the standoffs and secure it with screws in a star pattern.'},
            {'step': current_step + 2, 'title': 'Power Supply', 'text': f"Slide the {psu.get('name', 'PSU') if psu else 'Power Supply'} into the basement or slot. Connect the 24-pin motherboard and 8-pin CPU power cables."}
        ])
        current_step += 3
        
        if gpu:
            steps.append({'step': current_step, 'title': 'GPU Installation', 'text': f"Insert the {gpu.get('name', 'GPU')} into the top PCIe slot. Secure the bracket and connect the required power cables."})
            current_step += 1
            
        steps.append({'step': current_step, 'title': 'Final Cabling & Assembly', 'text': 'Connect front panel headers, USB, and audio connectors. Organize cables with zip ties to ensure clear airflow.'})
        current_step += 1

        if thermal_paste:
            steps.append({'step': current_step, 'title': 'Thermal Management', 'text': f"Apply a pea-sized amount of {thermal_paste.get('name', 'Thermal Paste')} to the CPU heatmap if not pre-applied on the cooler."})
            current_step += 1
            
        if wifi:
            steps.append({'step': current_step, 'title': 'Network Setup', 'text': f"Install the {wifi.get('name', 'Network Adapter')} into a PCIe slot or connect the USB receiver."})
            current_step += 1

        if ups:
            steps.append({'step': current_step, 'title': 'Power Protection', 'text': f"Connect your PC and Monitor to the {ups.get('name', 'UPS / Surge Protector')} for clean power and backup."})
            current_step += 1

        # 6. Setup Checklist
        checklist = [
            {'id': 'bios_boot', 'item': 'Power on and enter BIOS (usually Del or F2 key)', 'category': 'Initial Boot'},
            {'id': 'bios_check', 'item': 'Verify all RAM and storage drives appear in the BIOS summary', 'category': 'Validation'}
        ]
        
        if ram:
            checklist.append({'id': 'xmp_expo', 'item': 'Enable XMP, DOCP, or EXPO profile to ensure RAM runs at rated speed', 'category': 'Optimization'})
            
        checklist.extend([
            {'id': 'os_install', 'item': 'Boot from USB and follow the OS installation process', 'category': 'System Setup'},
            {'id': 'net_drivers', 'item': 'Install LAN/Wi-Fi drivers (if not automatically detected)', 'category': 'Drivers'}
        ])
        
        if gpu:
            checklist.append({'id': 'gpu_drivers', 'item': f"Install latest official drivers for the {gpu.get('name', 'GPU')}", 'category': 'Drivers'})

        return {
            'status': 'success',
            'overview': overview,
            'time_estimator': time_estimator,
            'safety_warnings': warnings,
            'upgrade_readiness': upgrade,
            'difficulty': difficulty,
            'assembly_steps': steps,
            'setup_checklist': checklist
        }
    except Exception as e:
        app.logger.error(f"Error in get_build_insights_data: {str(e)}")
        # Return at least basic data if something fails
        return {
            'status': 'success', 
            'overview': {'name': 'Error Loading Details', 'total_cost': format_price(0), 'difficulty': 'Unknown'},
            'assembly_steps': [{'step': 1, 'title': 'Error', 'text': f'Could not generate dynamic steps: {str(e)}'}],
            'setup_checklist': [{'id': 'error', 'item': 'Error loading checklist', 'category': 'Error'}],
            'time_estimator': {'total_minutes': 0, 'breakdown': []},
            'safety_warnings': [{'title': 'Error', 'text': 'Safety data unavailable'}]
        }


@app.route('/api/order-components', methods=['POST'])
@login_required
def order_components():
    global db
    if db is None:
        db = get_db()
        
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
            
        request_data = request.json
        build_id = request_data.get('build_id')
        
        if not build_id:
            # Fallback to current selection if build_id not provided
            comp_ids = {
                'cpu': request_data.get('cpu_id'),
                'gpu': request_data.get('gpu_id'),
                'motherboard': request_data.get('motherboard_id'),
                'ram': request_data.get('ram_id'),
                'storage': request_data.get('storage_id'),
                'psu': request_data.get('psu_id'),
                'case': request_data.get('case_id'),
                'cooler': request_data.get('cooler_id'),
                'fans': request_data.get('fans_id'),
                'monitor': request_data.get('monitor_id'),
                'os': request_data.get('os_id'),
                'peripherals': request_data.get('peripherals_id'),
                'keyboard': request_data.get('keyboard_id'),
                'mouse': request_data.get('mouse_id'),
                'headset': request_data.get('headset_id'),
                'webcam': request_data.get('webcam_id'),
                'thermal_paste': request_data.get('thermal_paste_id'),
                'wifi': request_data.get('wifi_id'),
                'speakers': request_data.get('speakers_id'),
                'microphone': request_data.get('microphone_id'),
                'ups': request_data.get('ups_id'),
                'tool': request_data.get('tool_id')
            }
        else:
            build = db.saved_builds.find_one({
                '_id': ObjectId(build_id),
                'user_id': session.get('user_id')
            })
            if not build:
                return jsonify({'status': 'error', 'message': 'Build not found'}), 404
            comp_ids = {
                'cpu': build.get('cpu_id'),
                'gpu': build.get('gpu_id'),
                'motherboard': build.get('motherboard_id'),
                'ram': build.get('ram_id'),
                'storage': build.get('storage_id'),
                'psu': build.get('psu_id'),
                'case': build.get('case_id'),
                'cooler': build.get('cooler_id'),
                'fans': build.get('fans_id'),
                'monitor': build.get('monitor_id'),
                'os': build.get('os_id'),
                'peripherals': build.get('peripherals_id'),
                'keyboard': build.get('keyboard_id'),
                'mouse': build.get('mouse_id'),
                'headset': build.get('headset_id'),
                'webcam': build.get('webcam_id'),
                'thermal_paste': build.get('thermal_paste_id'),
                'wifi': build.get('wifi_id'),
                'speakers': build.get('speakers_id'),
                'microphone': build.get('microphone_id'),
                'ups': build.get('ups_id'),
                'tool': build.get('tool_id')
            }

        results = []
        
        # Check database for custom SerpAPI key first, then fallback to env
        custom_keys = get_site_setting('api_keys', {})
        db_serp_key = custom_keys.get('serpapi_key')
        serpapi_key = db_serp_key if db_serp_key else os.getenv('SERPAPI_KEY')
        for category, comp_id in comp_ids.items():
            if not comp_id:
                continue
                
            comp = get_component_by_id(comp_id)
            if not comp:
                continue
            
            app.logger.info(f"Order: Searching for {category}: {comp.get('name')}")

            query = f"{comp.get('name')} {category}"
            cache_query = f"{query}_{session.get('currency', 'USD')}"
            
            # Check cache
            cached = db.shopping_cache.find_one({'query': cache_query})
            if cached and cached['expires_at'] > datetime.now(timezone.utc):
                results.append({
                    'category': category,
                    'name': comp.get('name'),
                    'listings': cached['listings']
                })
                continue

            # Fetch from SerpAPI or Mock
            listings = []
            if serpapi_key:
                try:
                    params = {
                        "engine": "google_shopping",
                        "q": query,
                        "api_key": serpapi_key,
                        "num": 15
                    }
                    search_response = requests.get("https://serpapi.com/search", params=params, timeout=10)
                    search_data = search_response.json()
                    shopping_results = search_data.get('shopping_results', [])
                    
                    reputable_sources = [
                        "Amazon", "Best Buy", "B&H", "Micro Center", "Newegg", "Walmart", "Target",
                        "Adorama", "Corsair", "EVGA", "ASUS", "MSI", "Gigabyte", "Samsung", 
                        "Crucial", "Western Digital", "Seagate", "GameStop", "Costco", "Dell", "HP", "Lenovo"
                    ]
                    filtered_listings = []
                    
                    for res in shopping_results:
                        source = res.get('source', '')
                        rating = res.get('rating', 0)
                        reviews = res.get('reviews', 0)
                        
                        is_genuine = any(rep.lower() in source.lower() for rep in reputable_sources)
                        
                        # IMPORTANT: SerpAPI prices come in LOCAL CURRENCY based on geography or query.
                        # format_price() expects values in USD. We must normalize to USD first.
                        extracted_val = res.get('extracted_price')
                        price_str = res.get('price', '')
                        normalized_usd = 0.0
                        
                        try:
                            if isinstance(extracted_val, (int, float)):
                                # If we have a raw number, we still need to know its currency.
                                # Check the price string symbol.
                                cur_code = 'USD' # default
                                for code, sym in CURRENCY_SYMBOLS.items():
                                    if sym and sym in price_str and (sym != '$' or code == 'USD'):
                                        cur_code = code
                                        break
                                normalized_usd = float(extracted_val) / EXCHANGE_RATES.get(cur_code, 1.0)
                            elif price_str:
                                # Manual extraction and normalization
                                p_clean = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
                                if p_clean:
                                    cur_code = 'USD'
                                    for code, sym in CURRENCY_SYMBOLS.items():
                                        if sym and sym in price_str and (sym != '$' or code == 'USD'):
                                            cur_code = code
                                            break
                                    normalized_usd = float(p_clean) / EXCHANGE_RATES.get(cur_code, 1.0)
                        except:
                            normalized_usd = 0.0

                        display_price = format_price(normalized_usd) if normalized_usd > 0 else price_str
                            
                        if is_genuine or (rating >= 4.0 and reviews >= 10):
                            filtered_listings.append({
                                'title': res.get('title'),
                                'price': display_price,
                                'source': res.get('source'),
                                'link': res.get('link'),
                                'rating': rating,
                                'reviews': reviews
                            })
                    
                    # Sort primarily by rating and reviews
                    filtered_listings.sort(key=lambda x: (x['rating'] or 0, x['reviews'] or 0), reverse=True)
                    
                    # Also collect at most 3
                    for res in filtered_listings[:3]:
                        listings.append(res)
                        
                    # Fallback to standard if none met criteria
                    if not listings:
                        for res in shopping_results[:3]:
                            extracted_val = res.get('extracted_price')
                            price_str = res.get('price', '')
                            normalized_usd = 0.0
                            
                            try:
                                if isinstance(extracted_val, (int, float)):
                                    cur_code = 'USD'
                                    for code, sym in CURRENCY_SYMBOLS.items():
                                        if sym and sym in price_str and (sym != '$' or code == 'USD'):
                                            cur_code = code
                                            break
                                    normalized_usd = float(extracted_val) / EXCHANGE_RATES.get(cur_code, 1.0)
                                elif price_str:
                                    p_clean = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
                                    if p_clean:
                                        cur_code = 'USD'
                                        for code, sym in CURRENCY_SYMBOLS.items():
                                            if sym and sym in price_str and (sym != '$' or code == 'USD'):
                                                cur_code = code
                                                break
                                        normalized_usd = float(p_clean) / EXCHANGE_RATES.get(cur_code, 1.0)
                            except:
                                normalized_usd = 0.0

                            display_price = format_price(normalized_usd) if normalized_usd > 0 else price_str
                                
                            listings.append({
                                'title': res.get('title'),
                                'price': display_price,
                                'source': "Market Search", # Overwrite specific retailers like Amazon/Newegg
                                'link': res.get('link'),
                                'rating': 0 # Hide rating for consistency
                            })
                            
                except Exception as e:
                    app.logger.error(f"SerpAPI error for {query}: {e}")
            
            # Always injection the direct DB verified source if it exists and has an external URL
            db_link = comp.get('product_url') or comp.get('url')
            if db_link and db_link != '#' and len(str(db_link)) > 5:
                # Get correct price for verified listing
                verified_price = get_comp_price_usd(comp, est_cat=category)
                db_listing = {
                    'title': f"Verified: {comp.get('name')}",
                    'price': format_price(verified_price) if verified_price > 0 else "View Price",
                    'source': comp.get('retailer', "RigMaster Direct"),
                    'link': db_link,
                    'rating': 4.9,
                    'is_verified': True
                }
                # Check if it duplicates a live result (fuzzy match on retailer)
                is_duplicate = any(l.get('source', '').lower() in str(db_listing['source']).lower() for l in listings)
                if not is_duplicate:
                    listings.insert(0, db_listing)

            # Final fallbacks if still NO listings found
            if not listings:
                comp_price = get_comp_price_usd(comp, est_cat=category)
                search_path = urllib.parse.quote(query)
                
                if not serpapi_key:
                    price_str = format_price(comp_price) if comp_price > 0 else "Price Unavailable"
                    listings = [{
                        'title': comp.get('name'),
                        'price': price_str,
                        'source': comp.get('retailer', "Market Search"),
                        'link': f"https://www.google.com/search?q={search_path}&tbm=shop",
                        'rating': 0
                    }]
                else:
                    if comp_price > 0:
                        listings = [{
                            'title': f"Market Average: {comp.get('name')}",
                            'price': format_price(comp_price),
                            'source': "Price Index",
                            'link': f"https://www.google.com/search?q={search_path}&tbm=shop",
                            'rating': 4.0
                        }]
                    else:
                        listings = [{'title': 'Market listing not found', 'price': '', 'source': 'SerpAPI Fallback', 'link': '#'}]

            # Update cache
            db.shopping_cache.update_one(
                {'query': cache_query},
                {'$set': {
                    'listings': listings,
                    'expires_at': datetime.now(timezone.utc) + timedelta(hours=24)
                }},
                upsert=True
            )
            
            results.append({
                'category': category,
                'name': comp.get('name'),
                'listings': listings
            })

        return jsonify({
            'status': 'success', 
            'results': results,
            'currency': session.get('currency', 'USD'),
            'currency_symbol': CURRENCY_SYMBOLS.get(session.get('currency', 'USD'), '$'),
            'exchange_rate': EXCHANGE_RATES.get(session.get('currency', 'USD'), 1.0)
        })
    except Exception as e:
        app.logger.error(f"Order components error: {e}")
        return jsonify({'status': 'error', 'message': "Purchase links temporarily unavailable"}), 500


@app.route('/api/ai-recommend', methods=['POST'])
@login_required
def api_ai_recommend():
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500

        data = request.json
        raw_budget = float(data.get('budget', 0))
        user_currency = session.get('currency', 'USD')
        rate = EXCHANGE_RATES.get(user_currency, 1.0)
        budget = raw_budget / rate  # work in USD internally
        usage = data.get('usage', 'gaming')
        requirements = data.get('requirements', '')

        if budget <= 0:
            return jsonify({'status': 'error', 'message': 'Please enter a valid budget'}), 400

        # --- Cache check ---
        import hashlib
        cache_key = f"rec_v16_{int(budget)}_{usage}_{hashlib.md5(requirements.encode()).hexdigest()}"
        cached = db.ai_cache.find_one({'cache_key': cache_key})
        if cached:
            app.logger.info(f"Serving cached recommendation for {cache_key}")
            symbol = CURRENCY_SYMBOLS.get(user_currency, '$')
            return jsonify({
                'status': 'success',
                'build': cached.get('build'),
                'total_estimated_cost': cached.get('total_estimated_cost'),
                'explanation': cached.get('explanation'),
                'cached': True,
                'currency': user_currency,
                'currency_symbol': symbol,
                'exchange_rate': rate
            })

        # --- All 16 component slots with budget allocation caps ---
        COMPONENT_SLOTS = [
            # (display_key, db_category,  budget_pct_cap)
            ('CPU',         'cpu',         0.30),
            ('GPU',         'gpu',         0.50),
            ('Motherboard', 'motherboard', 0.15),
            ('RAM',         'ram',         0.12),
            ('Storage',     'storage',     0.12),
            ('PSU',         'psu',         0.10),
            ('Case',        'case',        0.10),
            ('Cooler',      'cooler',      0.10),
            ('Monitor',     'monitor',     0.25),
            ('OS',          'os',          0.08),
            ('Fans',        'fans',        0.05),
            ('Keyboard',    'peripherals', 0.08),
            ('Mouse',       'peripherals', 0.06),
            ('Headset',     'peripherals', 0.07),
            ('Webcam',      'peripherals', 0.06),
            ('Peripherals', 'peripherals', 0.05),
            ('Thermal_Paste','thermal_paste', 0.02),
            ('Wifi',        'wifi_adapters', 0.03),
            ('Speakers',    'speakers',    0.05),
            ('Microphone',  'microphones',  0.06),
            ('UPS',         'ups',         0.08),
            ('Tools',       'tools',       0.03),
        ]

        # Sub-category filters for peripherals
        PERIPH_SUBCATS = {
            'Keyboard': 'keyboard',
            'Mouse':    'mouse',
            'Headset':  'headset',
            'Webcam':   'webcam',
        }

        # Build the component pool for the AI (from unified components collection)
        engine_pool = {}   # slot_key -> list of "ID:...|Name|Price:..." strings
        allowed_items = {} # slot_key -> list of raw component dicts
        symbol = CURRENCY_SYMBOLS.get(user_currency, '$')

        # Mapping from slot key to estimate category for pricing fallback
        _est_cat_map = {
            'CPU': 'cpus', 'GPU': 'gpus', 'Motherboard': 'motherboards',
            'RAM': 'ram', 'Storage': 'storage', 'PSU': 'psu',
            'Case': 'cases', 'Cooler': 'coolers', 'Monitor': 'monitors',
            'OS': 'os', 'Fans': 'fans',
            'Keyboard': 'keyboards', 'Mouse': 'mice',
            'Headset': 'headsets', 'Webcam': 'webcams', 'Peripherals': 'peripherals',
            'Thermal_Paste': 'thermal_paste', 'Wifi': 'wifi_adapters', 'Speakers': 'speakers', 
            'Microphone': 'microphones', 'UPS': 'ups', 'Tools': 'tools'
        }

        for slot_key, db_cat, cap_pct in COMPONENT_SLOTS:
            max_price_usd = budget * cap_pct
            query = {
                'category': db_cat,
                'status': {'$ne': 'Discontinued'}
            }
            if slot_key in PERIPH_SUBCATS:
                query['sub_category'] = PERIPH_SUBCATS[slot_key]

            raw_items = list(db.components.find(
                query,
                {'name': 1, 'price': 1, 'msrp': 1, 'cost': 1, 'status': 1,
                 'sub_category': 1, 'socket': 1, 'memory_type': 1, 'chipset': 1,
                 'tdp': 1, 'wattage': 1, 'watts': 1, 'type': 1}
            ).sort('name', 1).limit(300))

            # If sub_category filter gave nothing, try without it (fallback for peripherals)
            if not raw_items and slot_key in PERIPH_SUBCATS:
                query_fallback = {'category': db_cat, 'status': {'$ne': 'Discontinued'}}
                raw_items = list(db.components.find(
                    query_fallback,
                    {'name': 1, 'price': 1, 'msrp': 1, 'cost': 1, 'status': 1,
                     'sub_category': 1, 'socket': 1, 'memory_type': 1, 'chipset': 1,
                     'tdp': 1, 'wattage': 1, 'watts': 1, 'type': 1}
                ).sort('name', 1).limit(100))

            # Price every item — use heuristic estimate when no real price is stored
            est_cat = _est_cat_map.get(slot_key, 'peripherals')
            for item in raw_items:
                item['_usd_price'] = get_comp_price_usd(item, est_cat=est_cat)

            # Apply budget cap — but always keep at least the 5 cheapest as fallback
            within_budget = [it for it in raw_items if it['_usd_price'] <= max_price_usd]
            if not within_budget and raw_items:
                # All items over budget — take the cheapest 5 so the AI has something to pick
                within_budget = sorted(raw_items, key=lambda x: x['_usd_price'])[:5]
            valid = within_budget

            # Pick a highly curated sample to avoid "Payload Too Large" errors (Error 413)
            n = len(valid)
            if n <= 12:
                selected = valid
            else:
                top = valid[:4]
                mid = valid[n//2 - 2: n//2 + 2]
                bot = valid[max(0, n-4):]
                seen = set()
                selected = []
                for it in top + mid + bot:
                    sid = str(it['_id'])
                    if sid not in seen:
                        seen.add(sid)
                        selected.append(it)

            pool_strs = [
                f"ID:{it['_id']}|{it['name']}|{symbol}{int(it['_usd_price'] * rate):,}"
                for it in selected
            ]
            engine_pool[slot_key.lower()] = pool_strs
            allowed_items[slot_key] = selected


        # --- Call AI engine ---
        ai_engine = get_ai_engine()
        recommendation = ai_engine.get_pc_recommendation(
            budget=f"{symbol}{int(raw_budget):,}",
            use_case=usage,
            preferences={"requirements": requirements, "currency": user_currency, "currency_symbol": symbol},
            component_pool=engine_pool,
            user_currency=user_currency
        )
        ai_reasoning = None
        if recommendation:
            ai_reasoning = recommendation.get('reasoning') or recommendation.get('explanation')


        # --- Budget allocation ratios (used for heuristic selection when AI fails) ---
        alloc_pcts = {s[0]: s[2] for s in COMPONENT_SLOTS}

        # --- Parse AI response: extract IDs or fall back to name matching ---
        raw_build = {}  # slot_key -> 24-char hex ID str  OR  plain name str (fallback)
        if recommendation:
            for slot_key, _, _ in COMPONENT_SLOTS:
                ai_key = slot_key.lower()
                val = str(recommendation.get(ai_key, '')).strip()
                if not val or val.lower() in ('none', 'null', ''):
                    continue
                # Tier 1: proper ID embedded in AI response
                id_match = re.search(r'[0-9a-fA-F]{24}', val)
                if id_match:
                    raw_build[slot_key] = id_match.group(0)
                    continue
                # Tier 2: fuzzy name match inside the pre-built allowed pool
                val_up = val.upper()
                for item in allowed_items.get(slot_key, []):
                    item_name = str(item.get('name', '')).upper()
                    if item_name and (val_up in item_name or item_name in val_up):
                        raw_build[slot_key] = str(item['_id'])
                        break
                else:
                    # Store raw name for last-chance lookup later
                    raw_build[slot_key] = val

        # --- Tier 3 guarantee: any slot still missing → pick by budget allocation ---
        for slot_key, _, _ in COMPONENT_SLOTS:
            if slot_key not in raw_build and allowed_items.get(slot_key):
                target = budget * alloc_pcts.get(slot_key, 0.05)
                best = min(allowed_items[slot_key],
                           key=lambda x: abs(x.get('_usd_price', 0) - target))
                raw_build[slot_key] = str(best['_id'])

        # --- Post-process: resolve every slot to a real DB document ---
        final_build = {}
        total_usd = 0.0

        for slot_key, db_cat, _ in COMPONENT_SLOTS:
            comp_data = raw_build.get(slot_key)
            if not comp_data:
                continue

            comp_doc = None

            # Step A: ObjectId lookup in unified components collection
            id_match = re.search(r'[0-9a-fA-F]{24}', str(comp_data))
            if id_match:
                try:
                    comp_doc = db.components.find_one({'_id': ObjectId(id_match.group(0))})
                except Exception:
                    pass

            # Step B: name search in pre-built allowed pool
            if not comp_doc and allowed_items.get(slot_key):
                val_up = str(comp_data).upper()
                for item in allowed_items[slot_key]:
                    item_name = str(item.get('name', '')).upper()
                    if item_name and (val_up in item_name or item_name in val_up):
                        comp_doc = item
                        break

            # Step C: name search across entire category in db.components
            if not comp_doc:
                name_str = str(comp_data)
                if len(name_str) > 3:
                    try:
                        comp_doc = db.components.find_one(
                            {'category': db_cat, 'name': {'$regex': re.escape(name_str[:20]), '$options': 'i'}}
                        )
                    except Exception:
                        pass

            # Step D (ultimate fallback): pick best from allowed_items by budget allocation
            if not comp_doc and allowed_items.get(slot_key):
                target = budget * alloc_pcts.get(slot_key, 0.05)
                comp_doc = min(allowed_items[slot_key],
                               key=lambda x: abs(x.get('_usd_price', 0) - target))

            if not comp_doc:
                # Absolute last fallback — find ANY item in this category so we don't return null
                comp_doc = db.components.find_one({'category': db_cat})
                if not comp_doc:
                    continue  # truly nothing in DB for this category — skip

            comp_id = str(comp_doc['_id'])
            comp_name = comp_doc.get('name', 'Unknown Component')
            
            # Use PriceFetcher for real-time pricing instead of database estimates
            from price_fetcher import get_price_fetcher
            price_fetcher = get_price_fetcher()
            price_data = price_fetcher.fetch_component_price(comp_name)
            
            if price_data and price_data.get('price'):
                price_usd = price_data['price']
                price_source = price_data.get('source', 'api')
            else:
                # Fallback to database price if API fails
                price_usd = comp_doc.get('_usd_price') or get_comp_price_usd(comp_doc)
                price_source = 'database_fallback'

            final_build[slot_key] = {
                'id': comp_id,
                'name': comp_name,
                'estimated_price': round(price_usd, 2),
                'price_source': price_source
            }
            total_usd += price_usd

        if ai_reasoning:
            explanation = ai_reasoning
        else:
            explanation = (
                f"### RigMaster Smart Build — {usage}\n\n"
                f"AI inference nodes are currently unavailable. This complete build was assembled "
                f"**directly from your database** by allocating your **{symbol}{int(raw_budget):,} budget** proportionally "
                f"across all 16 component categories and selecting the best-matched real component for each slot.\n\n"
                f"Every component listed is a real item from your MongoDB components collection."
            )

        provider_label = 'ai assistant' if recommendation else 'RigMaster DB Selection'
        result = {
            'build': final_build,
            'total_estimated_cost': round(total_usd, 2),
            'explanation': explanation,
            'provider': provider_label
        }

        # Save to cache
        try:
            db.ai_cache.update_one(
                {'cache_key': cache_key},
                {'$set': {
                    'cache_key': cache_key,
                    'build': result['build'],
                    'total_estimated_cost': result['total_estimated_cost'],
                    'explanation': result['explanation'],
                    'created_at': datetime.now(timezone.utc)
                }},
                upsert=True
            )
        except Exception:
            pass

        symbol = CURRENCY_SYMBOLS.get(user_currency, '$')
        return jsonify({
            'status': 'success',
            'build': result['build'],
            'total_estimated_cost': result['total_estimated_cost'],
            'explanation': result['explanation'],
            'provider': result['provider'],
            'cached': False,
            'currency': user_currency,
            'currency_symbol': symbol,
            'exchange_rate': rate
        })

    except Exception as e:
        app.logger.error(f"Recommendation error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to generate recommendation. Please try again.'}), 500

@app.route('/ai-assistant', methods=['POST'])
@login_required
def ai_assistant():
    """Unified RigMaster Nexus AI Assistant endpoint — gives database-backed help."""
    try:
        data = request.json
        user_message = data.get('message')
        context_ids = data.get('context', {})
        page_context = str(context_ids.get('page', '')).lower()
        
        if not user_message:
            return jsonify({'status': 'error', 'message': 'Message is required'}), 400

        # Resolve component IDs to names for AI context (using unified components collection)
        # Supports all 16 slots plus any other build context
        resolved_context = {}
        for key, comp_id in context_ids.items():
            if key == 'page':
                continue
            if comp_id and len(str(comp_id)) == 24:
                try:
                    comp = db.components.find_one({'_id': ObjectId(comp_id)})
                    if comp:
                        label = key.replace('_id', '').replace('-', ' ').replace('_', ' ').upper()
                        resolved_context[label] = comp.get('name')
                except:
                    pass

        # --- DATABASE HARDWARE CONTEXT (Representative Sample) ---
        user_currency = session.get('currency', 'USD')
        rate = EXCHANGE_RATES.get(user_currency, 1.0)
        symbol = CURRENCY_SYMBOLS.get(user_currency, '$')
        
        db_context_list = []
        try:
            def parse_component_price(component):
                return get_comp_price_usd(component)

            if page_context == 'builder':
                builder_inventory = list(db.components.find(
                    {'status': {'$ne': 'Discontinued'}},
                    {'name': 1, 'category': 1, 'sub_category': 1, 'brand': 1, 'model': 1, 'price': 1, 'msrp': 1, 'cost': 1, 'status': 1}
                ).sort([('category', 1), ('sub_category', 1), ('name', 1)]))

                token_parts = [user_message]
                token_parts.extend(resolved_context.values())
                normalized_parts = " ".join([str(part).lower() for part in token_parts if part])
                raw_tokens = re.findall(r"[a-z0-9\-\+\.#]+", normalized_parts)
                stop_words = {
                    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'about', 'what', 'which',
                    'would', 'should', 'could', 'please', 'need', 'want', 'best', 'good', 'build', 'builder',
                    'page', 'show', 'find', 'component', 'components', 'option', 'options', 'recommend',
                    'recommendation', 'price', 'cost', 'under', 'over', 'than', 'into'
                }
                search_tokens = {token for token in raw_tokens if len(token) > 1 and token not in stop_words}

                category_counts = {}
                matching_inventory = []
                category_samples = {}

                for component in builder_inventory:
                    category_key = str(component.get('sub_category') or component.get('category') or 'unknown').lower()
                    category_counts[category_key] = category_counts.get(category_key, 0) + 1

                    haystack = " ".join([
                        str(component.get('name', '')),
                        str(component.get('brand', '')),
                        str(component.get('model', '')),
                        str(component.get('category', '')),
                        str(component.get('sub_category', ''))
                    ]).lower()

                    if search_tokens and any(token in haystack for token in search_tokens):
                        matching_inventory.append(component)

                    if category_key not in category_samples:
                        category_samples[category_key] = []
                    if len(category_samples[category_key]) < 3:
                        category_samples[category_key].append(component)

                db_context_list.append(
                    f"BUILDER INVENTORY MODE: Full components table searched with {len(builder_inventory)} active records."
                )
                if category_counts:
                    summary = ", ".join(
                        f"{cat.upper()}: {count}" for cat, count in sorted(category_counts.items())
                    )
                    db_context_list.append(f"AVAILABLE INVENTORY COUNTS: {summary}")

                if matching_inventory:
                    db_context_list.append(
                        f"RELEVANT MATCHES FOR THIS BUILDER REQUEST ({min(len(matching_inventory), 80)} shown of {len(matching_inventory)}):"
                    )
                    for component in matching_inventory[:80]:
                        category_label = str(component.get('sub_category') or component.get('category') or 'unknown').upper()
                        descriptor = " | ".join([part for part in [component.get('brand'), component.get('model')] if part])
                        price_value = parse_component_price(component)
                        price_label = format_price(price_value, user_currency) if price_value else "Price Unavailable"
                        if descriptor:
                            db_context_list.append(f"{category_label}: {component.get('name')} [{descriptor}] ({price_label})")
                        else:
                            db_context_list.append(f"{category_label}: {component.get('name')} ({price_label})")
                else:
                    db_context_list.append("NO DIRECT NAME MATCHES FOUND IN THE FULL COMPONENTS TABLE FOR THIS REQUEST.")
                    db_context_list.append("CATEGORY PREVIEW FROM THE BUILDER INVENTORY:")
                    for category_key, samples in sorted(category_samples.items()):
                        sample_lines = []
                        for component in samples:
                            price_value = parse_component_price(component)
                            price_label = format_price(price_value, user_currency) if price_value else "Price Unavailable"
                            sample_lines.append(f"{component.get('name')} ({price_label})")
                        db_context_list.append(f"{category_key.upper()}: " + "; ".join(sample_lines))
            else:
                # Sample across all categories to give AI a broad but balanced view of inventory
                # We take 4 items per slot (Top, Mid, Bottom) to represent the full price spectrum
                CORE_CATS = ['cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooler']
                EXTRA_CATS = ['monitor', 'os', 'fans', 'keyboard', 'mouse', 'headset', 'webcam', 'peripherals']
                
                for cat in CORE_CATS + EXTRA_CATS:
                    total_in_cat = db.components.count_documents({'category': cat, 'status': {'$ne': 'Discontinued'}})
                    if total_in_cat == 0:
                        continue
                    
                    top = list(db.components.find({'category': cat, 'status': {'$ne': 'Discontinued'}})
                               .sort('price', -1).limit(1))
                    bot = list(db.components.find({'category': cat, 'status': {'$ne': 'Discontinued'}})
                               .sort('price', 1).limit(1))
                    
                    mid = []
                    if total_in_cat > 3:
                        mid = list(db.components.find({'category': cat, 'status': {'$ne': 'Discontinued'}})
                                   .skip(total_in_cat // 2).limit(2))
                    
                    cat_sample = {str(i['_id']): i for i in (top + mid + bot)}.values()
                    
                    for it in cat_sample:
                        p = parse_component_price(it)
                        db_context_list.append(f"{cat.upper()}: {it.get('name')} ({symbol}{int(p * rate):,})")

        except Exception as e:
            app.logger.warning(f"Failed to fetch assistant DB context: {e}")

        # Construct system prompt
        system_role = (
            "You are 'ai assistant', the ultimate AI companion for PC building and hardware optimization. "
            "You provide technical guidance on all 16 components of the PC ecosystem, "
            "including core hardware, peripherals, and software.\n\n"
            + ("BUILDER PAGE MODE: You have access to the full components table for this page.\n\n" if page_context == 'builder' else "")
            + "INVENTORY CONTEXT ("
            + ("Full components table currently loaded from our MongoDB database" if page_context == 'builder'
               else "Representative items currently in our MongoDB database")
            + "):\n"
            + ("\n".join(db_context_list) if db_context_list else "Database temporarily offline.") + 
            "\n\nUSER'S CURRENT BUILD CONTEXT:\n" + 
            ("\n".join([f"- {k}: {v}" for k, v in resolved_context.items()]) if resolved_context else "No specific components selected yet.") +
            "\n\nCRITICAL AI ASSISTANT RULES:\n"
            "1. DATABASE-BACKED RECOMMENDATIONS: If a user asks for component recommendations, you MUST ONLY suggest items listed in the INVENTORY CONTEXT above. Do not suggest hardware from your external training data that is not in the list.\n"
            "2. ASSISTANT NAME: Always identify as 'ai assistant'.\n"
            "3. FULL ECOSYSTEM KNOWLEDGE: You are an expert on all 16 slots (CPU, GPU, Motherboard, RAM, Storage, PSU, Case, Cooler, Monitor, OS, Fans, Keyboard, Mouse, Headset, Webcam, Peripherals).\n"
            "4. RESPONSE STYLE: Use professional yet accessible language. Formatting with Markdown (bolding, lists) is encouraged. Be concise.\n"
            + ("5. BUILDER-SPECIFIC SCOPE: On the builder page, answer from the full components table and treat it as the source of truth for availability, options, and alternatives.\n" if page_context == 'builder' else "")
        )

        ai_engine = get_ai_engine()
        ai_response = ai_engine.generate_chat_response(system_role, user_message)

        if not ai_response:
             # Heuristic simple fallback for basic chat
             if "hello" in user_message.lower():
                 ai_response = "Greetings. I am ai assistant. How can I assist you with your PC hardware needs today?"
             else:
                 return jsonify({'status': 'error', 'message': 'AI nodes are currently offline. Please try again shortly.'}), 503

        return jsonify({
            'status': 'success',
            'response': ai_response,
            'provider': 'RigMaster Nexus AI'
        })
    except Exception as e:
        app.logger.error(f"AI Assistant Error: {e}")
        return jsonify({'status': 'error', 'message': 'Assistant unavailable'}), 500

@app.route('/api/compare-builds', methods=['POST'])
@login_required
def compare_builds():
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
            
        data = request.json
        build_ids = data.get('build_ids', [])
        
        if not build_ids or len(build_ids) < 2:
            return jsonify({'status': 'error', 'message': 'Select at least 2 builds to compare'}), 400
            
        if len(build_ids) > 3:
             return jsonify({'status': 'error', 'message': 'You can compare up to 3 builds maximum'}), 400

        comparison_data = []
        user_id = session.get('user_id')
        
        for build_id in build_ids:
            build = db.saved_builds.find_one({
                '_id': ObjectId(build_id),
                'user_id': user_id
            })
            
            if not build:
                continue
                
            # Helper to get component name and basic spec for comparison
            def get_comp_info(col, oid):
                if not oid: return "None Selected"
                try:
                    c = db[col].find_one({'_id': ObjectId(oid)})
                    if not c: return "Unknown Component"
                    return c.get('name', 'Unknown')
                except:
                    return "Error loading"

            # Resolve names
            details = {
                'id': str(build['_id']),
                'date': build.get('created_at', datetime.now(timezone.utc)).strftime('%Y-%m-%d'),
                'CPU': get_comp_info('cpus', build.get('cpu_id')),
                'GPU': get_comp_info('gpus', build.get('gpu_id')),
                'Motherboard': get_comp_info('motherboards', build.get('motherboard_id')),
                'RAM': get_comp_info('ram', build.get('ram_id')),
                'Storage': get_comp_info('storage', build.get('storage_id')),
                'PSU': get_comp_info('psu', build.get('psu_id')),
                'Case': get_comp_info('cases', build.get('case_id')),
                'Cooler': get_comp_info('coolers', build.get('cooler_id'))
            }
            
            # Add Analysis Results for this build
            # We mock some costs and readiness since we don't have a live pricing API or deep upgrade DB yet
            # but we can use our existing power analysis logic
            
            # Power Analysis
            power_res = run_power_analysis({
                'cpu_id': build.get('cpu_id'),
                'gpu_id': build.get('gpu_id'),
                'ram_id': build.get('ram_id'),
                'storage_id': build.get('storage_id'),
                'psu_id': build.get('psu_id')
            })
            
            # Validation (Compatibility)
            valid_res = run_validation_logic({
                'cpu_id': build.get('cpu_id'),
                'motherboard_id': build.get('motherboard_id'),
                'ram_id': build.get('ram_id')
            })

            details['power_status'] = power_res.get('adequacy_status', 'Unknown')
            details['power_wattage'] = f"{power_res.get('total_base_wattage', 0)}W / {power_res.get('selected_psu_wattage', 0)}W"
            details['compatibility'] = valid_res.get('status', 'Unknown')
            
            # Heuristic Cost (Just for UI demo since market prices are absent)
            # In a real app, this would query a pricing DB
            details['estimated_cost'] = "$ ---" 
            
            # Upgrade Readiness Heuristic
            details['upgrade_readiness'] = "High" if power_res.get('adequacy_status') == "Safe" else "Moderate"
            
            comparison_data.append(details)
            
        return jsonify({
            'status': 'success',
            'comparison': comparison_data
        })
    except Exception as e:
        app.logger.error(f"Comparison error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# RIGMASTER NEXUS - UNIFIED AI ASSISTANT ENDPOINT
# ============================================================
# AI Assistant chat route consolidated above

# AI Assistant chat logic consolidated in the primary ai_assistant() route above.


# ============================================================
# AI ASSISTANT ANALYSIS (DeepSeek-R1)
# ============================================================
@app.route('/ai/analyze', methods=['POST'])
@login_required
def ai_analyze():
    """
    DeepSeek-R1 AI Assistant endpoint
    Analyzes user budget and requirements, provides recommendations
    """
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500

        data = request.json
        raw_budget = float(data.get('budget', 0))
        # Convert budget to USD for internal processing
        user_currency = session.get('currency', 'USD')
        rate = EXCHANGE_RATES.get(user_currency, 1.0)
        budget = raw_budget / rate
        usage = data.get('usage', 'gaming')
        requirements = data.get('requirements', '')

        if budget <= 0:
            return jsonify({'status': 'error', 'message': 'Please enter a valid budget'}), 400

        # Fetch available components from database
        # Fetch available components from database
        components_data = {
            'cpus': list(db.components.find({'category': 'cpu'}, {'_id': 0, 'name': 1, 'price': 1, 'cores': 1, 'socket': 1}).limit(20)),
            'gpus': list(db.components.find({'category': 'gpu'}, {'_id': 0, 'name': 1, 'price': 1, 'vram': 1}).limit(20)),
            'motherboards': list(db.components.find({'category': 'motherboard'}, {'_id': 0, 'name': 1, 'price': 1, 'socket': 1, 'form_factor': 1}).limit(20)),
            'ram': list(db.components.find({'category': 'ram'}, {'_id': 0, 'name': 1, 'price': 1, 'capacity': 1, 'speed': 1}).limit(20)),
            'storage': list(db.components.find({'category': 'storage'}, {'_id': 0, 'name': 1, 'price': 1, 'capacity': 1, 'type': 1}).limit(20)),
            'psu': list(db.components.find({'category': 'psu'}, {'_id': 0, 'name': 1, 'price': 1, 'wattage': 1}).limit(20))
        }

        # Build system prompt for DeepSeek-R1
        system_prompt = """You are an AI assistant for PC system assembly and configuration.
Use ONLY the provided component data to make recommendations.
Explain recommendations in simple, educational language.
Do NOT make final decisions for the user.
Do NOT suggest components outside the provided database.
Focus on explaining trade-offs, compatibility, and value."""

        # Build user prompt with structured data
        user_prompt = f"""Budget: ${budget}
Primary Use: {usage}
Special Requirements: {requirements if requirements else 'None'}

Available Components:
CPUs: {len(components_data['cpus'])} options
GPUs: {len(components_data['gpus'])} options  
Motherboards: {len(components_data['motherboards'])} options
RAM: {len(components_data['ram'])} options
Storage: {len(components_data['storage'])} options
PSUs: {len(components_data['psu'])} options

Please analyze this build request and provide:
1. Budget allocation strategy
2. Component priority recommendations
3. Compatibility considerations
4. Performance expectations

Keep response concise (under 300 words)."""

        # Use unified AI Engine for analysis
        ai_engine = get_ai_engine()
        ai_response = ai_engine.analyze_build(budget, usage, requirements, components_data)
        
        if ai_response:
            return jsonify({'status': 'success', 'response': ai_response})
        else:
            return jsonify({'status': 'error', 'message': 'AI assistant temporarily unavailable'}), 500

    except Exception as e:
        app.logger.error(f"AI analyze error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/api/toggle_public/<build_id>', methods=['POST'])
@login_required
def toggle_public(build_id):
    try:
        build = db.saved_builds.find_one({'_id': ObjectId(build_id), 'user_id': session.get('user_id')})
        if not build:
            return jsonify({'status': 'error', 'message': 'Build not found'}), 404
            
        new_val = not build.get('is_public', False)
        db.saved_builds.update_one({'_id': ObjectId(build_id)}, {'$set': {'is_public': new_val}})
        return jsonify({'status': 'success', 'is_public': new_val})
    except Exception as e:
        app.logger.error(f"Toggle public error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/benchmark-simulator', methods=['POST'])
@login_required
def api_benchmark_simulator():
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
            
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        cpu_id = data.get('cpu_id')
        gpu_id = data.get('gpu_id')
        ram_id = data.get('ram_id', '16GB')

        # 1. Check Global Cache first
        cache_key = f"bench_{cpu_id}_{gpu_id}"
        cached_result = db.ai_cache.find_one({'cache_key': cache_key})
        
        if cached_result:
            return jsonify({
                'status': 'success',
                'benchmarks': cached_result.get('benchmarks'),
                'bottleneck_warning': cached_result.get('bottleneck_warning'),
                'fallback_used': False,
                'cached': True
            })

        # Helper to get component
        def get_comp(comp_id):
            if not comp_id: return None
            try:
                return db.components.find_one({'_id': ObjectId(comp_id)})
            except:
                return None

        # Fetch components
        cpu = get_comp(cpu_id)
        gpu = get_comp(gpu_id)
        ram = get_comp(ram_id)
        
        if not cpu or not gpu:
            return jsonify({'status': 'error', 'message': 'CPU and GPU are required for simulation'}), 400

        # Use unified AI Engine for performance estimation
        ai_engine = get_ai_engine()
        result = ai_engine.estimate_performance(
            cpu_name=cpu.get('name', 'Unknown CPU'),
            gpu_name=gpu.get('name', 'Unknown GPU'),
            ram_name=ram.get('name') if ram else '16GB',
            games=["Cyberpunk 2077", "COD: Warzone", "Valorant", "Elden Ring", "Forza Horizon 5"]
        )
        
        fallback_used = result.get('notes', '').startswith('Estimated performance based on GPU tier')

        # SAVE TO CACHE if the result was from AI
        if result and not fallback_used:
             try:
                 db.ai_cache.update_one(
                     {'cache_key': cache_key},
                     {'$set': {
                         'cache_key': cache_key,
                         'benchmarks': result.get('benchmarks'),
                         'bottleneck_warning': result.get('bottleneck_warning'),
                         'created_at': datetime.now(timezone.utc)
                     }},
                     upsert=True
                 )
             except:
                 pass

        return jsonify({
            'status': 'success',
            'benchmarks': result.get('benchmarks'),
            'bottleneck_warning': result.get('bottleneck_warning'),
            'fallback_used': fallback_used,
            'cached': False
        })

    except Exception as e:
        app.logger.error(f"Benchmark simulator critical error: {e}")
        return jsonify({
            'status': 'success', 
            'benchmarks': [{"game": "Service Busy", "1080p": "-", "1440p": "-", "4k": "-"}],
            'bottleneck_warning': "Local service busy."
        })



@app.route('/api/compare-builds', methods=['POST'])
@login_required
def api_compare_builds():
    try:
        data = request.json
        build_ids = data.get('build_ids', [])
        if not build_ids:
            return jsonify({'status': 'error', 'message': 'No builds selected'}), 400
            
        resolved_builds = []
        col_map = {
            'cpu_id': 'cpu', 'gpu_id': 'gpu', 'motherboard_id': 'motherboard',
            'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
            'case_id': 'case', 'cooler_id': 'cooler'
        }
        
        for bid in build_ids:
            build = db.saved_builds.find_one({'_id': ObjectId(bid)})
            if not build: continue
            
            bn = build.get('name')
            display_name = str(bn).strip() if bn and str(bn).strip() else "Custom Rig"
            
            b_data = {
                'id': str(build['_id']),
                'name': display_name,
                'date': build.get('created_at', datetime.now(timezone.utc)).strftime('%Y-%m-%d'),
            }
            
            # Resolve components
            for key, cat in col_map.items():
                cid = build.get(key)
                display_key = key.replace('_id', '').upper()
                if cid and cid != "None Selected":
                    item = db.components.find_one({'_id': ObjectId(cid)})
                    b_data[display_key] = item.get('name', 'Unknown') if item else 'Unknown'
                else:
                    b_data[display_key] = 'None'
            
            # Add analysis data
            p_res = run_power_analysis(build)
            v_res = run_validation_logic(build)
            
            b_data['compatibility'] = v_res.get('status')
            b_data['power_status'] = p_res.get('adequacy_status')
            b_data['power_wattage'] = f"{p_res.get('total_base_wattage', 0)}W / {p_res.get('selected_psu_wattage', 0)}W"
            b_data['upgrade_readiness'] = 'High' if p_res.get('adequacy_status') == 'Safe' else 'Moderate'
            
            # Pricing estimate (if available) - purely heuristic/dummy for now
            b_data['estimated_cost'] = "Calculated at Order" 
            
            resolved_builds.append(b_data)
            
        return jsonify({'status': 'success', 'comparison': resolved_builds})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/build-difficulty/<build_id>')
@login_required
def api_get_build_difficulty(build_id):
    try:
        user_id = session.get('user_id')
        user_ids = [user_id]
        try:
            user_ids.append(ObjectId(user_id))
        except:
            pass
            
        build = db.saved_builds.find_one({
            '_id': ObjectId(build_id), 
            'user_id': {'$in': user_ids}
        })
        
        if not build:
            return jsonify({'status': 'error', 'message': 'Build not found'}), 404
            
        db_name = build.get('name')
        display_name = str(db_name).strip() if db_name and str(db_name).strip() else "Custom Rig"
        
        # Calculate difficulty data
        diff_data = calculate_build_difficulty(build)
        
        return jsonify({
            'status': 'success',
            'name': display_name,
            'difficulty': diff_data['level'],
            'explanation': diff_data['explanation']
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/build-insights/<build_id>')
@login_required
def api_get_build_insights(build_id):
    try:
        user_id = session.get('user_id')
        user_ids = [user_id]
        try: 
            from bson.objectid import ObjectId
            user_ids.append(ObjectId(user_id))
        except: 
            pass
            
        app.logger.info(f"Fetching insights for build {build_id} (User: {user_id})")
        
        try:
            query = {'_id': ObjectId(build_id), 'user_id': {'$in': user_ids}}
            build = db.saved_builds.find_one(query)
        except Exception as id_err:
            app.logger.error(f"Invalid build ID format: {build_id} - {id_err}")
            return jsonify({'status': 'error', 'message': 'Invalid build ID format'}), 400
            
        if not build:
            app.logger.warning(f"Build {build_id} not found or access denied for user {user_id}")
            return jsonify({'status': 'error', 'message': 'Build not found or access denied'}), 404
            
        data = get_build_insights_data(build)
        if data.get('status') == 'error':
            return jsonify(data), 500
            
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Unexpected error in api_get_build_insights: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/vault-data/<build_id>')
@login_required
def api_get_vault_data(build_id):
    try:
        user_id = session.get('user_id')
        user_ids = [user_id]
        try:
            from bson.objectid import ObjectId
            user_ids.append(ObjectId(user_id))
        except:
            pass
            
        app.logger.info(f"Fetching vault data for build {build_id} (User: {user_id})")

        try:
            query = {'_id': ObjectId(build_id), 'user_id': {'$in': user_ids}}
            build = db.saved_builds.find_one(query)
        except Exception as id_err:
            app.logger.error(f"Invalid build ID format (Vault): {build_id} - {id_err}")
            return jsonify({'status': 'error', 'message': 'Invalid build ID format'}), 400
            
        if not build:
            app.logger.warning(f"Vault Build {build_id} not found or access denied for user {user_id}")
            return jsonify({'status': 'error', 'message': 'Build not found or access denied'}), 404

        # Resolve component names and warranty logic
        components = {}
        # Dictionary for price estimation mapping
        price_cat_map = {
            'cpu': 'cpus', 'gpu': 'gpus', 'motherboard': 'motherboards',
            'ram': 'ram', 'storage': 'storage', 'psu': 'psu',
            'case': 'cases', 'cooler': 'coolers',
            'keyboard': 'keyboards', 'mouse': 'mice', 'headset': 'headsets', 'webcam': 'webcams',
            'fans': 'fans', 'monitor': 'monitors', 'os': 'os'
        }
        
        warranty_terms = {
            'cpu': 3, 'gpu': 3, 'motherboard': 3, 'ram': 10,
            'storage': 5, 'psu': 7, 'case': 2, 'cooler': 3,
            'keyboard': 2, 'mouse': 2, 'headset': 2, 'webcam': 2, 'fans': 1, 'monitor': 3, 'os': 0
        }

        col_map = {
            'cpu_id': 'cpu', 'gpu_id': 'gpu', 'motherboard_id': 'motherboard',
            'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
            'case_id': 'case', 'cooler_id': 'cooler',
            'keyboard_id': 'keyboard', 'mouse_id': 'mouse', 'headset_id': 'headset', 'webcam_id': 'webcam',
            'fans_id': 'fans', 'monitor_id': 'monitor', 'os_id': 'os',
            'thermal_paste_id': 'thermal_paste', 'wifi_id': 'wifi_adapters',
            'speakers_id': 'speakers', 'microphone_id': 'microphones',
            'ups_id': 'ups', 'tool_id': 'tools'
        }

        total_original_cost = 0
        purchase_date = build.get('created_at', datetime.now(timezone.utc))
        years_owned = (datetime.now(timezone.utc) - purchase_date).days / 365.25
        
        for key, cat in col_map.items():
            cid = build.get(key)
            if cid:
                comp = get_component_by_id(cid)
                if comp:
                    name = comp.get('name', 'Unknown')
                    # Use the consolidated price helper for accuracy
                    price = get_comp_price_usd(comp, key, cat)
                    total_original_cost += price
                    
                    # Warranty Calc
                    term = warranty_terms.get(cat, 3)
                    expiry = purchase_date + timedelta(days=term * 365.25)
                    is_active = datetime.now(timezone.utc) < expiry
                    
                    # Depreciation Calc
                    dep_rate = 0.25 if cat in ['gpu', 'cpu'] else 0.15
                    current_value = price * ((1 - dep_rate) ** max(years_owned, 0))

                    components[cat] = {
                        'name': name,
                        'original_price': price,
                        'current_value': round(current_value, 2),
                        'warranty_expiry': expiry.strftime('%Y-%m-%d'),
                        'warranty_status': 'Active' if is_active else 'Expired',
                        'warranty_percent': max(0, min(100, (expiry - datetime.now(timezone.utc)).days / (term * 365.25) * 100)) if is_active else 0
                    }

        # Overall Rig Value
        current_total_value = sum(c['current_value'] for c in components.values())
        
        user_currency = session.get('currency', 'USD')
        rate = EXCHANGE_RATES.get(user_currency, 1.0)
        symbol = CURRENCY_SYMBOLS.get(user_currency, '$')

        return jsonify({
            'status': 'success',
            'components_warranty': components,
            'total_cost': total_original_cost,
            'current_value': round(current_total_value, 2),
            'purchase_date': purchase_date.strftime('%Y-%m-%d'),
            'currency': user_currency,
            'currency_symbol': symbol,
            'exchange_rate': rate
        })
    except Exception as e:
        app.logger.error(f"Vault Data Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/predict-resale/<build_id>')
@login_required
def api_predict_resale(build_id):
    prediction_data = None
    try:
        if db is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
            
        user_id = session.get('user_id')
        user_ids = [user_id]
        try:
            user_ids.append(ObjectId(user_id))
        except:
            pass
            
        build = db.saved_builds.find_one({
            '_id': ObjectId(build_id), 
            'user_id': {'$in': user_ids}
        })
        
        if not build:
            return jsonify({'status': 'error', 'message': 'Build not found'}), 404

        col_map = {
            'cpu_id': 'cpu', 'gpu_id': 'gpu', 'motherboard_id': 'motherboard',
            'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
            'case_id': 'case', 'cooler_id': 'cooler',
            'keyboard_id': 'keyboard', 'mouse_id': 'mouse',
            'headset_id': 'headset', 'webcam_id': 'webcam',
            'fans_id': 'fans', 'monitor_id': 'monitor', 'os_id': 'os',
            'thermal_paste_id': 'thermal_paste', 'wifi_id': 'wifi_adapters',
            'speakers_id': 'speakers', 'microphone_id': 'microphones',
            'ups_id': 'ups', 'tool_id': 'tools'
        }
        
        component_data = []
        for key, cat in col_map.items():
            cid = build.get(key)
            if cid:
                item = get_component_by_id(cid)
                if item:
                    component_data.append({
                        'category': key.replace('_id', '').upper(),
                        'name': item.get('name'),
                        'status': item.get('status', 'Active')
                    })

        if not component_data:
            return jsonify({'status': 'error', 'message': 'No components selected to predict value.'}), 400

        # AI Prompt for Resale Prediction with Schema
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
            "You are the RigMaster Pro AI, a world-class hardware market analyst. "
            "Analyze the provided PC components with extreme precision. "
            "For each component, provide a realistic current Used Market Price (eBay/Reddit/Marketplace) in USD. "
            "Never use 'N/A' or '$0'. Even for e-waste, use a symbolic value like '$4.50'. "
            "Provide a total system value that captures the synergy of the build. "
            "Provide elite, aggressive market advice on selling strategies, cleaning, and descriptions. "
            "Include your AI reasoning for the valuation in the market_advice."
            "CRITICAL: If a component is very new (e.g. RTX 4090/4080 super), ensure its resale is close to MSRP but discounted (85-90%). If it is old (e.g. GTX 1080), account for heavy depreciation."
            f"Respond ONLY in JSON with this exact schema: {json.dumps(schema)}"
        )
        user_content = "Build Components:\n" + "\n".join([f"- {c['category']}: {c['name']} (Status: {c['status']})" for c in component_data])

        # 1. Check Cache (v11 for refined accuracy & currency fix)
        cache_key = f"resale_v11_{build_id}"
        cached = db.ai_cache.find_one({'cache_key': cache_key})
        if cached:
            return jsonify({'status': 'success', 'prediction': cached.get('prediction'), 'cached': True})

        # 2. Advanced Heuristic Engine (Local Fallback)
        def get_heuristic_prediction(comps):
            total_val = 0
            results = []
            for c in comps:
                name = (c.get('name') or 'Unknown Component').upper()
                val = 15.0 # Minimum symbolic floor
                
                # Intelligent Hardware Tiers - Realistic Used Market (USD)
                # GPUs
                if '4090' in name: val = 1550
                elif '4080' in name: val = 840
                elif '7900 XTX' in name: val = 720
                elif '4070 TI' in name: val = 620
                elif '7900 XT' in name: val = 580
                elif '4070 SUPER' in name: val = 510
                elif '4070' in name or '7800 XT' in name: val = 440
                elif '3090 TI' in name: val = 780
                elif '3090' in name: val = 680
                elif '3080 TI' in name: val = 480
                elif '3080' in name: val = 390
                elif '4060 TI' in name: val = 330
                elif '4060' in name: val = 240
                elif '3070' in name or '3070 TI' in name: val = 280
                elif '3060 TI' in name: val = 220
                elif '3060' in name: val = 200
                elif '6800 XT' in name: val = 350
                elif '6700 XT' in name: val = 230
                
                # CPUs
                elif '7950X3D' in name: val = 480
                elif '7800X3D' in name: val = 340
                elif '14900' in name or '13900' in name: val = 420
                elif '14700' in name or '13700' in name: val = 290
                elif 'RYZEN 9' in name: val = 310
                elif 'RYZEN 7' in name: val = 180
                elif 'CORE I9' in name: val = 330
                elif 'CORE I7' in name: val = 210
                elif 'RYZEN 5' in name: val = 110
                elif 'CORE I5' in name: val = 140
                elif 'RYZEN 3' in name: val = 55
                elif 'CORE I3' in name: val = 75
                
                # Legacy / Low End
                elif '1080 TI' in name: val = 160
                elif '1070' in name or '1660' in name: val = 95
                elif '880G' in name or 'GXH' in name: val = 25 
                elif '7850K' in name or 'A10-' in name: val = 18
                elif 'AD2U' in name or 'DDR2' in name: val = 3
                
                # Others
                elif 'XPG' in name or 'CRUISER' in name or 'RAM' in name:
                    if '64GB' in name: val = 120
                    elif '32GB' in name: val = 75
                    elif '16GB' in name: val = 35
                    else: val = 45
                elif 'SSD' in name or 'ADATA' in name or 'STORAGE' in name:
                    if '4TB' in name: val = 210
                    elif '2TB' in name: val = 110
                    elif '1TB' in name: val = 60
                    else: val = 25
                elif 'PSU' in name:
                    if '1000W' in name: val = 140
                    elif '850W' in name: val = 110
                    elif '750W' in name: val = 85
                    else: val = 55
                elif '360MM' in name or 'LIQUID' in name: val = 65
                elif 'ALPINE' in name or 'COOLER' in name: val = 12
                
                total_val += val
                results.append({
                    "category": c.get('category', 'Hardware'),
                    "name": c.get('name', 'Unknown Part'),
                    "status": c.get('status', 'Active'),
                    "estimated_resale": format_price(val)
                })
            
            # Add System synergy premium (10% for assembly/testing)
            final_total = total_val * 1.10
            
            return {
                "total_system_value": format_price(final_total),
                "market_advice": "### System Appraisal: RigMaster Expert Engine\nLive AI appraisal nodes are currently under heavy load. This valuation was generated using our **Local Market Heuristic Engine v2.5**, which analyzes components against verified hardware price index tiers (2024-2025).\n\n*   **Selling Strategy:** Focus on listing this as a 'Complete Ready-to-Work/Play' system for local cash buyers.\n*   **Platform Tip:** Facebook Marketplace or local enthusiast forums will yield the best margins for this specific hardware tier.",
                "components": results,
                "provider": "RigMaster Heuristic 2.5"
            }


        # Use unified AI Engine for resale prediction
        ai_engine = get_ai_engine()
        p_data = ai_engine.get_resale_prediction(component_data)
        
        if p_data and p_data.get('total_system_value') and p_data.get('total_system_value') != 'N/A':
            # Always attempt to clean and format AI results for consistency
            user_currency = session.get('currency', 'USD')
            
            # Helper to clean and re-format value
            def safe_format_ai_price(val_str):
                try:
                    # Clean the AI output ($1,500 USD -> 1500)
                    numeric_v = float(re.sub(r'[^0-9.]', '', val_str))
                    # format_price handles the actual conversion to session currency
                    return format_price(numeric_v)
                except:
                    return val_str # Fallback to original AI string
            
            # Re-format total
            p_data['total_system_value'] = safe_format_ai_price(p_data['total_system_value'])
                
            # Re-format individual components
            for c in p_data.get('components', []):
                c['estimated_resale'] = safe_format_ai_price(c.get('estimated_resale', '0.00'))

            prediction_data = p_data
            prediction_data['provider'] = f'RigMaster AI ({p_data.get("provider", "Nexus")})'
            
            # Log AI success
            log_ai_request('resale_predictor', p_data.get('provider_used', 'unknown'), cached=False)

        # FINAL FAILSAFE: Always work
        if not prediction_data:
            prediction_data = get_heuristic_prediction(component_data)
            # Log AI failure/fallback
            log_ai_request('resale_predictor', 'heuristic_fallback', cached=False)

        # Verbose Logging
        with open('resale_final_log.json', 'w') as f:
            json.dump(prediction_data, f, indent=2)

        # Save to cache
        try:
            db.ai_cache.update_one({'cache_key': cache_key}, {'$set': {'cache_key': cache_key, 'prediction': prediction_data, 'created_at': datetime.now(timezone.utc)}}, upsert=True)
        except: pass

        return jsonify({'status': 'success', 'prediction': prediction_data, 'cached': False})

    except Exception as e:
        app.logger.error(f"Resale Prediction Error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal error generating prediction.'}), 500


@app.route('/export-build/<build_id>')
@login_required
def export_build(build_id):
    try:
        if db is None:
            flash("Database connection error")
            return redirect(url_for('saved_builds'))

        build = db.saved_builds.find_one({
            '_id': ObjectId(build_id),
            'user_id': session.get('user_id')
        })

        if not build:
            flash("Build not found or access denied")
            return redirect(url_for('saved_builds'))

        # Resolve components
        col_map = {
            'cpu_id': 'cpu', 'gpu_id': 'gpu', 'motherboard_id': 'motherboard',
            'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
            'case_id': 'case', 'cooler_id': 'cooler', 'monitor_id': 'monitor',
            'os_id': 'os', 'fans_id': 'fans', 'keyboard_id': 'keyboard',
            'mouse_id': 'mouse', 'headset_id': 'headset', 'webcam_id': 'webcam',
            'peripherals_id': 'peripherals', 'thermal_paste_id': 'thermal_paste',
            'wifi_id': 'wifi_adapters', 'speakers_id': 'speakers',
            'microphone_id': 'microphones', 'ups_id': 'ups', 'tool_id': 'tools'
        }
        
        components = {}
        for key, cat in col_map.items():
            comp_id = build.get(key)
            if comp_id:
                try:
                    comp = db.components.find_one({'_id': ObjectId(comp_id)})
                    if comp:
                        components[key.replace('_id', '').upper()] = comp.get('name', 'Unknown')
                    else:
                        components[key.replace('_id', '').upper()] = 'Not Selected'
                except:
                     components[key.replace('_id', '').upper()] = 'Error Loading'
            else:
                components[key.replace('_id', '').upper()] = 'Not Selected'

        # Analysis
        power_res = run_power_analysis({
            'cpu_id': build.get('cpu_id'),
            'gpu_id': build.get('gpu_id'),
            'ram_id': build.get('ram_id'),
            'storage_id': build.get('storage_id'),
            'psu_id': build.get('psu_id')
        })
        
        valid_res = run_validation_logic({
            'cpu_id': build.get('cpu_id'),
            'motherboard_id': build.get('motherboard_id'),
            'ram_id': build.get('ram_id')
        })

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("helvetica", 'B', 24)
        pdf.set_text_color(63, 81, 181) # RigMaster Primary approx
        pdf.cell(0, 20, "RigMaster AI - Build Report", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(5)
        
        # Section 1: Overview
        pdf.set_font("helvetica", 'B', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "1. Build Overview", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", '', 12)
        
        # Display Build Name prominently
        build_name = build.get('name', 'Custom Rig')
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(40, 8, "Build Name:", border=0)
        pdf.set_font("helvetica", '', 12)
        pdf.cell(0, 8, build_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.cell(0, 8, f"Build ID: {build_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, f"Date Created: {build.get('created_at', datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 8, f"Owner: {session.get('username')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)

        # Section 2: Components
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "2. Selected Components", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", '', 12)
        for cat, name in components.items():
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(50, 8, f"{cat}:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("helvetica", '', 12)
            # Use explicit width (0 means up to right margin)
            pdf.multi_cell(0, 8, f"{name}", border=0, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

        # Section 3: System Analysis
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "3. System Analysis", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", '', 12)
        
        # Compatibility
        comp_status = valid_res.get('status', 'Unknown')
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(50, 8, "Compatibility:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
        if comp_status == "Compatible":
            pdf.set_text_color(16, 185, 129) # Success
        else:
            pdf.set_text_color(248, 113, 113) # Error/Warning
        pdf.multi_cell(0, 8, comp_status, border=0, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        
        # Power
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(50, 8, "Power Adequacy:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
        p_status = power_res.get('adequacy_status', 'Unknown')
        if p_status == "Safe":
            pdf.set_text_color(16, 185, 129)
        else:
            pdf.set_text_color(248, 113, 113)
        pdf.multi_cell(0, 8, p_status, border=0, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font("helvetica", '', 12)
        pdf.cell(50, 8, "Power Usage:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.multi_cell(0, 8, f"{power_res.get('total_base_wattage', 0)}W / {power_res.get('selected_psu_wattage', 0)}W", border=0, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(50, 8, "Upgrade Readiness:", border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("helvetica", '', 12)
        pdf.multi_cell(0, 8, "High" if p_status == "Safe" else "Moderate", border=0, align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

        # Section 4: Assembly Guidance & Safety
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "4. Assembly Guidance & Safety", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        insights_data = get_build_insights_data(build)
        if insights_data.get('status') == 'success':
            # Time Estimate
            time_est = insights_data.get('time_estimator', {})
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(50, 8, "Estimated Build Time:", border=0)
            pdf.set_font("helvetica", '', 12)
            pdf.cell(0, 8, f"{time_est.get('total_minutes', 0)} minutes", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Safety Warnings
            warnings = insights_data.get('safety_warnings', [])
            if warnings:
                pdf.set_font("helvetica", 'B', 12)
                pdf.cell(0, 10, "Safety & Handling:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("helvetica", 'I', 10)
                pdf.set_text_color(180, 0, 0) # Dark Red for warnings
                for w in warnings:
                    pdf.multi_cell(0, 6, f"* {w['title']}: {w['text']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_text_color(0, 0, 0) # Reset to black
                pdf.ln(2)

            # Assembly Steps
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, "Component-Specific Instructions:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("helvetica", '', 11)
            for step in insights_data.get('assembly_steps', []):
                step_text = f"Step {step['step']} - {step['title']}: {step['text']}"
                # If step is float like 2.5, it represents a component specific insertion
                pdf.multi_cell(0, 7, step_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1)
            
            # Checklist
            if pdf.get_y() > 240: # Check if near bottom of page
                pdf.add_page()
                
            pdf.ln(3)
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 8, "Post-Assembly Setup Checklist:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("helvetica", '', 11)
            for item in insights_data.get('setup_checklist', []):
                pdf.cell(0, 7, f" [ ] [{item['category']}] {item['item']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.set_font("helvetica", 'I', 12)
            pdf.cell(0, 8, "Dynamic assembly guidance unavailable for this build.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Output to bytes
        pdf_output = pdf.output()
        buffer = io.BytesIO(pdf_output)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"RigMaster_Build_{build_id}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = {
        'users': db.users.count_documents({}),
        'builds': db.saved_builds.count_documents({}),
        'cpus': db.components.count_documents({'category': 'cpu'}),
        'gpus': db.components.count_documents({'category': 'gpu'}),
        'motherboards': db.components.count_documents({'category': 'motherboard'}),
        'ram': db.components.count_documents({'category': 'ram'}),
        'storage': db.components.count_documents({'category': 'storage'}),
        'psu': db.components.count_documents({'category': 'psu'}),
        'cases': db.components.count_documents({'category': 'case'}),
        'coolers': db.components.count_documents({'category': 'cooler'}),
        'fans': db.components.count_documents({'category': 'fans'}),
        'os': db.components.count_documents({'category': 'os'}),
        'monitors': db.components.count_documents({'category': 'monitor'}),
        'peripherals': db.components.count_documents({'category': 'peripherals'}),
        'thermal_paste': db.components.count_documents({'category': 'thermal_paste'}),
        'wifi': db.components.count_documents({'category': 'wifi_adapters'}),
        'speakers': db.components.count_documents({'category': 'speakers'}),
        'microphones': db.components.count_documents({'category': 'microphones'}),
        'ups': db.components.count_documents({'category': 'ups'}),
        'tools': db.components.count_documents({'category': 'tools'})
    }
    stats['total_components'] = sum([
        stats['cpus'], stats['gpus'], stats['motherboards'], stats['ram'], 
        stats['storage'], stats['psu'], stats['cases'], stats['coolers'],
        stats['fans'], stats['os'], stats['monitors'], stats['peripherals'],
        stats['thermal_paste'], stats['wifi'], stats['speakers'], stats['microphones'],
        stats['ups'], stats['tools']
    ])
    
    # AI stats
    try:
        ai_stats = {
            'total_requests': db.ai_cache.count_documents({}),
            'cached_hits': db.ai_cache.count_documents({'cached': True})
        }
    except:
        ai_stats = {'total_requests': 0, 'cached_hits': 0}
    
    # Recent activity
    try:
        recent_users = list(db.users.find({}, {'password': 0}).sort('_id', -1).limit(5))
        for user in recent_users:
            user['_id'] = str(user['_id'])
    except:
        recent_users = []
    
    try:
        recent_builds = list(db.saved_builds.find().sort('_id', -1).limit(5))
        for build in recent_builds:
            build['_id'] = str(build['_id'])
    except:
        recent_builds = []
    
    # Fetch settings
    settings = {
        'maintenance_mode': get_site_setting('maintenance_mode', False),
        'global_announcement': get_site_setting('global_announcement', ''),
        'preferred_ai_provider': get_preferred_ai_provider()
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         ai_stats=ai_stats,
                         recent_users=recent_users,
                         recent_builds=recent_builds,
                         **settings)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = list(db.users.find({}, {'password': 0}).sort('created_at', -1))
    for u in users:
        u['_id'] = str(u['_id'])
    return render_template('admin/users.html', users=users)

@app.route('/admin/components')
@admin_required
def admin_components():
    return render_template('admin/components.html')



@app.route('/api/admin/clear-cache', methods=['POST'])
@admin_required
def api_clear_cache():
    """Clear AI and shopping cache."""
    try:
        db = get_db()
        if db is not None:
            if 'shopping_cache' in db.list_collection_names():
                db.shopping_cache.delete_many({})
            if 'ai_cache' in db.list_collection_names():
                db.ai_cache.delete_many({})
            app.logger.info(f"Admin {session.get('username')} cleared all caches")
            return jsonify({'status': 'success', 'message': 'Caches cleared successfully'})
        return jsonify({'status': 'error', 'message': 'Database disconnected'}), 500
    except Exception as e:
        app.logger.error(f"Clear cache error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/ai-engine-console')
@admin_required
def admin_ai_engine_console():
    """View AI usage analytics and management console"""
    try:
        # AI cache stats
        total_requests = db.ai_cache.count_documents({}) if 'ai_cache' in db.list_collection_names() else 0
        cached_hits = db.ai_cache.count_documents({'cached': True}) if 'ai_cache' in db.list_collection_names() else 0
        
        ai_stats = {
            'total_requests': total_requests,
            'cached_hits': cached_hits,
            'cost_saved': round(cached_hits * 0.005, 3) # Roughly $0.005 per request saved
        }
        
        # Recent AI requests
        recent_requests = []
        if 'ai_cache' in db.list_collection_names():
            recent_requests = list(db.ai_cache.find().sort('_id', -1).limit(20))
            for req in recent_requests:
                req['_id'] = str(req['_id'])

        # Provider distribution
        provider_stats = {}
        if 'ai_cache' in db.list_collection_names():
            pipeline = [
                {"$group": {"_id": "$provider", "count": {"$sum": 1}}}
            ]
            results = list(db.ai_cache.aggregate(pipeline))
            for res in results:
                provider_stats[res['_id'] or 'Unknown'] = res['count']

        # Advanced Analytics: Usage over time (last 7 days)
        usage_over_time = []
        if 'ai_cache' in db.list_collection_names():
            today = datetime.now(timezone.utc)
            for i in range(6, -1, -1):
                date = today - timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                start = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
                end = start + timedelta(days=1)
                
                count = db.ai_cache.count_documents({
                    'created_at': {'$gte': start, '$lt': end}
                })
                usage_over_time.append({'date': date_str, 'count': count})

        # Latency (simulated or if available)
        avg_latency = 1.4 # Mocked for now as we don't store it yet
        
        # Real-time analytics additions
        analytics = {
            'usage_over_time': usage_over_time,
            'avg_latency': avg_latency,
            'efficiency_score': round((ai_stats['cached_hits'] / max(ai_stats['total_requests'], 1)) * 100, 1)
        }

        # Get system health for provider statuses
        health = {
            'ai_providers': {}
        }
        try:
            from ai_engine import get_ai_engine
            ai_engine = get_ai_engine()
            provider_health = ai_engine.get_provider_health()
            health['ai_providers'] = {p: h['status'] for p, h in provider_health.items()}
        except Exception as e:
            app.logger.error(f"Error getting AI health: {e}")
            pass

        custom_api_keys = get_site_setting('api_keys', {})
        preferred_provider = get_preferred_ai_provider()
        
        # Additional settings for the console
        smtp_settings = {
            'server': get_site_setting('SMTP_SERVER', os.getenv('SMTP_SERVER', '')),
            'port': get_site_setting('SMTP_PORT', os.getenv('SMTP_PORT', '587')),
            'email': get_site_setting('SMTP_EMAIL', os.getenv('SMTP_EMAIL', '')),
            'password': get_site_setting('SMTP_PASSWORD', os.getenv('SMTP_PASSWORD', ''))
        }

        return render_template('admin/ai_engine_console.html', 
                             stats=ai_stats,
                             recent_requests=recent_requests,
                             provider_stats=provider_stats,
                             health=health,
                             custom_keys=custom_api_keys,
                             smtp_settings=smtp_settings,
                             preferred_ai_provider=preferred_provider,
                             analytics=analytics)
    except Exception as e:
        app.logger.error(f"AI engine console error: {e}")
        return f"Error: {e}", 500

@app.route('/api/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings_api():
    """Generic endpoint to get or update any site-wide setting in the settings collection."""
    if request.method == 'GET':
        try:
            settings = list(db.settings.find())
            return jsonify({s['key']: s['value'] for s in settings})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        for key, value in data.items():
            # Special handling for api_keys to merge instead of overwrite if needed
            if key == 'api_keys' and isinstance(value, dict):
                current = get_site_setting('api_keys', {})
                current.update(value)
                db.settings.update_one(
                    {'key': 'api_keys'},
                    {'$set': {'value': current, 'updated_at': datetime.now(timezone.utc)}},
                    upsert=True
                )
            else:
                db.settings.update_one(
                    {'key': key},
                    {'$set': {'value': value, 'updated_at': datetime.now(timezone.utc)}},
                    upsert=True
                )
        
        app.logger.info(f"Admin {session.get('username')} updated settings: {list(data.keys())}")
        return jsonify({'status': 'success', 'message': 'Settings updated successfully'})
    except Exception as e:
        app.logger.error(f"Settings update error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/admin/settings/delete', methods=['POST'])
@admin_required
def admin_delete_setting():
    """Delete a setting from the database to allow fallback or full removal."""
    try:
        data = request.get_json()
        key = data.get('key')
        nested_key = data.get('nested_key') # For api_keys dictionary
        
        if not key:
            return jsonify({'status': 'error', 'message': 'Setting key required'}), 400
            
        if nested_key and key == 'api_keys':
            # Remove from the nested dictionary
            db.settings.update_one(
                {'key': 'api_keys'},
                {'$unset': {f'value.{nested_key}': ""}}
            )
        else:
            # Delete the entire setting row
            db.settings.delete_one({'key': key})
            
        return jsonify({'status': 'success', 'message': f'Setting {key} deleted'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/admin/system-health')
@admin_required
def admin_system_health():
    """Check system health status"""
    try:
        health = {
            'database': 'Connected' if db is not None else 'Disconnected',
            'collections': db.list_collection_names() if db is not None else [],
            'ai_providers': {}
        }
        
        # Check AI providers
        try:
            from ai_engine import get_ai_engine
            ai_engine = get_ai_engine()
            provider_health = ai_engine.get_provider_health()
            health['ai_providers'] = {p: h['status'] for p, h in provider_health.items()}
        except Exception as e:
            health['ai_providers'] = {'error': f'AI engine not available: {str(e)}'}
            
        # Check internal services
        auth_status = 'Operational' if db is not None else 'Down'
        builder_status = 'Operational' if db is not None and db.components.count_documents({}) > 0 else 'Degraded'
        ai_services_running = any('Available' in str(v) or 'Running' in str(v) for v in health['ai_providers'].values())
        
        health['services'] = {
            'authentication': 'Operational' if db is not None else 'Down',
            'builder': builder_status,
            'ai_recommendations': 'Operational' if ai_services_running else 'Degraded',
            'performance': 'Operational' if db is not None else 'Down',
            'export': 'Operational'
        }
        
        # Database stats
        db_stats = {}
        if db is not None:
            try:
                db_stats = db.command("dbStats")
            except:
                pass

        # Create snapshot
        overall_status = 'Healthy' if auth_status == 'Operational' and ai_services_running else 'Degraded'
        
        # Save snapshot for history (optional background logging)
        try:
            db.system_health_logs.insert_one({
                'timestamp': datetime.now(timezone.utc),
                'overall_status': overall_status,
                'database': {'status': health['database'], 'storage_size_mb': round(db_stats.get('storageSize', 0) / 1024 / 1024, 2)},
                'collections': health['collections'],
                'ai_providers': health['ai_providers'],
                'services': health['services'],
                'db_stats': db_stats
            })
        except:
            pass

        return render_template('admin/system_health.html', 
                             health={
                                 'database': health['database'],
                                 'collections': health['collections'],
                                 'ai_providers': health['ai_providers'],
                                 'services': health['services'],
                                 'overall_status': overall_status
                             }, 
                             db_stats=db_stats)
    except Exception as e:
        app.logger.error(f"System health error: {e}")
        return f"Error: {e}", 500

# Export routes
@app.route('/api/admin/system-health/logs', methods=['GET'])
@admin_required
def api_get_health_logs():
    """Fetch structured historical health data from MongoDB"""
    try:
        # Fetch last 50 health snapshots
        logs = list(db.system_health_logs.find().sort('timestamp', -1).limit(50))
        for log in logs:
            log['_id'] = str(log['_id'])
            if 'timestamp' in log and log['timestamp']:
                # Convert datetime to ISO string for JSON transport
                log['timestamp'] = log['timestamp'].isoformat() if hasattr(log['timestamp'], 'isoformat') else str(log['timestamp'])
        
        return jsonify({
            'status': 'success',
            'count': len(logs),
            'logs': logs
        })
    except Exception as e:
        app.logger.error(f"Error fetching health logs: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/export/users')
@admin_required
def admin_export_users():
    """Export all users as JSON file"""
    try:
        users = list(db.users.find({}, {'password': 0}))  # Exclude passwords
        for user in users:
            user['_id'] = str(user['_id'])
            # Convert datetime objects to strings
            if 'created_at' in user and user['created_at']:
                user['created_at'] = user['created_at'].isoformat() if hasattr(user['created_at'], 'isoformat') else str(user['created_at'])
        
        export_data = {
            'status': 'success',
            'count': len(users),
            'users': users,
            'exported_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Create response with download headers
        import json
        response = app.response_class(
            response=json.dumps(export_data, indent=2),
            status=200,
            mimetype='application/json'
        )
        response.headers['Content-Disposition'] = f'attachment; filename=users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        return response
    except Exception as e:
        app.logger.error(f"Export users error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/export/builds')
@admin_required
def admin_export_builds():
    """Export all builds as JSON file"""
    try:
        builds = list(db.saved_builds.find({}))
        for build in builds:
            build['_id'] = str(build['_id'])
            # Convert ObjectId fields to strings
            if 'user_id' in build and build['user_id']:
                build['user_id'] = str(build['user_id'])
            # Convert datetime objects to strings
            if 'created_at' in build and build['created_at']:
                build['created_at'] = build['created_at'].isoformat() if hasattr(build['created_at'], 'isoformat') else str(build['created_at'])
        
        export_data = {
            'status': 'success',
            'count': len(builds),
            'builds': builds,
            'exported_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Create response with download headers
        import json
        response = app.response_class(
            response=json.dumps(export_data, indent=2),
            status=200,
            mimetype='application/json'
        )
        response.headers['Content-Disposition'] = f'attachment; filename=builds_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        return response
    except Exception as e:
        app.logger.error(f"Export builds error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API for managing users
@app.route('/api/admin/users/<user_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_user_status(user_id):
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    new_status = not user.get('is_active', True)
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'is_active': new_status}})
    app.logger.info(f"Admin {session.get('username')} toggled user {user_id} status to {new_status}")
    return jsonify({'status': 'success', 'is_active': new_status})


@app.route('/api/admin/users/create', methods=['POST'])
@admin_required
def admin_create_user():
    """Create a new user (usually an admin) from the admin dashboard"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        is_admin = data.get('is_admin', False)

        if not username or not email or not password:
            return jsonify({'status': 'error', 'message': 'All fields are required'}), 400
        
        # Check if user already exists
        if db.users.find_one({'$or': [{'email': email}, {'username': username}]}):
            return jsonify({'status': 'error', 'message': 'Username or email already exists'}), 400
        
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(password)
        db.users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password,
            'is_admin': is_admin,
            'is_active': True,
            'created_at': datetime.now(timezone.utc)
        })
        
        app.logger.info(f"Admin {session.get('username')} created new {'admin' if is_admin else 'user'}: {username}")
        return jsonify({'status': 'success', 'message': f"Account created for {username}"})
    except Exception as e:
        app.logger.error(f"Error creating user: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500




@app.route('/api/admin/users/<user_id>/make-admin', methods=['POST'])
@admin_required
def admin_make_user_admin(user_id):
    """Promote a user to administrator status"""
    try:
        db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'is_admin': True}})
        app.logger.info(f"Admin {session.get('username')} promoted user {user_id} to admin")
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/users/<user_id>/delete', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id):
    """Delete a user permanently"""
    try:
        # Prevent deleting yourself
        current_admin_id = session.get('user_id')
        if str(user_id) == str(current_admin_id):
            return jsonify({'status': 'error', 'message': "You cannot delete your own account"}), 400

        db.users.delete_one({'_id': ObjectId(user_id)})
        # Also clean up their builds? Keep for now but we could delete them
        # db.saved_builds.delete_many({'user_id': user_id})
        
        app.logger.info(f"Admin {session.get('username')} deleted user {user_id}")
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/builds/<build_id>', methods=['DELETE'])
@admin_required
def admin_delete_build(build_id):
    """Delete a build permanently"""
    try:
        db.saved_builds.delete_one({'_id': ObjectId(build_id)})
        app.logger.info(f"Admin {session.get('username')} deleted build {build_id}")
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# API for components
@app.route('/api/admin/components/<category>', methods=['GET'])
@admin_required
def admin_get_components(category):
    cat_map = {
        'cpus': 'cpu', 'gpus': 'gpu', 'motherboards': 'motherboard',
        'ram': 'ram', 'storage': 'storage', 'psu': 'psu',
        'cases': 'case', 'coolers': 'cooler', 'fans': 'fans',
        'monitors': 'monitor', 'os': 'os', 'peripherals': 'peripherals',
        'keyboards': 'peripherals', 'mice': 'peripherals',
        'headsets': 'peripherals', 'webcams': 'peripherals',
        'thermal_paste': 'thermal_paste', 'wifi_adapters': 'wifi_adapters',
        'speakers': 'speakers', 'microphones': 'microphones',
        'ups': 'ups', 'tools': 'tools'
    }
    
    if category not in cat_map:
        return jsonify({'status': 'error', 'message': 'Invalid category'}), 400
    
    target_cat = cat_map[category]
    query = {'category': target_cat}
    
    # Handle sub-category mapping for admin filtering
    subcat_map = {
        'keyboards': 'keyboard',
        'mice': 'mouse',
        'headsets': 'headset',
        'webcams': 'webcam'
    }
    
    if category in subcat_map:
        query['sub_category'] = subcat_map[category]
    
    status_filter = request.args.get('status')
    if status_filter:
        query['status'] = status_filter

    search_query = request.args.get('search')
    if search_query:
        query['name'] = {'$regex': search_query, '$options': 'i'}

    # Generic query to components table
    items = list(db.components.find(query).sort('name', 1))
    app.logger.info(f"Hardware Query: {query} -> Found {len(items)} items")
    for item in items:
        item['_id'] = str(item['_id'])
        if 'status' not in item: item['status'] = 'Active'
    return jsonify({'status': 'success', 'components': items})

@app.route('/api/admin/components/<category>', methods=['POST'])
@admin_required
def admin_add_component(category):
    cat_map = {
        'cpus': 'cpu', 'gpus': 'gpu', 'motherboards': 'motherboard',
        'ram': 'ram', 'storage': 'storage', 'psu': 'psu',
        'cases': 'case', 'coolers': 'cooler', 'fans': 'fans',
        'monitors': 'monitor', 'os': 'os', 'peripherals': 'peripherals',
        'keyboards': 'peripherals', 'mice': 'peripherals',
        'headsets': 'peripherals', 'webcams': 'peripherals',
        'thermal_paste': 'thermal_paste', 'wifi_adapters': 'wifi_adapters',
        'speakers': 'speakers', 'microphones': 'microphones',
        'ups': 'ups', 'tools': 'tools'
    }
    target_cat = cat_map.get(category)
    if not target_cat:
        return jsonify({'status': 'error', 'message': 'Invalid category'}), 400

    data = request.json
    if not data or 'name' not in data:
        return jsonify({'status': 'error', 'message': 'Name is required'}), 400
    
    # Auto-assign sub-category if applicable
    subcat_map = {
        'keyboards': 'keyboard',
        'mice': 'mouse',
        'headsets': 'headset',
        'webcams': 'webcam'
    }
    if category in subcat_map:
        data['sub_category'] = subcat_map[category]
    
    # Check for duplicates
    query = {'category': target_cat, 'name': data['name']}
    if category in subcat_map:
        query['sub_category'] = subcat_map[category]
        
    if db.components.find_one(query):
        return jsonify({'status': 'error', 'message': 'Component already exists'}), 400
    
    # Ensure default status and category
    if 'status' not in data: data['status'] = 'Active'
    data['category'] = target_cat
    
    db.components.insert_one(data)
    app.logger.info(f"Admin {session.get('username')} added component to {category}: {data['name']}")
    return jsonify({'status': 'success'})

@app.route('/api/admin/components/<category>/<comp_id>', methods=['PUT', 'DELETE'])
@admin_required
def admin_manage_component(category, comp_id):
    try:
        # We don't strictly need category for ID lookup but it helps validation
        if request.method == 'DELETE':
            db.components.delete_one({'_id': ObjectId(comp_id)})
            app.logger.info(f"Admin {session.get('username')} deleted component {comp_id}")
            return jsonify({'status': 'success'})
        
        if request.method == 'PUT':
            data = request.json
            if '_id' in data: del data['_id']
            # Prevent changing category via edit if risky, but allow updates
            db.components.update_one({'_id': ObjectId(comp_id)}, {'$set': data})
            app.logger.info(f"Admin {session.get('username')} updated component {comp_id}")
            return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/admin/import-components', methods=['POST'])
@admin_required
def admin_import_components():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({'status': 'error', 'message': 'Only CSV files are allowed'}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        
        stats = {'total': 0, 'added': 0, 'skipped': 0, 'errors': []}
        
        # Valid collections
        collections = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers', 'fans', 'monitors', 'os', 'peripherals', 'thermal_paste', 'wifi_adapters', 'speakers', 'microphones', 'ups', 'tools']
        
        for row in reader:
            stats['total'] += 1
            try:
                # 1. Validate mandatory fields
                comp_type = row.get('type', '').lower().strip()
                # Handle plurals if user provides them
                if not comp_type.endswith('s') and comp_type not in ['ram', 'storage', 'psu']:
                    if comp_type == 'motherboard': comp_type = 'motherboards'
                    elif comp_type == 'case': comp_type = 'cases'
                    elif comp_type == 'cooler': comp_type = 'coolers'
                    else: comp_type += 's'
                
                if comp_type not in collections:
                    stats['skipped'] += 1
                    stats['errors'].append(f"Row {stats['total']}: Invalid component type '{row.get('type')}'")
                    continue
                
                name = row.get('name') or row.get('model')
                if not name:
                    stats['skipped'] += 1
                    stats['errors'].append(f"Row {stats['total']}: Missing Name/Model")
                    continue
                
                # 2. Duplicate Check
                if db[comp_type].find_one({'name': name}):
                    stats['skipped'] += 1
                    continue
                
                # 3. Clean and Insert
                # We store generic fields and specific ones
                doc = {}
                for k, v in row.items():
                    if v and v.strip():
                        # Try to convert numbers
                        try:
                            if '.' in v: doc[k] = float(v)
                            else: doc[k] = int(v)
                        except:
                            doc[k] = v.strip()
                
                # Ensure 'name' is set
                doc['name'] = name
                if 'type' in doc: del doc['type']
                
                db[comp_type].insert_one(doc)
                stats['added'] += 1
                
            except Exception as row_err:
                stats['skipped'] += 1
                stats['errors'].append(f"Row {stats['total']}: {str(row_err)}")
        
        app.logger.info(f"Admin {session.get('username')} imported CSV: {stats['added']} added, {stats['skipped']} skipped.")
        return jsonify({'status': 'success', 'stats': stats})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Failed to parse CSV: {str(e)}"}), 500

# ==========================================
# ADVANCED ANALYSIS FEATURES
# ==========================================

@app.route('/advanced-analysis')
@login_required
def advanced_analysis():
    return render_template('advanced_analysis.html')

@app.route('/api/bottleneck-analyzer', methods=['POST'])
@login_required
def api_bottleneck_analyzer():
    try:
        data = request.json
        build = data.get('build', {})
        
        # Extract components
        cpu_id = build.get('CPU')
        gpu_id = build.get('GPU')
        
        if not cpu_id or not gpu_id:
            return jsonify({'status': 'error', 'message': 'Missing CPU or GPU'}), 400
            
        cpu = db.components.find_one({'_id': ObjectId(cpu_id)})
        gpu = db.components.find_one({'_id': ObjectId(gpu_id)})
        
        if not cpu or not gpu:
            return jsonify({'status': 'error', 'message': 'Components not found'}), 404
            
        # Heuristic scoring based on price (proxy for performance in absence of benchmarks)
        # In a real app, use PassMark/Cinebench scores from DB
        cpu_score = cpu.get('price', 200) * 1.2  # Adjustment factor
        gpu_score = gpu.get('price', 400)
        
        # Calculate balance
        # Ideal ratio: GPU should be roughly 1.5x - 2.5x CPU price for gaming
        ratio = gpu_score / max(cpu_score, 1)
        
        bottleneck_percent = 0
        component = "None"
        suggestions = []
        
        if ratio > 3.0:
            # GPU too strong for CPU
            bottleneck_percent = min(int((ratio - 3.0) * 10), 100)
            component = "CPU"
            explanation = f"Your GPU is significantly more powerful than your CPU. The {cpu['name']} may limit the performance of the {gpu['name']}."
            suggestions.append("Consider upgrading your CPU to match the GPU power.")
        elif ratio < 1.0:
            # CPU too strong for GPU (common in workstations, bad for gaming)
            bottleneck_percent = min(int((1.0 - ratio) * 20), 100)
            component = "GPU"
            explanation = f"Your CPU is very powerful compared to your GPU. In gaming, the {gpu['name']} will be the bottleneck."
            suggestions.append("For gaming, consider a more powerful GPU or a cheaper CPU to save money.")
        else:
            explanation = "Your CPU and GPU are well-balanced for most tasks."
            
        return jsonify({
            'status': 'success',
            'bottleneck_component': component,
            'bottleneck_percentage': bottleneck_percent,
            'explanation': explanation,
            'suggestions': suggestions,
            'cpu_name': cpu.get('name'),
            'gpu_name': gpu.get('name')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/thermal-noise', methods=['POST'])
@login_required
def api_thermal_noise():
    try:
        data = request.json
        build = data.get('build', {})
        
        # Fetch components
        comps = {}
        total_tdp = 0
        for k, v in build.items():
            if v and len(v) == 24:
                # Determine collection name (unused logic now, we use unified)
                
                # Try finding in components table directly
                item = db.components.find_one({'_id': ObjectId(v)})
                if item:
                    comps[k] = item
                    # Extract TDP/Wattage
                    tdp_val = 0
                    tdp_str = str(item.get('tdp', item.get('wattage', '0')))
                    import re
                    match = re.search(r'(\d+)', tdp_str)
                    if match:
                        tdp_val = int(match.group(1))
                    
                    if k in ['CPU', 'GPU']:
                        total_tdp += tdp_val

        # Estimates
        cpu_temp_idle = 35
        cpu_temp_load = 70
        gpu_temp_idle = 30
        gpu_temp_load = 75
        noise_level = 30 # dB (base)
        
        # Adjust based on Cooler
        cooler = comps.get('Cooler')
        if cooler:
            if 'Liquid' in cooler.get('type', '') or 'AIO' in cooler.get('name', ''):
                cpu_temp_load -= 10
                noise_level += 5 # Pump noise based
            elif 'Air' in cooler.get('type', ''):
                cpu_temp_load -= 5
                
        # Adjust based on Case
        case = comps.get('Case')
        if case:
            if 'Airflow' in case.get('name', ''):
                cpu_temp_load -= 3
                gpu_temp_load -= 3
                noise_level += 2 # More holes = more sound leak
                
        # Noise calculation approx
        if total_tdp > 500:
            noise_level += 15 # Fans spinning hard
        elif total_tdp > 300:
            noise_level += 10
            
        return jsonify({
            'status': 'success',
            'cpu_temp_load': cpu_temp_load,
            'gpu_temp_load': gpu_temp_load,
            'estimated_noise_db': noise_level,
            'total_tdp': total_tdp,
            'recommendation': "Cooling looks sufficient." if cpu_temp_load < 85 else "Consider better cooling."
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/overclocking-potential', methods=['POST'])
@login_required
def api_overclocking_potential():
    try:
        data = request.json
        build = data.get('build', {})
        
        cpu = db.components.find_one({'_id': ObjectId(build.get('CPU'))})
        mobo = db.components.find_one({'_id': ObjectId(build.get('Motherboard'))})
        
        if not cpu or not mobo:
            return jsonify({'status': 'error', 'message': 'Missing CPU or Motherboard'}), 400
            
        can_overclock = False
        reason = ""
        
        # Logic for Intel
        if 'Intel' in cpu.get('name', ''):
            if 'K' in cpu.get('name', '') or 'X' in cpu.get('name', ''):
                if 'Z' in mobo.get('chipset', '') or 'X' in mobo.get('chipset', ''):
                    can_overclock = True
                    reason = "Unlocked 'K/X' series CPU paired with 'Z/X' series motherboard."
                else:
                    reason = "CPU is unlocked, but motherboard chipset does not support overclocking."
            else:
                reason = "CPU is locked (non-K series)."
                
        # Logic for AMD
        elif 'AMD' in cpu.get('name', ''):
            # Most Ryzen are unlocked, check chipset
            if 'A320' in mobo.get('chipset', '') or 'A520' in mobo.get('chipset', ''):
                reason = "Ryzen CPUs allow OC, but entry-level A-series chipsets typically do not."
            else:
                can_overclock = True
                reason = "Ryzen CPU paired with B/X series motherboard supports overclocking."
                
        return jsonify({
            'status': 'success',
            'can_overclock': can_overclock,
            'reason': reason,
            'estimated_gain': "5-15% Performance Boost" if can_overclock else "0%",
            'monitor_impact': "High power draw & heat increase" if can_overclock else "Standard operation"
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/build-optimizer', methods=['POST'])
@login_required
def api_build_optimizer():
    try:
        data = request.json
        build = data.get('build', {})
        budget = data.get('budget', 2000)
        
        suggestions = []
        
        # 1. Check for cheaper RAM with same specs
        ram = db.components.find_one({'_id': ObjectId(build.get('RAM'))})
        if ram:
            cheaper_ram = list(db.components.find({
                'category': 'ram',
                'capacity': ram.get('capacity'),
                'type': ram.get('type'),
                'price': {'$lt': ram.get('price', 0)}
            }).sort('price', 1).limit(1))
            
            if cheaper_ram:
                alt = cheaper_ram[0]
                diff = ram.get('price') - alt.get('price')
                if diff > 10:
                    suggestions.append({
                        'component': 'RAM',
                        'current': ram.get('name'),
                        'suggested': alt.get('name'),
                        'savings': diff,
                        'message': f"Save ${diff} with similar specs."
                    })
                    
        # 2. Check for GPU upgrade if budget allows
        # (Simplified logic)
        
        return jsonify({
            'status': 'success',
            'suggestions': suggestions,
            'optimization_score': 85 if not suggestions else 70 # Arbitrary score
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- Forgot Password Logic ---

def send_email(to_email, otp):
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')

    if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
        print(f"[MOCK EMAIL] SMTP not configured. OTP for {to_email}: {otp}")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = "RigMaster AI - Password Reset OTP"

        body = f"Your OTP for password reset is: {otp}\n\nThis code expires in 10 minutes."
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_email, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
        # Fallback for dev/testing if email fails
        print(f"[FALLBACK] OTP for {to_email}: {otp}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.')
            return redirect(url_for('forgot_password'))

        global db
        if db is None: db = get_db()
        
        user = db.users.find_one({'email': email})
        if not user:
            # Security: Don't reveal if user exists
            flash('If an account exists with that email, we have sent an OTP.')
            return redirect(url_for('verify_otp'))

        otp = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        db.otps.update_one(
            {'email': email},
            {'$set': {'otp': otp, 'expires_at': expires_at}},
            upsert=True
        )

        if send_email(email, otp):
            flash('If an account exists with that email, we have sent an OTP.')
        else:
            flash(f'DEV MODE: Email failed. Your OTP is: {otp}')
            
        session['reset_email_pending'] = email
        return redirect(url_for('verify_otp'))

    return render_template('forgot_password.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp_input = request.form.get('otp')
        email = session.get('reset_email_pending')

        if not email or not otp_input:
            flash('Session expired or invalid input.')
            return redirect(url_for('forgot_password'))

        global db
        if db is None: db = get_db()

        record = db.otps.find_one({'email': email})
        
        if not record:
            flash('Invalid or expired OTP.')
            return redirect(url_for('verify_otp'))

        if datetime.now(timezone.utc) > record['expires_at'].replace(tzinfo=timezone.utc):
            flash('OTP has expired.')
            return redirect(url_for('forgot_password'))

        if record['otp'] != otp_input:
            flash('Invalid OTP.')
            return redirect(url_for('verify_otp'))

        # OTP Verified
        session.pop('reset_email_pending', None)
        session['reset_email_verified'] = email # Authorized for reset
        
        # Clean up OTP
        db.otps.delete_one({'email': email})
        
        return redirect(url_for('reset_password'))

    return render_template('verify_otp.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email_verified')
    if not email:
        flash('Unauthorized access. Please start over.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.')
            return redirect(url_for('reset_password'))

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('reset_password'))

        global db
        if db is None: db = get_db()

        hashed = generate_password_hash(password)
        db.users.update_one(
            {'email': email},
            {'$set': {'password': hashed}}
        )

        session.pop('reset_email_verified', None)
        flash('Password reset successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('reset_password.html')





# PRICE TRACKER FEATURE - Real-Time Component Pricing
# ============================================================================

@app.route('/api/component-prices', methods=['POST'])
@login_required
def api_component_prices():
    """
    Get current market prices for all components in a build.
    Returns price data with retailer information.
    """
    try:
        data = request.json
        component_ids = {
            'cpu': data.get('cpu_id'),
            'gpu': data.get('gpu_id'),
            'motherboard': data.get('motherboard_id'),
            'ram': data.get('ram_id'),
            'storage': data.get('storage_id'),
            'psu': data.get('psu_id'),
            'case': data.get('case_id'),
            'cooler': data.get('cooler_id'),
            'monitor': data.get('monitor_id'),
            'os': data.get('os_id'),
            'peripherals': data.get('peripherals_id'),
            'keyboard': data.get('keyboard_id'),
            'mouse': data.get('mouse_id'),
            'headset': data.get('headset_id'),
            'webcam': data.get('webcam_id'),
            'fans': data.get('fans_id'),
            'thermal_paste': data.get('thermal_paste_id'),
            'wifi': data.get('wifi_id'),
            'speakers': data.get('speakers_id'),
            'microphone': data.get('microphone_id'),
            'ups': data.get('ups_id'),
            'tools': data.get('tool_id')
        }
        
        prices = {}
        total_cost = 0
        
        for category, comp_id in component_ids.items():
            if not comp_id or comp_id == "None Selected":
                continue
                
            try:
                # Try unified components table first
                comp = db.components.find_one({'_id': ObjectId(comp_id)})
                
                # Fallback to category-specific tables
                if not comp:
                    col_map = {
                        'cpu': 'cpus', 'gpu': 'gpus', 'motherboard': 'motherboards',
                        'ram': 'ram', 'storage': 'storage', 'psu': 'psu',
                        'case': 'cases', 'cooler': 'coolers', 'monitor': 'monitors',
                        'os': 'os', 'peripherals': 'peripherals', 'fans': 'fans',
                        'thermal_paste': 'thermal_paste', 'wifi': 'wifi_adapters', 
                        'speakers': 'speakers', 'microphone': 'microphones', 
                        'ups': 'ups', 'tools': 'tools'
                    }
                    col = col_map.get(category, category)
                    comp = db[col].find_one({'_id': ObjectId(comp_id)})
                
                if comp:
                    # Use consistent price helper
                    price = get_comp_price_usd(comp, category)
                    
                    if price and price > 0:
                        prices[category] = {
                            'name': comp.get('name', 'Unknown'),
                            'price': round(price, 2),
                            'currency': 'USD',
                            'retailer': comp.get('retailer', 'Market Average'),
                            'url': comp.get('product_url', '#'),
                            'in_stock': comp.get('in_stock', True)
                        }
                        total_cost += price
                    else:
                        # Safety fallback although get_comp_price_usd should already have handled it
                        prices[category] = {
                            'name': comp.get('name', 'Unknown'),
                            'price': None,
                            'currency': 'USD',
                            'retailer': 'Price unavailable',
                            'url': '#',
                            'in_stock': False
                        }
                        
            except Exception as e:
                app.logger.error(f"Error fetching price for {category}: {e}")
                continue
        
        user_currency = session.get('currency', 'USD')
        rate = EXCHANGE_RATES.get(user_currency, 1.0)
        symbol = CURRENCY_SYMBOLS.get(user_currency, '$')

        return jsonify({
            'status': 'success',
            'prices': prices,
            'total_cost': round(total_cost, 2),
            'currency': user_currency,
            'currency_symbol': symbol,
            'exchange_rate': rate,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Component prices error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/price-alert', methods=['POST'])
@login_required
def api_set_price_alert():
    """
    Set a price alert for a specific component.
    User will be notified when price drops below target.
    """
    try:
        data = request.json
        user_id = session.get('user_id')
        
        component_id = data.get('component_id')
        target_price = float(data.get('target_price', 0))
        
        if not component_id or target_price <= 0:
            return jsonify({
                'status': 'error',
                'message': 'Invalid component ID or target price'
            }), 400
        
        # Create or update price alert
        alert = {
            'user_id': ObjectId(user_id),
            'component_id': ObjectId(component_id),
            'target_price': target_price,
            'created_at': datetime.now(),
            'triggered': False
        }
        
        # Upsert (update if exists, insert if not)
        db.price_alerts.update_one(
            {
                'user_id': ObjectId(user_id),
                'component_id': ObjectId(component_id)
            },
            {'$set': alert},
            upsert=True
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Price alert set for ${target_price:.2f}'
        })
        
    except Exception as e:
        app.logger.error(f"Price alert error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/price-history/<component_id>', methods=['GET'])
@login_required
def api_price_history(component_id):
    """
    Get 30-day price history for a component.
    Returns simulated historical data for demonstration.
    """
    try:
        # Get current price
        comp = db.components.find_one({'_id': ObjectId(component_id)})
        if not comp:
            # Try category-specific tables
            for col in ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']:
                comp = db[col].find_one({'_id': ObjectId(component_id)})
                if comp:
                    break
        
        if not comp:
            return jsonify({
                'status': 'error',
                'message': 'Component not found'
            }), 404
        
        current_price = comp.get('price', comp.get('msrp', 299))
        if isinstance(current_price, str):
            current_price = float(current_price.replace('$', '').replace(',', ''))
        
        # Generate simulated 30-day price history
        import random
        from datetime import timedelta
        
        history = []
        base_price = current_price
        
        for i in range(30, 0, -1):
            date = datetime.now() - timedelta(days=i)
            # Add random variation (Â±10%)
            variation = random.uniform(-0.10, 0.10)
            price = base_price * (1 + variation)
            
            history.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': round(price, 2),
                'retailer': 'Market Average'
            })
        
        # Add current price as most recent
        history.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'price': round(current_price, 2),
            'retailer': comp.get('retailer', 'Market Average')
        })
        
        return jsonify({
            'status': 'success',
            'component_name': comp.get('name', 'Unknown'),
            'history': history,
            'lowest_30d': round(min([h['price'] for h in history]), 2),
            'highest_30d': round(max([h['price'] for h in history]), 2),
            'average_30d': round(sum([h['price'] for h in history]) / len(history), 2)
        })
        
    except Exception as e:
        app.logger.error(f"Price history error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# GROUP PC BUILDER FEATURE
# ============================================================================

@app.route('/group-builder', endpoint='group_builder_page')
@login_required
def group_builder():
    """Render the Group PC Builder page"""
    global db
    if db is None:
        db = get_db()
    if db is None:
        return render_template('error.html', message="Database connection unavailable. Please check your network or try again later."), 503

    try:
        user_id = session.get('user_id')
        from bson.objectid import ObjectId
        
        # Robust query for user_id
        id_variants = [user_id]
        if isinstance(user_id, str):
            try: id_variants.append(ObjectId(user_id))
            except: pass
            
        # Fetch user's saved builds for the dropdown
        saved_builds = list(db.saved_builds.find({'user_id': {'$in': id_variants}}))
        
        # Fetch existing group builds to display on the same page
        group_builds = list(db.group_builds.find({'user_id': {'$in': id_variants}}).sort('created_at', -1))
        
        current_currency = session.get('currency', 'USD')
        exchange_rate = EXCHANGE_RATES.get(current_currency, 1.0)
        
        return render_template('group_builder.html', 
                               saved_builds=saved_builds, 
                               group_builds=group_builds,
                               exchange_rate=exchange_rate)
    except Exception as e:
        app.logger.error(f"Error loading group builder: {e}")
        return render_template('error.html', message="Could not load group builder"), 500

@app.route('/api/calculate-group-build', methods=['POST'])
@login_required
def api_calculate_group_build():
    """Calculate requirements and costs for a bulk build"""
    try:
        data = request.json
        build_id = data.get('build_id')
        quantity = int(data.get('quantity', 0))
        
        if not build_id or quantity < 2:
            return jsonify({'status': 'error', 'message': 'Invalid parameters'}), 400
            
        # 1. Fetch the base build
        base_build = db.saved_builds.find_one({
            '_id': ObjectId(build_id),
            'user_id': session.get('user_id')
        })
        
        if not base_build:
            return jsonify({'status': 'error', 'message': 'Build not found'}), 404
            
        # 2. Helper to resolve component details and cost
        def get_comp_details(comp_id, category):
            if not comp_id: return None
            comp = db.components.find_one({'_id': ObjectId(comp_id)})
            if not comp: return None
            
            # Use consistent price helper
            price = get_comp_price_usd(comp, est_cat=category)
            
            return {
                'id': str(comp['_id']),
                'name': comp.get('name'),
                'price': price,
                'tdp': comp.get('tdp', 0),
                'category': category
            }
            
        # 3. Process components
        components = {}
        total_unit_cost = 0
        
        # Mapping build keys to categories (Aligned with frontend)
        key_map = {
            'cpu_id': 'cpu', 'gpu_id': 'gpu', 'motherboard_id': 'motherboard',
            'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
            'case_id': 'case', 'cooler_id': 'cooler',
            'keyboard_id': 'keyboard', 'mouse_id': 'mouse',
                        'headset_id': 'headset', 'webcam_id': 'webcam', 'fans_id': 'fans', 
            'peripherals_id': 'peripherals', 'monitor_id': 'monitor', 'os_id': 'os',
            'thermal_paste_id': 'thermal_paste', 'wifi_id': 'wifi_adapters',
            'speakers_id': 'speakers', 'microphone_id': 'microphones',
            'ups_id': 'ups', 'tool_id': 'tools'
        }
        
        for key, cat in key_map.items():
            comp_id = base_build.get(key)
            app.logger.info(f"Group Calc: Processing {key} ({cat}) with ID {comp_id}")
            if comp_id:
                details = get_comp_details(comp_id, cat)
                if details:
                    app.logger.info(f"Group Calc: Found {cat}: {details['name']}")
                    components[cat] = details
                    total_unit_cost += details['price']
                else:
                    app.logger.warning(f"Group Calc: Component {comp_id} NOT FOUND for {cat}")
                    
        # 4. Calculate totals
        total_group_cost = total_unit_cost * quantity
        
        return jsonify({
            'status': 'success',
            'result': {
                'base_build_name': base_build.get('name'),
                'quantity': quantity,
                'unit_cost': round(total_unit_cost, 2),
                'total_cost': round(total_group_cost, 2),
                'components': components
            }
        })
        
    except Exception as e:
        app.logger.error(f"Group calculation error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/save-group-build', methods=['POST'])
@login_required
def api_save_group_build():
    """Save the group build to the database"""
    try:
        global db
        data = request.json
        user_id = session.get('user_id')
        app.logger.info(f"Saving group build for user {user_id}: {data.get('base_build_name')} x {data.get('quantity')}")
        
        record = {
            'user_id': user_id,
            'base_build_name': data.get('base_build_name'),
            'quantity': data.get('quantity'),
            'unit_cost': data.get('unit_cost'),
            'total_cost': data.get('total_cost'),
            'components': data.get('components'),
            'created_at': datetime.now(timezone.utc)
        }
        
        db.group_builds.insert_one(record)
        return jsonify({'status': 'success', 'message': 'Project plan saved to your vault!'})
        
    except Exception as e:
        app.logger.error(f"Group save error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/delete-group-build/<plan_id>', methods=['DELETE'])
@login_required
def api_delete_group_build(plan_id):
    """Delete a saved group build plan"""
    print(f"DEBUG: api_delete_group_build hit for plan_id: {plan_id}")
    if not plan_id or len(str(plan_id).strip()) < 10:
        return jsonify({'status': 'error', 'message': 'Invalid plan ID provided'}), 400
        
    try:
        user_id = session.get('user_id')
        plan_id_clean = str(plan_id).strip()
        result = db.group_builds.delete_one({
            '_id': ObjectId(plan_id_clean),
            'user_id': user_id
        })
        
        if result.deleted_count > 0:
            return jsonify({'status': 'success', 'message': 'Project plan deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Project plan not found or access denied'}), 404
            
    except Exception as e:
        app.logger.error(f"Group delete error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/export-group-build/<plan_id>', endpoint='api_export_group_build')
@login_required
def api_export_group_build(plan_id):
    """Export the group build manifest as a PDF file"""
    try:
        user_id = session.get('user_id')
        plan = db.group_builds.find_one({
            '_id': ObjectId(plan_id),
            'user_id': user_id
        })
        
        if not plan:
            return "Project plan not found", 404
            
        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("helvetica", 'B', 24)
        pdf.set_text_color(63, 81, 181) # RigMaster Primary
        pdf.cell(0, 20, "RigMaster AI - Deployment Manifest", border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(5)
        
        # Project Info
        pdf.set_font("helvetica", 'B', 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "Project Overview", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", '', 12)
        
        pdf.cell(50, 8, "Project Ref:", border=0)
        pdf.cell(0, 8, f"GRP-{plan_id[-6:]}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.cell(50, 8, "Configuration:", border=0)
        pdf.cell(0, 8, plan.get('base_build_name', 'Standard Rig'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.cell(50, 8, "Quantity:", border=0)
        pdf.cell(0, 8, str(plan.get('quantity', 0)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.cell(50, 8, "Unit Cost:", border=0)
        pdf.cell(0, 8, format_price(plan.get('unit_cost', 0), for_pdf=True), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(50, 8, "Total Budget:", border=0)
        pdf.cell(0, 8, format_price(plan.get('total_cost', 0), for_pdf=True), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", '', 12)
        
        pdf.cell(50, 8, "Date Generated:", border=0)
        pdf.cell(0, 8, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(50, 8, "Currency Context:", border=0)
        pdf.cell(0, 8, session.get('currency', 'USD'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(10)
        
        # Components Table
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "Bill of Materials", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        # Table Header
        pdf.set_font("helvetica", 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(80, 10, "COMPONENT", border=1, fill=True)
        pdf.cell(30, 10, "CATEGORY", border=1, fill=True, align='C')
        pdf.cell(40, 10, "UNIT PRICE", border=1, fill=True, align='C')
        pdf.cell(40, 10, "TOTAL PRICE", border=1, fill=True, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("helvetica", '', 9)
        components = plan.get('components', {})
        qty = plan.get('quantity', 0)
        
        for cat, details in components.items():
            price = details.get('price', 0)
            name = details.get('name', 'Unknown')
            
            # Truncate name if too long for simple cell
            display_name = (name[:42] + '..') if len(name) > 42 else name
            
            pdf.cell(80, 8, display_name, border=1)
            pdf.cell(30, 8, cat.upper(), border=1, align='C')
            pdf.cell(40, 8, format_price(price, for_pdf=True), border=1, align='C')
            pdf.cell(40, 8, format_price(price * qty, for_pdf=True), border=1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
        pdf.ln(5)
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(150, 10, "GRAND TOTAL", border=0, align='R')
        pdf.cell(40, 10, format_price(plan.get('total_cost', 0), for_pdf=True), border=1, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Section 4: Logistical Breakdown
        pdf.ln(10)
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "Deployment Logistics", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
        
        # Calculate logistics
        total_tdp = 0
        for cat, details in components.items():
            tdp_val = details.get('tdp', 0)
            try:
                total_tdp += int(tdp_val)
            except:
                pass
            
        total_power_kw = (total_tdp * qty) / 1000.0
        # Estimated weight: ~14kg average for a built mid-tower PC with packaging
        unit_weight = 14.0
        total_weight_kg = unit_weight * qty
        
        # Deployment time: ~1.25 hours per PC (assembly + automated OS deployment)
        total_hours = qty * 1.25
        
        pdf.set_font("helvetica", '', 11)
        pdf.cell(60, 7, "Total Fleet Power Draw:", border=0)
        pdf.cell(0, 7, f"{total_power_kw:.2f} kW (Estimated peak draw for {qty} units)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.cell(60, 7, "Estimated Freight Weight:", border=0)
        pdf.cell(0, 7, f"{total_weight_kg:,.0f} kg (Includes chassis and protective packaging)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.cell(60, 7, "Deployment Effort:", border=0)
        pdf.cell(0, 7, f"{total_hours:,.1f} Man-Hours (Build + Network OS Deployment)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Section 5: Performance Scaling & Infrastructure
        pdf.ln(10)
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "Performance Scaling & Infrastructure", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
        
        # Heuristic Performance Tier
        gpu_name = components.get('gpu', {}).get('name', '').upper()
        cpu_name = components.get('cpu', {}).get('name', '').upper()
        
        tier = "Standard Enterprise"
        if any(x in gpu_name for x in ['4090', '4080', '7900 XTX', '5090']): tier = "Ultra-Deep AI/Render Node"
        elif any(x in gpu_name for x in ['4070', '3080', '7800']): tier = "High-Performance Compute"
        elif any(x in gpu_name for x in ['4060', '3060', '7700']): tier = "Advanced Creative Workstation"
        
        # Infrastructure Impact
        heat_output_btu = (total_tdp * qty) * 3.41  # Conversion from Watts to BTU/hr
        rack_units_est = qty * 4 # Standard tower takes ~4U space
        
        pdf.set_font("helvetica", 'B', 11)
        pdf.cell(60, 7, "Fleet Classification:", border=0)
        pdf.set_font("helvetica", '', 11)
        pdf.cell(0, 7, tier, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("helvetica", 'B', 11)
        pdf.cell(60, 7, "Thermal Output:", border=0)
        pdf.set_font("helvetica", '', 11)
        pdf.cell(0, 7, f"{heat_output_btu:,.0f} BTU/hr (HVAC load for synchronized operation)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("helvetica", 'B', 11)
        pdf.cell(60, 7, "Space Requirement:", border=0)
        pdf.set_font("helvetica", '', 11)
        pdf.cell(0, 7, f"~{rack_units_est}U Volumetric Equivalent (Approx {qty} Tower Formats)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.ln(5)
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, "Infrastructure Recommendations:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", '', 10)
        
        recommendations = [
            f"Power Distribution: Recommend dedicated 20A circuits per every {max(1, 2500//(total_tdp or 100))} units.",
            "Network: Managed L3 Switches with 2.5GbE backbone advised for rapid fleet re-imaging.",
            "Climate Control: Precision air cooling with cold/hot aisle containment for densities >10kW."
        ]
        for rec in recommendations:
            pdf.multi_cell(0, 5, f" - {rec}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(15)
        
        # Certification & Disclaimer
        pdf.set_line_width(0.5)
        pdf.set_draw_color(63, 81, 181)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(0, 7, "RigMaster Nexus AI Certification", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.set_font("helvetica", 'I', 8)
        pdf.set_text_color(100, 100, 100)
        disclaimer = "This deployment manifest is an AI-generated estimate based on RigMaster hardware benchmarks. RigMaster Pro verifies component compatibility for the selected configuration. Power requirements are based on peak thermal design power (TDP); actual operational draw may vary significantly under differing workloads."
        pdf.multi_cell(0, 5, disclaimer, align='C')

        pdf_output = pdf.output()
        
        return send_file(
            io.BytesIO(pdf_output),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"deployment_manifest_{plan_id[:8]}.pdf"
        )
        
    except Exception as e:
        app.logger.error(f"Export error: {e}")
        return f"Error generating export: {str(e)}", 500

# ============================================================================

# PROFILE API ENDPOINTS
@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def api_change_password():
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Missing data'}), 400
        
    user_id = session.get('user_id')
    user = db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user or not check_password_hash(user['password'], current_password):
        return jsonify({'success': False, 'message': 'Incorrect current password'}), 401
        
    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'password': generate_password_hash(new_password)}}
    )
    return jsonify({'success': True, 'message': 'Password updated successfully'})

@app.route('/api/profile/export-data')
@login_required
def api_export_user_data():
    user_id = session.get('user_id')
    user = db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0})
    builds = list(db.saved_builds.find({'user_id': user_id}))
    
    # Handle serialization
    def serialize(obj):
        if isinstance(obj, ObjectId): return str(obj)
        if isinstance(obj, datetime): return obj.isoformat()
        return obj

    export_data = {
        'user': {k: serialize(v) for k, v in user.items()},
        'builds': [{k: serialize(v) for k, v in b.items()} for b in builds],
        'exported_at': datetime.now(timezone.utc).isoformat()
    }
    
    return jsonify(export_data)

@app.route('/api/profile/delete-account', methods=['POST'])
@login_required
def api_delete_account():
    data = request.json
    if data.get('confirm') != 'DELETE':
        return jsonify({'success': False, 'message': 'Confirmation failed'}), 400
        
    user_id = session.get('user_id')
    db.saved_builds.delete_many({'user_id': user_id})
    db.group_builds.delete_many({'user_id': user_id})
    db.users.delete_one({'_id': ObjectId(user_id)})
    
    session.clear()
    return jsonify({'success': True, 'message': 'Account deleted successfully'})

@app.route('/api/profile/toggle-2fa', methods=['POST'])
@login_required
def api_toggle_2fa():
    user_id = session.get('user_id')
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
        
    new_status = not user.get('two_factor_enabled', False)
    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'two_factor_enabled': new_status}}
    )
    return jsonify({'success': True, 'two_factor_enabled': new_status})

@app.route('/api/profile/update', methods=['POST'])
@login_required
def api_update_profile():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    
    if not username or not email:
        return jsonify({'success': False, 'message': 'Username and email are required'}), 400
        
    user_id = session.get('user_id')
    
    # Check if username/email already taken by another user
    existing = db.users.find_one({
        '_id': {'$ne': ObjectId(user_id)},
        '$or': [{'username': username}, {'email': email}]
    })
    
    if existing:
        return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
        
    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'username': username, 'email': email}}
    )
    
    session['username'] = username # Update session
    return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/api/profile/revoke-session', methods=['POST'])
@login_required
def api_revoke_session():
    # Simulations for revoking other sessions
    # In a real app, this would involve invalidating session tokens/IDs in the DB
    return jsonify({'success': True, 'message': 'Session revoked'})
@app.route('/api/profile/update-preferences', methods=['POST'])
@login_required
def api_update_preferences():
    """Update user market and display preferences"""
    try:
        data = request.json
        currency = data.get('currency', 'USD')
        units = data.get('units', 'Metric')
        
        user_id = session.get('user_id')
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'preferred_currency': currency,
                'preferred_units': units
            }}
        )
        
        # Update session for immediate UI feedback
        session['currency'] = currency
        session['currency_symbol'] = CURRENCY_SYMBOLS.get(currency, '$')
        session['units'] = units
        
        return jsonify({
            'success': True, 
            'message': 'Regional preferences updated',
            'symbol': session['currency_symbol']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/profile')
@login_required
def profile():
    """Display user profile with stats and recent activity"""
    try:
        user_id = session.get('user_id')
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('login'))
            
        build_count = db.saved_builds.count_documents({'user_id': user_id})
        group_count = db.group_builds.count_documents({'user_id': user_id})
        
        recent_builds = list(db.saved_builds.find(
            {'user_id': user_id}
        ).sort('created_at', -1).limit(3))
        
        recent_groups = list(db.group_builds.find(
            {'user_id': user_id}
        ).sort('created_at', -1).limit(3))
        
        return render_template(
            'profile.html',
            user=user,
            build_count=build_count,
            group_count=group_count,
            recent_builds=recent_builds,
            recent_groups=recent_groups,
            all_currencies=CURRENCY_SYMBOLS
        )
    except Exception as e:
        app.logger.error(f"Profile error: {e}")
        return render_template('error.html', message="Could not load profile"), 500


@app.route('/api/fetch-prices', methods=['POST'])
@login_required
def api_fetch_prices():
    """
    Fetch real-time prices for components using PriceFetcher
    """
    try:
        from price_fetcher import get_price_fetcher
        
        data = request.json
        component_names = data.get('component_names', [])
        
        if not component_names:
            return jsonify({'status': 'error', 'message': 'No component names provided'}), 400
        
        price_fetcher = get_price_fetcher()
        results = {}
        
        for comp_name in component_names:
            if not comp_name or not isinstance(comp_name, str):
                continue
                
            try:
                price_data = price_fetcher.fetch_component_price(comp_name)
                if price_data:
                    results[comp_name] = price_data
                else:
                    # Fallback to database price if available
                    comp = db.components.find_one({'name': {'$regex': comp_name, '$options': 'i'}})
                    if comp:
                        db_price = get_comp_price_usd(comp)
                        if db_price > 0:
                            results[comp_name] = {
                                'price': db_price,
                                'currency': 'USD',
                                'source': 'database_fallback',
                                'timestamp': datetime.now(timezone.utc).isoformat()
                            }
                        else:
                            results[comp_name] = {
                                'price': None,
                                'currency': 'USD',
                                'source': 'unavailable',
                                'error': 'Price not found in database'
                            }
                    else:
                        results[comp_name] = {
                            'price': None,
                            'currency': 'USD',
                            'source': 'unavailable',
                            'error': 'Component not found'
                        }
            except Exception as e:
                app.logger.error(f"Error fetching price for {comp_name}: {e}")
                results[comp_name] = {
                    'price': None,
                    'currency': 'USD',
                    'source': 'error',
                    'error': str(e)
                }
        
        return jsonify({
            'status': 'success',
            'prices': results,
            'currency': session.get('currency', 'USD'),
            'currency_symbol': CURRENCY_SYMBOLS.get(session.get('currency', 'USD'), '$')
        })
        
    except Exception as e:
        app.logger.error(f"Price fetch API error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    # On Windows, use_reloader=True can sometimes cause "OSError: [WinError 10038] An operation was attempted on something that is not a socket"
    # Disabling the reloader is a common workaround for this development server stability issue.
    # Port changed to 5005 to avoid conflicts with Windows built-in services like AirPlay.
    print("\n" + "*" * 50)
    print("  RIGMASTER IS LIVE")
    print("  Open your browser at: http://127.0.0.1:5005")
    print("*" * 50 + "\n")
    app.run(host='0.0.0.0', port=5005, debug=True, use_reloader=False, threaded=True)
