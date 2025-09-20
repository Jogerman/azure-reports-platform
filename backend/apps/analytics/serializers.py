# backend/apps/analytics/serializers.py
from rest_framework import serializers
from .models import UserActivity

class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer para actividades de usuario"""
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'activity_type', 'description', 
            'timestamp', 'ip_address', 'metadata'
        ]