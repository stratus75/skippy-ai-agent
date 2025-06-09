#!/usr/bin/env python3
"""
Debug the main workflow to see what's happening with routing
"""

import requests
import json

def test_routing_debug():
    """Test specific commands and show detailed responses"""
    
    main_url = "http://192.168.0.229:5678/webhook-test/skippy/chat"
    
    test_cases = [
        ("turn on the lights", "Should route to HOME"),
        ("tell me a joke", "Should route to AI"),
        ("help me plan my day", "Should route to AI")
    ]
    
    print("🔍 DEBUGGING MAIN WORKFLOW RESPONSES")
    print("=" * 60)
    
    for message, expected in test_cases:
        print(f"\n🧪 Testing: '{message}' ({expected})")
        print("-" * 50)
        
        payload = {"message": message, "user": "DebugUser"}
        
        try:
            response = requests.post(main_url, json=payload, timeout=20)
            print(f"📊 HTTP Status: {response.status_code}")
            print(f"📋 Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                # Try to parse as JSON
                try:
                    result = response.json()
                    print(f"✅ Valid JSON response")
                    print(f"📝 Keys in response: {list(result.keys())}")
                    
                    # Check for expected fields
                    for field in ['route', 'response', 'personality_mode', 'isHomeCommand']:
                        if field in result:
                            print(f"   ✅ {field}: {result[field]}")
                        else:
                            print(f"   ❌ {field}: MISSING")
                    
                    # Show response preview
                    if 'response' in result:
                        resp_preview = str(result['response'])[:150]
                        print(f"🎤 Response preview: {resp_preview}...")
                    
                except json.JSONDecodeError:
                    print(f"❌ NOT JSON - Raw text response:")
                    print(f"📄 Raw response: {response.text[:300]}...")
                    print(f"🔧 This is the problem - should be JSON!")
                    
            else:
                print(f"❌ HTTP Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")

def test_direct_components():
    """Test home automation directly to compare"""
    print(f"\n" + "=" * 60)
    print("🏠 TESTING HOME AUTOMATION DIRECTLY (for comparison)")
    print("=" * 60)
    
    home_url = "http://192.168.0.229:5678/webhook-test/skippy-home-control"
    
    payload = {"message": "turn on the lights", "user": "DebugUser"}
    
    try:
        response = requests.post(home_url, json=payload, timeout=15)
        print(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Home workflow returns valid JSON")
                print(f"📝 Keys: {list(result.keys())}")
                print(f"🎤 Response: {result.get('response', 'No response field')[:100]}...")
            except json.JSONDecodeError:
                print(f"❌ Home workflow also returns raw text: {response.text[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🕵️ MAIN WORKFLOW ROUTING DEBUGGER")
    print("=" * 50)
    
    test_routing_debug()
    test_direct_components()
    
    print(f"\n" + "=" * 60)
    print("🔧 DIAGNOSIS:")
    print("If you see 'NOT JSON - Raw text response' above, then:")
    print("1. Your main workflow is missing proper JSON formatting")
    print("2. The 'Respond to Webhook' node needs to respond with JSON")
    print("3. The response should include 'route', 'response', 'personality_mode' fields")
    print("\n💡 SOLUTION:")
    print("Check your main workflow's final response node configuration!")

if __name__ == "__main__":
    main()