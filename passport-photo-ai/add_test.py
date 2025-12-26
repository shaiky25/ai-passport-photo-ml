#!/usr/bin/env python3
"""
Add Test Helper - Easy way to add new tests to the deployment pipeline
Usage: python add_test.py --feature "feature-name" --category "category" --script "test_script.py"
"""

import argparse
import json
import sys
from datetime import datetime
from test_manager import TestManager

def main():
    parser = argparse.ArgumentParser(description='Add a new test to the deployment pipeline')
    parser.add_argument('--feature', required=True, help='Feature name (kebab-case)')
    parser.add_argument('--category', required=True, 
                       choices=['infrastructure', 'dependencies', 'core_functionality', 'api_endpoints', 'performance'],
                       help='Test category')
    parser.add_argument('--script', required=True, help='Test script filename')
    parser.add_argument('--name', required=True, help='Test display name')
    parser.add_argument('--description', required=True, help='Test description')
    parser.add_argument('--timeout', type=int, default=120, help='Test timeout in seconds')
    parser.add_argument('--required', action='store_true', default=True, help='Is this test required for deployment?')
    parser.add_argument('--optional', action='store_true', help='Mark test as optional')
    parser.add_argument('--success-pattern', help='Regex pattern that must be found in output for success')
    parser.add_argument('--type', choices=['script', 'curl', 'performance'], default='script', help='Test type')
    parser.add_argument('--url', help='URL for curl/performance tests')
    parser.add_argument('--threshold', type=float, help='Performance threshold in seconds')
    
    args = parser.parse_args()
    
    # Create test configuration
    test_config = {
        'name': args.name,
        'description': args.description,
        'feature': args.feature,
        'required': not args.optional,
        'timeout': args.timeout,
        'type': args.type
    }
    
    # Add type-specific fields
    if args.type == 'script':
        test_config['script'] = args.script
    elif args.type in ['curl', 'performance']:
        if not args.url:
            print("❌ URL required for curl/performance tests")
            sys.exit(1)
        test_config['url'] = args.url
        
        if args.type == 'performance' and args.threshold:
            test_config['threshold'] = args.threshold
    
    # Add success pattern if provided
    if args.success_pattern:
        test_config['success_pattern'] = args.success_pattern
    
    # Add test to registry
    manager = TestManager()
    success = manager.add_test(args.category, test_config)
    
    if success:
        print(f"\n✅ Test added successfully!")
        print(f"Category: {args.category}")
        print(f"Feature: {args.feature}")
        print(f"Script: {args.script}")
        print(f"Required: {test_config['required']}")
        print(f"\n🚀 Test will be included in next deployment pipeline run")
    else:
        print("❌ Failed to add test")
        sys.exit(1)

if __name__ == "__main__":
    main()