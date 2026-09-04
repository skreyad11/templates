# features.py - Feature Management

class FeatureManager:
    """Manages feature toggles and definitions"""
    
    FEATURES = {
        'hs_neck': {
            'name': 'HS Neck',
            'description': 'Headshot to neck mapping',
            'default': True,
            'category': 'hitbox'
        },
        'hs_chest': {
            'name': 'HS Chest',
            'description': 'Headshot to chest mapping',
            'default': True,
            'category': 'hitbox'
        },
        'zigzag': {
            'name': 'ZigZag',
            'description': 'PC-style zigzag movement',
            'default': True,
            'category': 'movement'
        },
        'backjump': {
            'name': 'Back Jump',
            'description': 'Instant backward jump',
            'default': True,
            'category': 'movement'
        },
        'noswap': {
            'name': 'No Swap',
            'description': 'No weapon swap delay',
            'default': True,
            'category': 'movement'
        },
        'bypass': {
            'name': 'Bypass',
            'description': 'Anti-ban bypass',
            'default': True,
            'category': 'security'
        },
        'speed_hack': {
            'name': 'Speed Hack',
            'description': 'Movement speed multiplier',
            'default': True,
            'category': 'stats'
        },
        'high_jump': {
            'name': 'High Jump',
            'description': 'Increased jump height',
            'default': True,
            'category': 'stats'
        }
    }
    
    @classmethod
    def get_all_features(cls):
        return cls.FEATURES
    
    @classmethod
    def get_feature(cls, name):
        return cls.FEATURES.get(name)
    
    @classmethod
    def get_defaults(cls):
        return {name: data['default'] for name, data in cls.FEATURES.items()}
    
    @classmethod
    def get_categories(cls):
        categories = {}
        for name, data in cls.FEATURES.items():
            cat = data.get('category', 'general')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)
        return categories