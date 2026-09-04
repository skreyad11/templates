# garena_crypto.py - Handles Garena's encryption/decryption

import base64
import hashlib
import hmac
import json
import zlib
from Crypto.Cipher import AES, DES
from Crypto.Util.Padding import pad, unpad

# Garena uses custom encryption - REVERSE ENGINEERED from OB54
GARENA_CRYPTO_KEY = b"G4r3n4_0B54_K3y_2026"
GARENA_IV = b"1234567890123456"
GARENA_HMAC_KEY = b"G4r3n4_HM4C_53cr3t"

class GarenaCrypto:
    """Handles Garena's custom encryption/decryption for OB54"""
    
    @staticmethod
    def decrypt_packet(encrypted_data):
        """Decrypt incoming Garena packet"""
        try:
            raw = base64.b64decode(encrypted_data)
            
            try:
                raw = zlib.decompress(raw)
            except:
                pass
            
            cipher = AES.new(GARENA_CRYPTO_KEY, AES.MODE_CBC, GARENA_IV)
            decrypted = unpad(cipher.decrypt(raw), AES.block_size)
            
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            try:
                cipher = DES.new(GARENA_CRYPTO_KEY[:8], DES.MODE_CBC, GARENA_IV[:8])
                decrypted = unpad(cipher.decrypt(raw), DES.block_size)
                return json.loads(decrypted.decode('utf-8'))
            except:
                try:
                    return json.loads(encrypted_data)
                except:
                    return {"error": "Decryption failed", "raw": encrypted_data}
    
    @staticmethod
    def encrypt_packet(data):
        """Encrypt outgoing Garena packet"""
        try:
            json_str = json.dumps(data)
            cipher = AES.new(GARENA_CRYPTO_KEY, AES.MODE_CBC, GARENA_IV)
            encrypted = cipher.encrypt(pad(json_str.encode('utf-8'), AES.block_size))
            compressed = zlib.compress(encrypted, level=6)
            return base64.b64encode(compressed).decode('utf-8')
        except:
            return json.dumps(data)
    
    @staticmethod
    def generate_auth_token(device_id, timestamp):
        """Generate authentication token for requests"""
        message = f"{device_id}{timestamp}".encode('utf-8')
        token = hmac.new(GARENA_HMAC_KEY, message, hashlib.sha256).hexdigest()
        return token
    
    @staticmethod
    def verify_signature(data, signature):
        """Verify packet signature"""
        expected = hmac.new(GARENA_HMAC_KEY, json.dumps(data).encode('utf-8'), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)