# apps/voter/urls.py
from django.urls import path
from .views import voter_list_create, voter_detail

app_name = 'voter'

urlpatterns = [
    # api/v1/elections/<election_pk>/voters/
    path('<int:election_pk>/voters/', voter_list_create, name='list-create'),
    
    # api/v1/elections/<election_pk>/voters/<pk>/
    path('<int:election_pk>/voters/<int:pk>/', voter_detail, name='detail-update-delete'),
]