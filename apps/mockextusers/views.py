# apps/mockextusers/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import TestUser
from .serializers import EligibilityCheckSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def check_eligibility_external(request):
    """
    Simula la API de un sistema externo para verificar la elegibilidad de un usuario.
    Recibe el email en el cuerpo (JSON) y los criterios de filtrado en los query params.
    """
    
    # 1. Obtener el email del cuerpo del POST (Requerido por el Proceso P4)
    email = request.data.get('email')
    if not email:
        return Response(
            {'detail': _('Se requiere el campo "email" en el cuerpo de la solicitud (JSON).')}, 
            status=status.HTTP_400_BAD_REQUEST
        )
        
    # 2. Obtener los criterios de filtrado de los Query Params
    query_params = request.query_params
    
    # Base: Buscar al usuario por email
    queryset = TestUser.objects.filter(email=email)
    
    # 3. Aplicar Filtros Dinámicos (Lógica Compleja de Elegibilidad)
    
    # Filtro 3.1: Roles (ej: ?role=STUDENT,PROFESSOR)
    roles = query_params.getlist('role')
    if roles:
        # Aplicamos el filtro OR para los roles especificados
        queryset = queryset.filter(role__in=roles)

    # Filtro 3.2: Estudiantes (Clase y Año Escolar)
    student_class = query_params.get('student_class')
    school_year = query_params.get('school_year')
    
    if student_class:
        # Si el filtro se aplica, el usuario debe ser ESTUDIANTE Y coincidir con la clase
        queryset = queryset.filter(
            Q(role=TestUser.Role.STUDENT) & Q(student_class__iexact=student_class)
        )
        
    if school_year:
        try:
            year = int(school_year)
            queryset = queryset.filter(
                Q(role=TestUser.Role.STUDENT) & Q(school_year=year)
            )
        except ValueError:
            pass 

    # Filtro 3.3: Profesores (Grado y Asignaturas)
    degree = query_params.get('degree')
    subject = query_params.get('subject')
    
    if degree:
        queryset = queryset.filter(
            Q(role=TestUser.Role.PROFESSOR) & Q(degree__iexact=degree)
        )
    
    if subject:
        # Utilizamos __contains en JSONField para simular la búsqueda en la lista de asignaturas
        queryset = queryset.filter(
            Q(role=TestUser.Role.PROFESSOR) & Q(subjects_taught__contains=[subject])
        )

    # 4. Evaluación Final: ¿El usuario existe Y pasó todos los filtros?
    user_passed_filters = queryset.exists()
    
    response_data = {}
    if user_passed_filters:
        response_data['is_eligible'] = True
        response_data['reason'] = _('Elegible según los criterios externos.')
        return Response(EligibilityCheckSerializer(response_data).data, status=status.HTTP_200_OK)
    else:
        # Identificar la razón de la falla para el registro de auditoría
        if not TestUser.objects.filter(email=email).exists():
            reason = _('Usuario no encontrado en el padrón externo (email no existe).')
        else:
            reason = _('Usuario encontrado, pero no cumple con los criterios de elegibilidad (filtros avanzados).')
            
        response_data['is_eligible'] = False
        response_data['reason'] = reason
        return Response(EligibilityCheckSerializer(response_data).data, status=status.HTTP_200_OK)