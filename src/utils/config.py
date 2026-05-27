import json
import os


class Config:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.default_settings = {
            'check_gifts': False,
            'check_stars': False,
            'check_premium': False,
            'check_channels': False,
            'use_proxy': True,
            'theme': 'light'
        }
        self.settings = self.load()
    
    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                self.save(self.default_settings)
                return self.default_settings.copy()
        else:
            self.save(self.default_settings)
            return self.default_settings.copy()
    
    def save(self, settings):
        self.settings = settings
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def get_all(self):
        return self.settings.copy()
