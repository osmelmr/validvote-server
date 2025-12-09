from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone # Añadida para published_at

# Importaciones de modelos
from apps.elections.models import Election
from apps.voter.models import Voter
from apps.mockchain.models import MockchainTx # Necesario para verify_my_vote
from .models import VoteRecord
from .serializers import VoteRecordSerializer, VoteTxRegistrationSerializer # Importación actualizada
# Eliminamos json, hashlib, requests y MOCKCHAIN_URL ya que la transacción es ahora responsabilidad del frontend

# --- NUEVA VISTA: REGISTRO DE TRANSACCIÓN (Proceso P6) ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def register_vote_transaction(request):
    """
    Proceso central para recibir la confirmación (tx_id, hash) del frontend 
    y realizar el registro final de auditoría y bloqueo del Voter.
    """
    serializer = VoteTxRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    election = data['election'] # 'election' resuelto por el serializer
    user = request.user

    # 1. Verificación Final de Voto Único y Elegibilidad (Voter.voted=False)
    try:
        # Usamos select_for_update para asegurar exclusividad en la transacción atómica
        voter_record = Voter.objects.select_for_update().get(election=election, user=user)
    except Voter.DoesNotExist:
        # Este error solo debería ocurrir si el usuario fue validado externamente y luego eliminado del padrón.
        return Response({'detail': _('Error de Elegibilidad: No tiene un registro de padrón válido para votar.')}, status=status.HTTP_403_FORBIDDEN)
        
    if not voter_record.allowed:
        return Response({'detail': _('Error de Seguridad: No está habilitado para votar.')}, status=status.HTTP_403_FORBIDDEN)
        
    if voter_record.voted:
        return Response({'detail': _('Error de Seguridad: Ya ha emitido su voto en esta elección.')}, status=status.HTTP_403_FORBIDDEN)

    # 2. Verificar que la TX exista en la Mockchain (Prevención de envío de hash falsos)
    # Buscamos por el hash del payload. Si no existe, alguien intenta enviar un registro inválido.
    try:
        MockchainTx.objects.get(
            payload_hash=data['vote_hash'], 
            tx_id=data['tx_id']
        )
    except MockchainTx.DoesNotExist:
         return Response({'detail': _('Error de Integridad: La transacción o el hash no se encontraron en el libro mayor inmutable (Mockchain).')}, status=status.HTTP_400_BAD_REQUEST)


    # 3. Registro Atómico (VoteRecord y bloqueo de Votante)
    try:
        vote_record = VoteRecord.objects.create(
            election=election,
            user=user,
            hash=data['vote_hash'],
            tx_id=data['tx_id'],
            published_at=timezone.now()
        )

        # 4. Bloqueo de Votante
        voter_record.voted = True
        voter_record.save()
        
        return Response(
            {'status': _('Voto registrado exitosamente en el sistema.'), 'tx_id': data['tx_id']}, 
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        # Si falla el guardado (ConstraintError, etc.), se hace ROLLBACK completo gracias a @transaction.atomic
        return Response({'detail': _('Error interno al finalizar el registro del voto.')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- VISTA EXISTENTE: VERIFICACIÓN INDIVIDUAL (P8) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_my_vote(request, election_pk):
    """
    Permite a un usuario verificar que su voto fue registrado.
    """
    user = request.user
    
    # 1. Buscar el registro local de auditoría (VoteRecord)
    try:
        vote_record = VoteRecord.objects.get(
            election_id=election_pk, 
            user=user
        )
    except VoteRecord.DoesNotExist:
        return Response({'detail': _('No se encontró registro de voto para esta elección.')}, status=status.HTTP_404_NOT_FOUND)

    # 2. Consultar la transacción simulada (MockchainTx) usando el hash o tx_id
    # Nota: Aquí usamos tx_id, pero se podría usar payload_hash (vote_record.hash) también.
    try:
        mock_tx = MockchainTx.objects.get(tx_id=vote_record.tx_id)
    except MockchainTx.DoesNotExist:
        return Response({'detail': _('El registro local no coincide con la transacción en la cadena. Contacte a soporte.')}, status=status.HTTP_404_NOT_FOUND)

    # 3. Devolver los datos de auditoría
    return Response({
        'status': _('Voto Registrado y Verificado'),
        'election_id': election_pk,
        'transaction_id': vote_record.tx_id,
        'vote_hash': vote_record.hash,
        'published_at': vote_record.published_at,
        'mockchain_payload_sample': mock_tx.payload # Muestra el contenido inmutable del voto (candidatos, prueba)
    }, status=status.HTTP_200_OK)