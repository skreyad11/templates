#!/usr/bin/env python3
# app.py - Main Flask Application Entry Point

from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask_cors import CORS
import secrets
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FFProxy')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)

# Import blueprints after app creation to avoid circular imports
from admin_routes import admin_bp
from user_routes import user_bp
from api_routes import api_bp
from proxy_server import proxy_bp

# Register blueprints
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(proxy_bp, url_prefix='/proxy')

# Database initialization
from database import Database
db = Database()

@app.route('/')
def home():
    """Landing page - redirect based on session"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
    elif session.get('user_activated'):
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('user.index'))

@app.route('/health')
def health():
    """Health check endpoint for uptime monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'OB54'
    })

@app.route('/get-config/<license_key>')
def get_config(license_key):
    """Generate localconfig.json for users"""
    from database import Database
    db = Database()
    
    # Validate license
    license_data = db.validate_license(license_key)
    
    if not license_data:
        return jsonify({"error": "Invalid license key"}), 401
    
    # Get features for this license
    features = db.get_feature_toggles(license_key)
    
    # Build the config
    config = {
        "resetGuest": True,
        "verAddr": f"{request.host_url}proxy/",
        "proxy": {
            "enabled": True,
            "host": request.host.split(':')[0],
            "port": 5000,
            "ssl": request.is_secure
        },
        "features": features,
        "license": license_key,
        "timestamp": datetime.now().isoformat(),
        "version": "OB54"
    }
    
    # Return as downloadable JSON
    response = jsonify(config)
    response.headers['Content-Disposition'] = 'attachment; filename=localconfig.json'
    return response

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)