# apps/storage/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# Registrar tus ViewSets aquí si los tienes
# router.register(r'files', views.FileViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
    # Si tienes una vista específica para upload:
    # path('upload/', views.FileUploadView.as_view(), name='file-upload'),
]
