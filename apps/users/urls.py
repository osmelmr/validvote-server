from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView
)
from .views import register_user, login_user, user_profile

app_name = 'users'

urlpatterns = [
    # 1. Login y Refresh (Login implementado con función, refresh con JWT)
    path('auth/login/', login_user, name='login'), # Usa login_user FBV
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # Usa CBV de JWT
    
    # 2. Registro de Usuario
    path('auth/register/', register_user, name='register'),
    
    # 3. Perfil del Usuario
    path('profile/', user_profile, name='profile'),
]