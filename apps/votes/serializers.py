from rest_framework import serializers
from .models import VoteRecord
from apps.elections.models import Election
# Ya no necesitamos Candidate, VoteEmissionSerializer ha sido reemplazado

class VoteTxRegistrationSerializer(serializers.Serializer):
    """
    Serializer para recibir los datos de confirmación de la Mockchain desde el frontend (Proceso P6).
    Solo valida la existencia de la elección, el ID de la transacción y el hash.
    """
    election_id = serializers.PrimaryKeyRelatedField(
        queryset=Election.objects.all(), 
        required=True,
        source='election' # Aseguramos que se resuelva al objeto Election
    )
    
    # Identificador de Transacción de la Mockchain
    tx_id = serializers.CharField(required=True, max_length=100)
    
    # Hash del contenido del voto, generado por el frontend y validado por la Mockchain
    vote_hash = serializers.CharField(required=True, max_length=64)


class VoteRecordSerializer(serializers.ModelSerializer):
    """
    Serializer para exponer el registro de auditoría del voto.
    """
    class Meta:
        model = VoteRecord
        fields = '__all__'
        read_only_fields = '__all__'