# test_skippy.py - Comprehensive testing script for Skippy AI Agent

import asyncio
import json
import requests
import websockets
import time
import logging
from datetime import datetime
import psycopg2
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SkippyTester:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.voice_ws_url = "ws://localhost:8765"
        self.n8n_url = "http://localhost:5678"
        self.results = {}
        
    def test_database_connection(self):
        """Test PostgreSQL database connectivity"""
        logger.info("Testing database connection...")
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="skippy",
                user="skippy",
                password="skippy_secure_password"
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM conversations")
                count = cursor.fetchone()[0]
                
            conn.close()
            self.results['database'] = {
                'status': 'PASS',
                'details': f'Connected successfully. {count} conversations in database.'
            }
            logger.info("✅ Database connection test passed")
            return True
            
        except Exception as e:
            self.results['database'] = {
                'status': 'FAIL',
                'details': f'Connection failed: {str(e)}'
            }
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    def test_redis_connection(self):
        """Test Redis connectivity"""
        logger.info("Testing Redis connection...")
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            
            # Test basic operations
            test_key = f"test:{datetime.now().isoformat()}"
            r.set(test_key, "test_value", ex=10)
            value = r.get(test_key)
            
            if value == "test_value":
                self.results['redis'] = {
                    'status': 'PASS',
                    'details': 'Connected successfully and basic operations work'
                }
                logger.info("✅ Redis connection test passed")
                return True
            else:
                raise Exception("Redis read/write test failed")
                
        except Exception as e:
            self.results['redis'] = {
                'status': 'FAIL',
                'details': f'Connection failed: {str(e)}'
            }
            logger.error(f"❌ Redis connection test failed: {e}")
            return False
    
    def test_personality_core_health(self):
        """Test Skippy Personality Core health endpoint"""
        logger.info("Testing Personality Core health...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                self.results['personality_health'] = {
                    'status': 'PASS',
                    'details': f'Health check passed. Services: {health_data.get("services", {})}'
                }
                logger.info("✅ Personality Core health test passed")
                return True
            else:
                raise Exception(f"Health check returned status {response.status_code}")
                
        except Exception as e:
            self.results['personality_health'] = {
                'status': 'FAIL',
                'details': f'Health check failed: {str(e)}'
            }
            logger.error(f"❌ Personality Core health test failed: {e}")
            return False
    
    def test_personality_core_chat(self):
        """Test Skippy Personality Core chat functionality"""
        logger.info("Testing Personality Core chat...")
        try:
            test_message = {
                "message": "Hello Skippy, this is a test message",
                "user_id": "test_user",
                "context": {"source": "test_script"}
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=test_message,
                timeout=15
            )
            
            if response.status_code == 200:
                chat_data = response.json()
                response_text = chat_data.get('response', '')
                
                if response_text and len(response_text) > 0:
                    self.results['personality_chat'] = {
                        'status': 'PASS',
                        'details': f'Chat successful. Response: "{response_text[:50]}..."'
                    }
                    logger.info("✅ Personality Core chat test passed")
                    return True
                else:
                    raise Exception("Empty response received")
            else:
                raise Exception(f"Chat request returned status {response.status_code}")
                
        except Exception as e:
            self.results['personality_chat'] = {
                'status': 'FAIL',
                'details': f'Chat test failed: {str(e)}'
            }
            logger.error(f"❌ Personality Core chat test failed: {e}")
            return False
    
    async def test_voice_service_websocket(self):
        """Test Voice Service WebSocket connectivity"""
        logger.info("Testing Voice Service WebSocket...")
        try:
            async with websockets.connect(self.voice_ws_url) as websocket:
                # Test status request
                status_request = {"type": "status"}
                await websocket.send(json.dumps(status_request))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                status_data = json.loads(response)
                
                if status_data.get('status') == 'running':
                    self.results['voice_websocket'] = {
                        'status': 'PASS',
                        'details': f'WebSocket connected. Voice service running. Services: {status_data.get("services", {})}'
                    }
                    logger.info("✅ Voice Service WebSocket test passed")
                    return True
                else:
                    raise Exception(f"Unexpected status: {status_data}")
                    
        except Exception as e:
            self.results['voice_websocket'] = {
                'status': 'FAIL',
                'details': f'WebSocket test failed: {str(e)}'
            }
            logger.error(f"❌ Voice Service WebSocket test failed: {e}")
            return False
    
    async def test_voice_service_tts(self):
        """Test Voice Service text-to-speech"""
        logger.info("Testing Voice Service TTS...")
        try:
            async with websockets.connect(self.voice_ws_url) as websocket:
                # Test TTS request
                tts_request = {
                    "type": "speak",
                    "text": "This is a test of Skippy's text to speech system"
                }
                await websocket.send(json.dumps(tts_request))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=15)
                response_data = json.loads(response)
                
                if response_data.get('status') == 'spoken':
                    self.results['voice_tts'] = {
                        'status': 'PASS',
                        'details': 'TTS test completed successfully'
                    }
                    logger.info("✅ Voice Service TTS test passed")
                    return True
                else:
                    raise Exception(f"TTS failed: {response_data}")
                    
        except Exception as e:
            self.results['voice_tts'] = {
                'status': 'FAIL',
                'details': f'TTS test failed: {str(e)}'
            }
            logger.error(f"❌ Voice Service TTS test failed: {e}")
            return False
    
    def test_n8n_connectivity(self):
        """Test n8n hub connectivity"""
        logger.info("Testing n8n connectivity...")
        try:
            # n8n health check endpoint
            response = requests.get(f"{self.n8n_url}/healthz", timeout=10)
            
            if response.status_code == 200:
                self.results['n8n_health'] = {
                    'status': 'PASS',
                    'details': 'n8n health check passed'
                }
                logger.info("✅ n8n connectivity test passed")
                return True
            else:
                raise Exception(f"n8n health check returned status {response.status_code}")
                
        except Exception as e:
            self.results['n8n_health'] = {
                'status': 'FAIL',
                'details': f'n8n connectivity failed: {str(e)}'
            }
            logger.error(f"❌ n8n connectivity test failed: {e}")
            return False
    
    def test_conversation_logging(self):
        """Test conversation logging functionality"""
        logger.info("Testing conversation logging...")
        try:
            # Send a test conversation
            test_message = {
                "message": "Test conversation logging",
                "user_id": "log_test_user",
                "context": {"source": "logging_test"}
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=test_message,
                timeout=15
            )
            
            if response.status_code != 200:
                raise Exception(f"Chat request failed with status {response.status_code}")
            
            # Wait a moment for logging to complete
            time.sleep(2)
            
            # Check if conversation was logged in database
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="skippy",
                user="skippy",
                password="skippy_secure_password"
            )
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM conversations 
                    WHERE user_id = 'log_test_user' 
                    AND message = 'Test conversation logging'
                """)
                count = cursor.fetchone()[0]
                
            conn.close()
            
            if count > 0:
                self.results['conversation_logging'] = {
                    'status': 'PASS',
                    'details': f'Conversation successfully logged to database'
                }
                logger.info("✅ Conversation logging test passed")
                return True
            else:
                raise Exception("Conversation not found in database")
                
        except Exception as e:
            self.results['conversation_logging'] = {
                'status': 'FAIL',
                'details': f'Logging test failed: {str(e)}'
            }
            logger.error(f"❌ Conversation logging test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests and generate report"""
        logger.info("🚀 Starting Skippy AI Agent comprehensive testing...")
        logger.info("=" * 60)
        
        # Database tests
        self.test_database_connection()
        self.test_redis_connection()
        
        # Service health tests
        self.test_personality_core_health()
        self.test_n8n_connectivity()
        
        # Functionality tests
        self.test_personality_core_chat()
        await self.test_voice_service_websocket()
        await self.test_voice_service_tts()
        
        # Integration tests
        self.test_conversation_logging()
        
        # Generate report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("=" * 60)
        logger.info("📊 SKIPPY AI AGENT TEST REPORT")
        logger.info("=" * 60)
        
        passed_tests = 0
        total_tests = len(self.results)
        
        for test_name, result in self.results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            logger.info(f"{status_icon} {test_name.upper()}: {result['status']}")
            logger.info(f"   Details: {result['details']}")
            logger.info("")
            
            if result['status'] == 'PASS':
                passed_tests += 1
        
        logger.info("=" * 60)
        logger.info(f"📈 SUMMARY: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Skippy AI Agent is ready to go!")
        else:
            logger.info("⚠️  Some tests failed. Please check the details above.")
            logger.info("   Common fixes:")
            logger.info("   - Ensure all Docker containers are running: docker-compose ps")
            logger.info("   - Check service logs: docker-compose logs [service-name]")
            logger.info("   - Verify network connectivity between services")
        
        logger.info("=" * 60)
        
        # Save report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
            },
            "results": self.results
        }
        
        with open("skippy_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"📄 Detailed report saved to: skippy_test_report.json")

async def main():
    """Main testing function"""
    tester = SkippyTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())

# ==================================================================
# quick_test.py - Simple connectivity test

#!/usr/bin/env python3
"""
Quick connectivity test for Skippy AI Agent
Run this to quickly verify all services are up and responding
"""

import requests
import sys
import time

def quick_test():
    print("🔍 Quick Skippy Health Check")
    print("-" * 30)
    
    services = {
        "Personality Core": "http://localhost:8080/health",
        "n8n Hub": "http://localhost:5678/healthz",
        "PostgreSQL": None,  # Will test via personality core
        "Redis": None,       # Will test via personality core
    }
    
    all_healthy = True
    
    for service_name, url in services.items():
        if url:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name}: Healthy")
                else:
                    print(f"❌ {service_name}: Unhealthy