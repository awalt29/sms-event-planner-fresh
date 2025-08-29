#!/usr/bin/env python3
"""Add a test endpoint to verify deployment version"""

# Add this to a route file to test if the deployment is working

@app.route('/test-guest-list', methods=['GET'])
def test_guest_list_endpoint():
    """Test endpoint to verify guest list feature is deployed"""
    return {
        "status": "success",
        "feature": "guest_list_in_availability_requests", 
        "version": "deployed",
        "timestamp": datetime.now().isoformat(),
        "commit": "6ccdfbb - Add guest list to availability requests"
    }
