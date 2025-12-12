# apps/mockchain/tests/views_tests.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
import hashlib
import json

from apps.mockchain.models import MockchainTx
from apps.mockchain.serializers import MockchainTxSerializer

class MockchainAPITests(APITestCase):
    
    def setUp(self):
        """Configuración inicial: URLs y datos de prueba."""
        
        self.publish_url = reverse('mockchain:publish-tx')
        
        # Payload de voto simulado
        self.vote_payload = {
            "election_id": 1,
            "voter_id": 101,
            "selections": [5, 6],
            "timestamp": "2025-12-10T12:00:00Z",
            "signature": "MOCK_SIG_XYZ123"
        }
        
        # Hash simulado (SHA-256 de la representación JSON del payload)
        payload_str = json.dumps(self.vote_payload, sort_keys=True)
        self.valid_payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        
        self.valid_data = {
            'payload_hash': self.valid_payload_hash,
            'payload': self.vote_payload,
        }

    # =============================================================
    # TESTS: PUBLICACIÓN DE TRANSACCIÓN (POST /mockchain/publish/)
    # =============================================================

    def test_publish_transaction_success(self):
        """Prueba que una transacción válida se publica correctamente (201)."""
        initial_count = MockchainTx.objects.count()
        
        response = self.client.post(self.publish_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MockchainTx.objects.count(), initial_count + 1)
        
        # 1. Verifica los campos devueltos en la respuesta
        self.assertIn('tx_id', response.data)
        self.assertIn('block_number', response.data)
        self.assertIn('payload_hash', response.data)
        self.assertEqual(response.data['payload_hash'], self.valid_payload_hash)
        
        # 2. Verifica los datos guardados en la BD
        tx = MockchainTx.objects.get(payload_hash=self.valid_payload_hash)
        self.assertEqual(tx.payload, self.vote_payload)
        self.assertEqual(tx.block_number, initial_count + 1) # Verifica el contador simulado

    def test_publish_transaction_missing_payload_hash_400(self):
        """Prueba que una transacción sin payload_hash falla (400)."""
        data = self.valid_data.copy()
        del data['payload_hash']
        
        response = self.client.post(self.publish_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('payload_hash', response.data)
        self.assertEqual(MockchainTx.objects.count(), 0)

    def test_publish_transaction_missing_payload_400(self):
        """Prueba que una transacción sin payload (datos de voto) falla (400)."""
        data = self.valid_data.copy()
        del data['payload']
        
        response = self.client.post(self.publish_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('payload', response.data)
        self.assertEqual(MockchainTx.objects.count(), 0)

    def test_publish_transaction_duplicate_payload_hash_400(self):
        """Prueba que una transacción con un payload_hash duplicado falla (400)."""
        # 1. Crear la primera transacción
        MockchainTx.objects.create(
            tx_id='original-tx-id',
            payload_hash=self.valid_payload_hash,
            payload={'data': 'original'}
        )
        initial_count = MockchainTx.objects.count()
        
        # 2. Intentar crear una segunda transacción con el mismo hash
        response = self.client.post(self.publish_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(MockchainTx.objects.count(), initial_count)
        # El error debe indicar que payload_hash ya existe (unique=True)
        self.assertIn('payload_hash', str(response.data)) 
        self.assertIn('already exists', str(response.data)) # Mensaje típico de unique
        
    def test_tx_id_and_block_number_are_generated(self):
        """Prueba que la vista genera tx_id y block_number, y son de solo lectura."""
        
        # 1. Intentar sobreescribir los campos generados
        data_with_overrides = self.valid_data.copy()
        data_with_overrides['tx_id'] = 'malicious-id'
        data_with_overrides['block_number'] = 999
        
        response = self.client.post(self.publish_url, data_with_overrides, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        tx = MockchainTx.objects.get(payload_hash=self.valid_payload_hash)
        
        # 2. Verificar que los valores generados fueron usados, no los enviados
        self.assertNotEqual(tx.tx_id, 'malicious-id') 
        self.assertNotEqual(tx.block_number, 999)
        self.assertEqual(tx.block_number, 1) # Primer registro, debe ser 1

        # 3. Publicar una segunda vez para verificar la secuencia del block_number
        second_payload = {
            "election_id": 2, "voter_id": 102, "selections": [1]
        }
        payload_str = json.dumps(second_payload, sort_keys=True)
        second_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        second_data = {
            'payload_hash': second_hash,
            'payload': second_payload,
        }
        
        response_2 = self.client.post(self.publish_url, second_data, format='json')
        self.assertEqual(response_2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_2.data['block_number'], 2)

    def test_publish_transaction_unauthenticated_allowed(self):
        """Prueba que el acceso es público (simulando un servicio de blockchain) (201)."""
        response = self.client.post(self.publish_url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MockchainTx.objects.count(), 1)