# user_routes.py - User-Facing Website Routes

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import Database
import json

user_bp = Blueprint('user', __name__)
db = Database()

@user_bp.route('/')
def index():
    """User landing page"""
    return render_template('user/index.html')

@user_bp.route('/activate', methods=['GET', 'POST'])
def activate():
    """License activation page"""
    if request.method == 'POST':
        license_key = request.form.get('license_key', '').strip()
        device_id = request.form.get('device_id', '')
        
        license_data = db.validate_license(license_key)
        if license_data:
            session['user_activated'] = True
            session['license_key'] = license_key
            session['tier'] = license_data['tier']
            session['expiry'] = license_data['expiry_date']
            
            db.register_device(license_key, device_id, request.remote_addr)
            return redirect(url_for('user.dashboard'))
        else:
            return render_template('user/activate.html', error="Invalid or expired license")
    
    return render_template('user/activate.html')

@user_bp.route('/dashboard')
def dashboard():
    """User dashboard"""
    if not session.get('user_activated'):
        return redirect(url_for('user.activate'))
    
    features = db.get_feature_toggles(session.get('license_key'))
    return render_template('user/dashboard.html', features=features, license_key=session.get('license_key'))

@user_bp.route('/logout')
def logout():
    """User logout"""
    session.pop('user_activated', None)
    session.pop('license_key', None)
    return redirect(url_for('user.index'))