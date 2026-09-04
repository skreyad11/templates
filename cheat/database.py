# database.py - SQLite Database Layer

import sqlite3
import json
import hashlib
import random
import string
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = "proxy_hack.db"

class Database:
    def __init__(self):
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database with all tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Licenses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    tier TEXT NOT NULL,
                    expiry_date TIMESTAMP NOT NULL,
                    max_users INTEGER DEFAULT 1,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    notes TEXT
                )
            ''')
            
            # Devices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activated_devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT NOT NULL,
                    device_id TEXT,
                    ip_address TEXT,
                    first_activated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_requests INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Features table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feature_toggles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT,
                    feature_name TEXT NOT NULL,
                    is_enabled INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(license_key, feature_name)
                )
            ''')
            
            # Logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proxy_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT,
                    endpoint TEXT,
                    method TEXT,
                    status_code INTEGER,
                    response_time INTEGER,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create default admin
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                password_hash = hashlib.sha256(b"admin123").hexdigest()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    ("admin", password_hash, "admin")
                )
            
            # Default settings
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) VALUES
                    ('proxy_port', '5000'),
                    ('enable_logging', '1'),
                    ('rate_limit', '100'),
                    ('maintenance_mode', '0')
            ''')
            
            conn.commit()
    
    def verify_user(self, username, password):
        """Verify admin credentials"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
                (username, password_hash)
            )
            user = cursor.fetchone()
            if user:
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user['id'],)
                )
                conn.commit()
                return dict(user)
        return None
    
    def generate_license(self, tier, expiry_days, max_users=1, created_by=None, notes=""):
        """Generate new license key"""
        prefix_map = {'trial': 'TRIAL', 'standard': 'PRO', 'premium': 'PREMIUM', 'lifetime': 'LIFE'}
        prefix = prefix_map.get(tier, 'KEY')
        
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        formatted_key = f"{prefix}-{random_part[:4]}-{random_part[4:8]}-{random_part[8:12]}"
        
        expiry_date = datetime.now() + timedelta(days=expiry_days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO licenses (key, tier, expiry_date, max_users, created_by, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (formatted_key, tier, expiry_date.isoformat(), max_users, created_by, notes)
            )
            conn.commit()
            
            # Default features
            default_features = ['hs_neck', 'hs_chest', 'zigzag', 'backjump', 'noswap', 'bypass', 'speed_hack', 'high_jump']
            for feature in default_features:
                cursor.execute(
                    "INSERT INTO feature_toggles (license_key, feature_name, is_enabled) VALUES (?, ?, 1)",
                    (formatted_key, feature)
                )
            conn.commit()
            
            return formatted_key
    
    def validate_license(self, license_key):
        """Validate a license key"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM licenses WHERE key = ? AND is_active = 1 AND expiry_date > datetime('now')",
                (license_key,)
            )
            license_data = cursor.fetchone()
            return dict(license_data) if license_data else None
    
    def get_all_licenses(self):
        """Get all licenses with usage stats"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.*, COUNT(DISTINCT a.id) as active_users
                FROM licenses l
                LEFT JOIN activated_devices a ON l.key = a.license_key AND a.is_active = 1
                GROUP BY l.id
                ORDER BY l.created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_license(self, license_key):
        """Soft delete license"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE licenses SET is_active = 0 WHERE key = ?", (license_key,))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_license(self, license_key, **kwargs):
        """Update license properties"""
        allowed = ['tier', 'expiry_date', 'max_users', 'notes']
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [license_key]
            cursor.execute(f"UPDATE licenses SET {set_clause} WHERE key = ?", values)
            conn.commit()
            return cursor.rowcount > 0
    
    def register_device(self, license_key, device_id, ip_address):
        """Register a device"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM activated_devices WHERE license_key = ? AND device_id = ?",
                (license_key, device_id)
            )
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute(
                    "UPDATE activated_devices SET last_active = CURRENT_TIMESTAMP, ip_address = ? WHERE id = ?",
                    (ip_address, existing['id'])
                )
            else:
                cursor.execute(
                    "INSERT INTO activated_devices (license_key, device_id, ip_address) VALUES (?, ?, ?)",
                    (license_key, device_id, ip_address)
                )
            conn.commit()
            return True
    
    def get_all_activated_users(self):
        """Get all activated devices"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, l.tier, l.expiry_date
                FROM activated_devices a
                JOIN licenses l ON a.license_key = l.key
                ORDER BY a.last_active DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_feature_toggles(self, license_key=None):
        """Get feature toggles"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if license_key:
                cursor.execute(
                    "SELECT feature_name, is_enabled FROM feature_toggles WHERE license_key = ?",
                    (license_key,)
                )
            else:
                cursor.execute(
                    "SELECT feature_name, is_enabled FROM feature_toggles WHERE license_key IS NULL"
                )
            return {row['feature_name']: bool(row['is_enabled']) for row in cursor.fetchall()}
    
    def set_feature_toggle(self, license_key, feature_name, enabled):
        """Set feature toggle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feature_toggles (license_key, feature_name, is_enabled) VALUES (?, ?, ?) ON CONFLICT(license_key, feature_name) DO UPDATE SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP",
                (license_key, feature_name, enabled, enabled)
            )
            conn.commit()
            return True
    
    def get_all_features(self):
        """Get all feature definitions"""
        return [
            {'name': 'hs_neck', 'label': 'HS Neck', 'desc': 'Headshot to neck mapping'},
            {'name': 'hs_chest', 'label': 'HS Chest', 'desc': 'Headshot to chest mapping'},
            {'name': 'zigzag', 'label': 'ZigZag', 'desc': 'PC-style zigzag movement'},
            {'name': 'backjump', 'label': 'Back Jump', 'desc': 'Instant backward jump'},
            {'name': 'noswap', 'label': 'No Swap', 'desc': 'No weapon swap delay'},
            {'name': 'bypass', 'label': 'Bypass', 'desc': 'Anti-ban bypass'},
            {'name': 'speed_hack', 'label': 'Speed Hack', 'desc': 'Movement speed multiplier'},
            {'name': 'high_jump', 'label': 'High Jump', 'desc': 'Increased jump height'}
        ]
    
    def log_proxy_request(self, license_key, endpoint, method, status_code, response_time, ip):
        """Log proxy request"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO proxy_logs (license_key, endpoint, method, status_code, response_time, ip_address) VALUES (?, ?, ?, ?, ?, ?)",
                (license_key, endpoint, method, status_code, response_time, ip)
            )
            conn.commit()
    
    def get_proxy_logs(self, limit=100, license_key=None):
        """Get recent logs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if license_key:
                cursor.execute(
                    "SELECT * FROM proxy_logs WHERE license_key = ? ORDER BY timestamp DESC LIMIT ?",
                    (license_key, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM proxy_logs ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            
            cursor.execute("SELECT COUNT(*) FROM licenses WHERE is_active = 1")
            stats['total_licenses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT device_id) FROM activated_devices WHERE is_active = 1")
            stats['active_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM proxy_logs WHERE DATE(timestamp) = DATE('now')")
            stats['todays_requests'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT tier, COUNT(*) as count FROM licenses WHERE is_active = 1 GROUP BY tier")
            stats['tier_breakdown'] = {row['tier']: row['count'] for row in cursor.fetchall()}
            
            return stats
    
    def get_settings(self):
        """Get system settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row['key']: row['value'] for row in cursor.fetchall()}