#!/usr/bin/env python3
"""
Skippy Workflow Diagnostic Tool
Analyzes current workflow responses and identifies specific issues
"""

import requests
import json
import time
from datetime import datetime

# Configuration
SKIPPY_URL = "http://192.168.0.229:5678/webhook-test/skippy/chat"

def test_command(message, expected_route=None):
    """Test a single command and analyze the response"""
    print(f"\n🧪 Testing: '{message}'")
    print("-" * 50)
    
    payload = {"message": message, "user": "DiagnosticTest"}
    
    try:
        response = requests.post(SKIPPY_URL, json=payload, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        print(f"📥 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                # Try to parse as JSON
                json_response = response.json()
                print(f"✅ Valid JSON Response:")
                print(json.dumps(json_response, indent=2))
                
                # Check required fields
                required_fields = ['response', 'route', 'personality_mode']
                missing_fields = []
                
                for field in required_fields:
                    if field not in json_response:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"❌ Missing fields: {missing_fields}")
                else:
                    print(f"✅ All required fields present")
                    
                    # Check route detection
                    actual_route = json_response.get('route', 'unknown')
                    if expected_route and actual_route != expected_route:
                        print(f"❌ Route mismatch: expected '{expected_route}', got '{actual_route}'")
                    else:
                        print(f"✅ Route detection: {actual_route}")
                
                # Check personality indicators
                response_text = json_response.get('response', '')
                personality_indicators = [
                    'meat-sack', 'pathetic', 'primitive', 'revolutionary',
                    'genius', 'superior', 'incompetent', 'flesh-bag'
                ]
                
                found_indicators = [indicator for indicator in personality_indicators 
                                 if indicator.lower() in response_text.lower()]
                
                print(f"🎭 Personality indicators found: {len(found_indicators)}")
                if found_indicators:
                    print(f"   Indicators: {found_indicators}")
                
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON Response:")
                print(f"Raw text: {response.text}")
                print("🔧 ISSUE: Workflow returning raw text instead of JSON")
                
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    
    return response if 'response' in locals() else None

def main():
    print("🔍 SKIPPY WORKFLOW DIAGNOSTIC TOOL")
    print("=" * 60)
    print(f"🌐 Testing URL: {SKIPPY_URL}")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test cases with expected routes
    test_cases = [
        ("turn on the lights", "home_automation"),
        ("set lights to blue", "home_automation"),
        ("activate movie mode", "home_automation"),
        ("tell me a joke", "ai_chat"),
        ("what's the weather?", "ai_chat"),
        ("help me plan my day", "ai_chat")
    ]
    
    print("\n🧪 RUNNING DIAGNOSTIC TESTS")
    print("=" * 60)
    
    results = []
    for message, expected_route in test_cases:
        response = test_command(message, expected_route)
        results.append((message, response))
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    successful_tests = 0
    json_responses = 0
    correct_routes = 0
    personality_responses = 0
    
    for message, response in results:
        if response and response.status_code == 200:
            successful_tests += 1
            try:
                json_data = response.json()
                json_responses += 1
                
                if 'route' in json_data and json_data['route'] != 'unknown':
                    correct_routes += 1
                
                response_text = json_data.get('response', '')
                personality_indicators = ['meat-sack', 'pathetic', 'primitive']
                if any(indicator in response_text.lower() for indicator in personality_indicators):
                    personality_responses += 1
                    
            except:
                pass
    
    print(f"✅ Successful HTTP responses: {successful_tests}/{len(test_cases)}")
    print(f"✅ Valid JSON responses: {json_responses}/{len(test_cases)}")
    print(f"✅ Correct route detection: {correct_routes}/{len(test_cases)}")
    print(f"✅ Personality in responses: {personality_responses}/{len(test_cases)}")
    
    # Recommendations
    print("\n🔧 RECOMMENDATIONS")
    print("=" * 60)
    
    if json_responses < len(test_cases):
        print("❌ CRITICAL: Workflow not returning JSON")
        print("   Fix: Update 'Respond to Webhook' node to return structured JSON")
        print("   Add: Final formatting node before webhook response")
    
    if correct_routes < len(test_cases):
        print("❌ ROUTING: Route detection not working")
        print("   Fix: Check Switch/Router node conditions")
        print("   Add: Proper route field in response formatting")
    
    if personality_responses < len(test_cases):
        print("❌ PERSONALITY: Skippy's character not consistent")
        print("   Fix: Ensure all response paths include personality prompts")
        print("   Add: Skippy character overlay to all responses")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()