#!/usr/bin/env python
"""
Validate that all required dependencies are installed and compatible.
"""

import sys
import importlib
from typing import Dict, List, Tuple

REQUIRED_PACKAGES = {
    'core': [
        'django',
        'rest_framework',
        'rest_framework_simplejwt',
        'celery',
    ],
    'ai': [
        'google.generativeai',
        'google.protobuf',
    ],
    'nlp': [
        'spacy',
        'numpy',
        'textstat',
    ],
    'web': [
        'newspaper',
        'requests',
        'wikipediaapi',
        'bs4',
    ],
    'validation': [
        'pydantic',
    ]
}

def check_package(package_name: str) -> Tuple[bool, str]:
    """Check if a package is installed and get its version"""
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, ''
    except Exception as e:
        return False, f'Error: {str(e)}'

def validate_dependencies() -> Dict[str, List[Tuple[str, bool, str]]]:
    """Validate all dependencies and return results"""
    results = {}
    
    for category, packages in REQUIRED_PACKAGES.items():
        category_results = []
        for package in packages:
            installed, version = check_package(package)
            category_results.append((package, installed, version))
        results[category] = category_results
    
    return results

def print_results(results: Dict[str, List[Tuple[str, bool, str]]]) -> None:
    """Print validation results in a formatted way"""
    all_installed = True
    
    print("\nDependency Validation Results:\n")
    print("{:<30} {:<10} {:<15}".format("Package", "Installed", "Version"))
    print("-" * 55)
    
    for category, packages in results.items():
        print(f"\n{category.upper()} DEPENDENCIES:")
        for package, installed, version in packages:
            status = "✓" if installed else "✗"
            if not installed:
                all_installed = False
            print("{:<30} {:<10} {:<15}".format(package, status, str(version)))
    
    print("\nSUMMARY:")
    if all_installed:
        print("✓ All dependencies are installed.")
    else:
        print("✗ Some dependencies are missing. Please install them using pip.")

def main() -> int:
    """Main function"""
    results = validate_dependencies()
    print_results(results)
    
    # Return exit code based on whether all dependencies are installed
    all_installed = all(installed for category in results.values() 
                      for _, installed, _ in category)
    return 0 if all_installed else 1

if __name__ == "__main__":
    sys.exit(main())