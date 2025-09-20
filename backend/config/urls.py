# backend/config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse

def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'Azure Reports Platform API',
        'version': '1.0.0'
    })

# Router principal
router = DefaultRouter()

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('api/health/', health_check, name='health-check'),
    
    # API Routes
    path('api/auth/', include('apps.authentication.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/files/', include('apps.storage.urls')),
    path('api/dashboard/', include('apps.analytics.urls')),
    
    # Traditional Django views (para templates) - AGREGAR ESTA LÍNEA
    path('auth/', include('apps.authentication.traditional_urls')),
    
    # Root API
    path('api/', include(router.urls)),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)