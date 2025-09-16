from django.db import models

# Create your models here.
# apps/reports/models.py - Migrado desde tu código existente
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
import uuid
from django.utils import timezone

User = get_user_model()

class CSVFile(models.Model):
    """Archivos CSV subidos para análisis - Migrado y mejorado"""
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Información del archivo
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=100, default='text/csv')
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS_CHOICES, 
        default='pending'
    )
    
    # Azure Storage info
    azure_blob_url = models.URLField(null=True, blank=True)
    azure_blob_name = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Estado de procesamiento
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Metadatos del análisis
    rows_count = models.PositiveIntegerField(null=True, blank=True)
    columns_count = models.PositiveIntegerField(null=True, blank=True)
    analysis_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    upload_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reports_csvfile'
        ordering = ['-upload_date']
        verbose_name = 'Archivo CSV'
        verbose_name_plural = 'Archivos CSV'
        indexes = [
            models.Index(fields=['user', 'processing_status']),
            models.Index(fields=['upload_date']),
        ]

    def __str__(self):
        return f"{self.original_filename} - {self.user.email}"

    def save(self, *args, **kwargs):
        if self.processing_status == 'completed' and not self.processed_date:
            self.processed_date = timezone.now()
        super().save(*args, **kwargs)

class Report(models.Model):
    """Reportes generados - Migrado y expandido"""
    STATUS_CHOICES = [
        ('generating', 'Generando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('expired', 'Expirado'),
    ]
    
    REPORT_TYPES = [
        ('executive', 'Ejecutivo'),
        ('detailed', 'Detallado'),
        ('summary', 'Resumen'),
        ('custom', 'Personalizado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    csv_file = models.ForeignKey(CSVFile, on_delete=models.CASCADE, related_name='reports')
    
    # Información básica
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='executive')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    
    # Datos del análisis (migrado desde tu código)
    analysis_data = models.JSONField(default=dict)
    
    # Archivos generados
    pdf_file_url = models.URLField(blank=True)
    html_preview_url = models.URLField(blank=True)
    pdf_azure_blob_name = models.CharField(max_length=255, blank=True)
    
    # Configuración de generación
    user_prompt = models.TextField(blank=True)
    generation_config = models.JSONField(default=dict)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Métricas
    generation_time_seconds = models.PositiveIntegerField(null=True, blank=True)
    file_size_mb = models.FloatField(null=True, blank=True)
    pages_count = models.PositiveIntegerField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reports_report'
        ordering = ['-created_at']
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['report_type']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)