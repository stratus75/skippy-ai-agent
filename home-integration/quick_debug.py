#!/usr/bin/env python3
"""
Quick debug script to identify the exact routing issue
"""

import requests
import json

def test_specific_commands():
    """Test specific commands that should route differently"""
    
    print("🔍 DEBUGGING ROUTING ISSUES")
    print("=" * 50)
    
    # Test commands with expected routes
    test_cases = [
        ("turn on the lights", "Should route to HOME"),
        ("tell me a joke", "Should route to AI"),
        ("activate movie mode", "Should route to HOME"),
        ("what is 2+2", "Should route to AI")
    ]
    
    main_url = "http://192.168.0.229:5678/webhook-test/skippy/chat"
    
    for message, expected in test_cases:
        print(f"\n🧪 Testing: '{message}' ({expected})")
        print("-" * 40)
        
        payload = {"message": message, "user": "DebugUser"}
        
        try:
            response = requests.post(main_url, json=payload, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # Print key fields for debugging
                    print(f"✅ Success!")
                    print(f"Route: {result.get('route', 'NOT FOUND')}")
                    print(f"Response length: {len(result.get('response', ''))}")
                    print(f"Has personality_mode: {'personality_mode' in result}")
                    print(f"Has commandType: {'commandType' in result}")
                    
                    # Show first 100 chars of response
                    resp = result.get('response', '')
                    if resp:
                        print(f"Response preview: {resp[:100]}...")
                    else:
                        print("❌ NO RESPONSE CONTENT")
                        
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON response: {response.text[:200]}")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def check_workflow_endpoints():
    """Check if both endpoints are reachable"""
    print("\n🔌 CHECKING WORKFLOW ENDPOINTS")
    print("=" * 40)
    
    endpoints = [
        ("Main Workflow", "http://192.168.0.229:5678/webhook/skippy/chat"),
        ("Home Workflow", "http://192.168.0.229:5678/webhook/skippy-home-control")
    ]
    
    for name, url in endpoints:
        print(f"\n📡 {name}: {url}")
        try:
            response = requests.post(url, 
                                   json={"message": "test", "user": "ConnTest"}, 
                                   timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Response: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    print("🕵️ SKIPPY ROUTING DEBUGGER")
    print("=" * 50)
    
    check_workflow_endpoints()
    test_specific_commands()
    
    print("\n" + "=" * 50)
    print("🔧 NEXT STEPS:")
    print("1. Check that both workflows are ACTIVE (green toggle)")
    print("2. Verify webhook URLs in n8n match URLs above")
    print("3. Look for routing issues in Smart Router node")
    print("4. Check if Switch node conditions are correct")

if __name__ == "__main__":
    main()