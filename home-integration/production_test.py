#!/usr/bin/env python3
"""
Test the new single production workflow
"""

import requests
import json

# Your single production URL
SKIPPY_URL = "http://192.168.0.229:5678/webhook-test/skippy/chat"

def test_commands():
    """Test both home automation and AI commands"""
    
    test_cases = [
        # Home automation tests
        ("turn on the lights", "home_automation", "Light control"),
        ("activate movie mode", "home_automation", "Scene control"),
        ("set volume to 80%", "home_automation", "Media control"),
        ("show device status", "home_automation", "Status request"),
        
        # AI chat tests  
        ("tell me a joke", "ai_chat", "AI humor"),
        ("what's 2+2?", "ai_chat", "AI math"),
        ("help me plan my day", "ai_chat", "AI planning"),
        ("explain quantum physics", "ai_chat", "AI knowledge")
    ]
    
    print("🧪 TESTING SINGLE PRODUCTION WORKFLOW")
    print("=" * 60)
    print(f"🌐 URL: {SKIPPY_URL}")
    print("=" * 60)
    
    passed = 0
    total = len(test_cases)
    
    for message, expected_route, description in test_cases:
        print(f"\n🔹 {description}: '{message}'")
        print(f"   Expected route: {expected_route}")
        print("-" * 40)
        
        payload = {"message": message, "user": "ProductionTest"}
        
        try:
            response = requests.post(SKIPPY_URL, json=payload, timeout=20)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # Check all expected fields
                    actual_route = result.get('route', 'missing')
                    personality_mode = result.get('personality_mode', 'missing')
                    success = result.get('success', False)
                    response_text = result.get('response', '')
                    
                    print(f"✅ Valid JSON response")
                    print(f"🔀 Route: {actual_route}")
                    print(f"🎭 Personality: {personality_mode}")
                    print(f"🎯 Success: {success}")
                    print(f"🎤 Response: {response_text[:100]}...")
                    
                    # Check routing correctness
                    if actual_route == expected_route:
                        print(f"✅ CORRECT ROUTING!")
                        passed += 1
                    else:
                        print(f"❌ Wrong routing: got '{actual_route}', expected '{expected_route}'")
                        
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {response.text[:200]}...")
                    
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ Request error: {e}")
        
        print()  # Add spacing
    
    print("=" * 60)
    print("🎯 FINAL RESULTS")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{total}")
    print(f"📊 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 PERFECT! All tests passed!")
        print("✅ Single workflow handles both home automation and AI")
        print("✅ Proper JSON responses with routing information")
        print("✅ Skippy personality working for both modes")
        print(f"✅ Production URL ready: {SKIPPY_URL}")
        
        print("\n🚀 READY FOR:")
        print("   🎤 Voice integration")
        print("   📱 Telegram bot")
        print("   🏠 Home Assistant connection")
        print("   🌐 Any external service")
        
    elif passed >= total * 0.75:
        print("\n✅ GOOD! Most tests passed with minor issues")
        
    else:
        print("\n⚠️  ISSUES DETECTED!")
        print("Check workflow import and activation")

def quick_test():
    """Quick single test"""
    print("🚀 QUICK PRODUCTION TEST")
    print("=" * 30)
    
    payload = {"message": "turn on the lights", "user": "QuickTest"}
    
    try:
        response = requests.post(SKIPPY_URL, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS!")
            print(f"Route: {result.get('route', 'unknown')}")
            print(f"Response: {result.get('response', '')[:150]}...")
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🤖 SKIPPY PRODUCTION WORKFLOW TESTER")
    print("=" * 50)
    print("1. Full Test Suite")
    print("2. Quick Test")
    
    choice = input("\nChoose (1-2): ").strip()
    
    if choice == "1":
        test_commands()
    elif choice == "2":
        quick_test()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()