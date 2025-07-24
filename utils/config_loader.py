#!/usr/bin/env python3
"""
Configuration loader for ImmortyX system
"""

import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Load and manage system configuration"""
    
    @staticmethod
    def load_config(config_path: str = None) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if config_path is None:
            # Default to longevity_config.json in the root directory
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'longevity_config.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    @staticmethod
    def get_research_themes() -> list:
        """Get list of research themes"""
        config = ConfigLoader.load_config()
        return config.get('research_themes', [])
    
    @staticmethod
    def get_query_templates(theme: str = None) -> Dict[str, list]:
        """Get query templates for a specific theme or all themes"""
        config = ConfigLoader.load_config()
        templates = config.get('query_templates', {})
        
        if theme:
            return templates.get(theme, [])
        return templates
    
    @staticmethod
    def get_source_config() -> Dict[str, Any]:
        """Get data source configuration"""
        config = ConfigLoader.load_config()
        return config.get('sources', {})
    
    @staticmethod
    def get_llm_config() -> Dict[str, Any]:
        """Get LLM configuration"""
        return {
            'base_url': 'http://80.209.242.40:8000/v1',
            'api_key': 'dummy-key',
            'model': 'llama-3.3-70b-instruct',
            'max_tokens': 75,
            'temperature': 0.5
        }
