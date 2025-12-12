# apps/elections/views.py (Fragmento de la nueva vista)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db import transaction
# Si no existe, añade esta importación para la llamada externa:
import requests 
from requests.exceptions import RequestException
# Importaciones de modelos y serializers
from .models import Election 
from .serializers import ElectionSerializer # Asumimos que este existe
from apps.voter.models import Voter
# Asegúrate de que las vistas election_list_create y election_detail estén definidas arriba

# ... [election_list_create, election_detail, y otras vistas deben estar aquí] ...

# --- NUEVA VISTA: VERIFICACIÓN DE ELEGIBILIDAD (Proceso P4) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def verify_eligibility(request, election_pk):
    """
    Implementa el Proceso P4. Verifica elegibilidad consultando Voter y, si es necesario, una API externa.
    """
    election = get_object_or_404(Election, pk=election_pk)
    user = request.user
    
    # 1. Verificación Local (Consulta Voter)
    try:
        voter_record = Voter.objects.select_for_update().get(election=election, user=user)
        
        if voter_record.voted:
            return Response({'eligible': False, 'reason': _('Ya ha votado.')}, status=status.HTTP_200_OK)
        if voter_record.allowed:
            return Response({'eligible': True, 'source': 'internal'}, status=status.HTTP_200_OK)
        else:
            return Response({'eligible': False, 'reason': _('No está habilitado.')}, status=status.HTTP_200_OK)
            
    except Voter.DoesNotExist:
        # 2. Verificación Externa Condicional (Caso C)
        if not election.ext_validation_url:
            return Response({'eligible': False, 'reason': _('No está en el padrón y no hay API externa configurada.')}, status=status.HTTP_200_OK)
            
        # 3. Llamada a API Externa
        try:
            # NOTA: Se debe asegurar que 'requests' esté disponible (pip install requests)
            external_response = requests.post(
                election.ext_validation_url, 
                json={'email': user.email}
            )
            external_response.raise_for_status() # Lanza error para códigos 4xx/5xx
            
            # Asumimos que la respuesta tiene un campo 'is_eligible' o similar
            is_eligible = external_response.json().get('is_eligible', False)
            
            if is_eligible:
                # 4. Registro de Autorización Externa (Paso Atómico)
                Voter.objects.create(
                    election=election, 
                    user=user, 
                    allowed=True, 
                    ext_verified=True, 
                    voted=False
                )
                return Response({'eligible': True, 'source': 'external'}, status=status.HTTP_200_OK)
            else:
                return Response({'eligible': False, 'reason': _('Rechazado por el validador externo.')}, status=status.HTTP_200_OK)

        except RequestException:
            # Falla de red, tiempo de espera o respuesta inválida del servicio externo
            return Response(
                {'eligible': False, 'reason': _('Error al contactar el servicio de validación externo.')}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

# apps/elections/views.py

# ... (otras vistas y imports arriba) ...

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def election_list_create(request):
    """
    GET: Lista todas las elecciones (solo visibles para usuarios autenticados).
    POST: Crea una nueva elección (solo para administradores).
    """
    # -----------------------------------
    # GET: Listar Elecciones
    # -----------------------------------
    if request.method == 'GET':
        # Listamos todas las elecciones, o podríamos filtrar solo las activas/abiertas
        elections = Election.objects.all().order_by('-start_at')
        serializer = ElectionSerializer(elections, many=True)
        return Response(serializer.data)

    # -----------------------------------
    # POST: Crear Nueva Elección (Requiere Admin)
    # -----------------------------------
    elif request.method == 'POST':
        # Restricción: Solo usuarios administradores pueden crear elecciones
        if not request.user.is_staff:
            return Response(
                {'detail': _('Solo los administradores pueden crear elecciones.')},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = ElectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# apps/elections/views.py

# ... (otras vistas y imports arriba) ...

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def election_detail(request, pk):
    """
    GET: Detalle de una elección.
    PUT/PATCH: Actualiza una elección (Solo Admin).
    DELETE: Elimina una elección (Solo Admin).
    """
    election = get_object_or_404(Election, pk=pk)

    # -----------------------------------
    # GET: Detalle
    # -----------------------------------
    if request.method == 'GET':
        serializer = ElectionSerializer(election)
        return Response(serializer.data)

    # -----------------------------------
    # PUT/PATCH/DELETE: Requiere Admin
    # -----------------------------------
    if not request.user.is_staff:
        return Response(
            {'detail': _('Solo los administradores pueden modificar o eliminar elecciones.')},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # -----------------------------------
    # PUT / PATCH: Actualizar
    # -----------------------------------
    if request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ElectionSerializer(election, data=request.data, partial=partial)
        
        # Opcional: Impedir la edición si la elección ya está abierta/cerrada
        if election.is_active_or_finished: 
             return Response(
                {'detail': _('No se puede modificar una elección una vez que está activa o ha finalizado.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # -----------------------------------
    # DELETE: Eliminar
    # -----------------------------------
    elif request.method == 'DELETE':
        # Se puede añadir lógica para impedir la eliminación si ya hay votos registrados
        election.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)