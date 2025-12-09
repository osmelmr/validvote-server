# apps/mockchain/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import uuid

from .models import MockchainTx
from .serializers import MockchainTxSerializer

# Usamos AllowAny porque esta vista simula un servicio público de blockchain
@api_view(['POST']) 
def publish_transaction(request):
    """
    Simula la publicación de una transacción de voto en la blockchain.
    Genera un tx_id único y un número de bloque simulado.
    """
    data = request.data.copy()
    
    # 1. Simular generación de ID de transacción y número de bloque
    data['tx_id'] = str(uuid.uuid4())
    # NOTA: En una implementación real, este número sería secuencial y real.
    # Aquí lo simulamos con un valor fijo por simplicidad.
    data['block_number'] = MockchainTx.objects.count() + 1 

    serializer = MockchainTxSerializer(data=data)
    
    if serializer.is_valid():
        try:
            tx = serializer.save()
            # Retornamos solo los datos esenciales de la transacción confirmada
            return Response({
                'tx_id': tx.tx_id,
                'block_number': tx.block_number,
                'payload_hash': tx.payload_hash,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
             # Captura errores de unicidad (payload_hash/tx_id duplicado)
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)