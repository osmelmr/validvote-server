# apps/candidates/urls.py
from django.urls import path
from .views import candidate_list_create, candidate_detail

app_name = 'candidates'

urlpatterns = [
    # api/v1/elections/<election_pk>/candidates/
    # Usamos la FK de la elección en la URL para anidar la ruta.
    path('<int:election_pk>/candidates/', candidate_list_create, name='list-create'),
    
    # api/v1/elections/<election_pk>/candidates/<pk>/
    path('<int:election_pk>/candidates/<int:pk>/', candidate_detail, name='detail-update-delete'),
]