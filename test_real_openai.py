#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/aaronwalters/Planner_app_live')

# Use actual environment - don't override the API key
from app import create_app
from app.utils.ai import get_ai_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_openai_client():
    """Test if OpenAI client initializes properly with real environment."""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Testing OpenAI client initialization...")
        print("=" * 50)
        
        # Check environment variables
        api_key = app.config.get('OPENAI_API_KEY')
        print(f"API Key configured: {'Yes' if api_key else 'No'}")
        if api_key:
            print(f"API Key length: {len(api_key)}")
            print(f"API Key starts with: {api_key[:10]}...")
        print()
        
        # Test AI service initialization
        ai_service = get_ai_service()
        
        # Force client initialization
        ai_service._initialize_client()
        
        print(f"Client initialized: {'Yes' if ai_service.client else 'No'}")
        
        if ai_service.client:
            print("✅ OpenAI client is working!")
            
            # Test actual venue suggestion with real API
            print("\n🎯 Testing real venue suggestions...")
            result = ai_service.suggest_venues("Chinese restaurant", "Brooklyn")
            
            print("Result:")
            import json
            print(json.dumps(result, indent=2))
            
        else:
            print("❌ OpenAI client failed to initialize")
            print("This explains why it's using fallback suggestions")

if __name__ == "__main__":
    test_real_openai_client()
