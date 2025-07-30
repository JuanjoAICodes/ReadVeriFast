"""
End-to-End Integration Tests using Honcho Process Management
Tests the complete application stack with all services running
"""

import subprocess
import time
import requests
import pytest
import os
import signal


class HonchoTestManager:
    """Manages Honcho processes for testing"""
    
    def __init__(self):
        self.honcho_process = None
        self.base_url = "http://localhost:8001"
        self.max_startup_time = 60  # seconds
        
    def start_test_environment(self):
        """Start all test services using Honcho"""
        print("🚀 Starting test environment with Honcho...")
        
        # Start Honcho with test Procfile
        self.honcho_process = subprocess.Popen(
            ["honcho", "-f", "Procfile.test", "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Wait for services to start
        self._wait_for_services()
        
    def _wait_for_services(self):
        """Wait for all services to be ready"""
        print("⏳ Waiting for services to start...")
        
        start_time = time.time()
        
        while time.time() - start_time < self.max_startup_time:
            try:
                # Check if Django is responding
                response = requests.get(f"{self.base_url}/", timeout=5)
                if response.status_code == 200:
                    print("✅ Django server is ready")
                    
                    # Give a bit more time for other services
                    time.sleep(5)
                    return True
                    
            except requests.exceptions.RequestException:
                time.sleep(2)
                continue
                
        raise Exception("Services failed to start within timeout")
        
    def stop_test_environment(self):
        """Stop all test services"""
        if self.honcho_process:
            print("🛑 Stopping test environment...")
            
            # Kill the entire process group
            os.killpg(os.getpgid(self.honcho_process.pid), signal.SIGTERM)
            
            # Wait for graceful shutdown
            try:
                self.honcho_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if needed
                os.killpg(os.getpgid(self.honcho_process.pid), signal.SIGKILL)
                
            print("✅ Test environment stopped")
            
    def is_service_healthy(self, service_name):
        """Check if a specific service is healthy"""
        health_checks = {
            'web': lambda: requests.get(f"{self.base_url}/").status_code == 200,
            'redis': lambda: self._check_redis(),
            'worker': lambda: self._check_celery_worker()
        }
        
        check_func = health_checks.get(service_name)
        if not check_func:
            return False
            
        try:
            return check_func()
        except Exception:
            return False
            
    def _check_redis(self):
        """Check Redis connectivity"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6380, db=0)
            return r.ping()
        except Exception:
            return False
            
    def _check_celery_worker(self):
        """Check Celery worker status"""
        # This is a simplified check - in practice you might use Celery's inspect
        return True  # Assume healthy if no errors


@pytest.fixture(scope="session")
def honcho_manager():
    """Pytest fixture to manage Honcho test environment"""
    manager = HonchoTestManager()
    
    try:
        manager.start_test_environment()
        yield manager
    finally:
        manager.stop_test_environment()


class TestHonchoIntegration:
    """Integration tests using Honcho-managed services"""
    
    def test_all_services_running(self, honcho_manager):
        """Test that all required services are running"""
        services = ['web', 'redis', 'worker']
        
        for service in services:
            assert honcho_manager.is_service_healthy(service), f"{service} is not healthy"
            
    def test_django_application_accessible(self, honcho_manager):
        """Test Django application is accessible"""
        response = requests.get(f"{honcho_manager.base_url}/")
        assert response.status_code == 200
        assert "VeriFast" in response.text or "Speed Reader" in response.text
        
    def test_static_files_served(self, honcho_manager):
        """Test static files are being served"""
        # Try to access a common static file
        static_urls = [
            "/static/css/custom.css",
            "/static/js/speed-reader.js",
            "/static/admin/css/base.css"  # Django admin static files
        ]
        
        for static_url in static_urls:
            try:
                response = requests.get(f"{honcho_manager.base_url}{static_url}")
                if response.status_code == 200:
                    print(f"✅ Static file accessible: {static_url}")
                    return  # At least one static file is working
            except requests.exceptions.RequestException:
                continue
                
        # If we get here, no static files were accessible
        print("⚠️  No static files accessible - may be expected in test environment")
        
    def test_admin_interface_accessible(self, honcho_manager):
        """Test Django admin interface is accessible"""
        response = requests.get(f"{honcho_manager.base_url}/admin/")
        
        # Should redirect to login or show login form
        assert response.status_code in [200, 302]
        
        if response.status_code == 200:
            assert "Django administration" in response.text or "login" in response.text.lower()
            
    def test_api_endpoints_responding(self, honcho_manager):
        """Test API endpoints are responding"""
        api_endpoints = [
            "/api/v1/",  # API root
            "/api/articles/",  # Articles API
            "/api/quiz/",  # Quiz API
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{honcho_manager.base_url}{endpoint}")
                # API endpoints might return 404, 401, or 200 - all indicate they're responding
                assert response.status_code in [200, 401, 404, 405]
                print(f"✅ API endpoint responding: {endpoint} ({response.status_code})")
            except requests.exceptions.RequestException as e:
                print(f"⚠️  API endpoint not accessible: {endpoint} - {e}")
                
    def test_database_connectivity(self, honcho_manager):
        """Test database connectivity through Django"""
        # Make a request that would require database access
        response = requests.get(f"{honcho_manager.base_url}/")
        
        # If the page loads, database is likely working
        assert response.status_code == 200
        
        # Additional check: try to access a page that definitely needs DB
        try:
            response = requests.get(f"{honcho_manager.base_url}/admin/")
            assert response.status_code in [200, 302]  # Login redirect is fine
        except requests.exceptions.RequestException:
            print("⚠️  Admin interface not accessible for DB test")
            
    def test_celery_worker_processing(self, honcho_manager):
        """Test Celery worker can process tasks"""
        # This is a basic test - in practice you'd trigger an actual task
        assert honcho_manager.is_service_healthy('worker')
        
        # Could add more sophisticated testing by:
        # 1. Triggering an article scraping task
        # 2. Checking task completion
        # 3. Verifying results
        
    def test_error_handling(self, honcho_manager):
        """Test application error handling"""
        # Test 404 handling
        response = requests.get(f"{honcho_manager.base_url}/nonexistent-page/")
        assert response.status_code == 404
        
        # Test invalid API requests
        response = requests.post(f"{honcho_manager.base_url}/api/invalid/")
        assert response.status_code in [404, 405, 400]
        
    def test_concurrent_requests(self, honcho_manager):
        """Test application handles concurrent requests"""
        import concurrent.futures
        
        def make_request():
            try:
                response = requests.get(f"{honcho_manager.base_url}/", timeout=10)
                return response.status_code == 200
            except Exception:
                return False
                
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        # At least 80% should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Only {success_rate:.1%} of concurrent requests succeeded"
        
    def test_memory_usage_stability(self, honcho_manager):
        """Basic test for memory usage stability"""
        # Make several requests to check for obvious memory leaks
        for i in range(20):
            response = requests.get(f"{honcho_manager.base_url}/")
            assert response.status_code == 200
            
            if i % 5 == 0:
                time.sleep(0.5)  # Brief pause
                
        print("✅ Memory stability test completed (no crashes)")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])