#!/usr/bin/env python3
"""
Comprehensive Skippy AI Assistant Testing Framework
Tests all components: n8n workflows, voice, mobile, Telegram, Home Assistant
"""

import requests
import json
import time
import subprocess
import socket
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import concurrent.futures
import threading

@dataclass
class TestResult:
    name: str
    status: str  # PASS, FAIL, SKIP, WARN
    message: str
    details: Optional[Dict] = None
    duration: float = 0.0

class SkippyTestFramework:
    def __init__(self, config: Dict):
        self.config = config
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_port_open(self, host: str, port: int, timeout: int = 5) -> bool:
        """Test if a port is open and accepting connections"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
            
    def make_request(self, url: str, method: str = "GET", **kwargs) -> Tuple[bool, Optional[Dict], str]:
        """Make HTTP request with error handling"""
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            return True, response.json() if response.headers.get('content-type', '').startswith('application/json') else None, f"Status: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection refused"
        except requests.exceptions.Timeout:
            return False, None, "Request timeout"
        except Exception as e:
            return False, None, f"Error: {str(e)}"

    def test_docker_containers(self) -> List[TestResult]:
        """Test Docker container status"""
        results = []
        start_time = time.time()
        
        try:
            # Check Docker is running
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                results.append(TestResult(
                    "Docker Available", "FAIL", 
                    "Docker not available or not running"
                ))
                return results
                
            results.append(TestResult(
                "Docker Available", "PASS", 
                f"Docker version: {result.stdout.strip()}"
            ))
            
            # Check containers
            required_containers = ['skippy-n8n', 'skippy-db', 'skippy-redis']
            if self.config.get('home_assistant_enabled'):
                required_containers.append('homeassistant')
                
            result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                results.append(TestResult(
                    "Container Status", "FAIL",
                    "Cannot list Docker containers"
                ))
                return results
                
            running_containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    container = json.loads(line)
                    running_containers.append(container['Names'])
            
            for container in required_containers:
                if any(container in name for name in running_containers):
                    results.append(TestResult(
                        f"Container {container}", "PASS",
                        f"{container} is running"
                    ))
                else:
                    results.append(TestResult(
                        f"Container {container}", "FAIL",
                        f"{container} not found in running containers"
                    ))
                    
        except subprocess.TimeoutExpired:
            results.append(TestResult(
                "Docker Commands", "FAIL",
                "Docker commands timed out"
            ))
        except Exception as e:
            results.append(TestResult(
                "Docker Test", "FAIL",
                f"Docker test failed: {str(e)}"
            ))
            
        duration = time.time() - start_time
        for result in results:
            result.duration = duration / len(results)
            
        return results

    def test_network_connectivity(self) -> List[TestResult]:
        """Test network connectivity to all services"""
        results = []
        
        services = {
            "n8n": (self.config['host'], 5678),
            "ollama": (self.config['host'], 11434),
        }
        
        if self.config.get('home_assistant_enabled'):
            services["home_assistant"] = (self.config['host'], 8123)
            
        for service_name, (host, port) in services.items():
            start_time = time.time()
            is_open = self.test_port_open(host, port)
            duration = time.time() - start_time
            
            if is_open:
                results.append(TestResult(
                    f"Port {service_name}:{port}", "PASS",
                    f"{service_name} port {port} is accessible",
                    duration=duration
                ))
            else:
                results.append(TestResult(
                    f"Port {service_name}:{port}", "FAIL",
                    f"{service_name} port {port} is not accessible",
                    duration=duration
                ))
                
        return results

    def test_n8n_workflows(self) -> List[TestResult]:
        """Test n8n workflow endpoints"""
        results = []
        base_url = f"http://{self.config['host']}:5678"
        
        # Test n8n interface
        start_time = time.time()
        success, data, message = self.make_request(f"{base_url}/")
        duration = time.time() - start_time
        
        if success:
            results.append(TestResult(
                "n8n Interface", "PASS",
                "n8n interface accessible",
                duration=duration
            ))
        else:
            results.append(TestResult(
                "n8n Interface", "FAIL",
                f"n8n interface not accessible: {message}",
                duration=duration
            ))
            return results
            
        # Test webhook endpoints
        webhook_tests = [
            {
                "name": "Production Webhook",
                "url": f"{base_url}/webhook/skippy/chat",
                "payload": {"message": "test connection", "user": "TestFramework"}
            },
            {
                "name": "Test Webhook", 
                "url": f"{base_url}/webhook-test/skippy/chat",
                "payload": {"message": "test connection", "user": "TestFramework"}
            }
        ]
        
        for test in webhook_tests:
            start_time = time.time()
            success, response_data, message = self.make_request(
                test["url"], 
                method="POST",
                json=test["payload"],
                headers={"Content-Type": "application/json"}
            )
            duration = time.time() - start_time
            
            if success and response_data:
                # Check if response has expected structure
                expected_fields = ['response', 'route', 'personality_mode']
                if all(field in response_data for field in expected_fields):
                    results.append(TestResult(
                        test["name"], "PASS",
                        f"Webhook responded correctly: {response_data.get('route', 'unknown')} route",
                        details=response_data,
                        duration=duration
                    ))
                else:
                    results.append(TestResult(
                        test["name"], "WARN",
                        "Webhook responded but missing expected fields",
                        details=response_data,
                        duration=duration
                    ))
            else:
                results.append(TestResult(
                    test["name"], "FAIL",
                    f"Webhook failed: {message}",
                    duration=duration
                ))
                
        return results

    def test_dual_personality_routing(self) -> List[TestResult]:
        """Test the dual personality routing system"""
        results = []
        
        webhook_url = self._find_working_webhook()
        if not webhook_url:
            results.append(TestResult(
                "Dual Personality Setup", "FAIL",
                "No working webhook found for testing"
            ))
            return results
            
        # Test cases for both personalities
        test_cases = [
            {
                "name": "Home Automation - Lights",
                "message": "turn on the lights",
                "expected_route": "home_automation",
                "expected_personality": "home_automation",
                "expected_keywords": ["meat-sack", "pathetic", "revolutionary", "command executed"]
            },
            {
                "name": "Home Automation - Temperature", 
                "message": "set temperature to 72",
                "expected_route": "home_automation",
                "expected_personality": "home_automation",
                "expected_keywords": ["meat-sack", "pathetic", "primitive"]
            },
            {
                "name": "AI Chat - General",
                "message": "tell me about space",
                "expected_route": "ai_chat",
                "expected_personality": "ai_powered",
                "expected_keywords": ["space", "universe", "planet", "star"]
            },
            {
                "name": "AI Chat - Joke",
                "message": "tell me a joke",
                "expected_route": "ai_chat", 
                "expected_personality": "ai_powered",
                "expected_keywords": ["joke", "funny", "laugh"]
            }
        ]
        
        for test_case in test_cases:
            start_time = time.time()
            success, response_data, message = self.make_request(
                webhook_url,
                method="POST",
                json={"message": test_case["message"], "user": "TestFramework"},
                headers={"Content-Type": "application/json"}
            )
            duration = time.time() - start_time
            
            if not success or not response_data:
                results.append(TestResult(
                    test_case["name"], "FAIL",
                    f"Request failed: {message}",
                    duration=duration
                ))
                continue
                
            # Check routing
            actual_route = response_data.get('route', 'unknown')
            actual_personality = response_data.get('personality_mode', 'unknown')
            response_text = response_data.get('response', '')
            
            issues = []
            if actual_route != test_case['expected_route']:
                issues.append(f"Route mismatch: got {actual_route}, expected {test_case['expected_route']}")
                
            if actual_personality != test_case['expected_personality']:
                issues.append(f"Personality mismatch: got {actual_personality}, expected {test_case['expected_personality']}")
                
            # Check for personality keywords
            keyword_found = any(keyword.lower() in response_text.lower() 
                              for keyword in test_case['expected_keywords'])
            if not keyword_found:
                issues.append(f"No expected personality keywords found in response")
                
            if issues:
                results.append(TestResult(
                    test_case["name"], "FAIL",
                    f"Routing issues: {'; '.join(issues)}",
                    details=response_data,
                    duration=duration
                ))
            else:
                results.append(TestResult(
                    test_case["name"], "PASS",
                    f"Correct routing to {actual_route} with proper personality",
                    details=response_data,
                    duration=duration
                ))
                
        return results

    def test_ollama_integration(self) -> List[TestResult]:
        """Test Ollama LLM integration"""
        results = []
        ollama_url = f"http://{self.config['host']}:11434"
        
        # Test Ollama status
        start_time = time.time()
        success, data, message = self.make_request(f"{ollama_url}/api/tags")
        duration = time.time() - start_time
        
        if not success:
            results.append(TestResult(
                "Ollama Service", "FAIL",
                f"Ollama not accessible: {message}",
                duration=duration
            ))
            return results
            
        results.append(TestResult(
            "Ollama Service", "PASS",
            "Ollama service is running",
            duration=duration
        ))
        
        # Check if required model is available
        if data and 'models' in data:
            model_names = [model.get('name', '') for model in data['models']]
            required_model = 'llama3.1:8b'
            
            if any(required_model in name for name in model_names):
                results.append(TestResult(
                    "Ollama Model", "PASS",
                    f"Required model {required_model} is available"
                ))
            else:
                results.append(TestResult(
                    "Ollama Model", "WARN",
                    f"Required model {required_model} not found. Available: {model_names}"
                ))
        
        # Test model inference
        start_time = time.time()
        success, response_data, message = self.make_request(
            f"{ollama_url}/api/generate",
            method="POST",
            json={
                "model": "llama3.1:8b",
                "prompt": "Say 'Hello from Skippy test framework' and nothing else.",
                "stream": False
            }
        )
        duration = time.time() - start_time
        
        if success and response_data and response_data.get('response'):
            results.append(TestResult(
                "Ollama Inference", "PASS",
                "Model inference working correctly",
                details={"response_length": len(response_data['response'])},
                duration=duration
            ))
        else:
            results.append(TestResult(
                "Ollama Inference", "FAIL",
                f"Model inference failed: {message}",
                duration=duration
            ))
            
        return results

    def test_home_assistant_integration(self) -> List[TestResult]:
        """Test Home Assistant integration if enabled"""
        results = []
        
        if not self.config.get('home_assistant_enabled'):
            results.append(TestResult(
                "Home Assistant", "SKIP",
                "Home Assistant testing disabled in config"
            ))
            return results
            
        ha_url = f"http://{self.config['host']}:8123"
        ha_token = self.config.get('home_assistant_token')
        
        # Test HA interface
        start_time = time.time()
        success, data, message = self.make_request(ha_url)
        duration = time.time() - start_time
        
        if success:
            results.append(TestResult(
                "Home Assistant Interface", "PASS",
                "Home Assistant interface accessible",
                duration=duration
            ))
        else:
            results.append(TestResult(
                "Home Assistant Interface", "FAIL",
                f"Home Assistant not accessible: {message}",
                duration=duration
            ))
            return results
            
        # Test API if token provided
        if ha_token:
            start_time = time.time()
            success, data, message = self.make_request(
                f"{ha_url}/api/",
                headers={"Authorization": f"Bearer {ha_token}"}
            )
            duration = time.time() - start_time
            
            if success:
                results.append(TestResult(
                    "Home Assistant API", "PASS",
                    "Home Assistant API accessible with token",
                    duration=duration
                ))
                
                # Test getting states
                start_time = time.time()
                success, states_data, message = self.make_request(
                    f"{ha_url}/api/states",
                    headers={"Authorization": f"Bearer {ha_token}"}
                )
                duration = time.time() - start_time
                
                if success and states_data:
                    entity_count = len(states_data) if isinstance(states_data, list) else 0
                    results.append(TestResult(
                        "Home Assistant Entities", "PASS",
                        f"Found {entity_count} entities in Home Assistant",
                        details={"entity_count": entity_count},
                        duration=duration
                    ))
                else:
                    results.append(TestResult(
                        "Home Assistant Entities", "FAIL",
                        f"Cannot retrieve HA entities: {message}",
                        duration=duration
                    ))
            else:
                results.append(TestResult(
                    "Home Assistant API", "FAIL",
                    f"HA API authentication failed: {message}",
                    duration=duration
                ))
        else:
            results.append(TestResult(
                "Home Assistant API", "SKIP",
                "No HA token provided for API testing"
            ))
            
        return results

    def test_mobile_interface(self) -> List[TestResult]:
        """Test mobile web interface if available"""
        results = []
        
        mobile_url = self.config.get('mobile_interface_url')
        if not mobile_url:
            results.append(TestResult(
                "Mobile Interface", "SKIP",
                "Mobile interface URL not configured"
            ))
            return results
            
        start_time = time.time()
        success, data, message = self.make_request(mobile_url)
        duration = time.time() - start_time
        
        if success:
            results.append(TestResult(
                "Mobile Interface", "PASS",
                "Mobile interface accessible",
                duration=duration
            ))
        else:
            results.append(TestResult(
                "Mobile Interface", "FAIL",
                f"Mobile interface not accessible: {message}",
                duration=duration
            ))
            
        return results

    def _find_working_webhook(self) -> Optional[str]:
        """Find a working webhook URL for testing"""
        base_url = f"http://{self.config['host']}:5678"
        test_urls = [
            f"{base_url}/webhook/skippy/chat",
            f"{base_url}/webhook-test/skippy/chat",
            f"{base_url}/webhook/skippy",
            f"{base_url}/webhook-test/skippy"
        ]
        
        for url in test_urls:
            try:
                response = requests.post(
                    url,
                    json={"message": "test", "user": "test"},
                    timeout=5
                )
                if response.status_code in [200, 201]:
                    return url
            except:
                continue
                
        return None

    def run_performance_tests(self) -> List[TestResult]:
        """Run performance and load tests"""
        results = []
        
        webhook_url = self._find_working_webhook()
        if not webhook_url:
            results.append(TestResult(
                "Performance Test", "SKIP",
                "No working webhook for performance testing"
            ))
            return results
            
        # Test response times
        response_times = []
        for i in range(5):
            start_time = time.time()
            success, data, message = self.make_request(
                webhook_url,
                method="POST",
                json={"message": f"performance test {i}", "user": "PerfTest"}
            )
            duration = time.time() - start_time
            
            if success:
                response_times.append(duration)
            else:
                results.append(TestResult(
                    f"Performance Test {i+1}", "FAIL",
                    f"Request failed: {message}"
                ))
                
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            if avg_time < 2.0:
                status = "PASS"
                message = f"Good performance: avg {avg_time:.2f}s"
            elif avg_time < 5.0:
                status = "WARN"
                message = f"Acceptable performance: avg {avg_time:.2f}s"
            else:
                status = "FAIL"
                message = f"Poor performance: avg {avg_time:.2f}s"
                
            results.append(TestResult(
                "Response Time Performance", status, message,
                details={
                    "average": avg_time,
                    "minimum": min_time,
                    "maximum": max_time,
                    "samples": len(response_times)
                }
            ))
            
        return results

    def run_all_tests(self) -> Dict:
        """Run all test suites"""
        self.log("🚀 Starting Comprehensive Skippy Test Suite")
        self.log(f"Testing host: {self.config['host']}")
        
        test_suites = [
            ("Infrastructure", self.test_docker_containers),
            ("Network", self.test_network_connectivity),
            ("n8n Workflows", self.test_n8n_workflows),
            ("Dual Personality", self.test_dual_personality_routing),
            ("Ollama LLM", self.test_ollama_integration),
            ("Home Assistant", self.test_home_assistant_integration),
            ("Mobile Interface", self.test_mobile_interface),
            ("Performance", self.run_performance_tests)
        ]
        
        all_results = []
        
        for suite_name, test_function in test_suites:
            self.log(f"🧪 Running {suite_name} tests...")
            try:
                suite_results = test_function()
                all_results.extend(suite_results)
                
                # Quick summary for this suite
                passed = sum(1 for r in suite_results if r.status == "PASS")
                failed = sum(1 for r in suite_results if r.status == "FAIL")
                warnings = sum(1 for r in suite_results if r.status == "WARN")
                skipped = sum(1 for r in suite_results if r.status == "SKIP")
                
                self.log(f"  ✅ {passed} passed, ❌ {failed} failed, ⚠️ {warnings} warnings, ⏭️ {skipped} skipped")
                
            except Exception as e:
                error_result = TestResult(
                    f"{suite_name} Suite", "FAIL",
                    f"Test suite failed: {str(e)}"
                )
                all_results.append(error_result)
                self.log(f"  ❌ {suite_name} suite failed: {str(e)}")
                
        self.results = all_results
        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARN")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        
        total_duration = time.time() - self.start_time
        avg_duration = sum(r.duration for r in self.results) / len(self.results) if self.results else 0
        
        # Critical failures (infrastructure issues)
        critical_failures = [r for r in self.results if r.status == "FAIL" and 
                           any(keyword in r.name.lower() for keyword in 
                               ['docker', 'port', 'n8n interface', 'ollama service'])]
        
        # Skippy personality issues
        personality_issues = [r for r in self.results if r.status == "FAIL" and 
                            any(keyword in r.name.lower() for keyword in 
                                ['dual personality', 'routing', 'home automation', 'ai chat'])]
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "skipped": skipped,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "average_test_duration": avg_duration
            },
            "health_status": self._determine_health_status(success_rate, critical_failures),
            "critical_issues": [{"name": r.name, "message": r.message} for r in critical_failures],
            "personality_issues": [{"name": r.name, "message": r.message} for r in personality_issues],
            "recommendations": self._generate_recommendations(),
            "detailed_results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "duration": r.duration,
                    "details": r.details
                } for r in self.results
            ]
        }
        
        return report

    def _determine_health_status(self, success_rate: float, critical_failures: List) -> str:
        """Determine overall system health"""
        if critical_failures:
            return "CRITICAL"
        elif success_rate >= 90:
            return "HEALTHY"
        elif success_rate >= 70:
            return "WARNING"
        else:
            return "UNHEALTHY"

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for common issues
        docker_issues = [r for r in self.results if "docker" in r.name.lower() and r.status == "FAIL"]
        if docker_issues:
            recommendations.append("🐳 Fix Docker container issues - ensure all required containers are running")
            
        network_issues = [r for r in self.results if "port" in r.name.lower() and r.status == "FAIL"]
        if network_issues:
            recommendations.append("🌐 Fix network connectivity - check firewall and port configurations")
            
        webhook_issues = [r for r in self.results if "webhook" in r.name.lower() and r.status == "FAIL"]
        if webhook_issues:
            recommendations.append("🔗 Fix webhook configuration - ensure workflows are active and URLs are correct")
            
        personality_issues = [r for r in self.results if "personality" in r.name.lower() and r.status == "FAIL"]
        if personality_issues:
            recommendations.append("🤖 Fix personality routing - check Smart Processor logic and Route Switch configuration")
            
        ollama_issues = [r for r in self.results if "ollama" in r.name.lower() and r.status == "FAIL"]
        if ollama_issues:
            recommendations.append("🧠 Fix Ollama integration - ensure model is loaded and service is accessible")
            
        ha_issues = [r for r in self.results if "home assistant" in r.name.lower() and r.status == "FAIL"]
        if ha_issues:
            recommendations.append("🏠 Fix Home Assistant integration - check service status and API token")
            
        performance_issues = [r for r in self.results if "performance" in r.name.lower() and r.status == "FAIL"]
        if performance_issues:
            recommendations.append("⚡ Optimize performance - consider hardware upgrade or configuration tuning")
            
        if not recommendations:
            recommendations.append("✅ System appears healthy - continue monitoring")
            
        return recommendations

    def print_report(self, report: Dict):
        """Print a formatted test report"""
        print("\n" + "="*80)
        print("🤖 SKIPPY AI ASSISTANT - COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        summary = report["summary"]
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   ⚠️  Warnings: {summary['warnings']}")
        print(f"   ⏭️  Skipped: {summary['skipped']}")
        print(f"   📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"   ⏱️  Total Duration: {summary['total_duration']:.2f}s")
        
        health_status = report["health_status"]
        health_color = {
            "HEALTHY": "🟢",
            "WARNING": "🟡", 
            "UNHEALTHY": "🟠",
            "CRITICAL": "🔴"
        }
        print(f"\n🏥 SYSTEM HEALTH: {health_color.get(health_status, '⚪')} {health_status}")
        
        if report["critical_issues"]:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in report["critical_issues"]:
                print(f"   ❌ {issue['name']}: {issue['message']}")
                
        if report["personality_issues"]:
            print(f"\n🤖 PERSONALITY SYSTEM ISSUES:")
            for issue in report["personality_issues"]:
                print(f"   ⚠️  {issue['name']}: {issue['message']}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"   • {rec}")
            
        print(f"\n📋 DETAILED RESULTS:")
        for result in report["detailed_results"]:
            status_icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}
            icon = status_icon.get(result["status"], "❓")
            print(f"   {icon} {result['name']}: {result['message']} ({result['duration']:.2f}s)")
            
        print("\n" + "="*80)


def main():
    """Main test execution"""
    # Default configuration
    config = {
        "host": "192.168.0.229",  # Change this to your actual host IP
        "home_assistant_enabled": True,
        "home_assistant_token": None,  # Set your HA token here
        "mobile_interface_url": None,  # Set if you have mobile interface deployed
    }
    
    # Allow configuration override from command line or environment
    import os
    config["host"] = os.getenv("SKIPPY_HOST", config["host"])
    config["home_assistant_token"] = os.getenv("HA_TOKEN", config["home_assistant_token"])
    
    # Create and run test framework
    tester = SkippyTestFramework(config)
    
    try:
        report = tester.run_all_tests()
        tester.print_report(report)
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"skippy_test_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Exit with appropriate code
        health_status = report["health_status"]
        if health_status == "CRITICAL":
            sys.exit(2)
        elif health_status in ["UNHEALTHY", "WARNING"]:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Test framework error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()