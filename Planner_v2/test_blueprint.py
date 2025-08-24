#!/usr/bin/env python3

# Minimal test to identify the blueprint issue
import sys
sys.path.append('.')

try:
    print("Testing imports...")
    
    print("1. Importing Flask...")
    from flask import Flask
    
    print("2. Creating app...")
    app = Flask(__name__)
    
    print("3. Importing SMS blueprint...")
    from app.routes.sms import sms_bp
    
    print("4. Registering blueprint...")
    app.register_blueprint(sms_bp)
    
    print("✅ SUCCESS: No blueprint registration errors!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
