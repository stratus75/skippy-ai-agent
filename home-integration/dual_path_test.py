#!/usr/bin/env python3
"""
Dual Path Test Script
Tests both home automation and AI chat paths
"""

import requests
import json
import time
from datetime import datetime

def test_both_paths():
    """Test both workflow paths"""
    print("🧪 DUAL PATH TEST")
    print("=" * 40)
    
    url = "http://192.168.0.229:5678/webhook-test/skippy/chat"
    
    test_cases = [
        {
            "message": "turn on the lights",
            "expected_route": "home_automation",
            "description": "Home Automation Path"
        },
        {
            "message": "tell me a joke",
            "expected_route": "ai_chat", 
            "description": "AI Chat Path"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print(f"📤 Message: '{test_case['message']}'")
        print(f"🎯 Expected Route: {test_case['expected_route']}")
        print("-" * 40)
        
        payload = {
            "message": test_case['message'],
            "user": "DualPathTest"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            status = response.status_code
            
            print(f"📊 Status: {status}")
            
            if status == 200:
                response_text = response.text.strip()
                
                if response_text:
                    print(f"✅ Got response ({len(response_text)} chars)")
                    
                    try:
                        json_data = response.json()
                        print(f"✅ Valid JSON response")
                        
                        actual_route = json_data.get('route', 'unknown')
                        success = json_data.get('success', False)
                        
                        print(f"🎯 Route: {actual_route}")
                        print(f"✅ Success: {success}")
                        
                        if actual_route == test_case['expected_route']:
                            print(f"✅ Correct routing!")
                        else:
                            print(f"⚠️  Route mismatch")
                            
                    except json.JSONDecodeError:
                        print(f"❌ Raw text response:")
                        print(f"📝 {response_text[:200]}...")
                        
                else:
                    print(f"❌ Empty response - likely Merge node failure")
                    
            else:
                print(f"❌ Error {status}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        if i < len(test_cases):
            print("\n⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    print(f"\n🔧 NEXT STEPS:")
    print("=" * 40)
    print("1. If home automation works but AI chat fails:")
    print("   → Fix the Merge Responses node")
    print("2. If both fail with empty responses:")
    print("   → Check final response node configuration")
    print("3. If you get raw text instead of JSON:")
    print("   → Update 'Respond to Webhook' node")

if __name__ == "__main__":
    test_both_paths()