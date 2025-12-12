# apps/votes/tests/views_tests.py

from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
import hashlib
import json

from apps.elections.models import Election
from apps.voter.models import Voter
from apps.mockchain.models import MockchainTx
from apps.votes.models import VoteRecord

User = get_user_model()

class VoteRecordAPITests(APITestCase):
    
    def setUp(self):
        """Configuración inicial: usuarios, elecciones, padrón y mockchain."""
        
        # 1. Usuarios
        self.owner_user = User.objects.create_user(email='owner@test.com', name='Owner', password='pass')
        self.eligible_voter = User.objects.create_user(email='eligible@test.com', name='EligibleVoter', password='pass')
        self.ineligible_user = User.objects.create_user(email='ineligible@test.com', name='Ineligible', password='pass')
        
        # 2. Elección Abierta
        self.open_election = Election.objects.create(
            owner=self.owner_user,
            title='Elección Activa',
            status=Election.Status.OPEN,
            start_at=timezone.now() - timedelta(days=1),
            end_at=timezone.now() + timedelta(days=7),
        )
        
        # 3. Registro de Padrón (Voter)
        self.eligible_voter_record = Voter.objects.create(
            election=self.open_election,
            user=self.eligible_voter,
            allowed=True,
            voted=False
        )
        Voter.objects.create(
            election=self.open_election,
            user=self.ineligible_user,
            allowed=False, # No habilitado
            voted=False
        )
        
        # 4. Datos de Voto y Mockchain
        self.vote_payload_data = {
            "election_id": self.open_election.pk,
            "selections": [1, 2],
            "nonce": 12345
        }
        payload_str = json.dumps(self.vote_payload_data, sort_keys=True)
        self.vote_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        self.tx_id = 'TX_A_' + self.vote_hash[:15]
        
        # Creamos la TX en la Mockchain (Simulando que el frontend ya la publicó)
        MockchainTx.objects.create(
            tx_id=self.tx_id,
            payload_hash=self.vote_hash,
            payload=self.vote_payload_data,
            block_number=10
        )
        
        # 5. URLs
        self.register_url = reverse('votes:register-tx')
        self.verify_url = reverse('votes:verify-vote', kwargs={'election_pk': self.open_election.pk})
        
        # 6. Datos de Petición Válida
        self.valid_post_data = {
            'election_id': self.open_election.pk,
            'tx_id': self.tx_id,
            'vote_hash': self.vote_hash
        }


    # =============================================================
    # TESTS: REGISTRO DE TRANSACCIÓN (POST /votes/register-tx/)
    # =============================================================

    def test_register_vote_transaction_success(self):
        """Prueba el registro exitoso de un voto válido."""
        self.client.force_authenticate(user=self.eligible_voter)
        
        response = self.client.post(self.register_url, self.valid_post_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(VoteRecord.objects.filter(tx_id=self.tx_id, user=self.eligible_voter).exists())
        
        # Verifica el bloqueo del votante
        self.eligible_voter_record.refresh_from_db()
        self.assertTrue(self.eligible_voter_record.voted)
        self.assertIn('Voto registrado exitosamente', response.data['status'])

    def test_register_vote_transaction_already_voted_forbidden(self):
        """Prueba que un usuario no puede votar dos veces (Voter.voted=True)."""
        self.client.force_authenticate(user=self.eligible_voter)
        
        # Simular que ya votó
        self.eligible_voter_record.voted = True
        self.eligible_voter_record.save()
        
        initial_count = VoteRecord.objects.count()
        response = self.client.post(self.register_url, self.valid_post_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Ya ha emitido su voto', response.data['detail'])
        self.assertEqual(VoteRecord.objects.count(), initial_count)

    def test_register_vote_transaction_not_allowed_forbidden(self):
        """Prueba que un usuario en el padrón pero no habilitado (allowed=False) no puede votar."""
        self.client.force_authenticate(user=self.ineligible_user) # Usuario no allowed
        
        initial_count = VoteRecord.objects.count()
        response = self.client.post(self.register_url, self.valid_post_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No está habilitado para votar', response.data['detail'])
        self.assertEqual(VoteRecord.objects.count(), initial_count)

    def test_register_vote_transaction_mockchain_tx_not_found_400(self):
        """Prueba que el registro falla si la transacción no existe en la Mockchain."""
        self.client.force_authenticate(user=self.eligible_voter)
        
        invalid_data = self.valid_post_data.copy()
        invalid_data['tx_id'] = 'TX_FAKE_12345'
        invalid_data['vote_hash'] = 'a' * 64
        
        response = self.client.post(self.register_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('La transacción o el hash no se encontraron', response.data['detail'])
        
        # Verificar que Voter.voted NO cambió
        self.eligible_voter_record.refresh_from_db()
        self.assertFalse(self.eligible_voter_record.voted)

    def test_register_vote_transaction_unauthenticated_forbidden(self):
        """Prueba que un usuario no autenticado no puede registrar el voto (401)."""
        response = self.client.post(self.register_url, self.valid_post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_register_vote_transaction_fails_on_vote_record_unique_constraint(self):
        """Prueba que una falla en la restricción de unicidad (VoteRecord) causa ROLLBACK total."""
        self.client.force_authenticate(user=self.eligible_voter)
        
        # 1. Crear un VoteRecord duplicado manualmente ANTES del intento
        VoteRecord.objects.create(
            election=self.open_election,
            user=self.eligible_voter,
            hash='PREVIOUS_HASH',
            tx_id='PREVIOUS_TX_ID',
            published_at=timezone.now()
        )
        
        # Reiniciar el estado del votante para el test
        self.eligible_voter_record.voted = False
        self.eligible_voter_record.save()
        
        initial_count = VoteRecord.objects.count()
        
        # 2. Intentar registrar el voto
        # Esto fallará en el paso 3 de la vista (VoteRecord.objects.create)
        response = self.client.post(self.register_url, self.valid_post_data, format='json')
        
        # El error esperado es 500 porque es un fallo de integridad capturado por el bloque except
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('Error interno al finalizar el registro del voto.', response.data['detail'])
        
        # 3. Verificar ROLLBACK: VoteRecord no se crea y Voter.voted no se actualiza
        self.assertEqual(VoteRecord.objects.count(), initial_count) # No debe haber más de 1 (el creado manualmente)
        self.eligible_voter_record.refresh_from_db()
        self.assertFalse(self.eligible_voter_record.voted) # Debe seguir en False (ROLLBACK)


    # =============================================================
    # TESTS: VERIFICACIÓN INDIVIDUAL (GET /votes/verify/<election_pk>/)
    # =============================================================

    def test_verify_my_vote_success(self):
        """Prueba la verificación exitosa de un voto registrado."""
        # 1. Registrar un voto primero
        self.client.force_authenticate(user=self.eligible_voter)
        self.client.post(self.register_url, self.valid_post_data, format='json')
        
        # 2. Intentar verificar
        response = self.client.get(self.verify_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Voto Registrado y Verificado', response.data['status'])
        self.assertEqual(response.data['transaction_id'], self.tx_id)
        self.assertEqual(response.data['vote_hash'], self.vote_hash)
        # Verifica que se incluye la carga útil de la Mockchain
        self.assertEqual(response.data['mockchain_payload_sample'], self.vote_payload_data)

    def test_verify_my_vote_no_record_404(self):
        """Prueba la verificación cuando el usuario no ha votado."""
        self.client.force_authenticate(user=self.eligible_voter)
        
        # No registramos el voto
        response = self.client.get(self.verify_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('No se encontró registro de voto', response.data['detail'])

    def test_verify_my_vote_tx_mismatch_404(self):
        """Prueba la verificación cuando el registro local existe, pero no la TX en la Mockchain."""
        self.client.force_authenticate(user=self.eligible_voter)
        
        # 1. Crear un registro local inválido (apunta a una TX inexistente)
        VoteRecord.objects.create(
            election=self.open_election,
            user=self.eligible_voter,
            hash='FAKE_HASH',
            tx_id='TX_ID_INEXISTENTE',
            published_at=timezone.now()
        )
        
        # 2. Intentar verificar
        response = self.client.get(self.verify_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('El registro local no coincide con la transacción en la cadena', response.data['detail'])