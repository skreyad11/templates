# admin_routes.py - Admin Panel Routes

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from database import Database
import json

admin_bp = Blueprint('admin', __name__)
db = Database()

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = db.verify_user(username, password)
        if user and user['role'] == 'admin':
            session['admin_logged_in'] = True
            session['admin_id'] = user['id']
            session['admin_username'] = user['username']
            return redirect(url_for('admin.dashboard'))
        else:
            return render_template('admin/login.html', error="Invalid credentials")
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.clear()
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with stats"""
    stats = db.get_dashboard_stats()
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/keys')
@admin_required
def keys():
    """License key management"""
    licenses = db.get_all_licenses()
    return render_template('admin/keys.html', licenses=licenses)

@admin_bp.route('/users')
@admin_required
def users():
    """User management"""
    users = db.get_all_activated_users()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/logs')
@admin_required
def logs():
    """Proxy logs"""
    logs = db.get_proxy_logs(limit=200)
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/settings')
@admin_required
def settings():
    """System settings"""
    settings = db.get_settings()
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/features')
@admin_required
def features():
    """Feature management"""
    features = db.get_all_features()
    return render_template('admin/features.html', features=features)