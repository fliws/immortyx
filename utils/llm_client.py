#!/usr/bin/env python3
"""
LLM Client for ImmortyX system
Wrapper for OpenAI API client to interact with Llama server
"""

import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with the LLM server"""
    
    def __init__(self):
        """Initialize the LLM client"""
        try:
            config = ConfigLoader.get_llm_config()
            self.client = OpenAI(
                base_url=config['base_url'],
                api_key=config['api_key']
            )
            self.model = config['model']
            self.max_tokens = config['max_tokens']
            self.temperature = config['temperature']
            logger.info("LLM client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.client = None
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion"""
        if not self.client:
            return "LLM client not available"
        
        try:
            # Override default parameters with kwargs
            params = {
                'model': kwargs.get('model', self.model),
                'messages': messages,
                'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                'temperature': kwargs.get('temperature', self.temperature)
            }
            
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            return f"Error generating response: {str(e)}"
    
    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Summarize a piece of text"""
        messages = [
            {
                "role": "system",
                "content": f"Summarize the following text in no more than {max_length} words, focusing on key insights related to longevity and aging research."
            },
            {
                "role": "user",
                "content": text
            }
        ]
        
        return self.chat_completion(messages, max_tokens=max_length)
    
    def extract_entities(self, text: str) -> str:
        """Extract named entities from text"""
        messages = [
            {
                "role": "system",
                "content": "Extract and list the following entities from the text: genes, proteins, drugs, companies, researchers, methods, and key concepts. Format as a structured list."
            },
            {
                "role": "user",
                "content": text
            }
        ]
        
        return self.chat_completion(messages, max_tokens=300)
    
    def assess_scientific_quality(self, text: str) -> str:
        """Assess the scientific quality and reliability of content"""
        messages = [
            {
                "role": "system",
                "content": "Assess the scientific quality of this content. Look for: peer review status, methodology description, sample sizes, statistical analysis, potential biases, and overall reliability. Provide a brief assessment."
            },
            {
                "role": "user",
                "content": text
            }
        ]
        
        return self.chat_completion(messages, max_tokens=200)
    
    def detect_pseudoscience(self, text: str) -> str:
        """Detect potential pseudoscience indicators"""
        messages = [
            {
                "role": "system",
                "content": "Analyze this content for pseudoscience indicators such as: extraordinary claims without evidence, cherry-picking data, appeal to authority, conspiracy theories, rejection of peer review, or misleading statistics. Rate the risk level (Low/Medium/High) and explain."
            },
            {
                "role": "user",
                "content": text
            }
        ]
        
        return self.chat_completion(messages, max_tokens=150)
    
    def is_available(self) -> bool:
        """Check if LLM client is available"""
        return self.client is not None
