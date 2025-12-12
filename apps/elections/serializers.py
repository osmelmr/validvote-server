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
    
    def validate(self, data):
        # Obtiene las fechas validadas o las existentes si es un PATCH
        start_at = data.get('start_at', self.instance.start_at if self.instance else None)
        end_at = data.get('end_at', self.instance.end_at if self.instance else None)

        if start_at and end_at and end_at <= start_at:
            raise serializers.ValidationError({
                'end_at': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })

        return data
    
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