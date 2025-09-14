# config/urls.py - URL principal
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Router principal
router = DefaultRouter()

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/', include('apps.reports.urls')),
    path('api/storage/', include('apps.storage.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    
    # Health check
    path('api/health/', lambda request: JsonResponse({'status': 'ok'})),
    
    # API root
    path('api/', include(router.urls)),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)