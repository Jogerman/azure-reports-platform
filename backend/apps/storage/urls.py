# apps/storage/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FilesListView, FileUploadView

urlpatterns = [
    # Endpoint principal que usa el frontend para listar archivos
    path('', FilesListView.as_view(), name='files-list'),
    
    # Endpoint para upload
    path('upload/', FileUploadView.as_view(), name='file-upload'),
]