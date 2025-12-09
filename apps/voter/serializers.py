# apps/voter/serializers.py
from rest_framework import serializers
from .models import Voter

class VoterSerializer(serializers.ModelSerializer):
    """
    Serializer para la gestión del padrón electoral (Voter).
    Permite al administrador asignar usuarios a una elección (allowed).
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    election_title = serializers.CharField(source='election.title', read_only=True)
    
    class Meta:
        model = Voter
        fields = (
            'id', 
            'election', 
            'election_title',
            'user', 
            'user_email',
            'allowed',
            'voted',
            'ext_verified',
            'created_at', 
            'updated_at'
        )
        read_only_fields = (
            'voted',          # Solo el sistema de votación puede marcar 'voted'
            'user_email', 
            'election_title',
            'created_at', 
            'updated_at'
        )

    def validate(self, data):
        """
        Garantiza que no se intente modificar 'voted' durante la gestión del padrón.
        """
        if self.instance and 'voted' in data and data['voted'] != self.instance.voted:
            raise serializers.ValidationError({"voted": "El estado de voto ('voted') solo puede ser modificado por el sistema."})
        return data