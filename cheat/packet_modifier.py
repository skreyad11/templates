# packet_modifier.py - Core Packet Modification Engine

import json
import random

class PacketModifier:
    """Modifies Garena packets in real-time"""
    
    def modify_packet(self, data, endpoint, features):
        """Main modification entry point"""
        if not isinstance(data, dict):
            return data
        
        modified = data.copy()
        
        # Player stats modification
        if 'player' in endpoint or 'stats' in endpoint:
            modified = self.modify_player_stats(modified, features)
        
        # Hitbox modification
        if 'hitbox' in endpoint or 'damage' in endpoint:
            modified = self.modify_hitbox(modified, features)
        
        # Match modification
        if 'match' in endpoint:
            modified = self.modify_match(modified, features)
        
        # Movement modification
        if 'movement' in endpoint or 'speed' in endpoint:
            modified = self.modify_movement(modified, features)
        
        # Inventory modification
        if 'inventory' in endpoint or 'items' in endpoint:
            modified = self.modify_inventory(modified, features)
        
        # Bypass
        if 'verify' in endpoint or 'auth' in endpoint:
            modified = self.apply_bypass(modified, features)
        
        return modified
    
    def modify_player_stats(self, data, features):
        """Modify player statistics"""
        if features.get('hs_neck', True) or features.get('hs_chest', True):
            if 'hp' in data:
                data['hp'] = 9999
            if 'health' in data:
                data['health'] = 9999
            if 'shield' in data:
                data['shield'] = 9999
        
        if features.get('speed_hack', True):
            if 'speed' in data:
                data['speed'] = min(data.get('speed', 0) * 2.5, 500.0)
            if 'move_speed' in data:
                data['move_speed'] = min(data.get('move_speed', 0) * 2.5, 500.0)
        
        if features.get('high_jump', True):
            if 'jump_height' in data:
                data['jump_height'] = min(data.get('jump_height', 0) * 3.0, 10.0)
        
        return data
    
    def modify_hitbox(self, data, features):
        """Modify hitbox mapping"""
        if features.get('hs_neck', True):
            if 'head' in data:
                data['head'] = 'neck'
        
        if features.get('hs_chest', True):
            if 'chest' in data:
                data['chest'] = 'head'
        
        return data
    
    def modify_match(self, data, features):
        """Modify match data"""
        if 'position' in data:
            data['position'] = 1
        if 'rank' in data:
            data['rank'] = 1
        if 'rewards' in data:
            if 'coins' in data['rewards']:
                data['rewards']['coins'] = min(data['rewards'].get('coins', 0) * 10, 999999)
        return data
    
    def modify_movement(self, data, features):
        """Modify movement"""
        if features.get('zigzag', True):
            if 'movement' in data:
                data['movement']['zigzag'] = True
        
        if features.get('backjump', True):
            if 'jump' in data:
                data['jump']['backflip'] = True
        
        if features.get('noswap', True):
            if 'weapon' in data:
                data['weapon']['swap_speed'] = 0.0
        
        return data
    
    def modify_inventory(self, data, features):
        """Modify inventory"""
        if 'items' in data and isinstance(data['items'], list):
            for item in data['items']:
                if 'quantity' in item:
                    item['quantity'] = min(item.get('quantity', 0) * 100, 9999)
        return data
    
    def apply_bypass(self, data, features):
        """Apply bypass"""
        if features.get('bypass', True):
            if 'detection' in data:
                data['detection'] = {'status': 'clean', 'score': 0}
            if 'security' in data:
                data['security']['flagged'] = False
                data['security']['trust_score'] = 100
        return data