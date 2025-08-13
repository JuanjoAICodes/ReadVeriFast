#!/usr/bin/env python3
"""
Simple API Endpoint Test Script
Tests that VeriFast API endpoints are accessible and working
"""

import requests
import json
import sys
from urllib.parse import urljoin

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_base = urljoin(base_url, "/api/v1/")
        self.session = requests.Session()
        self.token = None
        
    def test_endpoint(self, endpoint, method="GET", data=None, auth_required=True):
        """Test a single API endpoint"""
        url = urljoin(self.api_base, endpoint)
        
        headers = {'Content-Type': 'application/json'}
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data)
            else:
                return False, f"Unsupported method: {method}"
            
            return True, {
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'response_size': len(response.content),
                'response_preview': response.text[:200] if response.text else ''
            }
            
        except requests.exceptions.ConnectionError:
            return False, "Connection refused - Django server not running"
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
    
    def test_all_endpoints(self):
        """Test all major API endpoints"""
        print("🧪 Testing VeriFast API Endpoints")
        print("=" * 50)
        
        # Test endpoints that don't require authentication
        public_endpoints = [
            ("auth/login/", "POST"),
            ("auth/register/", "POST"),
        ]
        
        print("\n📖 Testing Public Endpoints:")
        for endpoint, method in public_endpoints:
            success, result = self.test_endpoint(endpoint, method, auth_required=False)
            status_icon = "✅" if success else "❌"
            
            if success:
                status_code = result['status_code']
                if status_code in [200, 201, 400, 405]:  # Expected responses
                    print(f"  {status_icon} {method} {endpoint} - HTTP {status_code}")
                else:
                    print(f"  ⚠️  {method} {endpoint} - HTTP {status_code} (unexpected)")
            else:
                print(f"  {status_icon} {method} {endpoint} - {result}")
        
        # Test endpoints that require authentication (will get 401)
        protected_endpoints = [
            ("auth/profile/", "GET"),
            ("articles/", "GET"),
            ("users/me/stats/", "GET"),
            ("xp/balance/", "GET"),
            ("xp/features/", "GET"),
        ]
        
        print("\n🔒 Testing Protected Endpoints (expecting 401 without auth):")
        for endpoint, method in protected_endpoints:
            success, result = self.test_endpoint(endpoint, method, auth_required=False)
            status_icon = "✅" if success else "❌"
            
            if success:
                status_code = result['status_code']
                if status_code == 401:  # Expected for protected endpoints
                    print(f"  {status_icon} {method} {endpoint} - HTTP {status_code} (protected)")
                elif status_code in [200, 403]:
                    print(f"  ✅ {method} {endpoint} - HTTP {status_code} (accessible)")
                else:
                    print(f"  ⚠️  {method} {endpoint} - HTTP {status_code} (unexpected)")
            else:
                print(f"  {status_icon} {method} {endpoint} - {result}")
        
        # Test article-specific endpoints
        article_endpoints = [
            ("articles/1/", "GET"),
            ("articles/1/quiz/", "GET"),
            ("articles/1/comments/", "GET"),
        ]
        
        print("\n📰 Testing Article Endpoints (expecting 401/404):")
        for endpoint, method in article_endpoints:
            success, result = self.test_endpoint(endpoint, method, auth_required=False)
            status_icon = "✅" if success else "❌"
            
            if success:
                status_code = result['status_code']
                if status_code in [401, 404]:  # Expected responses
                    print(f"  {status_icon} {method} {endpoint} - HTTP {status_code}")
                elif status_code == 200:
                    print(f"  ✅ {method} {endpoint} - HTTP {status_code} (working)")
                else:
                    print(f"  ⚠️  {method} {endpoint} - HTTP {status_code} (unexpected)")
            else:
                print(f"  {status_icon} {method} {endpoint} - {result}")
    
    def test_server_connection(self):
        """Test basic server connectivity"""
        try:
            response = requests.get(self.base_url, timeout=5)
            return True, f"Server responding - HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Django server not running on http://localhost:8000"
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def run_tests(self):
        """Run all API tests"""
        print("🚀 VeriFast API Test Suite")
        print("=" * 50)
        
        # Test server connection first
        print("🔍 Testing server connection...")
        success, message = self.test_server_connection()
        
        if not success:
            print(f"❌ {message}")
            print("\n💡 To start the Django server:")
            print("   python manage.py runserver")
            print("   # OR")
            print("   ./quick_start.sh  # Choose option 1 or 2")
            return False
        
        print(f"✅ {message}")
        
        # Test API endpoints
        self.test_all_endpoints()
        
        print("\n📊 Test Summary:")
        print("✅ = Endpoint accessible and responding")
        print("⚠️  = Unexpected response (may need investigation)")
        print("❌ = Connection or server error")
        
        print("\n💡 Next Steps:")
        print("1. If endpoints show 401/403: Authentication is working correctly")
        print("2. If endpoints show 200: API is fully accessible")
        print("3. If endpoints show 500: Check Django logs for errors")
        print("4. Test with actual authentication using Django admin or frontend")
        
        return True


def main():
    """Main test function"""
    tester = APITester()
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        tester = APITester(base_url)
        print(f"Testing API at: {base_url}")
    
    tester.run_tests()


if __name__ == "__main__":
    main()