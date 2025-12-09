from rest_framework import serializers
from .models import Election

class ElectionSerializer(serializers.ModelSerializer):
    """
    Serializer para la gestión y listado de procesos electorales.
    """
    # Campo de solo lectura para mostrar el nombre del dueño
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    
    # Campo de solo lectura para mostrar el estado en formato legible
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Campo de solo lectura para mostrar el tipo en formato legible
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Election
        fields = (
            'id', 
            'owner', 
            'owner_name', 
            'title', 
            'desc', 
            'start_at', 
            'end_at', 
            'type', 
            'type_display',
            'max_sel', 
            'status', 
            'status_display',
            'ext_validation_url',  # <--- CAMBIO: AÑADIDO
            'created_at', 
            'updated_at'
        )
        read_only_fields = (
            'owner',
            'status',
            'owner_name',
            'status_display',
            'type_display',
            'created_at', 
            'updated_at'
        )