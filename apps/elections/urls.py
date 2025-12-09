from django.urls import path
from .views import election_list_create, election_detail, verify_eligibility # <-- CAMBIO: AÑADIDA

app_name = 'elections'

urlpatterns = [
    # api/v1/elections/
    path('', election_list_create, name='list-create'),
    
    # api/v1/elections/<pk>/verify-eligibility/ <-- CAMBIO: NUEVA RUTA
    path('<int:election_pk>/verify-eligibility/', verify_eligibility, name='verify-eligibility'),
    
    # api/v1/elections/<pk>/
    path('<int:pk>/', election_detail, name='detail-update-delete'),
]