# apps/candidates/serializers.py
from rest_framework import serializers
from .models import Candidate

class CandidateSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro y visualización de candidatos.
    Campos 'image' (URL) y 'ext_id' ELIMINADO.
    """
    # Campo de solo lectura para mostrar el nombre completo del usuario asociado a la candidatura
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    # Campo de solo lectura para mostrar el título de la elección asociada
    election_title = serializers.CharField(source='election.title', read_only=True)
    
    class Meta:
        model = Candidate
        fields = (
            'id', 
            'election', 
            'election_title',
            'user', 
            'user_name',
            'name', 
            'bio', 
            'image', # CAMBIO DE NOMBRE: de 'photo' a 'image'
        )
        # Se elimina 'ext_id' de fields
        read_only_fields = ('user_name', 'election_title',)
        
    def create(self, validated_data):
        return super().create(validated_data)