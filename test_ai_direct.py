import sys
sys.path.append('.')

from app import create_app
from app.services.ai_processing_service import AIProcessingService

print('🧪 Testing AI Service Directly')
print('=' * 40)

app = create_app()

with app.app_context():
    ai_service = AIProcessingService()
    
    test_input = "Aaron(9145606464)"
    
    prompt = f"""Parse guest information from: "{test_input}"

Return JSON with:
- success: true/false  
- guests: array with name and phone (phone REQUIRED)
- error: string if failed

Example:
"Aaron(9145606464)" -> {{"success": true, "guests": [{{"name": "Aaron", "phone": "9145606464"}}]}}"""

    print(f"Testing AI with input: '{test_input}'")
    print("Prompt:")
    print(prompt)
    print("\n" + "-" * 40)
    
    try:
        response = ai_service.make_completion(prompt, 200)
        print(f"AI Response: '{response}'")
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(response) if response else 0}")
        
        if response:
            import json
            try:
                parsed = json.loads(response)
                print(f"Parsed JSON: {parsed}")
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
        else:
            print("AI returned None or empty response")
            
    except Exception as e:
        print(f"AI service error: {e}")
    
    print("\n" + "=" * 40)
