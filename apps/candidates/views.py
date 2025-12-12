from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from apps.elections.models import Election
from .models import Candidate
from .serializers import CandidateSerializer
from apps.core.permissions import IsOwnerOrReadOnly # Clase de permiso reusada

# --- VISTA DE LISTADO Y CREACIÓN (LIST / CREATE) ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def candidate_list_create(request, election_pk):
    """
    GET: Lista todos los candidatos de una elección específica.
    POST: Permite crear un nuevo candidato en esa elección.
    """
    election = get_object_or_404(Election, pk=election_pk)
    
    # 1. Validación de Lógica de Negocio para POST (Creación)
    if request.method == 'POST':
        # Se verifica que la elección no esté en estado OPEN o CLOSED
        if election.status in [Election.Status.OPEN, Election.Status.CLOSED]:
            return Response(
                {'detail': _('No se pueden añadir candidatos a una elección que está en curso o finalizada.')}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        # El usuario que crea el candidato debe ser el dueño de la elección
        if election.owner != request.user:
            return Response(
                {'detail': _('Solo el administrador de la elección puede añadir candidatos.')},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Serialización y guardado
        data = request.data.copy()
        data['election'] = election_pk # Aseguramos que el FK sea la elección correcta
        
        # El 'user' debe ser el ID del usuario que se postula (enviado en el cuerpo)
        serializer = CandidateSerializer(data=data)
        if serializer.is_valid():
            try:
                # El serializer debe validar la unicidad (election_id, user_id)
                candidate = serializer.save()
                return Response(CandidateSerializer(candidate).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # 3. Manejo de GET (Listado)
    elif request.method == 'GET':
        # Listado público de candidatos para esa elección
        candidates = Candidate.objects.filter(election=election).select_related('user')
        serializer = CandidateSerializer(candidates, many=True)
        return Response(serializer.data)


# --- VISTA DE DETALLE, ACTUALIZACIÓN Y ELIMINACIÓN (RETRIEVE / UPDATE / DELETE) ---
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated]) # La verificación de propiedad se hace manualmente
def candidate_detail(request, election_pk, pk):
    """
    GET: Consulta el detalle de un candidato.
    PUT: Actualiza un candidato.
    DELETE: Elimina un candidato.
    """
    candidate = get_object_or_404(Candidate, pk=pk, election_id=election_pk)
    
    # 1. Verificación de Permisos: Solo el dueño de la elección puede modificar/eliminar
    election = candidate.election
    if (election.owner != request.user) and (request.method != "GET") :
        return Response(
            {'detail': _('No tienes permiso para modificar esta candidatura.')}, 
            status=status.HTTP_403_FORBIDDEN
        )

    # 2. Validación de Estado de Elección
    if request.method in ['PUT', 'DELETE'] and election.status in [Election.Status.OPEN, Election.Status.CLOSED]:
        return Response(
            {'detail': _('No se puede modificar ni eliminar una candidatura en una elección en curso o finalizada.')}, 
            status=status.HTTP_403_FORBIDDEN
        )
        
    # 3. Manejo de Métodos
    if request.method == 'GET':
        serializer = CandidateSerializer(candidate)
        return Response(serializer.data)

    elif request.method == 'PUT':
        # La FK 'election' no debe ser editable, por eso usamos partial=True
        serializer = CandidateSerializer(candidate, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        candidate.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)