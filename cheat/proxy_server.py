# proxy_server.py - MITM Proxy Engine

from flask import Blueprint, request, jsonify, Response
import requests
import json
import time
import logging
from datetime import datetime
from database import Database
from packet_modifier import PacketModifier
from garena_crypto import GarenaCrypto
from ob54_endpoints import GARENA_HOSTS, OB54_HEADERS, OB54_SPOOF_HEADERS

proxy_bp = Blueprint('proxy', __name__)
db = Database()
modifier = PacketModifier()
crypto = GarenaCrypto()

logger = logging.getLogger('FFProxy')

# Rate limiting
RATE_LIMIT = {}
MAX_REQUESTS_PER_MINUTE = 100

@proxy_bp.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@proxy_bp.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_handler(path):
    """Main proxy handler - catches ALL requests to /proxy/"""
    
    # Get license key
    license_key = request.headers.get('X-License-Key') or request.args.get('key')
    
    # Validate license
    if not validate_license(license_key):
        return jsonify({"error": "Invalid or expired license"}), 401
    
    # Rate limiting
    if not check_rate_limit(license_key):
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    # Build target URL
    target_url = build_target_url(path)
    
    # Prepare request
    headers = build_request_headers(request)
    data = request.get_data()
    
    start_time = time.time()
    
    try:
        # Forward to Garena
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=data,
            params=request.args,
            timeout=10
        )
        
        # Process response
        response_data = process_response(resp, license_key, path)
        
        # Log to database
        response_time = int((time.time() - start_time) * 1000)
        db.log_proxy_request(
            license_key=license_key,
            endpoint=path,
            method=request.method,
            status_code=resp.status_code,
            response_time=response_time,
            ip=request.remote_addr
        )
        
        # Return modified response
        return Response(
            response=json.dumps(response_data) if isinstance(response_data, dict) else response_data,
            status=resp.status_code,
            headers=dict(resp.headers)
        )
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Garena server timeout"}), 504
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return jsonify({"error": str(e)}), 500

def validate_license(license_key):
    """Validate license key"""
    if not license_key:
        return False
    license_data = db.validate_license(license_key)
    return license_data is not None

def check_rate_limit(license_key):
    """Check rate limit"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    key = f"{license_key}:{now}"
    
    if key not in RATE_LIMIT:
        RATE_LIMIT[key] = 0
    
    RATE_LIMIT[key] += 1
    
    # Clean old entries
    if len(RATE_LIMIT) > 1000:
        for k in list(RATE_LIMIT.keys()):
            if k.split(':')[0] != license_key:
                del RATE_LIMIT[k]
    
    return RATE_LIMIT[key] <= MAX_REQUESTS_PER_MINUTE

def build_target_url(path):
    """Build Garena target URL"""
    if path.startswith('verify') or path.startswith('auth'):
        return f"https://verify.garena.com/{path}"
    return f"https://api.garena.com/{path}"

def build_request_headers(request):
    """Build request headers with spoofing"""
    headers = {}
    
    for key, value in request.headers.items():
        if key.lower() not in ['host', 'content-length', 'connection']:
            headers[key] = value
    
    # Add spoof headers
    for key, value in OB54_SPOOF_HEADERS.items():
        if key not in headers:
            headers[key] = value
    
    return headers

def process_response(response, license_key, endpoint):
    """Process and modify response"""
    try:
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            try:
                data = response.json()
            except:
                data = {"raw": response.text}
            
            # Get features for this license
            features = db.get_feature_toggles(license_key)
            
            # Modify packet
            modified = modifier.modify_packet(data, endpoint, features)
            return modified
        
        return response.text
        
    except Exception as e:
        logger.error(f"Response processing error: {e}")
        return response.text