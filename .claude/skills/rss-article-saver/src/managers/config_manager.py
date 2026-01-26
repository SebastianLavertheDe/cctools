"""
Configuration Manager - Loads YAML config
"""

import os
import sys
import yaml
from typing import Dict


class RSSConfig:
    """RSS configuration management"""

    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load YAML configuration"""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"Config file {self.config_file} not found")

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print(f"Loaded config: {self.config_file}")
                return config
        except Exception as e:
            print(f"Failed to load config: {e}")
            sys.exit(1)

    def get_opml_file(self) -> str:
        """Get OPML file path"""
        return self.config.get('opml_file', 'subscriptions.opml')

    def get_max_articles_per_feed(self) -> int:
        """Get max articles to process per feed"""
        return self.config.get('max_articles_per_feed', 20)

    def get_content_settings(self) -> Dict:
        """Get content extraction settings"""
        return self.config.get('content', {})

    def get_ai_settings(self) -> Dict:
        """Get AI processing settings"""
        return self.config.get('ai', {})

    def get_notion_settings(self) -> Dict:
        """Get Notion sync settings"""
        return self.config.get('notion', {'sync': True})

    def get_translation_settings(self) -> Dict:
        """Get translation settings"""
        return self.config.get('translation', {'enabled': False, 'provider': 'nvidia'})
