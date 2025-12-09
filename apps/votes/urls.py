from django.urls import path
from .views import register_vote_transaction, verify_my_vote # <-- CAMBIO: VISTA ACTUALIZADA

app_name = 'votes'

urlpatterns = [
    # api/v1/votes/register-tx/ <-- CAMBIO: NUEVA RUTA PARA REGISTRO (Proceso P6)
    path('register-tx/', register_vote_transaction, name='register-tx'),
    
    # api/v1/votes/verify/<int:election_pk>/
    path('verify/<int:election_pk>/', verify_my_vote, name='verify-vote'),
]