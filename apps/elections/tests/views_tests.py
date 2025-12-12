# apps/elections/tests/views_tests.py
# py .\manage.py test apps.elections.tests.views_tests

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
import requests

# Importa tus modelos y serializers
from apps.elections.models import Election
from apps.elections.serializers import ElectionSerializer
from apps.voter.models import Voter # Necesario para los tests de elegibilidad

User = get_user_model()

class ElectionAPITests(APITestCase):
    
    def setUp(self):
        """
        Configuración inicial: crea usuarios y URLs.
        """
        # 1. Creación de Usuarios de Prueba
        self.staff_user = User.objects.create_user(
            email='admin@test.com', name='Admin', password='pass', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            email='voter@test.com', name='Voter', password='pass', is_staff=False
        )

        # 2. Definición de URLs usando el namespace 'elections'
        self.list_create_url = reverse('elections:list-create')
        # URL de detalle (usaremos un PK más tarde)
        self.detail_url_name = 'elections:detail-update-delete'
        # URL de elegibilidad
        self.verify_eligibility_url_name = 'elections:verify-eligibility'
        
        # 3. Datos base para crear una elección válida
        future_start = timezone.now() + timedelta(days=1)
        future_end = future_start + timedelta(days=7)
        
        self.valid_data = {
            'title': 'Elección de Prueba',
            'desc': 'Prueba para el sistema de votación.',
            'start_at': future_start.isoformat(),
            'end_at': future_end.isoformat(),
            'type': Election.Type.PRIVATE,
            'max_sel': 1,
            # NOTA: 'owner' y 'status' son read_only o se asignan automáticamente.
        }

        # 4. Creación de una Elección inicial (propiedad del staff)
        self.election = Election.objects.create(
            owner=self.staff_user,
            title='Elección Base',
            start_at=future_start,
            end_at=future_end,
        )
        
        # URL de detalle específica para la elección base
        self.detail_url = reverse(self.detail_url_name, kwargs={'pk': self.election.pk})

    # =============================================================
    # TESTS: CREACIÓN DE ELECCIONES (POST /api/v1/elections/)
    # =============================================================

    def test_create_election_by_admin_success(self):
        """Prueba que un usuario Staff (Admin) puede crear una elección (201)."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.list_create_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Election.objects.count(), 2) # Base + Nueva
        self.assertEqual(response.data['title'], self.valid_data['title'])
        # Verifica que el 'owner' se asignó automáticamente al usuario logueado
        self.assertEqual(response.data['owner'], self.staff_user.pk)
        
    def test_create_election_by_non_admin_forbidden(self):
        """Prueba que un usuario normal no puede crear una elección (403)."""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(self.list_create_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Election.objects.count(), 1) # Solo la base

    def test_create_election_unauthenticated_unauthorized(self):
        """Prueba que un usuario no autenticado no puede crear (401)."""
        response = self.client.post(self.list_create_url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_election_invalid_dates(self):
        """Prueba que la validación clean() de fechas funcione (400)."""
        self.client.force_authenticate(user=self.staff_user)
        invalid_data = self.valid_data.copy()
        # Fin antes del inicio
        invalid_data['start_at'] = timezone.now().isoformat()
        invalid_data['end_at'] = (timezone.now() - timedelta(hours=1)).isoformat()

        response = self.client.post(self.list_create_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Verifica que el error de validación sea sobre 'end_at'
        self.assertIn('end_at', response.data)
        
    # =============================================================
    # TESTS: LISTADO (GET /api/v1/elections/)
    # =============================================================

    def test_list_elections_authenticated(self):
        """Prueba que un usuario autenticado puede listar las elecciones (200)."""
        Election.objects.create(owner=self.normal_user, **self.valid_data) # Elección extra
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.list_create_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
    def test_list_elections_unauthenticated_unauthorized(self):
        """Prueba que un usuario no autenticado no puede listar (401)."""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    # =============================================================
    # TESTS: DETALLE (GET/PUT/DELETE /api/v1/elections/<pk>/)
    # =============================================================

    def test_get_election_detail_success(self):
        """Prueba obtener los detalles de una elección (200)."""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.election.title)

    def test_update_election_by_admin_success(self):
        """Prueba que un Admin puede actualizar una elección (PUT/PATCH)."""
        self.client.force_authenticate(user=self.staff_user)
        new_title = {'title': 'Título Actualizado'}
        response = self.client.patch(self.detail_url, new_title)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.election.refresh_from_db()
        self.assertEqual(self.election.title, new_title['title'])

    def test_delete_election_by_admin_success(self):
        """Prueba que un Admin puede eliminar una elección (204)."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Election.objects.filter(pk=self.election.pk).exists())

    def test_update_election_non_admin_forbidden(self):
        """Prueba que un usuario normal no puede actualizar (403)."""
        self.client.force_authenticate(user=self.normal_user)
        new_title = {'title': 'Título Malicioso'}
        response = self.client.patch(self.detail_url, new_title)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Asegura que no haya cambiado en DB
        self.election.refresh_from_db()
        self.assertNotEqual(self.election.title, new_title['title'])

    # =============================================================
    # TESTS: ELEGIBILIDAD (GET /api/v1/elections/<pk>/verify-eligibility/)
    # =============================================================

    @patch('apps.elections.views.requests')
    def test_verify_eligibility_no_voter_record_no_ext_url(self, mock_requests):
        """Prueba Case C: No hay registro local y no hay URL externa."""
        # Usuario normal no tiene registro en Voter
        self.client.force_authenticate(user=self.normal_user)
        verify_url = reverse(self.verify_eligibility_url_name, kwargs={'election_pk': self.election.pk})

        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['eligible'])
        self.assertIn('No está en el padrón', response.data['reason'])
        mock_requests.post.assert_not_called()

    def test_verify_eligibility_local_allowed(self):
        """Prueba Case 1: Registro local permitido y no ha votado."""
        # Crea registro local, allowed=True, voted=False
        Voter.objects.create(
            election=self.election, user=self.normal_user, allowed=True, voted=False
        )
        self.client.force_authenticate(user=self.normal_user)
        verify_url = reverse(self.verify_eligibility_url_name, kwargs={'election_pk': self.election.pk})

        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['eligible'])
        self.assertEqual(response.data['source'], 'internal')
        
    def test_verify_eligibility_local_voted(self):
        """Prueba Case 1: Registro local, ya votó."""
        # Crea registro local, allowed=True, voted=True
        Voter.objects.create(
            election=self.election, user=self.normal_user, allowed=True, voted=True
        )
        self.client.force_authenticate(user=self.normal_user)
        verify_url = reverse(self.verify_eligibility_url_name, kwargs={'election_pk': self.election.pk})

        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['eligible'])
        self.assertIn('Ya ha votado', response.data['reason'])
        
    @patch('apps.elections.views.requests')
    def test_verify_eligibility_external_success_and_save(self, mock_requests):
        """Prueba Case 3/4: Llama a API externa, es elegible, y se crea registro Voter."""
        
        # 1. Configura la Elección con una URL Externa
        self.election.ext_validation_url = 'http://mock.external.validator/check/'
        self.election.save()
        
        # 2. Mockea la Respuesta Externa (simula éxito)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'is_eligible': True}
        mock_requests.post.return_value = mock_response

        # 3. Ejecuta la prueba
        self.client.force_authenticate(user=self.normal_user)
        verify_url = reverse(self.verify_eligibility_url_name, kwargs={'election_pk': self.election.pk})
        
        response = self.client.get(verify_url)

        # 4. Aserciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['eligible'])
        self.assertEqual(response.data['source'], 'external')
        
        # 5. Verifica que la llamada externa se hizo correctamente
        mock_requests.post.assert_called_once_with(
            self.election.ext_validation_url, 
            json={'email': self.normal_user.email}
        )
        # 6. Verifica que el registro Voter se haya creado
        self.assertTrue(Voter.objects.filter(
            user=self.normal_user, 
            election=self.election, 
            allowed=True, 
            ext_verified=True
        ).exists())

    @patch('apps.elections.views.requests')
    def test_verify_eligibility_external_api_failure(self, mock_requests):
        """Prueba que el error de la API externa se maneje correctamente (503)."""
        
        self.election.ext_validation_url = 'http://mock.external.validator/check/'
        self.election.save()
        
        # Simula un error de conexión/red o timeout
        mock_requests.post.side_effect = requests.exceptions.RequestException("Network Error")

        self.client.force_authenticate(user=self.normal_user)
        verify_url = reverse(self.verify_eligibility_url_name, kwargs={'election_pk': self.election.pk})

        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(response.data['eligible'])
        self.assertIn('Error al contactar el servicio', response.data['reason'])
        self.assertFalse(Voter.objects.filter(user=self.normal_user).exists())