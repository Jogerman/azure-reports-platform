# apps/reports/admin.py
from django.contrib import admin
from .models import CSVFile, Report

@admin.register(CSVFile)
class CSVFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'user', 'processing_status', 'upload_date', 'file_size']
    list_filter = ['processing_status', 'upload_date']
    search_fields = ['original_filename', 'user__email']
    readonly_fields = ['id', 'upload_date', 'processed_date']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'report_type', 'status', 'created_at']
    list_filter = ['status', 'report_type', 'created_at']
    search_fields = ['title', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'completed_at']