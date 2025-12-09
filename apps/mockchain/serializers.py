# apps/mockchain/serializers.py
from rest_framework import serializers
from .models import MockchainTx

class MockchainTxSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de una transacción simulada en la cadena.
    """
    class Meta:
        model = MockchainTx
        fields = '__all__'
        read_only_fields = ('tx_id', 'block_number', 'created_at',)