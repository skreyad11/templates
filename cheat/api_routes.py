# api_routes.py - API Endpoints for AJAX

from flask import Blueprint, request, jsonify, session
from database import Database
import json
from datetime import datetime

api_bp = Blueprint('api', __name__)
db = Database()

# ---- ADMIN API ----
@api_bp.route('/admin/keys/create', methods=['POST'])
def create_key():
    """Create a new license key"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    tier = data.get('tier', 'standard')
    expiry_days = int(data.get('expiry_days', 30))
    max_users = int(data.get('max_users', 1))
    notes = data.get('notes', '')
    
    license_key = db.generate_license(
        tier=tier,
        expiry_days=expiry_days,
        max_users=max_users,
        created_by=session.get('admin_id'),
        notes=notes
    )
    
    return jsonify({
        "success": True,
        "license_key": license_key,
        "message": "License created successfully"
    })

@api_bp.route('/admin/keys/delete/<license_key>', methods=['DELETE'])
def delete_key(license_key):
    """Delete a license key"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    success = db.delete_license(license_key)
    return jsonify({
        "success": success,
        "message": "License deleted" if success else "License not found"
    })

@api_bp.route('/admin/keys/update/<license_key>', methods=['PUT'])
def update_key(license_key):
    """Update license properties"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    success = db.update_license(license_key, **data)
    return jsonify({
        "success": success,
        "message": "License updated" if success else "Update failed"
    })

@api_bp.route('/admin/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    stats = db.get_dashboard_stats()
    return jsonify(stats)

# ---- USER API ----
@api_bp.route('/user/features/toggle', methods=['POST'])
def toggle_feature():
    """Toggle a feature for the current user"""
    if not session.get('user_activated'):
        return jsonify({"error": "Not activated"}), 401
    
    data = request.json
    feature_name = data.get('feature')
    enabled = data.get('enabled', True)
    license_key = session.get('license_key')
    
    success = db.set_feature_toggle(license_key, feature_name, enabled)
    return jsonify({
        "success": success,
        "feature": feature_name,
        "enabled": enabled
    })

@api_bp.route('/user/features', methods=['GET'])
def get_features():
    """Get all features for current user"""
    if not session.get('user_activated'):
        return jsonify({"error": "Not activated"}), 401
    
    features = db.get_feature_toggles(session.get('license_key'))
    return jsonify(features)

@api_bp.route('/user/validate', methods=['POST'])
def validate_license():
    """Validate a license key"""
    data = request.json
    license_key = data.get('license_key', '').strip()
    device_id = data.get('device_id', '')
    
    license_data = db.validate_license(license_key)
    if license_data:
        db.register_device(license_key, device_id, request.remote_addr)
        return jsonify({
            "valid": True,
            "tier": license_data['tier'],
            "expiry": license_data['expiry_date']
        })
    else:
        return jsonify({"valid": False, "message": "Invalid or expired license"})