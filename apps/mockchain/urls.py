# apps/mockchain/urls.py
from django.urls import path
from .views import publish_transaction

app_name = 'mockchain'

urlpatterns = [
    # api/v1/mockchain/publish/
    path('publish/', publish_transaction, name='publish-tx'),
]