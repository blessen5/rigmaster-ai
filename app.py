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

# Auto-startup: Automatically start Ollama and warm up models
import auto_startup

load_dotenv()
from pymongo import MongoClient
from bson.objectid import ObjectId
from ai_engine import get_ai_engine



app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_rigmaster_8822')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB Limit

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
    if cat == 'cpus':
        if 'THREADRIPPER' in name: return 1500
        if 'RYZEN 9' in name or 'CORE I9' in name: return 580
        if 'RYZEN 7' in name or 'CORE I7' in name: return 380
        if 'RYZEN 5' in name or 'CORE I5' in name: return 240
        return 140
    if cat == 'gpus':
        if '4090' in name: return 1800
        if '4080' in name or '7900 XTX' in name: return 1100
        if '4070 TI' in name or '7900 XT' in name: return 850
        if '4070 SUPER' in name or '4070' in name or '7800 XT' in name: return 650
        if '4060 TI' in name or '7700 XT' in name: return 420
        if '4060' in name or '7600' in name: return 320
        return 250
    if cat == 'motherboards': 
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
    if cat == 'cases': return 130
    if cat == 'coolers': 
        if 'LIQUID' in name or 'AIO' in name or '420' in name or '360' in name: return 160
        return 60
    if cat == 'monitors':
        if '4K' in name: return 600
        if '1440P' in name or '2K' in name: return 350
        return 180
    if cat == 'os':
        if 'PRO' in name: return 150
        return 110
    if cat == 'peripherals':
        return 80
    if cat == 'fans':
        return 30
    return 100

def get_component_by_id(comp_id):
    if db is None or not comp_id: return None
    try:
        if isinstance(comp_id, str) and comp_id == "None Selected": return None
        return db.components.find_one({'_id': ObjectId(comp_id)})
    except:
        return None

# Currency Support
EXCHANGE_RATES = {
    'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79, 'INR': 83.0, 'AUD': 1.52, 'CAD': 1.35,
    'JPY': 150.0, 'CHF': 0.88, 'CNY': 7.2, 'HKD': 7.8, 'NZD': 1.65, 'SEK': 10.5,
    'KRW': 1330.0, 'SGD': 1.34, 'NOK': 10.6, 'MXN': 17.0, 'RUB': 90.0, 'ZAR': 19.0,
    'TRY': 31.0, 'BRL': 5.0, 'TWD': 31.5, 'DKK': 6.8, 'PLN': 4.0, 'THB': 36.0,
    'IDR': 15600.0, 'HUF': 360.0, 'CZK': 23.5, 'ILS': 3.6, 'PHP': 56.0, 'AED': 3.67,
    'MYR': 4.7, 'VND': 24500.0, 'NGN': 1500.0
}
CURRENCY_SYMBOLS = {
    'USD': '$', 'EUR': '€', 'GBP': '£', 'INR': '₹', 'AUD': 'A$', 'CAD': 'C$',
    'JPY': '¥', 'CHF': 'CHF', 'CNY': '¥', 'HKD': 'HK$', 'NZD': 'NZ$', 'SEK': 'kr',
    'KRW': '₩', 'SGD': 'S$', 'NOK': 'kr', 'MXN': '$', 'RUB': '₽', 'ZAR': 'R',
    'TRY': '₺', 'BRL': 'R$', 'TWD': 'NT$', 'DKK': 'kr', 'PLN': 'zł', 'THB': '฿',
    'IDR': 'Rp', 'HUF': 'Ft', 'CZK': 'Kč', 'ILS': '₪', 'PHP': '₱', 'AED': 'د.إ',
    'MYR': 'RM', 'VND': '₫', 'NGN': '₦'
}

def format_price(amount, currency=None):
    if currency is None:
        currency = session.get('currency', 'USD')
    
    rate = EXCHANGE_RATES.get(currency, 1.0)
    converted_amount = amount * rate
    symbol = CURRENCY_SYMBOLS.get(currency, '$')
    
    # Format with appropriate decimals
    if currency == 'INR':
        return f"{symbol}{int(converted_amount):,}"
    return f"{symbol}{converted_amount:,.2f}"

@app.route('/api/set-currency', methods=['POST'])
def set_currency():
    try:
        data = request.get_json(silent=True, force=True) or {}
        currency = data.get('currency', 'USD')
        if currency in EXCHANGE_RATES:
            session['currency'] = currency
            return jsonify({'status': 'success', 'currency': currency})
        return jsonify({'status': 'error', 'message': f'Invalid currency: {currency}'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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

# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://rigmaster_user:MMdm2NPf8J737U8D@cluster0.99f5zmr.mongodb.net/rigmaster?retryWrites=true&w=majority&appName=Cluster0')
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
                _mongo_client = MongoClient(
                    MONGO_URI, 
                    serverSelectionTimeoutMS=5000, 
                    tz_aware=True,
                    tlsAllowInvalidCertificates=True,
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

@app.before_request
def ensure_db():
    global db, _last_db_retry
    if db is None:
        import time
        now = time.time()
        if now - _last_db_retry > DB_RETRY_INTERVAL:
            _last_db_retry = now
            db = get_db()
    
    try:
        from ai_engine import get_ai_engine
        ai_engine = get_ai_engine()
        ai_engine.preferred_provider = get_site_setting('preferred_ai_provider', 'auto')
        custom_api_keys = get_site_setting('api_keys', {})
        if custom_api_keys:
            ai_engine.update_api_keys(custom_api_keys)
    except:
        pass

# Global System Settings Helpers
def get_site_setting(key, default=None):
    try:
        if db is None: return default
        setting = db.settings.find_one({'key': key})
        return setting['value'] if setting else default
    except:
        return default

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
        'preferred_ai_provider': get_site_setting('preferred_ai_provider', 'auto')
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
        
        req_cat = request.args.get('category', 'cpus')
        search = request.args.get('search', '').strip()
        
        valid_categories = {
            'cpus': 'Processors',
            'gpus': 'Graphics Cards',
            'motherboards': 'Motherboards',
            'ram': 'Memory',
            'storage': 'Storage',
            'psu': 'Power Supplies',
            'cases': 'Chassis',
            'coolers': 'Cooling',
            'monitors': 'Monitors',
            'os': 'Operating Systems',
            'peripherals': 'Peripherals',
            'fans': 'Case Fans'
        }
        
        if req_cat not in valid_categories:
            req_cat = 'cpus'
            
        db_cat = category_map.get(req_cat, 'cpu')
            
        query = {'category': db_cat}
        if search:
            query['name'] = {'$regex': search, '$options': 'i'}
            
        # Generic query to components table
        items = list(db.components.find(query).sort('name', 1))
        for item in items:
            item['_id'] = str(item['_id'])
            
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
    """Send contact form details via email using SMTP settings from .env"""
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')

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
def resources():
    return redirect(url_for('support_page'))

@app.route('/help')
def help_center():
    return redirect(url_for('support_page', _anchor='help-center'))

@app.route('/contact')
def contact():
    return redirect(url_for('support_page', _anchor='contact'))

@app.route('/feedback')
def feedback():
    return redirect(url_for('support_page', _anchor='contact'))

@app.route('/admin/complaints')
@admin_required
def admin_complaints():
    try:
        db = get_db()
        if not db:
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
    
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')

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
    if not db:
        flash("Database unavailable.")
        return redirect(url_for('admin_dashboard'))
    user_count = db.users.count_documents({})
    return render_template('admin/broadcast.html', user_count=user_count)

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
    if not db:
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
    # Map id_key -> category in DB
    col_map = {
        'cpu_id': 'cpu', 'gpu_id': 'gpu', 'motherboard_id': 'motherboard',
        'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
        'case_id': 'case', 'cooler_id': 'cooler',
        'monitor_id': 'monitor', 'os_id': 'os',
        'peripherals_id': 'peripherals', 'fans_id': 'fans'
    }
    
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
        
        total_unit_cost = 0
        # For price calculation, we need to map id keys to the categories used in get_estimated_price
        price_cat_map = {
            'cpu_id': 'cpus', 'gpu_id': 'gpus', 'motherboard_id': 'motherboards',
            'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
            'case_id': 'cases', 'cooler_id': 'coolers',
            'monitor_id': 'monitors', 'os_id': 'os',
            'peripherals_id': 'peripherals', 'fans_id': 'fans'
        }

        for key, cat in col_map.items():
            comp_id = build.get(key)
            if comp_id:
                try:
                    comp = db.components.find_one({'_id': ObjectId(comp_id)})
                    if comp:
                        cname = comp.get('name', 'Unknown')
                        build_details['components'][key.replace('_id', '').upper()] = cname
                        total_unit_cost += get_estimated_price(cname, price_cat_map.get(key))
                except:
                    build_details['components'][key.replace('_id', '').upper()] = "Unknown Component"
            else:
                build_details['components'][key.replace('_id', '').upper()] = "None Selected"
        
        build_details['project_total'] = format_price(total_unit_cost * qty)
        
        # Add difficulty info
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
        
        # sort by name, include status and brand for builder logic
        items = list(db.components.find({'category': target_cat}, {'name': 1, 'status': 1, 'brand': 1}).sort('name', 1))
        print(f"API Debug: Category '{target_cat}' returned {len(items)} items")
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
def api_cpus():
    return jsonify(get_component_list('cpus'))

@app.route('/api/gpus')
def api_gpus():
    return jsonify(get_component_list('gpus'))

@app.route('/api/motherboards')
def api_motherboards():
    return jsonify(get_component_list('motherboards'))

@app.route('/api/ram')
def api_ram():
    return jsonify(get_component_list('ram'))

@app.route('/api/psu')
def api_psu():
    return jsonify(get_component_list('psu'))

@app.route('/api/storage')
def api_storage():
    return jsonify(get_component_list('storage'))

@app.route('/api/cases')
def api_cases():
    return jsonify(get_component_list('cases'))

@app.route('/api/coolers')
def api_coolers():
    return jsonify(get_component_list('coolers'))

@app.route('/api/monitors')
def api_monitors():
    return jsonify(get_component_list('monitors'))

@app.route('/api/os')
def api_os():
    return jsonify(get_component_list('os'))

@app.route('/api/peripherals')
def api_peripherals():
    return jsonify(get_component_list('peripherals'))

@app.route('/api/fans')
def api_fans():
    return jsonify(get_component_list('fans'))


# Test route to verify MongoDB connection
@app.route('/db-status')
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
        build_id = data.get('build_id')
        quantity = int(data.get('quantity', 1))
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
            
        # Ensure build_name is not something weird like a bool or empty
        if not build_name or str(build_name).strip() == "":
            build_name = "Custom Rig"
        else:
            build_name = str(build_name).strip()

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
            'fans_id': data.get('fans_id'),
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
def api_validate_build():
    data = request.json
    return jsonify(run_validation_logic(data))

@app.route('/api/fix-compatibility', methods=['POST'])
def api_fix_compatibility():
    """
    Identifies incompatibilities and suggests real parts from the database to fix them.
    In the analysis page if the build incompatible provide an option for users to make it compatible.
    """
    try:
        data = request.json
        cpu_id = data.get('cpu_id')
        mobo_id = data.get('motherboard_id')
        ram_id = data.get('ram_id')
        
        # Helper to get component safely
        def get_comp(comp_id):
            if not comp_id: return None
            try: 
                from bson.objectid import ObjectId
                return db.components.find_one({'_id': ObjectId(comp_id)})
            except: return None

        cpu = get_comp(cpu_id)
        mobo = get_comp(mobo_id)
        ram = get_comp(ram_id)
        
        suggestions = []
        
        # 1. Socket Check
        cpu_sock = infer_cpu_socket(cpu) if cpu else None
        mobo_sock = infer_mobo_socket(mobo) if mobo else None
        
        if cpu_sock and mobo_sock:
            mobo_sockets = [s.strip() for s in mobo_sock.split('/')]
            if cpu_sock not in mobo_sockets:
                # Fix 1: Change Motherboard to match CPU
                query = {'category': 'motherboard'}
                mobos = list(db.components.find(query).limit(500))
                compatible_mobos = []
                for m in mobos:
                    ms = infer_mobo_socket(m)
                    if ms and cpu_sock in [s.strip() for s in ms.split('/')]:
                        compatible_mobos.append({'id': str(m['_id']), 'name': m.get('name')})
                        if len(compatible_mobos) >= 3: break
                
                if compatible_mobos:
                    suggestions.append({
                        'category': 'motherboard',
                        'title': f'Change Motherboard to match {cpu.get("name")}',
                        'reason': f'Current board socket ({mobo_sock}) is incompatible with {cpu.get("name")} ({cpu_sock}).',
                        'options': compatible_mobos
                    })
                
                # Fix 2: Change CPU to match Motherboard
                target_sock = mobo_sockets[0]
                cpus = list(db.components.find({'category': 'cpu'}).limit(500))
                compatible_cpus = []
                for c in cpus:
                    cs = infer_cpu_socket(c)
                    if cs == target_sock:
                        compatible_cpus.append({'id': str(c['_id']), 'name': c.get('name')})
                        if len(compatible_cpus) >= 3: break
                
                if compatible_cpus:
                    suggestions.append({
                        'category': 'cpu',
                        'title': f'Change CPU to match {mobo.get("name")}',
                        'reason': f'Current CPU ({cpu.get("name")}) does not fit this motherboard socket ({mobo_sock}).',
                        'options': compatible_cpus
                    })

        # 2. RAM Check
        ram_gen = infer_ram_generation(ram, is_mobo=False) if ram else None
        mobo_ram_gen = infer_ram_generation(mobo, is_mobo=True) if mobo else None
        
        if ram_gen and mobo_ram_gen and ram_gen != mobo_ram_gen:
            # Fix: Change RAM to match Motherboard
            rams = list(db.components.find({'category': 'ram'}).limit(500))
            compatible_rams = []
            for r in rams:
                rg = infer_ram_generation(r, is_mobo=False)
                if rg == mobo_ram_gen:
                    compatible_rams.append({'id': str(r['_id']), 'name': r.get('name')})
                    if len(compatible_rams) >= 3: break
            
            if compatible_rams:
                suggestions.append({
                    'category': 'ram',
                    'title': f'Change RAM to {mobo_ram_gen}',
                    'reason': f'Motherboard requires {mobo_ram_gen} memory, but selected RAM is {ram_gen}.',
                    'options': compatible_rams
                })

        return jsonify({
            'status': 'success',
            'suggestions': suggestions
        })
    except Exception as e:
        app.logger.error(f"Fix compatibility error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/simulate-upgrade', methods=['POST'])
@login_required
def api_simulate_upgrade():
    """
    Analyzes an upgrade path using the upgraded AI Engine.
    """
    try:
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
                        'FANS': get_name(build.get('fans_id'))
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
                'FANS': get_name(orig.get('fans_id'))
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
            'FANS': get_name(upgrades.get('fans_id'))
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

        cpu = get_comp('cpus', data.get('cpu_id'))
        mobo = get_comp('motherboards', data.get('motherboard_id'))
        psu = get_comp('psu', data.get('psu_id'))
        gpu = get_comp('gpus', data.get('gpu_id'))
        ram = get_comp('ram', data.get('ram_id'))

        results = {
            'ram': {'status': 'Ready', 'message': 'Expansion slots available.'},
            'storage': {'status': 'Ready', 'message': 'M.2 and SATA ports detected.'},
            'gpu': {'status': 'Ready', 'message': 'PSU headroom looks sufficient.'},
            'cpu': {'status': 'Ready', 'message': 'Modern socket supports future chips.'}
        }

        # 1. RAM Check
        if mobo and ram:
            # Assume 4 slots for most, 2 for ITX
            max_slots = 4
            if 'ITX' in str(mobo.get('name', '')).upper(): max_slots = 2
            
            # Simple heuristic: if name contains "2x" or "4x"
            ram_name = str(ram.get('name', '')).upper()
            if f'{max_slots}X' in ram_name:
                results['ram'] = {'status': 'Limited', 'message': 'All memory slots occupied. Requires full replacement to upgrade.'}
        
        # 2. GPU / PSU Check
        power = run_power_analysis(data)
        if power.get('adequacy_status') != 'Safe':
            results['gpu'] = {'status': 'Limited', 'message': 'Estimated power draw is near PSU limits. PSU upgrade recommended for higher-tier GPUs.'}

        # 3. CPU Check
        if cpu:
            name = str(cpu.get('name', '')).upper()
            if 'AM4' in name or 'LGA1200' in name or 'LGA1151' in name:
                results['cpu'] = {'status': 'Limited', 'message': 'End-of-life socket. Significant upgrades require a new motherboard.'}
            elif 'AM5' in name or 'LGA1700' in name:
                results['cpu'] = {'status': 'Ready', 'message': 'Active socket. Supports latest and upcoming processor generations.'}

        return jsonify(results)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- Helpers for Robust Inference (Top Level) ---
def normalize(s):
    return str(s).strip().upper() if s else ""

def infer_cpu_socket(doc):
    import re
    # 1. Check explicit fields
    s = normalize(doc.get('socket') or doc.get('socket_cpu') or doc.get('socket_type'))
    if s: return s
    
    # 2. Infer from Microarchitecture (More reliable than Name sometimes)
    micro = normalize(doc.get('microarchitecture'))
    if micro:
        if 'ZEN' in micro: return 'AM4'
        if 'BULLDOZER' in micro or 'PILEDRIVER' in micro or 'STEAMROLLER' in micro: return 'AM3+'
        if 'EXCAVATOR' in micro: return 'FM2+'
        if 'K10' in micro or 'STARS' in micro or 'K8' in micro: return 'AM3'
        if 'BOBCAT' in micro or 'JAGUAR' in micro: return 'AM1'
        
        # Intel Micros
        if 'RAPTOR' in micro or 'ALDER' in micro: return 'LGA1700'
        if 'ROCKET' in micro or 'COMET' in micro: return 'LGA1200'
        if 'COFFEE' in micro or 'KABY' in micro or 'SKYLAKE' in micro: return 'LGA1151'
        if 'HASWELL' in micro or 'BROADWELL' in micro: return 'LGA1150'
        if 'SANDY' in micro or 'IVY' in micro: return 'LGA1155'
        if 'CORE' in micro: return 'LGA775'

    # 3. Infer from Name (Fallback)
    name = normalize(doc.get('name'))
    if 'RYZEN' in name:
        if ' 7' in name and any(x in name for x in ['7600', '7700', '7800', '7900', '7950']): return 'AM5'
        if ' 9' in name and '79' in name: return 'AM5'
        import re
        if re.search(r'RYZEN.*[789]\d\d\d', name): return 'AM5'
        return 'AM4' 
    if 'THREADRIPPER' in name: return 'sTRX4'
    if 'ATHLON' in name:
        if ' 200GE' in name or ' 3000G' in name: return 'AM4'
        if 'X4 9' in name: return 'AM4'
        if 'II' in name or 'X4 6' in name or 'X3' in name or 'X2' in name: return 'AM3'
        return 'AM4' 
    if 'FX' in name: return 'AM3+'
    if 'PHENOM' in name: return 'AM3'
    if 'A-SERIES' in name:
        if '9600' in name or '9800' in name: return 'AM4'
        return 'FM2+'
    if 'SEMPRON' in name:
        if '145' in name: return 'AM3'
    
    if 'CORE' in name:
        import re
        match = re.search(r'CORE.*-(\d{3,5})', name)
        if match:
            num_str = match.group(1)
            if len(num_str) >= 4:
                if num_str.startswith('14') or num_str.startswith('13') or num_str.startswith('12'): return 'LGA1700'
                if num_str.startswith('11') or num_str.startswith('10'): return 'LGA1200'
                if num_str.startswith('9') or num_str.startswith('8') or num_str.startswith('7') or num_str.startswith('6'): return 'LGA1151'
                if num_str.startswith('4') or num_str.startswith('5'): return 'LGA1150'
                if num_str.startswith('2') or num_str.startswith('3'): return 'LGA1155'
    
    if 'PENTIUM' in name:
        if 'GOLD' in name: return 'LGA1200' 
    
    return None

def infer_mobo_socket(doc):
    s = normalize(doc.get('socket_cpu') or doc.get('socket') or doc.get('socket_type'))
    if s: return s
    return None

def infer_ram_generation(doc, is_mobo=False):
    import re
    search_fields = []
    if is_mobo:
        search_fields = [doc.get('memory_type'), doc.get('name')]
    else:
        search_fields = [doc.get('type'), doc.get('memory_type'), doc.get('name')]
    
    for field in search_fields:
        val = normalize(field)
        if not val: continue
        match = re.search(r'DDR(\d)', val)
        if match: return f"DDR{match.group(1)}"
        if re.search(r'PC[ -]?5', val): return 'DDR5'
        if re.search(r'PC4|PC[ -]?1[79]\d{3}', val): return 'DDR4'
        if re.search(r'PC3|PC[ -]?1[02]\d{3}|PC[ -]?8500', val): return 'DDR3'
        if re.search(r'PC2|PC[ -]?6400|PC[ -]?5300|PC[ -]?4200', val): return 'DDR2'
        if re.search(r'PC1|PC[ -]?3200|PC[ -]?2700', val): return 'DDR'
        if re.search(r'AD5', val): return 'DDR5'
        if re.search(r'AD4', val): return 'DDR4'
        if re.search(r'PC2', val): return 'DDR2'
        if '1600' in val or '1333' in val: return 'DDR3'
        if '2133' in val or '2400' in val or '2666' in val or '3000' in val or '3200' in val:
            if 'DDR4' not in val: return 'DDR4'

    if is_mobo:
        sock = infer_mobo_socket(doc)
        if sock:
            if 'AM5' in sock: return 'DDR5'
            if 'AM4' in sock: return 'DDR4'
            if 'AM3' in sock: return 'DDR3'
            if 'FM2' in sock: return 'DDR3'
            if 'LGA1700' in sock: return 'DDR4'
            if 'LGA1200' in sock: return 'DDR4'
            if 'LGA1151' in sock: return 'DDR4'
            if 'LGA1150' in sock: return 'DDR3'
            if 'LGA775' in sock: return 'DDR2'
    return None

def run_validation_logic(data):
    try:
        cpu_id = data.get('cpu_id')
        mobo_id = data.get('motherboard_id')
        ram_id = data.get('ram_id')
        gpu_id = data.get('gpu_id')
        storage_id = data.get('storage_id')
        psu_id = data.get('psu_id')

        messages = []
        status = "Compatible"



        # --- Main Logic ---

        if not cpu_id or not mobo_id or not ram_id:
             return {'status': 'Incomplete Selection', 'messages': ['Please select CPU, Motherboard, and RAM to perform validation.']}

        # Helper
        def get_doc(oid):
            if not oid: return None
            # Find in components table by ID
            return db.components.find_one({'_id': ObjectId(oid)})

        cpu = get_doc(cpu_id)
        mobo = get_doc(mobo_id)
        ram = get_doc(ram_id)
        gpu = get_doc(gpu_id)
        storage = get_doc(storage_id)
        psu = get_doc(psu_id)

        if not cpu or not mobo or not ram:
            return {'status': 'Error', 'messages': ['Components not found in database']}

        # 1. CPU Socket Check
        cpu_sock = infer_cpu_socket(cpu)
        mobo_sock = infer_mobo_socket(mobo)
        
        if not cpu_sock:
            status = "Unknown"
            c_name = normalize(cpu.get('name'))
            c_micro = normalize(cpu.get('microarchitecture'))
            messages.append(f"Could not verify CPU socket. CPU: '{c_name}' (Micro: '{c_micro}')")
        elif not mobo_sock:
             status = "Unknown"
             messages.append(f"Could not verify Motherboard socket.")
        else:
            match = False
            # Handle list-like strings e.g. "AM3+/AM3"
            mobo_sockets = [s.strip() for s in mobo_sock.split('/')]
            
            if cpu_sock in mobo_sockets: match = True
            elif 'AM3+' in mobo_sockets and cpu_sock == 'AM3': match = True
            elif 'FM2+' in mobo_sockets and cpu_sock == 'FM2': match = True
            
            if not match:
                status = "Not Compatible"
                messages.append(f"Socket Mismatch: CPU ({cpu_sock}) does not fit Motherboard ({mobo_sock}).")

        # 2. RAM Generation Check
        cpu_ram_gen = infer_ram_generation(ram, is_mobo=False)
        mobo_ram_gen = infer_ram_generation(mobo, is_mobo=True)

        if cpu_ram_gen and mobo_ram_gen:
            if cpu_ram_gen != mobo_ram_gen:
                status = "Not Compatible"
                messages.append(f"RAM Type Mismatch: Motherboard requires {mobo_ram_gen} but RAM is {cpu_ram_gen}.")
        else:
            if not cpu_ram_gen: messages.append(f"Could not identify RAM generation: {ram.get('name')}")

        # 3. Storage Check
        if storage:
            # Simple check: If storage is M.2, does mobo have M.2?
            storage_name = normalize(storage.get('name'))
            storage_type = normalize(storage.get('type') or storage.get('form_factor'))
            
            is_m2 = 'M.2' in storage_name or 'NVME' in storage_name or 'M.2' in storage_type
            
            if is_m2:
                mobo_name = normalize(mobo.get('name'))
                # List of likely old chipsets without M.2 
                likely_no_m2 = any(cs in mobo_name for cs in ['H81', 'H61', 'A960', '760G', 'G41', 'P55'])
                
                if likely_no_m2:
                    messages.append("Warning: Selected NVMe/M.2 storage but Motherboard might be too old to support it native (Check specs).")
                    if status == "Compatible": status = "Borderline"

        if not messages and status == "Compatible":
            messages.append("Core components (CPU, Motherboard, RAM) are compatible!")

        return {'status': status, 'messages': messages}

    except Exception as e:
        app.logger.error(f"Validation internal error: {e}")
        return {'status': 'Error', 'messages': [str(e)]}

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
        
        # RAG Strategy: Get available components from database components table
        component_pool = {}
        try:
            component_pool['cpus'] = [c['name'] for c in db.components.find({'category': 'cpu'}, {'name': 1}).limit(20)]
            component_pool['gpus'] = [c['name'] for c in db.components.find({'category': 'gpu'}, {'name': 1}).limit(20)]
            component_pool['motherboards'] = [c['name'] for c in db.components.find({'category': 'motherboard'}, {'name': 1}).limit(15)]
            component_pool['ram'] = [c['name'] for c in db.components.find({'category': 'ram'}, {'name': 1}).limit(15)]
            component_pool['storage'] = [c['name'] for c in db.components.find({'category': 'storage'}, {'name': 1}).limit(15)]
            component_pool['psu'] = [c['name'] for c in db.components.find({'category': 'psu'}, {'name': 1}).limit(15)]
        except Exception as e:
            app.logger.warning(f"Could not fetch component pool: {e}")
            component_pool = None
        
        # Get AI recommendation
        ai_engine = get_ai_engine()
        recommendation = ai_engine.get_pc_recommendation(
            budget=budget,
            use_case=use_case,
            preferences=preferences,
            component_pool=component_pool
        )
        
        # Try to match AI recommendations to actual database components
        matched_components = {}
        if not recommendation.get('fallback', False):
            for comp_type in ['cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooler']:
                ai_suggestion = recommendation.get(comp_type, '')
                if ai_suggestion:
                    collection = comp_type + 's' if comp_type != 'psu' else 'psu'
                    if collection == 'rams':
                        collection = 'ram'
                    
                    search_terms = ai_suggestion.split()[:3]
                    regex_pattern = '|'.join(search_terms)
                    
                    try:
                        match = db[collection].find_one(
                            {'name': {'$regex': regex_pattern, '$options': 'i'}}
                        )
                        if match:
                            matched_components[comp_type + '_id'] = str(match['_id'])
                            matched_components[comp_type + '_name'] = match['name']
                    except:
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
            'fans_id': 'FANS'
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



@app.route('/api/analyze_power', methods=['POST'])
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
        # Field is usually 'tdp' (int) in W.
        if cpu:
            cpu_tdp = cpu.get('tdp')
            # Handle string '65W' etc if database has dirty data
            if isinstance(cpu_tdp, str):
                import re
                nums = re.findall(r'\d+', cpu_tdp)
                cpu_tdp = int(nums[0]) if nums else 65
            elif not isinstance(cpu_tdp, (int, float)):
                cpu_tdp = 65 # Default estimate
            
            power_breakdown['cpu'] = cpu_tdp
            total_base_watts += cpu_tdp
        else:
            power_breakdown['cpu'] = 0

        # 2. GPU Power
        # Field 'tdp' usually.
        if gpu:
            gpu_tdp = gpu.get('tdp')
            if isinstance(gpu_tdp, str):
                import re
                nums = re.findall(r'\d+', gpu_tdp)
                gpu_tdp = int(nums[0]) if nums else 50
            elif not isinstance(gpu_tdp, (int, float)):
                # Fallback: estimate based on name?
                gpu_tdp = 200 # Safe average for discrete GPU
            
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

        # 5. Fans Power
        fans = get_component_by_id(data.get('fans_id'))
        fans_power = 0
        if fans:
            # Estimate ~15W for a kit or ~5W for single
            fans_power = 15 if 'KIT' in str(fans.get('name', '')).upper() or '3-PACK' in str(fans.get('name', '')).upper() else 5
            
        power_breakdown['fans'] = fans_power
        total_base_watts += fans_power

        # 6. Motherboard (Base Overhead)
        base_overhead = 35 # 35W for mobo
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
            # Field often 'wattage' (int) or 'watts'
            w = psu.get('wattage') or psu.get('watts')
            if w:
                if isinstance(w, str):
                   import re
                   nums = re.findall(r'\d+', w)
                   w = int(nums[0]) if nums else 0
                psu_wattage = int(w)
            
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

        # Total components check
        comp_count = sum(1 for k in ['cpu_id', 'gpu_id', 'motherboard_id', 'ram_id', 'storage_id', 'psu_id', 'case_id', 'cooler_id'] if build.get(k) and build.get(k) != "None Selected")
        if comp_count >= 8:
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

        # 1. Overview & Difficulty
        comp_keys = ['cpu_id', 'gpu_id', 'motherboard_id', 'ram_id', 'storage_id', 'psu_id', 'case_id', 'cooler_id']
        comp_count = sum(1 for k in comp_keys if build.get(k) and build.get(k) != "None Selected")
        
        difficulty = calculate_build_difficulty(build)
        
        # Calculate Cost
        total_cost = 0
        cat_map = {
            'cpu': ('cpu_id', 'cpus'), 'gpu': ('gpu_id', 'gpus'), 'motherboard': ('motherboard_id', 'motherboards'),
            'ram': ('ram_id', 'ram'), 'storage': ('storage_id', 'storage'), 'psu': ('psu_id', 'psu'),
            'case': ('case_id', 'cases'), 'cooler': ('cooler_id', 'coolers')
        }
        
        for cat, (key, est_cat) in cat_map.items():
            cid = build.get(key)
            if cid and cid != "None Selected":
                comp = get_component_by_id(cid)
                if comp:
                    total_cost += get_estimated_price(comp.get('name', ''), est_cat)

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
            
        steps.append({'step': current_step, 'title': 'Final Cabling', 'text': 'Connect front panel headers, USB, and audio connectors. Organize cables with zip ties to ensure clear airflow.'})

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
                'cooler': request_data.get('cooler_id')
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
                'cooler': build.get('cooler_id')
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
                    
                    reputable_sources = ["Amazon", "Best Buy", "B&H", "Micro Center", "Newegg", "Walmart", "Target"]
                    filtered_listings = []
                    
                    for res in shopping_results:
                        source = res.get('source', '')
                        rating = res.get('rating', 0)
                        reviews = res.get('reviews', 0)
                        
                        is_genuine = any(rep.lower() in source.lower() for rep in reputable_sources)
                        
                        extracted = res.get('extracted_price')
                        if isinstance(extracted, (int, float)):
                            display_price = format_price(extracted)
                        else:
                            display_price = res.get('price', '')
                            
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
                            extracted = res.get('extracted_price')
                            if isinstance(extracted, (int, float)):
                                display_price = format_price(extracted)
                            else:
                                display_price = res.get('price', '')
                                
                            listings.append({
                                'title': res.get('title'),
                                'price': display_price,
                                'source': res.get('source'),
                                'link': res.get('link'),
                                'rating': res.get('rating', '')
                            })
                            
                except Exception as e:
                    app.logger.error(f"SerpAPI error for {query}: {e}")
            
            # Mock data if no results or no API key
            # Mock data if no results or no API key
            if not listings:
                if not serpapi_key:
                    # Generic mock for demo - use a real Google Shopping search link
                    search_path = urllib.parse.quote(query)
                    
                    # Extract price from component data similar to api_component_prices
                    comp_price = comp.get('price', comp.get('msrp'))
                    
                    # Sometimes the unified table has placeholders like 404 or 0. Fetch real price if so:
                    if not comp_price or comp_price == 404 or comp_price == 0:
                        col_map = {
                            'cpu': 'cpus', 'gpu': 'gpus', 'motherboard': 'motherboards',
                            'ram': 'ram', 'storage': 'storage', 'psu': 'psu',
                            'case': 'cases', 'cooler': 'coolers'
                        }
                        spec_col = col_map.get(category, category)
                        spec_comp = db[spec_col].find_one({'_id': ObjectId(comp_id)})
                        if spec_comp:
                            comp_price = spec_comp.get('price', spec_comp.get('msrp', comp_price))
                    
                    if isinstance(comp_price, str):
                        try:
                            # Handle string price (e.g., "$299.99", "299.99")
                            clean_price = comp_price.replace('$', '').replace(',', '')
                            if clean_price.strip():
                                comp_price = float(clean_price)
                            else:
                                comp_price = None
                        except (ValueError, AttributeError):
                            comp_price = None
                    
                    if isinstance(comp_price, (int, float)) and comp_price > 0 and comp_price != 404:
                        price_str = format_price(comp_price)
                    else:
                        price_str = "Price Unavailable"
                        
                    listings = [{
                        'title': f"Buy {comp.get('name')}",
                        'price': price_str,
                        'source': "RigMaster Database",
                        'link': f"https://www.google.com/search?q={search_path}&tbm=shop",
                        'rating': 4.8
                    }]
                else:
                    listings = [{'title': 'No genuine listing found', 'price': '', 'source': '', 'link': '#'}]

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
        # Convert budget to USD for internal processing
        user_currency = session.get('currency', 'USD')
        rate = EXCHANGE_RATES.get(user_currency, 1.0)
        budget = raw_budget / rate
        usage = data.get('usage', 'gaming')
        requirements = data.get('requirements', '')

        if budget <= 0:
            return jsonify({'status': 'error', 'message': 'Please enter a valid budget'}), 400

        # 1. Check Global AI Cache (v12 - budget matching)
        import hashlib
        cache_key = f"rec_v12_{budget}_{usage}_{hashlib.md5(requirements.encode()).hexdigest()}"
        cached = db.ai_cache.find_one({'cache_key': cache_key})
        if cached:
            app.logger.info(f"Serving cached recommendation for {cache_key}")
            return jsonify({
                'status': 'success',
                'build': cached.get('build'),
                'total_estimated_cost': cached.get('total_estimated_cost'),
                'explanation': cached.get('explanation'),
                'cached': True
            })

        # Fetch a reasonable subset from each collection, prioritizing a range of tiers
        def fetch_sample(col, limit=250):
            # Sort by price DESCENDING to get highest tiers first
            # We fetch more to allow for a wider selection in Python
            return list(db[col].find(
                {'status': {'$ne': 'Discontinued'}}, 
                {'name': 1, 'socket': 1, 'memory_type': 1, 'type': 1, 'chipset': 1, 'tdp': 1, 'wattage': 1, 'watts': 1, 'status': 1, 'price': 1}
            ).sort([('price', -1)]).limit(limit))

        sample_data = {
            'CPUs': fetch_sample('cpus'),
            'GPUs': fetch_sample('gpus'),
            'Motherboards': fetch_sample('motherboards'),
            'RAM': fetch_sample('ram'),
            'Storage': fetch_sample('storage'),
            'PSU': fetch_sample('psu'),
            'Cases': fetch_sample('cases'),
            'Coolers': fetch_sample('coolers'),
            'Monitors': fetch_sample('monitors'),
            'OperatingSystems': fetch_sample('os'),
            'Peripherals': fetch_sample('peripherals'),
            'Fans': fetch_sample('fans')
        }

        # Format component list for the AI - including logic to pick diverse tiers
        engine_pool = {}
        allowed_items = {}
        for cat_key, items in sample_data.items():
            pool_items = []
            category_allowed = []
            category = cat_key.lower()
            if category == 'rams': category = 'ram'
            
            # FIRST: Apply budget filters to the entire sample to get VALID items
            valid_items = []
            for i in items:
                p = i.get('price')
                if not p or p == 0 or str(p) == '---':
                    p = get_estimated_price(i['name'], category)
                
                try:
                    p_float = float(str(p).replace('$', '').replace(',', '').strip())
                    # Strict budget percentage caps per category
                    if category == 'gpus' and p_float > (budget * 0.55): continue
                    if category == 'cpus' and p_float > (budget * 0.35): continue
                    if category == 'motherboards' and p_float > (budget * 0.18): continue
                    if category == 'ram' and p_float > (budget * 0.15): continue
                    if category == 'psu' and p_float > (budget * 0.12): continue
                    if category == 'storage' and p_float > (budget * 0.12): continue
                    if category in ['cases', 'coolers'] and p_float > (budget * 0.12): continue
                    
                    # Store derived price back into item for easier formatting
                    i['_pool_price'] = p_float
                    valid_items.append(i)
                except: continue

            # SECOND: Pick diverse tiers from the VALID items only
            total_valid = len(valid_items)
            if total_valid > 0:
                indices = []
                if total_valid <= 35:
                    indices = range(total_valid)
                else:
                    # Pick 15 from top, 15 from middle, 5 from bottom of valid list
                    indices.extend(range(0, 15))
                    indices.extend(range(total_valid // 2 - 7, total_valid // 2 + 8))
                    indices.extend(range(total_valid - 5, total_valid))
                
                selected_indices = sorted(list(set(indices)))
                for idx in selected_indices:
                    if idx < 0 or idx >= total_valid: continue
                    i = valid_items[idx]
                    pool_items.append(f"ID:{i['_id']}|{i['name']}|Price:${i['_pool_price']}")
                    category_allowed.append(i)
            
            engine_pool[cat_key.lower()] = pool_items
            allowed_items[cat_key] = category_allowed

        # Tiered Rotation for Recommendation (Unified Engine)
        ai_engine = get_ai_engine()
        result = None
        
        recommendation = ai_engine.get_pc_recommendation(
            budget=f"${int(budget)}",
            use_case=usage,
            preferences={"requirements": requirements},
            component_pool=engine_pool
        )

        if recommendation:
            result = {
                'build': {},
                'total_estimated_cost': budget,
                'explanation': recommendation.get('reasoning', ''),
                'provider': 'RigMaster Engine'
            }

            id_mapping = {
                'cpu': 'CPU', 'gpu': 'GPU', 'motherboard': 'Motherboard', 
                'ram': 'RAM', 'storage': 'Storage', 'psu': 'PSU', 
                'case': 'Case', 'cooler': 'Cooler', 'monitor': 'Monitor', 
                'os': 'OS', 'peripherals': 'Peripherals', 'fans': 'Fans'
            }
            for ai_key, target_key in id_mapping.items():
                val = str(recommendation.get(ai_key, ''))
                import re
                id_match = re.search(r'ID:([0-9a-fA-F]{24})', val)
                if id_match:
                    result['build'][target_key] = id_match.group(1)
                else:
                    cat_name = target_key + 's' if target_key != 'PSU' else 'PSU'
                    cat_name = next((k for k in allowed_items.keys() if k.lower() == cat_name.lower()), cat_name)
                    # Use allowed_items instead of sample_data to force budget compliance
                    for item in allowed_items.get(cat_name, []):
                        if val.upper() in str(item['name']).upper() or str(item['name']).upper() in val.upper():
                            result['build'][target_key] = str(item['_id'])
                            break
                    if target_key not in result['build']: result['build'][target_key] = val

        # FINAL FAILSAFE: Heuristic Recommendation with Budget Allocation
        if not result:
            app.logger.info("Using local heuristic fallback for recommendation")
            
            # Budget allocation strategy (percentages)
            allocations = {
                'CPUs': 0.15,
                'GPUs': 0.25,
                'Motherboards': 0.10,
                'RAM': 0.08,
                'Storage': 0.08,
                'PSU': 0.06,
                'Cases': 0.05,
                'Coolers': 0.04,
                'Monitors': 0.12,
                'OperatingSystems': 0.03,
                'Peripherals': 0.02,
                'Fans': 0.02
            }
            
            fallback_build = {}
            mapping = {
                'CPUs': 'CPU', 'GPUs': 'GPU', 'Motherboards': 'Motherboard',
                'RAM': 'RAM', 'Storage': 'Storage', 'PSU': 'PSU',
                'Cases': 'Case', 'Coolers': 'Cooler', 'Monitors': 'Monitor',
                'OperatingSystems': 'OS', 'Peripherals': 'Peripherals', 'Fans': 'Fans'
            }
            
            for cat_key, items in sample_data.items():
                if items:
                    # Calculate target price for this category
                    target_price = budget * allocations.get(cat_key, 0.10)
                    
                    # Find component with price closest to target
                    active_items = [i for i in items if i.get('status') == 'Active']
                    search_pool = active_items if active_items else items
                    
                    # Select component closest to target price
                    best_match = min(search_pool, 
                                   key=lambda x: abs(x.get('price', x.get('estimated_price', 100)) - target_price))
                    
                    target_key = mapping.get(cat_key, cat_key[:-1].upper())
                    fallback_build[target_key] = str(best_match['_id'])
            
            result = {
                'build': fallback_build,
                'total_estimated_cost': budget,
                'explanation': "### RigMaster Heuristic Recommendation\nLive AI nodes are currently under heavy load. I've generated this balanced build using our local compatibility matrix based on your budget and usage requirements.",
                'provider': 'RigMaster Local'
            }

        # Helper Wrappers (Global)
        clean_name = clean_comp_name 
        est_price = get_estimated_price

        # POST-PROCESSING: Normalize and Resolve IDs to Full Objects for Frontend
        final_build = {}
        target_keys = ['CPU', 'GPU', 'Motherboard', 'RAM', 'Storage', 'PSU', 'Case', 'Cooler', 'Monitor', 'OS', 'Peripherals', 'Fans']
        col_map = {
            'CPU': 'cpus', 'GPU': 'gpus', 'Motherboard': 'motherboards',
            'RAM': 'ram', 'Storage': 'storage', 'PSU': 'psu',
            'Case': 'cases', 'Cooler': 'coolers', 'Monitor': 'monitors',
            'OS': 'os', 'Peripherals': 'peripherals', 'Fans': 'fans'
        }
        
        raw_build = result.get('build', {})
        total_calculated_cost = 0
        
        for key in target_keys:
            comp_data = None
            possible_keys = [key, key.lower(), key.upper(), key.lower() + 's', key.upper() + 's', key.replace('CPU', 'processor').lower(), key.replace('GPU', 'graphics').lower()]
            for pk in possible_keys:
                if pk in raw_build:
                    comp_data = raw_build[pk]
                    break
            
            if not comp_data:
                continue
            
            best_name = "Unknown Component"
            best_price = "---"
            comp_id = None
            
            # Extract ID aggressively - prioritize finding the hex ID
            if isinstance(comp_data, str):
                # First try: extract any 24-char hex string
                match = re.search(r'[0-9a-fA-F]{24}', comp_data)
                if match: 
                    comp_id = match.group(0)
                    # Don't trust the AI string - use placeholder until DB lookup
                    best_name = "Component"
                else:
                    # No ID found, use the string as name (fallback)
                    best_name = comp_data
            elif isinstance(comp_data, dict):
                for k_id in ['id', 'ID', '_id', 'oid']:
                    if k_id in comp_data:
                        match = re.search(r'[0-9a-fA-F]{24}', str(comp_data[k_id]))
                        if match: 
                            comp_id = match.group(0)
                            break
                # Only use dict name if no ID was found
                if not comp_id:
                    best_name = comp_data.get('name') or comp_data.get('label') or best_name
                best_price = comp_data.get('price') or comp_data.get('estimated_price') or best_price
            
            # Database lookup - ALWAYS prioritize DB name over AI string
            if comp_id:
                try:
                    from bson.objectid import ObjectId
                    col = col_map[key]
                    db_comp = db[col].find_one({'_id': ObjectId(comp_id)})
                    if db_comp:
                        # CRITICAL: Always use database name, never trust AI string
                        best_name = db_comp.get('name', 'Unknown Component')
                        price_val = db_comp.get('price') or db_comp.get('estimated_price')
                        if price_val and str(price_val) != '---' and price_val != 0:
                            best_price = price_val
                except: pass
            
            # Only clean the name if we didn't get it from database
            # (Database names are already clean)
            if best_name == "Component" or best_name == "Unknown Component":
                # Name came from AI or fallback, needs cleaning
                best_name = clean_comp_name(best_name) if best_name != "Component" else "Unknown Component"
            
            # Ensure price is valid (v9 improvement)
            price_raw = str(best_price).replace('$', '').replace(',', '').strip()
            use_heuristic = False
            if price_raw == "---" or not price_raw:
                use_heuristic = True
            else:
                try:
                    p_num = float(price_raw)
                    if p_num <= 0: use_heuristic = True
                except: use_heuristic = True
            
            if use_heuristic:
                best_price = est_price(best_name, col_map[key])

            final_build[key] = {
                'id': comp_id or "",
                'name': best_name,
                'estimated_price': str(best_price).replace('$', '').strip()
            }
            
            try:
                p_val = str(final_build[key]['estimated_price']).replace(',', '').strip()
                total_calculated_cost += float(p_val)
            except: pass
        
        result['build'] = final_build
        if total_calculated_cost > 0:
            result['total_estimated_cost'] = round(total_calculated_cost, 2)

        # FINAL BUDGET SANITY CHECK: If AI totally overshot (>10% over), 
        # warn specifically and provide a note. If over 30%, it's a failure.
        if result.get('provider') == 'RigMaster Engine' and total_calculated_cost > (budget * 1.10):
            app.logger.warning(f"AI Overshot budget ($ {total_calculated_cost} vs $ {budget}).")
            result['explanation'] = "⚠️ **Budget Warning:** Our calculation nodes indicate this specific configuration ($ {total_calculated_cost}) slightly exceeds your target budget ($ {budget}). " + result.get('explanation', '')
            
            if total_calculated_cost > (budget * 1.30):
                result['explanation'] = "⚠️ **Crucial Note:** This AI recommendation is significantly over your budget. We recommend adjusting individual parts or lowering the hardware tier for a more balanced total." + result.get('explanation', '')

        # Save to Cache
        try:
            db.ai_cache.update_one(
                {'cache_key': cache_key},
                {'$set': {
                    'cache_key': cache_key,
                    'build': result.get('build'),
                    'total_estimated_cost': result.get('total_estimated_cost'),
                    'explanation': result.get('explanation'),
                    'created_at': datetime.now(timezone.utc)
                }},
                upsert=True
            )
        except: pass

        user_currency = session.get('currency', 'USD')
        rate = EXCHANGE_RATES.get(user_currency, 1.0)
        symbol = CURRENCY_SYMBOLS.get(user_currency, '$')

        return jsonify({
            'status': 'success',
            'build': result.get('build'),
            'total_estimated_cost': result.get('total_estimated_cost'),
            'explanation': result.get('explanation'),
            'provider': result.get('provider'),
            'cached': False,
            'currency': user_currency,
            'currency_symbol': symbol,
            'exchange_rate': rate
        })

    except Exception as e:
        app.logger.error(f"Recommendation error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to generate recommendation. Please try again.'}), 500

@app.route('/ai-assistant', methods=['POST'])
@login_required
def ai_assistant():
    try:
        data = request.json
        user_message = data.get('message')
        # Current selection context
        context_ids = data.get('context', {})
        budget = data.get('budget', 'Not specified')
        usage = data.get('usage', 'Not specified')

        if not user_message:
            return jsonify({'status': 'error', 'message': 'Message is required'}), 400

        # Resolve component IDs to names for AI context
        resolved_context = {}
        col_map = {
            'cpu_id': 'cpus', 'gpu_id': 'gpus', 'motherboard_id': 'motherboards',
            'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu'
        }
        
        for key, comp_id in context_ids.items():
            if comp_id and db is not None:
                col_name = col_map.get(key)
                if col_name:
                    try:
                        comp = db[col_name].find_one({'_id': ObjectId(comp_id)})
                        if comp:
                            resolved_context[key.replace('_id', '').upper()] = comp.get('name')
                    except:
                        pass

        # Construct system prompt
        system_role = (
            "You are the RigMaster AI Assistant, an expert in computer hardware and PC building. "
            "Help the user with their build questions, explain component choices, compatibility, and upgrades. "
            "Be clear, educational, and helpful. Do not force decisions. Do not hallucinate hardware. "
            "Current selection context: " + (", ".join([f"{k}: {v}" for k, v in resolved_context.items()]) if resolved_context else "No components selected yet.")
        )

        # AI API configuration
        # Use unified AI Engine for chat
        ai_engine = get_ai_engine()
        
        ai_response = ai_engine.generate_chat_response(system_role, user_message)
        provider_used = 'RigMaster AI Assistant'

        if not ai_response:
             return jsonify({'status': 'error', 'message': 'AI services are currently overloaded. Please try again in a few minutes.'}), 503

        return jsonify({
            'status': 'success',
            'response': ai_response,
            'provider': provider_used
        })

    except Exception as e:
        app.logger.error(f"AI Assistant endpoint error: {e}")
        return jsonify({'status': 'error', 'message': 'AI assistant temporarily unavailable'}), 500

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
@app.route('/ai-assistant', methods=['POST'])
@login_required
def ai_assistant_chat():
    try:
        data = request.json
        message = data.get('message')
        provider = data.get('provider', 'Groq')
        context = data.get('context', {})
        
        # Construct Contextual Prompt
        system_instruction = "You are RigMaster Nexus, an elite PC building expert. "
        if context:
            system_instruction += f"The user is currently viewing: {context}. "
        system_instruction += "Provide concise, accurate technical advice. Formatting: Use Markdown."

        response_text = "I am currently calibrating. Please try again."

        # ---------------------------------------------------------
        # PROVIDER HANDLERS
        # ---------------------------------------------------------
        if provider == 'Groq':
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key: raise Exception("Groq configuration missing")
            
            payload = {
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": message}
                ],
                "model": "llama3-8b-8192",
                "temperature": 0.6
            }
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if resp.status_code != 200: 
                app.logger.error(f"Groq API Error: {resp.text}")
                return jsonify({'status': 'error', 'message': "Groq Overloaded"}), 503
            response_text = resp.json()['choices'][0]['message']['content']

        elif provider == 'Gemini':
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key: raise Exception("Gemini configuration missing")
            
            # Gemini REST API (Simplified)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{
                    "parts": [{"text": f"{system_instruction}\n\nUser: {message}"}]
                }]
            }
            resp = requests.post(url, json=payload)
            if resp.status_code != 200: return jsonify({'status': 'error', 'message': "Gemini Busy"}), 503
            response_text = resp.json()['candidates'][0]['content']['parts'][0]['text']

        elif provider == 'DeepSeek':
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if not api_key: raise Exception("DeepSeek configuration missing")
            
            resp = requests.post(
                "https://api.deepseek.com/chat/completions",
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": message}
                    ]
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if resp.status_code != 200: return jsonify({'status': 'error', 'message': "DeepSeek Busy"}), 503
            response_text = resp.json()['choices'][0]['message']['content']

        elif provider == 'Mistral':
            api_key = os.getenv('MISTRAL_API_KEY')
            if not api_key: raise Exception("Mistral configuration missing")
            
            resp = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                json={
                    "model": "mistral-small-latest",
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": message}
                    ]
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            if resp.status_code != 200: return jsonify({'status': 'error', 'message': "Mistral Busy"}), 503
            response_text = resp.json()['choices'][0]['message']['content']

        elif provider == 'HuggingFace':
            api_key = os.getenv('HUGGINGFACE_API_KEY')
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            
            # Reliable Free Tier Strategy: Cycle through high-availability models
            models = [
                "HuggingFaceH4/zephyr-7b-beta",
                "microsoft/Phi-3-mini-4k-instruct",
                "google/gemma-1.1-7b-it"
            ]
            
            last_error = "No models available"
            response_text = None
            
            for model in models:
                try:
                    # Adjust prompt based on model family (simplified for broad compatibility)
                    if "zephyr" in model:
                        prompt = f"<|system|>\n{system_instruction}</s>\n<|user|>\n{message}</s>\n<|assistant|>"
                    elif "Phi" in model:
                        prompt = f"<|user|>\n{system_instruction}\n\n{message}<|end|>\n<|assistant|>"
                    else: # Gemma / General
                        prompt = f"<start_of_turn>user\n{system_instruction}\n\n{message}<end_of_turn>\n<start_of_turn>model\n"
                    
                    # API endpoint updated to new router URL
                    api_url = f"https://router.huggingface.co/models/{model}"
                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 512, 
                            "temperature": 0.7, 
                            "return_full_text": False
                        }
                    }
                    
                    # app.logger.info(f"Attempting HF Model: {model}")
                    resp = requests.post(api_url, headers=headers, json=payload, timeout=25)
                    
                    if resp.status_code == 200:
                        result = resp.json()
                        if isinstance(result, list) and 'generated_text' in result[0]:
                            response_text = result[0]['generated_text'].strip()
                            # Clean up if model leaked prompt
                            if "<|assistant|>" in response_text: response_text = response_text.split("<|assistant|>")[-1].strip()
                            break # Success!
                    
                    elif resp.status_code == 503:
                        last_error = f"{model} is loading (503)"
                        continue # Try next
                    else:
                        last_error = f"{model} error {resp.status_code}"
                        
                except Exception as e:
                    last_error = f"{model} failed: {str(e)}"
                    continue

            if response_text:
                # Success
                pass # Already set
            else:
                 return jsonify({'status': 'error', 'message': f"HF All Busy: {last_error}"}), 503

        elif provider == 'Ollama':
            # Assumes Ollama is running on the SERVER (localhost:11434)
            try:
                resp = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": f"{system_instruction}\n\nUser: {message}",
                        "stream": False
                    },
                    timeout=5
                )
                if resp.status_code != 200: raise Exception("Ollama Error")
                response_text = resp.json()['response']
            except:
                return jsonify({'status': 'error', 'message': "Local AI Offline"}), 503
            
        else:
            return jsonify({'status': 'error', 'message': "Unknown Provider"}), 400

        return jsonify({'status': 'success', 'response': response_text})

    except Exception as e:
        app.logger.error(f"Nexus AI Error ({provider}): {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
            'case': 'cases', 'cooler': 'coolers'
        }
        
        warranty_terms = {
            'cpu': 3, 'gpu': 3, 'motherboard': 3, 'ram': 10,
            'storage': 5, 'psu': 7, 'case': 2, 'cooler': 3
        }

        col_map = {
            'cpu_id': 'cpu', 'gpu_id': 'gpu', 'motherboard_id': 'motherboard',
            'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
            'case_id': 'case', 'cooler_id': 'cooler'
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
                    price = get_estimated_price(name, price_cat_map.get(cat, cat))
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
            'case_id': 'case', 'cooler_id': 'cooler'
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
            f"Respond ONLY in JSON with this exact schema: {json.dumps(schema)}"
        )
        user_content = "Build Components:\n" + "\n".join([f"- {c['category']}: {c['name']} (Status: {c['status']})" for c in component_data])

        # 1. Check Cache (v9 for final stability)
        cache_key = f"resale_v9_{build_id}"
        cached = db.ai_cache.find_one({'cache_key': cache_key})
        if cached:
            return jsonify({'status': 'success', 'prediction': cached.get('prediction'), 'cached': True})

        # 2. Advanced Heuristic Engine (Local Fallback)
        def get_heuristic_prediction(comps):
            total_val = 0
            results = []
            for c in comps:
                name = (c.get('name') or 'Unknown Component').upper()
                val = 12.0 # Minimum symbolic floor
                
                # Intelligent Hardware Tiers
                if '4090' in name or '4080' in name: val = 950
                elif '3080' in name or '3090' in name: val = 420
                elif '7900' in name or '7800' in name: val = 350
                elif '3070' in name or '4070' in name: val = 300
                elif '3060' in name or '4060' in name: val = 180
                elif 'RYZEN 9' in name or 'CORE I9' in name: val = 280
                elif 'RYZEN 7' in name or 'CORE I7' in name: val = 160
                elif 'RYZEN 5' in name or 'CORE I5' in name: val = 90
                elif 'RYZEN 3' in name or 'CORE I3' in name: val = 45
                elif '880G' in name or 'GXH' in name: val = 35 
                elif '7850K' in name or 'A10-' in name: val = 22
                elif 'AD2U' in name or 'DDR2' in name: val = 4
                elif 'XPG' in name or 'CRUISER' in name: val = 40
                elif 'SSD' in name or 'ADATA' in name: val = 15
                elif 'ALPINE' in name or 'COOLER' in name: val = 10
                
                total_val += val
                results.append({
                    "category": c.get('category', 'Hardware'),
                    "name": c.get('name', 'Unknown Part'),
                    "status": c.get('status', 'Active'),
                    "estimated_resale": format_price(val)
                })
            
            # Add System synergy premium (15%)
            final_total = total_val * 1.15
            
            return {
                "total_system_value": format_price(final_total),
                "market_advice": "### System Appraisal: RigMaster Expert Engine\nLive AI appraisal nodes are currently under heavy load. This valuation was generated using our **Local Market Heuristic Engine**, which analyzes components against verified hardware price index tiers.\n\n*   **Selling Strategy:** Focus on listing this as a 'Complete Ready-to-Work/Play' system for local cash buyers.\n*   **Platform Tip:** Facebook Marketplace or local enthusiast forums will yield the best margins for this specific hardware tier.",
                "components": results,
                "provider": "RigMaster Heuristic 2.0"
            }


        # Use unified AI Engine for resale prediction
        ai_engine = get_ai_engine()
        p_data = ai_engine.get_resale_prediction(component_data)
        
        if p_data and p_data.get('total_system_value') and p_data.get('total_system_value') != 'N/A':
            # Convert AI results from USD to local
            user_currency = session.get('currency', 'USD')
            if user_currency != 'USD':
                rate = EXCHANGE_RATES.get(user_currency, 1.0)
                
                # Convert total
                try:
                    total_v = float(p_data['total_system_value'].replace('$', '').replace(',', '').replace('USD', '').strip())
                    p_data['total_system_value'] = format_price(total_v)
                except: pass
                
                # Convert components
                for c in p_data.get('components', []):
                    try:
                        cv = float(c['estimated_resale'].replace('$', '').replace(',', '').replace('USD', '').strip())
                        c['estimated_resale'] = format_price(cv)
                    except: pass

            prediction_data = p_data
            prediction_data['provider'] = 'RigMaster AI'

        # FINAL FAILSAFE: Always work
        if not prediction_data:
            prediction_data = get_heuristic_prediction(component_data)

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
            'case_id': 'case', 'cooler_id': 'cooler'
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
        'peripherals': db.components.count_documents({'category': 'peripherals'})
    }
    stats['total_components'] = sum([
        stats['cpus'], stats['gpus'], stats['motherboards'], stats['ram'], 
        stats['storage'], stats['psu'], stats['cases'], stats['coolers'],
        stats['fans'], stats['os'], stats['monitors'], stats['peripherals']
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
        'preferred_ai_provider': get_site_setting('preferred_ai_provider', 'auto')
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
    try:
        db = get_db()
        if db is not None:
            db.shopping_cache.delete_many({})
            db.ai_cache.delete_many({})
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Database disconnected'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/ai-analytics')
@admin_required
def admin_ai_analytics():
    """View AI usage analytics"""
    try:
        # AI cache stats
        ai_stats = {
            'total_requests': db.ai_cache.count_documents({}) if 'ai_cache' in db.list_collection_names() else 0,
            'cached_hits': db.ai_cache.count_documents({'cached': True}) if 'ai_cache' in db.list_collection_names() else 0
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

        # Get system health for provider statuses
        health = {
            'ai_providers': {}
        }
        try:
            from ai_engine import get_ai_engine
            ai_engine = get_ai_engine()
            health['ai_providers'] = {
                'groq': 'Available' if ai_engine.groq_key else 'Not configured',
                'mistral': 'Available' if ai_engine.mistral_key else 'Not configured',
                'gemini': 'Available' if ai_engine.gemini_key else 'Not configured',
                'deepseek': 'Available' if ai_engine.deepseek_key else 'Not configured',
                'hf': 'Available' if (ai_engine.hf_key and ai_engine.is_hf_installed) else ('Missing library' if not ai_engine.is_hf_installed else 'Not configured'),
                'ollama': 'Checking...'
            }
            import requests
            try:
                resp = requests.get('http://localhost:11434/api/tags', timeout=1)
                health['ai_providers']['ollama'] = 'Running' if resp.status_code == 200 else 'Not running'
            except:
                health['ai_providers']['ollama'] = 'Not running'
        except:
            pass

        custom_api_keys = get_site_setting('api_keys', {})

        return render_template('admin/ai_analytics.html', 
                             stats=ai_stats,
                             recent_requests=recent_requests,
                             provider_stats=provider_stats,
                             health=health,
                             custom_keys=custom_api_keys)
    except Exception as e:
        app.logger.error(f"AI analytics error: {e}")
        return f"Error: {e}", 500

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
            health['ai_providers'] = {
                'groq': 'Available' if ai_engine.groq_key else 'Not configured',
                'mistral': 'Available' if ai_engine.mistral_key else 'Not configured',
                'gemini': 'Available' if ai_engine.gemini_key else 'Not configured',
                'deepseek': 'Available' if ai_engine.deepseek_key else 'Not configured',
                'hf': 'Available' if (ai_engine.hf_key and ai_engine.is_hf_installed) else ('Missing library' if not ai_engine.is_hf_installed else 'Not configured'),
                'ollama': 'Checking...'
            }
            
            # Check Ollama
            import requests
            try:
                resp = requests.get('http://localhost:11434/api/tags', timeout=2)
                health['ai_providers']['ollama'] = 'Running' if resp.status_code == 200 else 'Not running'
            except:
                health['ai_providers']['ollama'] = 'Not running'
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

        # Python version and platform
        import sys
        import platform
        server_info = {
            'python_version': sys.version,
            'platform': platform.platform(),
            'processor': platform.processor()
        }
        
        return render_template('admin/system_health.html', 
                             health=health, 
                             db_stats=db_stats,
                             server_info=server_info,
                             python_version=sys.version.split(' ')[0])
    except Exception as e:
        app.logger.error(f"System health error: {e}")
        return f"Error: {e}", 500

# Export routes
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


@app.route('/api/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings_api():
    """Get or update global site settings"""
    if request.method == 'GET':
        settings = list(db.settings.find())
        return jsonify({s['key']: s['value'] for s in settings})
    
    try:
        data = request.json
        for key, value in data.items():
            db.settings.update_one({'key': key}, {'$set': {'value': value}}, upsert=True)
        app.logger.info(f"Admin {session.get('username')} updated settings: {data}")
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/admin/clear-cache', methods=['POST'])
@admin_required
def admin_clear_cache():
    """Clear AI cache in emergency"""
    try:
        if 'ai_cache' in db.list_collection_names():
            db.ai_cache.delete_many({})
        app.logger.info(f"Admin {session.get('username')} cleared AI cache")
        return jsonify({'status': 'success'})
    except Exception as e:
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
        'cases': 'case', 'coolers': 'cooler'
    }
    
    if category not in cat_map:
        return jsonify({'status': 'error', 'message': 'Invalid category'}), 400
    
    target_cat = cat_map[category]
    query = {'category': target_cat}
    
    status_filter = request.args.get('status')
    if status_filter:
        query['status'] = status_filter

    items = list(db.components.find(query))
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
        'cases': 'case', 'coolers': 'cooler'
    }
    target_cat = cat_map.get(category)
    if not target_cat:
        return jsonify({'status': 'error', 'message': 'Invalid category'}), 400

    data = request.json
    if not data or 'name' not in data:
        return jsonify({'status': 'error', 'message': 'Name is required'}), 400
    
    # Check for duplicates
    if db.components.find_one({'category': target_cat, 'name': data['name']}):
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
        collections = ['cpus', 'gpus', 'motherboards', 'ram', 'storage', 'psu', 'cases', 'coolers']
        
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
def advanced_analysis():
    return render_template('advanced_analysis.html')

@app.route('/api/bottleneck-analyzer', methods=['POST'])
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
            'fans': data.get('fans_id')
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
                        'os': 'os', 'peripherals': 'peripherals', 'fans': 'fans'
                    }
                    col = col_map.get(category, category)
                    comp = db[col].find_one({'_id': ObjectId(comp_id)})
                
                if comp:
                    # Extract price from component data
                    price = comp.get('price', comp.get('msrp', 0))
                    
                    # Handle price as string (e.g., "$299.99")
                    if isinstance(price, str):
                        price = float(price.replace('$', '').replace(',', ''))
                    
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
                        # No price data available
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
        
        return render_template('group_builder.html', 
                               saved_builds=saved_builds, 
                               group_builds=group_builds)
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
            
            # Estimate price if not present
            price = comp.get('price')
            if not price:
                price = get_estimated_price(comp.get('name'), category)
            elif isinstance(price, str):
                try:
                    price = float(price.replace('$', '').replace(',', ''))
                except:
                    price = get_estimated_price(comp.get('name'), category)
            
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
        
        # Mapping build keys to categories
        key_map = {
            'cpu_id': 'cpu', 'gpu_id': 'gpu', 'motherboard_id': 'motherboard',
            'ram_id': 'ram', 'storage_id': 'storage', 'psu_id': 'psu',
            'case_id': 'case', 'cooler_id': 'cooler'
        }
        
        for key, cat in key_map.items():
            comp_id = base_build.get(key)
            if comp_id:
                details = get_comp_details(comp_id, cat)
                if details:
                    components[cat] = details
                    total_unit_cost += details['price']
                    
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

@app.route('/api/export-group-build/<plan_id>', endpoint='api_export_group_build')
@login_required
def api_export_group_build(plan_id):
    """Export the group build manifest as a CSV file"""
    try:
        user_id = session.get('user_id')
        plan = db.group_builds.find_one({
            '_id': ObjectId(plan_id),
            'user_id': user_id
        })
        
        if not plan:
            return "Project plan not found", 404
            
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header Info
        writer.writerow(['RIGMASTER AI - DEPLOYMENT MANIFEST'])
        writer.writerow(['Project Ref', f"GRP-{plan_id[-6:]}"])
        writer.writerow(['Base Configuration', plan.get('base_build_name', 'Standard Rig')])
        writer.writerow(['Quantity', plan.get('quantity', 0)])
        writer.writerow(['Unit Cost', format_price(plan.get('unit_cost', 0))])
        writer.writerow(['Total Project Budget', format_price(plan.get('total_cost', 0))])
        writer.writerow(['Date Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        # Component List
        writer.writerow(['COMPONENT', 'CATEGORY', 'UNIT PRICE', 'TOTAL REQUIRED', 'LINE TOTAL'])
        
        components = plan.get('components', {})
        qty = plan.get('quantity', 0)
        
        for cat, details in components.items():
            price = details.get('price', 0)
            writer.writerow([
                details.get('name', 'Unknown'),
                cat.upper(),
                format_price(price),
                qty,
                format_price(price * qty)
            ])
            
        writer.writerow([])
        writer.writerow(['', '', '', 'GRAND TOTAL', format_price(plan.get('total_cost', 0))])
        
        output.seek(0)
        csv_data = output.getvalue()
        
        return send_file(
            io.BytesIO(csv_data.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"deployment_manifest_{plan_id[:8]}.csv"
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
    return jsonify({'success': True, 'message': 'Session revoked successfully'})

# ============================================================================

# USER PROFILE PAGE
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
        ).sort('created_at', -1).limit(5))
        
        return render_template(
            'profile.html',
            user=user,
            build_count=build_count,
            group_count=group_count,
            recent_builds=recent_builds
        )
    except Exception as e:
        app.logger.error(f"Profile error: {e}")
        return render_template('error.html', message="Could not load profile"), 500

# ============================================================================



# ============================================================================
# CHATBOT ROUTES
# ============================================================================



@app.route('/ai-assistant', methods=['POST'])
@login_required
def rigmaster_chat_endpoint():
    """Endpoint for AI Assistant (Smart AI)"""
    try:
        data = request.json
        user_message = data.get('message')
        context = data.get('context', {})
        
        if not user_message:
            return jsonify({'status': 'error', 'message': 'No message provided'}), 400
            
        system_role = (
            "You are RigMaster Nexus, an advanced AI assistant for PC building. "
            "Help the user with complex hardware questions, compatibility, troubleshooting, and advice. "
            "Be concise, use Markdown. If asked for recommendations, ask about budget/use-case first."
        )
        
        if context:
            system_role += f"\n\nContext: {json.dumps(context)}"
            
        ai_engine = get_ai_engine() 
        response_text = ai_engine.generate_chat_response(system_role, user_message)
        
        if response_text:
            return jsonify({'status': 'success', 'response': response_text})
        else:
            return jsonify({'status': 'error', 'message': 'AI failed to respond'}), 500
            
    except Exception as e:
        app.logger.error(f"AI Assistant Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    # On Windows, use_reloader=True can sometimes cause "OSError: [WinError 10038] An operation was attempted on something that is not a socket"
    # Disabling the reloader is a common workaround for this development server stability issue.
    # Port changed to 5001 to avoid conflicts with Windows built-in services like AirPlay.
    print("\n" + "*" * 50)
    print("  RIGMASTER IS LIVE")
    print("  Open your browser at: http://127.0.0.1:5001")
    print("*" * 50 + "\n")
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False, threaded=True)
