#!/usr/bin/env python3
"""
Quick test with the correct URL from your previous tests
"""

import requests
import json

# Use your actual working URL
MAIN_URL = "http://192.168.0.229:5678/webhook/skippy/chat"
HOME_URL = "http://192.168.0.229:5678/webhook/skippy-home-control"

def quick_test():
    print("🧪 QUICK TEST WITH CORRECT URLS")
    print("=" * 40)
    
    tests = [
        (MAIN_URL, "turn on the lights", "Main workflow - home command"),
        (MAIN_URL, "tell me a joke", "Main workflow - AI command"), 
        (HOME_URL, "turn on the lights", "Home workflow direct")
    ]
    
    for url, message, description in tests:
        print(f"\n🔹 {description}")
        print(f"URL: {url}")
        print(f"Message: '{message}'")
        
        try:
            response = requests.post(url, 
                                   json={"message": message, "user": "TestUser"},
                                   timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success")
                print(f"Route: {result.get('route', 'Not specified')}")
                print(f"Response: {result.get('response', 'No response')[:100]}...")
            else:
                print(f"❌ Failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()