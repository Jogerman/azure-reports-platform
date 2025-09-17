# apps/storage/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FilesListView, FileUploadView

# No usar router para APIView, solo para ViewSets
urlpatterns = [
    path('', FilesListView.as_view(), name='files-list'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
]