from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

from .health import ServiceHealthChecker

@require_GET
@never_cache
def health_check(request):
    """Health check endpoint for service status monitoring"""
    checker = ServiceHealthChecker()
    service_status = checker.check_all_services()
    
    # Determine overall health
    all_healthy = all(info['status'] == 'healthy' for info in service_status.values())
    
    return JsonResponse({
        'status': 'healthy' if all_healthy else 'degraded',
        'services': service_status
    })