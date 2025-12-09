# apps/results/urls.py
from django.urls import path
from .views import election_results

app_name = 'results'

urlpatterns = [
    # api/v1/results/<election_pk>/
    path('<int:election_pk>/', election_results, name='election-results'),
]