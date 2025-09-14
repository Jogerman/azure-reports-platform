# apps/storage/services/azure_storage.py
from azure.storage.blob import BlobServiceClient, ContentSettings
from django.conf import settings
import logging
import io
import pandas as pd
from typing import Optional, Union

logger = logging.getLogger(__name__)

class AzureStorageService:
    """Servicio para gestionar Azure Blob Storage"""
    
    def __init__(self):
        if not settings.USE_AZURE_STORAGE:
            raise ValueError("Azure Storage no está configurado")
        
        self.account_name = settings.AZURE_ACCOUNT_NAME
        self.account_key = settings.AZURE_ACCOUNT_KEY
        self.container_name = settings.AZURE_CONTAINER
        
        # Crear cliente
        account_url = f"https://{self.account_name}.blob.core.windows.net"
        self.blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=self.account_key
        )
    
    def upload_file(self, file_content: Union[bytes, io.BytesIO], blob_name: str, content_type: str = None) -> str:
        """Subir archivo a Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Configurar content settings
            content_settings = None
            if content_type:
                content_settings = ContentSettings(content_type=content_type)
            
            # Subir archivo
            blob_client.upload_blob(
                file_content,
                overwrite=True,
                content_settings=content_settings
            )
            
            # Retornar URL
            return blob_client.url
            
        except Exception as e:
            logger.error(f"Error subiendo archivo {blob_name}: {e}")
            raise
    
    def download_file(self, blob_name: str) -> bytes:
        """Descargar archivo desde Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            return blob_client.download_blob().readall()
            
        except Exception as e:
            logger.error(f"Error descargando archivo {blob_name}: {e}")
            raise
    
    def download_csv_to_dataframe(self, blob_name: str) -> pd.DataFrame:
        """Descargar CSV y convertir a DataFrame"""
        try:
            file_content = self.download_file(blob_name)
            return pd.read_csv(io.BytesIO(file_content))
            
        except Exception as e:
            logger.error(f"Error leyendo CSV {blob_name}: {e}")
            raise
    
    def delete_file(self, blob_name: str) -> bool:
        """Eliminar archivo de Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando archivo {blob_name}: {e}")
            return False
    
    def list_files(self, prefix: str = None) -> list:
        """Listar archivos en el container"""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            blobs = container_client.list_blobs(name_starts_with=prefix)
            return [blob.name for blob in blobs]
            
        except Exception as e:
            logger.error(f"Error listando archivos: {e}")
            return []
    
    def get_file_url(self, blob_name: str) -> str:
        """Obtener URL de un archivo"""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        return blob_client.url

# Funciones de conveniencia
storage_service = AzureStorageService() if settings.USE_AZURE_STORAGE else None

def upload_blob(file_content: Union[bytes, io.BytesIO], blob_name: str, content_type: str = None) -> str:
    """Función de conveniencia para subir archivos"""
    if storage_service:
        return storage_service.upload_file(file_content, blob_name, content_type)
    else:
        # Fallback para desarrollo local
        return f"/media/{blob_name}"

def download_blob(blob_name: str) -> bytes:
    """Función de conveniencia para descargar archivos"""
    if storage_service:
        return storage_service.download_file(blob_name)
    else:
        # Fallback para desarrollo local
        from django.conf import settings
        file_path = settings.MEDIA_ROOT / blob_name
        with open(file_path, 'rb') as f:
            return f.read()

def download_blob_to_dataframe(blob_name: str) -> pd.DataFrame:
    """Función de conveniencia para descargar CSV"""
    if storage_service:
        return storage_service.download_csv_to_dataframe(blob_name)
    else:
        from django.conf import settings
        file_path = settings.MEDIA_ROOT / blob_name
        return pd.read_csv(file_path)

def get_blob_file(blob_name: str) -> io.BytesIO:
    """Obtener archivo como stream"""
    content = download_blob(blob_name)
    return io.BytesIO(content)