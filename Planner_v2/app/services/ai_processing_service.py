from typing import Optional
import logging
import os
import requests
import json

logger = logging.getLogger(__name__)

class AIProcessingService:
    """Lightweight AI client for handlers to use - HTTP-based to avoid library issues"""
    
    def __init__(self):
        """Initialize OpenAI HTTP client"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            logger.error("OPENAI_API_KEY environment variable is required - AI features will be disabled")
            self.api_key = None  # Explicitly set to None for safety
        else:
            logger.info("AI Processing Service initialized with HTTP client")
    
    def make_completion(self, prompt: str, max_tokens: int = 200) -> Optional[str]:
        """Make a completion request via HTTP - handlers parse the response"""
        if not self.api_key:
            logger.error("No OpenAI API key available")
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"OpenAI API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            return None