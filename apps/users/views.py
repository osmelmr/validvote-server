from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .serializers import UserRegistrationSerializer, UserSerializer

# Importamos las clases de JWT para la lógica de login, ya que no usaremos la vista TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken 

User = get_user_model()

# --- VISTA DE REGISTRO (SIGN UP) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Permite registrar un nuevo usuario en el sistema."""
    
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Opcional: Generar tokens JWT inmediatamente después del registro exitoso
        refresh = RefreshToken.for_user(user)
        
        # Retornar los datos del perfil y los tokens
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- VISTA DE LOGIN (SIGN IN / CUSTOM TOKEN OBTAIN) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Permite el login mediante email y password, retornando tokens JWT.
    Reemplaza la funcionalidad de rest_framework_simplejwt.views.TokenObtainPairView.
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if email is None or password is None:
        return Response({'detail': _('Debe proporcionar email y contraseña.')}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': _('Credenciales no válidas.')}, status=status.HTTP_401_UNAUTHORIZED)
    
    if user.check_password(password):
        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)
    else:
        return Response({'detail': _('Credenciales no válidas.')}, status=status.HTTP_401_UNAUTHORIZED)


# --- VISTA DE PERFIL (PROFILE) ---
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Permite ver (GET) y actualizar (PUT) los datos del usuario autenticado."""
    
    user = request.user
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        # Nota: Por seguridad, no permitiremos cambiar el email o la contraseña aquí
        # La contraseña requiere un serializer especial (PasswordChangeSerializer).
        
        # Al usar partial=True, permitimos que se actualice solo el campo 'name'
        serializer = UserSerializer(user, data=request.data, partial=True) 
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)