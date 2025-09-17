# apps/storage/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StorageFileViewSet, FilesListView

router = DefaultRouter()
router.register(r'storage-files', StorageFileViewSet, basename='storagefile')

urlpatterns = [
    path('', include(router.urls)),
    # Endpoint principal que usa el frontend
    path('', FilesListView.as_view(), name='files-list'),
    # Endpoint específico para upload (si tienes una vista de upload)
    # path('upload/', FileUploadView.as_view(), name='file-upload'),
]