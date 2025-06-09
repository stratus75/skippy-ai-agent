#!/usr/bin/env python3
"""
Simple N8N Workflow Debugger for Skippy AI Agent
Tests both home automation and AI chat paths
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://192.168.0.229:5678"

def test_skippy():
    """Test the Skippy workflow with multiple message types"""
    
    url = f"{BASE_URL}/webhook-test/skippy/chat"
    
    # Test cases for both paths
    test_cases = [
        {
            "message": "turn on the lights",
            "user": "DebugTest",
            "expected_route": "home_automation",
            "description": "🏠 Home Automation Test"
        },
        {
            "message": "tell me a joke",
            "user": "DebugTest", 
            "expected_route": "ai_chat",
            "description": "🤖 AI Chat Test"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"🧪 TEST {i}/2: {test_case['description']}")
        print(f"{'='*50}")
        print("📤 Sending test request to:", url)
        print("📦 Payload:", {k:v for k,v in test_case.items() if k not in ['expected_route', 'description']})
        print("⏳ Sending request...")
        
        try:
            response = requests.post(url, json={
                "message": test_case["message"],
                "user": test_case["user"]
            }, timeout=15)  # Longer timeout for AI requests
            
            print(f"✅ Request sent! Status: {response.status_code}")
            
            if response.text:
                # Parse the response to check routing
                try:
                    response_json = response.json()
                    route = response_json.get('route', 'unknown')
                    response_text = response_json.get('response', 'No response')
                    
                    print(f"🎯 Route: {route}")
                    print(f"🎭 Expected: {test_case['expected_route']}")
                    
                    # Truncate long responses for readability
                    if len(response_text) > 100:
                        response_text = response_text[:100] + "..."
                    print(f"📝 Response: {response_text}")
                    
                    # Check if routing is correct
                    if route == test_case['expected_route']:
                        print("✅ ROUTING SUCCESS!")
                    else:
                        print("❌ ROUTING FAILED!")
                        
                except Exception as e:
                    # If JSON parsing fails, just show raw response
                    response_text = response.text
                    if len(response_text) > 150:
                        response_text = response_text[:150] + "..."
                    print(f"📝 Raw response: {response_text}")
                    
            else:
                print("⚠️  Empty response - Route Switch likely has no output!")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            
        # Small delay between tests
        if i < len(test_cases):
            print("\n⏳ Waiting 2 seconds before next test...")
            time.sleep(2)

def print_debug_guide():
    """Print debugging instructions"""
    print("\n🔍 NOW CHECK N8N INTERFACE:")
    print("=" * 40)
    print("1. Go to your n8n workflow")
    print("2. Look for nodes with green checkmarks (executed)")
    print("3. Click each node and check for data:")
    print("   📋 Smart Processor Node:")
    print("      • Click the node")
    print("      • Look for 'Output' or 'Data' tab")
    print("      • Should show: route, isHomeCommand, commandType")
    print("   📋 Route Switch Node:")
    print("      • Click the node")
    print("      • Check if it has ANY output data")
    print("      • If empty = condition failing")
    print("      • If has data = condition working")
    print("   📋 Final Nodes:")
    print("      • Merge Responses")
    print("      • Final Response")
    print("      • Check which one (if any) received data")

if __name__ == "__main__":
    print("🧪 N8N WORKFLOW DEBUG HELPER")
    print("=" * 40)
    
    # Test both paths
    test_skippy()
    
    # Print debugging guide
    print_debug_guide()
    
    print("\n🎯 SUMMARY:")
    print("=" * 30)
    print("✅ Both tests should work:")
    print("   🏠 Home Automation → Skippy's sassy response")
    print("   🤖 AI Chat → Ollama AI response")
    print("")
    print("❌ If either fails, check the n8n interface!")