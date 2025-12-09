"""
URL configuration for validvote project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas Administrativas y de Usuario
    path('api/v1/users/', include('apps.users.urls')),
    
    # Rutas de Gestión de Elecciones y Componentes Anidados (P1, P2, P3)
    path('api/v1/elections/', include('apps.elections.urls')),
    path('api/v1/elections/', include('apps.candidates.urls')),
    path('api/v1/elections/', include('apps.voter.urls')),
    
    # Rutas de Votación y Auditoría (P5, P6, P8)
    path('api/v1/votes/', include('apps.votes.urls')),
    path('api/v1/mockchain/', include('apps.mockchain.urls')),
    
    # Rutas de Resultados
    path('api/v1/results/', include('apps.results.urls')),
    
    # --- NUEVA RUTA DE SIMULACIÓN (Mock de Elegibilidad Externa - P4) ---
    # La API Externa se ubica en una ruta separada para simular un servicio independiente.
    path('api/v1/external-validator/', include('apps.mockextusers.urls')), # <-- CAMBIO: AÑADIDO
]