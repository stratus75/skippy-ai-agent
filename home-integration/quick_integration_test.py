#!/usr/bin/env python3
"""
Updated test script with the correct working URLs
"""

import requests
import json
import time
from datetime import datetime

# Configuration - UPDATED with your working URLs
SKIPPY_MAIN_URL = "http://192.168.0.229:5678/webhook/skippy/chat"
SKIPPY_HOME_URL = "http://192.168.0.229:5678/webhook/skippy-home-control"

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")

def print_test(test_name, description):
    """Print test information"""
    print(f"\n🧪 {test_name}")
    print(f"   {description}")
    print("-" * 50)

def send_request(url, message, user="TestUser"):
    """Send a test request and return the response"""
    payload = {
        "message": message,
        "user": user
    }
    
    try:
        print(f"📤 Sending: '{message}'")
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Success!")
                
                # Pretty print the response
                if 'response' in result:
                    print(f"🎤 Skippy says: {result['response'][:200]}{'...' if len(result['response']) > 200 else ''}")
                
                if 'route' in result:
                    print(f"🔀 Route: {result['route']}")
                    
                if 'commandType' in result:
                    print(f"🏠 Command Type: {result['commandType']}")
                
                return True, result
                
            except json.JSONDecodeError:
                print(f"✅ Raw response: {response.text[:200]}")
                return True, {"response": response.text}
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed to {url}")
        print(f"   Check that n8n is running and workflows are active")
        return False, None
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None

def test_direct_commands():
    """Test both URLs with the same commands to compare"""
    print_header("DIRECT URL COMPARISON")
    
    test_commands = [
        "turn on the lights",
        "tell me a joke", 
        "activate movie mode"
    ]
    
    for message in test_commands:
        print(f"\n🔄 Testing: '{message}'")
        print("=" * 40)
        
        # Test main URL
        print("📍 Main URL:")
        main_success, main_result = send_request(SKIPPY_MAIN_URL, message)
        
        # Test alternative URL if it exists
        alt_url = "http://192.168.0.229:5678/webhook/skippy/chat"
        print("\n📍 Alternative URL:")
        alt_success, alt_result = send_request(alt_url, message)
        
        time.sleep(1)

def test_home_automation_direct():
    """Test home automation workflow directly"""
    print_header("HOME AUTOMATION DIRECT TEST")
    
    test_commands = [
        ("turn on the lights", "Basic light control"),
        ("set lights to blue", "Color control"),
        ("activate movie mode", "Scene activation"),
        ("show device status", "Status request")
    ]
    
    passed = 0
    total = len(test_commands)
    
    for message, description in test_commands:
        print_test(f"Direct Test: {message}", description)
        success, response = send_request(SKIPPY_HOME_URL, message)
        
        if success:
            passed += 1
        
        time.sleep(1)
    
    print(f"\n📊 Direct Tests: {passed}/{total} passed")
    return passed == total

def test_routing_logic():
    """Test routing between home automation and AI"""
    print_header("ROUTING LOGIC TEST")
    
    test_cases = [
        # Should route to home automation
        ("turn on the lights", "Should be HOME automation"),
        ("activate relax mode", "Should be HOME automation"),
        ("set volume to 80%", "Should be HOME automation"),
        
        # Should route to AI
        ("tell me a joke", "Should be AI chat"),
        ("what's 2+2", "Should be AI chat"),
        ("help me plan my day", "Should be AI chat"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for message, expected in test_cases:
        print_test(f"Routing: {message}", expected)
        success, response = send_request(SKIPPY_MAIN_URL, message)
        
        if success and response:
            route = response.get('route', 'unknown')
            personality_mode = response.get('personality_mode', 'unknown')
            
            print(f"🔀 Actual route: {route}")
            print(f"🎭 Personality mode: {personality_mode}")
            
            # Check if routing makes sense
            if ('home' in expected.lower() and 'home' in route) or \
               ('ai' in expected.lower() and 'ai' in route):
                print(f"✅ Correct routing!")
                passed += 1
            else:
                print(f"❌ Unexpected routing")
        
        time.sleep(1)
    
    print(f"\n📊 Routing Tests: {passed}/{total} passed")
    return passed == total

def run_quick_integration_test():
    """Run a quick integration test"""
    print_header("QUICK INTEGRATION TEST")
    print(f"🌐 Main URL: {SKIPPY_MAIN_URL}")
    print(f"🏠 Home URL: {SKIPPY_HOME_URL}")
    
    # Test results
    results = {}
    
    # Test direct home automation
    print("\n🏠 Phase 1: Home Automation Direct")
    results['home_direct'] = test_home_automation_direct()
    
    # Test routing logic
    print("\n🔀 Phase 2: Routing Logic")
    results['routing'] = test_routing_logic()
    
    # Final summary
    print_header("INTEGRATION TEST RESULTS")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.upper()}: {status}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} test phases passed")
    
    if passed == total:
        print("\n🎉 EXCELLENT! Integration is working!")
        print("✅ Home automation commands work")
        print("✅ Routing logic is correct")
        print("✅ Ready for voice integration!")
    else:
        print("\n⚠️  Some issues remain:")
        for test_name, result in results.items():
            if not result:
                print(f"❌ {test_name} needs attention")

def main():
    """Main function"""
    print("🤖🏠 SKIPPY INTEGRATION - QUICK TEST")
    print("=" * 50)
    print("Choose test type:")
    print("1. Quick Integration Test (recommended)")
    print("2. Direct URL Comparison")
    print("3. Full Test Suite")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        run_quick_integration_test()
    elif choice == "2":
        test_direct_commands()
    elif choice == "3":
        # Use your existing full test but with updated URLs
        print("Running full test suite with correct URLs...")
        # You can copy the full test functions here
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()