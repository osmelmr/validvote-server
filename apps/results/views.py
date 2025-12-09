# apps/results/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny # Permitimos consulta pública
from django.utils.translation import gettext_lazy as _
from .services import calculate_election_results

@api_view(['GET'])
@permission_classes([AllowAny])
def election_results(request, election_pk):
    """
    Consulta los resultados finales de una elección a través de la Mockchain.
    """
    results, error = calculate_election_results(election_pk)

    if error:
        return Response({'detail': error}, status=status.HTTP_404_NOT_FOUND)
    
    # Restricción: Los resultados solo son finales cuando la elección está cerrada.
    if results['status'] != 'CLOSED':
        return Response(
            {'detail': _('Los resultados solo están disponibles después de que la elección ha finalizado y cerrado.')}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # 3. Formatear y añadir nombres de candidatos (necesitaríamos un Serializer o lógica adicional para esto)
    
    # Por ahora, retornamos los conteos brutos:
    return Response(results, status=status.HTTP_200_OK)