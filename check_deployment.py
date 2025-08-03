#!/usr/bin/env python3
"""
Deployment verification script.
Run this to check if your app is properly configured for deployment.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check if all required environment variables are set."""
    
    required_vars = {
        'TWILIO_SID': 'Twilio Account SID',
        'TWILIO_AUTH': 'Twilio Auth Token', 
        'TWILIO_NUMBER': 'Twilio Phone Number',
        'OPENAI_API_KEY': 'OpenAI API Key',
        'SECRET_KEY': 'Flask Secret Key'
    }
    
    print("🔍 Checking Environment Variables...")
    print("=" * 50)
    
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'TOKEN' in var or 'SECRET' in var:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Missing")
            missing_vars.append(var)
    
    return missing_vars

def check_dependencies():
    """Check if all required dependencies are installed."""
    
    print("\n📦 Checking Dependencies...")
    print("=" * 50)
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'twilio',
        'openai',
        'dotenv',  # The actual import name is 'dotenv', not 'python_dotenv'
        'gunicorn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Installed")
        except ImportError:
            print(f"❌ {package}: Missing")
            missing_packages.append(package)
    
    return missing_packages

def check_files():
    """Check if required deployment files exist."""
    
    print("\n📄 Checking Deployment Files...")
    print("=" * 50)
    
    required_files = [
        'requirements.txt',
        'Procfile',
        'run.py',
        'app/__init__.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: Found")
        else:
            print(f"❌ {file_path}: Missing")
            missing_files.append(file_path)
    
    return missing_files

def main():
    """Main verification function."""
    
    print("🚀 Event Planner Deployment Check")
    print("=" * 50)
    
    # Check environment variables
    missing_vars = check_environment()
    
    # Check dependencies
    missing_packages = check_dependencies()
    
    # Check files
    missing_files = check_files()
    
    # Summary
    print("\n📊 Summary")
    print("=" * 50)
    
    if not missing_vars and not missing_packages and not missing_files:
        print("🎉 All checks passed! Your app is ready for deployment.")
        print("\nNext steps:")
        print("1. Push your code to GitHub")
        print("2. Deploy to Railway/Render/Heroku")
        print("3. Set environment variables in your platform")
        print("4. Run update_twilio_webhook.py after deployment")
        return True
    else:
        print("❌ Some issues found:")
        
        if missing_vars:
            print(f"\n🔧 Missing environment variables: {', '.join(missing_vars)}")
            print("   Create a .env file or set these in your deployment platform")
        
        if missing_packages:
            print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
            print("   Run: pip install -r requirements.txt")
        
        if missing_files:
            print(f"\n📄 Missing files: {', '.join(missing_files)}")
            print("   Make sure all required files are in your project")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
