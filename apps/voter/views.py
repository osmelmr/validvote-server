# apps/voter/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from apps.elections.models import Election
from .models import Voter
from .serializers import VoterSerializer
# Reutilizamos la clase de permisos de la app core
from apps.core.permissions import IsOwnerOrReadOnly 

# --- VISTA DE LISTADO Y CREACIÓN DE VOTANTES (LIST / ADD) ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def voter_list_create(request, election_pk):
    """
    GET: Lista el padrón de una elección (solo para el dueño de la elección).
    POST: Agrega o habilita un usuario en el padrón de una elección.
    """
    election = get_object_or_404(Election, pk=election_pk)
    
    # 1. Verificación de Permisos: Solo el dueño puede crear/listar el padrón
    if election.owner != request.user:
        return Response(
            {'detail': _('Solo el administrador de la elección puede gestionar el padrón.')},
            status=status.HTTP_403_FORBIDDEN
        )

    # 2. Validación de Lógica de Negocio (Estado de Elección)
    if request.method == 'POST' and election.status in [Election.Status.OPEN, Election.Status.CLOSED]:
        return Response(
            {'detail': _('No se puede modificar el padrón de una elección que está en curso o finalizada.')}, 
            status=status.HTTP_403_FORBIDDEN
        )

    # 3. Manejo de POST (Creación de registro en el padrón)
    if request.method == 'POST':
        data = request.data.copy()
        data['election'] = election_pk
        
        # Validación de unicidad: unique_together de Voter se encarga de que (election, user) sea único
        serializer = VoterSerializer(data=data)
        if serializer.is_valid():
            try:
                voter_record = serializer.save()
                return Response(VoterSerializer(voter_record).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # 4. Manejo de GET (Listado del padrón)
    elif request.method == 'GET':
        voters = Voter.objects.filter(election=election).select_related('user')
        serializer = VoterSerializer(voters, many=True)
        return Response(serializer.data)


# --- VISTA DE DETALLE Y ACTUALIZACIÓN (RETRIEVE / UPDATE / DELETE) ---
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def voter_detail(request, election_pk, pk):
    """
    GET: Consulta el detalle de un registro en el padrón.
    PUT: Actualiza el estado (ej. 'allowed') de un votante.
    DELETE: Elimina un votante del padrón (si la elección no ha iniciado/terminado).
    """
    voter_record = get_object_or_404(Voter, pk=pk, election_id=election_pk)
    election = voter_record.election

    # 1. Verificación de Permisos
    if election.owner != request.user:
        return Response(
            {'detail': _('Solo el administrador de la elección puede modificar el padrón.')}, 
            status=status.HTTP_403_FORBIDDEN
        )

    # 2. Validación de Estado de Elección (para PUT y DELETE)
    if request.method in ['PUT', 'DELETE'] and election.status in [Election.Status.OPEN, Election.Status.CLOSED]:
        return Response(
            {'detail': _('No se puede modificar el padrón de una elección en curso o finalizada.')}, 
            status=status.HTTP_403_FORBIDDEN
        )
        
    # 3. Manejo de Métodos
    if request.method == 'GET':
        serializer = VoterSerializer(voter_record)
        return Response(serializer.data)

    elif request.method == 'PUT':
        # Se requiere el objeto actual para las validaciones en el serializer
        serializer = VoterSerializer(voter_record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Nota: La eliminación de un registro del padrón es riesgosa, pero posible si es borrador.
        voter_record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)