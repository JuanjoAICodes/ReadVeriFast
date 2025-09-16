#!/usr/bin/env python
"""
Test runner script for VeriFast application.
"""

import os
import sys
import django
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def run_unit_tests():
    """Run unit tests only"""
    print("Running unit tests...")
    cmd = [
        sys.executable, '-m', 'pytest',
        'verifast_app/tests/test_services.py',
        'verifast_app/tests/test_health.py',
        '-v', '--tb=short'
    ]
    return subprocess.run(cmd).returncode

def run_integration_tests():
    """Run integration tests only"""
    print("Running integration tests...")
    cmd = [
        sys.executable, '-m', 'pytest',
        'verifast_app/tests/test_tasks.py',
        'verifast_app/tests/test_integration.py',
        '-v', '--tb=short'
    ]
    return subprocess.run(cmd).returncode

def run_all_tests():
    """Run all tests"""
    print("Running all tests...")
    cmd = [
        sys.executable, '-m', 'pytest',
        'verifast_app/tests/',
        '-v', '--tb=short'
    ]
    return subprocess.run(cmd).returncode

def run_coverage_tests():
    """Run tests with coverage report"""
    print("Running tests with coverage...")
    cmd = [
        sys.executable, '-m', 'pytest',
        'verifast_app/tests/',
        '--cov=verifast_app',
        '--cov-report=html',
        '--cov-report=term-missing',
        '-v'
    ]
    return subprocess.run(cmd).returncode

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_tests.py [unit|integration|all|coverage]")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    if test_type == 'unit':
        exit_code = run_unit_tests()
    elif test_type == 'integration':
        exit_code = run_integration_tests()
    elif test_type == 'all':
        exit_code = run_all_tests()
    elif test_type == 'coverage':
        exit_code = run_coverage_tests()
    else:
        print(f"Unknown test type: {test_type}")
        print("Available options: unit, integration, all, coverage")
        sys.exit(1)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()