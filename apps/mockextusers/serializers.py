# apps/mockextusers/serializers.py
from rest_framework import serializers
from .models import TestUser

class TestUserSerializer(serializers.ModelSerializer):
    """
    Serializer para administrar los usuarios de prueba en el panel de Django/API.
    """
    class Meta:
        model = TestUser
        fields = '__all__'
        
class EligibilityCheckSerializer(serializers.Serializer):
    """
    Serializer de respuesta para la API de verificación de elegibilidad.
    """
    is_eligible = serializers.BooleanField(help_text="True si el usuario cumple con los filtros.")
    reason = serializers.CharField(required=False, help_text="Razón del resultado, si aplica.")