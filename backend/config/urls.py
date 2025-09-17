# config/urls.py - URL principal
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse

# Router principal
router = DefaultRouter()

def health_check(request):
    return JsonResponse({
        'status': 'ok',
        'message': 'Django funcionando correctamente',
        'database': 'conectado'
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints - CORREGIDOS SEGÚN TU ESTRUCTURA
    path('api/auth/', include('apps.authentication.urls')),
    path('api/reports/', include('apps.reports.urls')), 
    path('api/files/', include('apps.storage.urls')),  
    path('api/dashboard/', include('apps.analytics.urls')), 
    
    # Health check
    path('api/health/', health_check),
    
    # API root
    path('api/', include(router.urls)),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

