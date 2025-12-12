# apps/results/tests.py
# py .\manage.py test apps.results.tests

from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

# Importamos modelos necesarios para la FK, aunque no los usemos directamente en el test
from apps.elections.models import Election
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

# Simulamos la existencia de una elección para obtener la PK
class ResultsSetupMixin:
    """Configuración base para crear elecciones con diferentes estados."""
    def setUp(self):
        super().setUp()
        self.owner_user = User.objects.create_user(email='owner@test.com', password='pass')
        
        # Elección Cerrada (CLOSED): Debe permitir ver resultados
        self.closed_election = Election.objects.create(
            owner=self.owner_user,
            title='Elección Cerrada',
            status=Election.Status.CLOSED,
            start_at=timezone.now() - timedelta(days=2),
            end_at=timezone.now() - timedelta(days=1),
        )
        # Elección Abierta (OPEN): No debe permitir ver resultados
        self.open_election = Election.objects.create(
            owner=self.owner_user,
            title='Elección Abierta',
            status=Election.Status.OPEN,
            start_at=timezone.now() - timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1),
        )
        # Elección Borrador (DRAFT): No debe permitir ver resultados
        self.draft_election = Election.objects.create(
            owner=self.owner_user,
            title='Elección Borrador',
            status=Election.Status.DRAFT,
            start_at=timezone.now() + timedelta(days=1),
            end_at=timezone.now() + timedelta(days=7),
        )

        # URL base para la elección cerrada (éxito)
        self.closed_url = reverse('results:election-results', kwargs={'election_pk': self.closed_election.pk})
        # URL para la elección abierta (falla por estado)
        self.open_url = reverse('results:election-results', kwargs={'election_pk': self.open_election.pk})
        # URL para la elección borrador (falla por estado)
        self.draft_url = reverse('results:election-results', kwargs={'election_pk': self.draft_election.pk})


class ElectionResultsAPITests(ResultsSetupMixin, APITestCase):
    
    # Simulación de la respuesta exitosa del servicio calculate_election_results
    MOCK_SUCCESS_RESULTS = {
        'status': 'CLOSED',
        'total_votes': 100,
        'winner_id': 5,
        'candidate_counts': {
            '5': 60,
            '6': 40
        }
    }

    # =============================================================
    # TESTS DE ÉXITO (Elección CERRADA)
    # =============================================================
    
    @patch('apps.results.views.calculate_election_results')
    def test_get_results_success_when_closed(self, mock_calculate):
        """Prueba que se obtienen los resultados correctamente si la elección está CLOSED (200)."""
        mock_calculate.return_value = (self.MOCK_SUCCESS_RESULTS, None)
        
        # La vista es pública (AllowAny), no necesitamos autenticar
        response = self.client.get(self.closed_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('candidate_counts', response.data)
        self.assertEqual(response.data['total_votes'], 100)
        
        # Verificar que el servicio fue llamado con la PK correcta
        mock_calculate.assert_called_once_with(self.closed_election.pk)


    # =============================================================
    # TESTS DE RESTRICCIÓN POR ESTADO DE ELECCIÓN
    # =============================================================

    @patch('apps.results.views.calculate_election_results')
    def test_get_results_forbidden_when_open(self, mock_calculate):
        """Prueba que los resultados son prohibidos (403) si la elección está OPEN."""
        # Simulamos que el servicio devuelve el estado actual de la elección (OPEN)
        mock_calculate.return_value = ({'status': 'OPEN'}, None) 
        
        response = self.client.get(self.open_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Los resultados solo están disponibles después de que la elección ha finalizado y cerrado.', response.data['detail'])

    @patch('apps.results.views.calculate_election_results')
    def test_get_results_forbidden_when_draft(self, mock_calculate):
        """Prueba que los resultados son prohibidos (403) si la elección está DRAFT."""
        # Simulamos que el servicio devuelve el estado actual de la elección (DRAFT)
        mock_calculate.return_value = ({'status': 'DRAFT'}, None) 
        
        response = self.client.get(self.draft_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Los resultados solo están disponibles después de que la elección ha finalizado y cerrado.', response.data['detail'])


    # =============================================================
    # TESTS DE ERROR DEL SERVICIO
    # =============================================================
    
    @patch('apps.results.views.calculate_election_results')
    def test_get_results_election_not_found(self, mock_calculate):
        """Prueba que se devuelve 404 si la PK no existe o el servicio falla."""
        # Simulamos el error del servicio (e.g., Election.DoesNotExist)
        ERROR_MSG = "Elección con id 999 no encontrada."
        mock_calculate.return_value = (None, ERROR_MSG) 
        
        # Usamos una PK que no existe para el caso de error
        non_existent_url = reverse('results:election-results', kwargs={'election_pk': 999})
        response = self.client.get(non_existent_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], ERROR_MSG)