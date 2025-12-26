#!/usr/bin/env python3
"""
Test Manager - Dynamic test execution based on test registry
Automatically runs all registered tests and makes it easy to add new ones
"""

import json
import subprocess
import time
import sys
import os
from datetime import datetime

class TestManager:
    def __init__(self, registry_file="test_registry.json"):
        self.registry_file = registry_file
        self.load_registry()
        self.results = {}
        
    def load_registry(self):
        """Load test registry from JSON file"""
        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)
                self.registry = data['test_registry']
                print(f"✅ Loaded test registry with {self.count_total_tests()} tests")
        except FileNotFoundError:
            print(f"❌ Test registry file not found: {self.registry_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in test registry: {e}")
            sys.exit(1)
    
    def count_total_tests(self):
        """Count total number of tests across all categories"""
        total = 0
        for category in self.registry['categories'].values():
            total += len(category['tests'])
        return total
    
    def run_script_test(self, test, category_name):
        """Run a Python script test"""
        script = test['script']
        timeout = test.get('timeout', 60)
        
        print(f"  Running: {script}")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                ['python', script], 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            success = result.returncode == 0
            
            # Check for success pattern if specified
            if success and 'success_pattern' in test:
                import re
                pattern = test['success_pattern']
                if not re.search(pattern, result.stdout):
                    success = False
                    result.stderr += f"\nSuccess pattern not found: {pattern}"
            
            self.results[f"{category_name}.{test['name']}"] = {
                'success': success,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
            if success:
                print(f"    ✅ PASSED ({execution_time:.2f}s)")
            else:
                print(f"    ❌ FAILED ({execution_time:.2f}s)")
                if result.stderr:
                    print(f"    Error: {result.stderr[:200]}...")
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"    ⏰ TIMEOUT after {timeout}s")
            self.results[f"{category_name}.{test['name']}"] = {
                'success': False,
                'execution_time': timeout,
                'stdout': '',
                'stderr': f'Test timed out after {timeout} seconds',
                'returncode': -1
            }
            return False
        except Exception as e:
            print(f"    ❌ EXCEPTION: {e}")
            self.results[f"{category_name}.{test['name']}"] = {
                'success': False,
                'execution_time': 0,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
            return False
    
    def run_curl_test(self, test, category_name):
        """Run a curl-based API test"""
        url = test['url']
        timeout = test.get('timeout', 10)
        success_pattern = test.get('success_pattern', '')
        
        print(f"  Testing: {url}")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                ['curl', '-s', url], 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            success = result.returncode == 0
            
            # Check for success pattern
            if success and success_pattern:
                import re
                if not re.search(success_pattern, result.stdout):
                    success = False
                    result.stderr += f"\nSuccess pattern not found: {success_pattern}"
            
            self.results[f"{category_name}.{test['name']}"] = {
                'success': success,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
            if success:
                print(f"    ✅ PASSED ({execution_time:.2f}s)")
            else:
                print(f"    ❌ FAILED ({execution_time:.2f}s)")
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"    ⏰ TIMEOUT after {timeout}s")
            return False
        except Exception as e:
            print(f"    ❌ EXCEPTION: {e}")
            return False
    
    def run_performance_test(self, test, category_name):
        """Run a performance test"""
        url = test['url']
        timeout = test.get('timeout', 10)
        threshold = test.get('threshold', 1.0)
        
        print(f"  Performance testing: {url}")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                ['curl', '-s', url], 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            success = result.returncode == 0 and execution_time < threshold
            
            self.results[f"{category_name}.{test['name']}"] = {
                'success': success,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr if not success else '',
                'returncode': result.returncode,
                'threshold': threshold
            }
            
            if success:
                print(f"    ✅ PASSED ({execution_time:.2f}s < {threshold}s)")
            else:
                print(f"    ❌ FAILED ({execution_time:.2f}s >= {threshold}s)")
            
            return success
            
        except Exception as e:
            print(f"    ❌ EXCEPTION: {e}")
            return False
    
    def run_category_tests(self, category_name, category_data):
        """Run all tests in a category"""
        print(f"\n🔍 {category_name.upper().replace('_', ' ')}")
        print(f"   {category_data['description']}")
        print("-" * 60)
        
        category_results = []
        
        for test in category_data['tests']:
            test_name = test['name']
            test_type = test.get('type', 'script')
            required = test.get('required', True)
            
            print(f"\n📋 {test_name}")
            print(f"   {test['description']}")
            
            if test_type == 'script':
                success = self.run_script_test(test, category_name)
            elif test_type == 'curl':
                success = self.run_curl_test(test, category_name)
            elif test_type == 'performance':
                success = self.run_performance_test(test, category_name)
            else:
                print(f"    ❌ Unknown test type: {test_type}")
                success = False
            
            category_results.append({
                'name': test_name,
                'success': success,
                'required': required
            })
        
        return category_results
    
    def run_all_tests(self):
        """Run all tests from the registry"""
        print("🚀 COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"Registry: {self.registry['description']}")
        print(f"Last Updated: {self.registry['last_updated']}")
        print(f"Total Tests: {self.count_total_tests()}")
        
        all_results = []
        
        for category_name, category_data in self.registry['categories'].items():
            category_results = self.run_category_tests(category_name, category_data)
            all_results.extend(category_results)
        
        return self.generate_summary(all_results)
    
    def generate_summary(self, all_results):
        """Generate test execution summary"""
        print("\n" + "=" * 70)
        print("📊 TEST EXECUTION SUMMARY")
        print("=" * 70)
        
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        required_tests = [r for r in all_results if r['required']]
        required_passed = sum(1 for r in required_tests if r['success'])
        required_failed = len(required_tests) - required_passed
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print()
        print(f"Required Tests: {len(required_tests)}")
        print(f"Required Passed: {required_passed}")
        print(f"Required Failed: {required_failed}")
        
        if required_failed == 0:
            print("\n🎉 ALL REQUIRED TESTS PASSED!")
            print("✅ Ready for deployment")
            deployment_ready = True
        else:
            print(f"\n❌ {required_failed} REQUIRED TESTS FAILED")
            print("❌ NOT ready for deployment")
            deployment_ready = False
        
        # Show failed tests
        failed_required = [r for r in required_tests if not r['success']]
        if failed_required:
            print("\n❌ Failed Required Tests:")
            for test in failed_required:
                print(f"  • {test['name']}")
        
        # Show optional test failures
        failed_optional = [r for r in all_results if not r['success'] and not r['required']]
        if failed_optional:
            print("\n⚠️ Failed Optional Tests:")
            for test in failed_optional:
                print(f"  • {test['name']}")
        
        return deployment_ready
    
    def add_test(self, category, test_config):
        """Add a new test to the registry"""
        if category not in self.registry['categories']:
            print(f"❌ Category '{category}' not found")
            return False
        
        # Add timestamp
        test_config['added_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Add to registry
        self.registry['categories'][category]['tests'].append(test_config)
        
        # Save updated registry
        self.save_registry()
        
        print(f"✅ Added test '{test_config['name']}' to category '{category}'")
        return True
    
    def save_registry(self):
        """Save the updated registry back to file"""
        try:
            data = {'test_registry': self.registry}
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Registry saved to {self.registry_file}")
        except Exception as e:
            print(f"❌ Failed to save registry: {e}")

def main():
    """Main execution function"""
    manager = TestManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--add-test':
        # Interactive test addition mode
        print("🔧 ADD NEW TEST MODE")
        print("=" * 30)
        
        # Show available categories
        print("Available categories:")
        for i, category in enumerate(manager.registry['categories'].keys(), 1):
            print(f"  {i}. {category}")
        
        # This would be expanded for interactive test addition
        print("Use the add_test() method programmatically for now")
        return
    
    # Run all tests
    success = manager.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()