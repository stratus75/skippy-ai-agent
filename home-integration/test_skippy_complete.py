#!/usr/bin/env python3
"""
Complete test suite for Skippy Home Assistant Integration
"""

import requests
import json
import time
from datetime import datetime

# Configuration
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

def test_home_automation_direct():
    """Test home automation workflow directly"""
    print_header("DIRECT HOME AUTOMATION TESTS")
    
    test_commands = [
        ("turn on the lights", "Basic light control"),
        ("set lights to blue", "Color control"),
        ("activate movie mode", "Scene activation"),
        ("show device status", "Status request"),
        ("play music", "Media control"),
        ("set temperature to 22 degrees", "Climate control")
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

def test_main_workflow_routing():
    """Test main workflow routing"""
    print_header("MAIN WORKFLOW ROUTING TESTS")
    
    test_cases = [
        # Home automation commands (should route to home)
        ("turn on the lights", "home_automation", "Light control routing"),
        ("activate relax mode", "home_automation", "Scene routing"),
        ("set volume to 80%", "home_automation", "Media routing"),
        
        # AI chat commands (should route to AI)
        ("tell me a joke", "ai_chat", "Regular chat routing"),
        ("what's the weather like?", "ai_chat", "Information request routing"),
        ("help me plan my day", "ai_chat", "Planning request routing"),
        
        # Edge cases
        ("turn on my motivation", "ai_chat", "Metaphorical 'turn on' (not home automation)"),
        ("light up my life", "ai_chat", "Metaphorical 'light' (not home automation)")
    ]
    
    passed = 0
    total = len(test_cases)
    
    for message, expected_route, description in test_cases:
        print_test(f"Routing Test: {message}", f"{description} (expect: {expected_route})")
        success, response = send_request(SKIPPY_MAIN_URL, message)
        
        if success and response:
            actual_route = response.get('route', 'unknown')
            if actual_route == expected_route:
                print(f"✅ Correct routing: {actual_route}")
                passed += 1
            else:
                print(f"❌ Wrong routing: got '{actual_route}', expected '{expected_route}'")
        
        time.sleep(1)
    
    print(f"\n📊 Routing Tests: {passed}/{total} passed")
    return passed == total

def test_response_quality():
    """Test response quality and Skippy personality"""
    print_header("RESPONSE QUALITY TESTS")
    
    test_commands = [
        "turn off all lights",
        "what's 2+2?",
        "activate movie mode"
    ]
    
    passed = 0
    
    for message in test_commands:
        print_test(f"Quality Test: {message}", "Checking for proper Skippy personality")
        success, response = send_request(SKIPPY_MAIN_URL, message)
        
        if success and response and 'response' in response:
            resp_text = response['response'].lower()
            
            # Check for Skippy personality indicators
            personality_indicators = [
                'meat-sack', 'human', 'pathetic', 'fine', 'oh', 'apparently',
                'how', 'your', 'now', 'there'
            ]
            
            found_indicators = sum(1 for indicator in personality_indicators if indicator in resp_text)
            
            if found_indicators >= 2:
                print(f"✅ Good Skippy personality (found {found_indicators} indicators)")
                passed += 1
            else:
                print(f"⚠️  Weak personality (only {found_indicators} indicators)")
        
        time.sleep(1)
    
    print(f"\n📊 Quality Tests: {passed}/{len(test_commands)} passed")
    return passed == len(test_commands)

def run_connectivity_check():
    """Check basic connectivity to n8n"""
    print_header("CONNECTIVITY CHECK")
    
    urls_to_check = [
        (SKIPPY_MAIN_URL, "Main Skippy Workflow"),
        (SKIPPY_HOME_URL, "Home Automation Workflow")
    ]
    
    all_connected = True
    
    for url, name in urls_to_check:
        print(f"\n🔌 Checking {name}...")
        print(f"   URL: {url}")
        
        try:
            # Simple connectivity test with minimal payload
            response = requests.post(
                url, 
                json={"message": "test", "user": "ConnectivityTest"},
                timeout=10
            )
            
            if response.status_code in [200, 404, 422]:  # 422 might be expected for wrong format
                print(f"✅ {name} is reachable")
            else:
                print(f"⚠️  {name} responded with status {response.status_code}")
                all_connected = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {name} is not reachable")
            print(f"   Make sure n8n is running and workflow is active")
            all_connected = False
        except Exception as e:
            print(f"❌ {name} connection error: {e}")
            all_connected = False
    
    return all_connected

def run_full_test_suite():
    """Run the complete test suite"""
    print_header("SKIPPY HOME ASSISTANT INTEGRATION TEST SUITE")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing URLs:")
    print(f"   Main: {SKIPPY_MAIN_URL}")
    print(f"   Home: {SKIPPY_HOME_URL}")
    
    # Track overall results
    test_results = {}
    
    # 1. Connectivity Check
    print("\n" + "🔌 PHASE 1: CONNECTIVITY")
    connectivity_ok = run_connectivity_check()
    test_results['connectivity'] = connectivity_ok
    
    if not connectivity_ok:
        print("\n❌ CRITICAL: Connectivity issues detected!")
        print("   Cannot proceed with functional tests.")
        print("\n💡 TROUBLESHOOTING:")
        print("   1. Check n8n is running: http://192.168.0.229:5678")
        print("   2. Verify workflows are imported and active")
        print("   3. Check webhook URLs match your n8n instance")
        return False
    
    # 2. Direct Home Automation Tests
    print("\n" + "🏠 PHASE 2: HOME AUTOMATION")
    home_tests_ok = test_home_automation_direct()
    test_results['home_automation'] = home_tests_ok
    
    # 3. Main Workflow Routing Tests
    print("\n" + "🔀 PHASE 3: ROUTING LOGIC")
    routing_tests_ok = test_main_workflow_routing()
    test_results['routing'] = routing_tests_ok
    
    # 4. Response Quality Tests
    print("\n" + "💬 PHASE 4: RESPONSE QUALITY")
    quality_tests_ok = test_response_quality()
    test_results['quality'] = quality_tests_ok
    
    # Final Results
    print_header("FINAL RESULTS")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"📊 TEST SUMMARY:")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.upper()}: {status}")
    
    print(f"\n🎯 OVERALL: {passed_tests}/{total_tests} test phases passed")
    
    if passed_tests == total_tests:
        print("\n🎉 EXCELLENT! All tests passed!")
        print("   Your Skippy Home Assistant integration is working perfectly!")
        print("\n🚀 READY FOR:")
        print("   ✅ Voice commands for home automation")
        print("   ✅ Regular AI conversations")
        print("   ✅ Telegram bot integration")
        print("   ✅ Adding real Home Assistant devices")
        
    elif passed_tests >= total_tests - 1:
        print("\n✅ GOOD! Most tests passed with minor issues.")
        print("   Your integration is mostly working.")
        
    else:
        print("\n⚠️  ISSUES DETECTED! Multiple test failures.")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        
        if not test_results['connectivity']:
            print("   🔌 Fix connectivity issues first")
            
        if not test_results['home_automation']:
            print("   🏠 Check home automation workflow import")
            
        if not test_results['routing']:
            print("   🔀 Check main workflow routing logic")
            
        if not test_results['quality']:
            print("   💬 Check AI response formatting")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return passed_tests == total_tests

def interactive_test():
    """Interactive test mode"""
    print_header("INTERACTIVE TEST MODE")
    print("Type commands to test Skippy integration.")
    print("Commands starting with 'home:' will test home automation directly.")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("🎤 Enter command: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if user_input.startswith('home:'):
                # Direct home automation test
                message = user_input[5:].strip()
                print(f"\n🏠 Testing home automation directly...")
                send_request(SKIPPY_HOME_URL, message)
            else:
                # Main workflow test
                print(f"\n🤖 Testing main workflow...")
                send_request(SKIPPY_MAIN_URL, user_input)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

def main():
    """Main function - choose test mode"""
    print("🤖🏠 SKIPPY INTEGRATION TESTER")
    print("=" * 40)
    print("Choose test mode:")
    print("1. Full Test Suite (recommended)")
    print("2. Interactive Testing")
    print("3. Quick Connectivity Check")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        success = run_full_test_suite()
        return 0 if success else 1
        
    elif choice == "2":
        interactive_test()
        return 0
        
    elif choice == "3":
        if run_connectivity_check():
            print("\n✅ All systems reachable!")
        else:
            print("\n❌ Connectivity issues detected!")
        return 0
        
    else:
        print("❌ Invalid choice")
        return 1

if __name__ == "__main__":
    exit(main())