# apps/mockextusers/urls.py
from django.urls import path
from .views import check_eligibility_external

app_name = 'mockextusers'

urlpatterns = [
    # Ruta de la API Externa para la verificación de elegibilidad
    # El administrador de ValidVote copiará esta URL para la configuración en Election.ext_validation_url
    path('check/', check_eligibility_external, name='check-eligibility'),
]