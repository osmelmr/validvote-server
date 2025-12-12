# apps/candidates/tests/views_tests.py
# py .\manage.py test apps.candidates.tests.views_tests

from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.elections.models import Election
from apps.candidates.models import Candidate
from apps.candidates.serializers import CandidateSerializer

User = get_user_model()

class CandidateAPITests(APITestCase):
    
    def setUp(self):
        """Configuración inicial: usuarios, elecciones y URLs."""
        
        # 1. Usuarios
        self.staff_user = User.objects.create_user(
            email='admin@test.com', name='Admin', password='pass', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            email='voter@test.com', name='Voter', password='pass', is_staff=False
        )
        self.other_user = User.objects.create_user(
            email='other@test.com', name='Other', password='pass', is_staff=False
        )
        
        # 2. Elecciones
        future_start = timezone.now() + timedelta(days=1)
        future_end = future_start + timedelta(days=7)
        
        # Elección en borrador (DRAFT) - Permite añadir/modificar candidatos
        self.draft_election = Election.objects.create(
            owner=self.staff_user,
            title='Elección Borrador',
            status=Election.Status.DRAFT,
            start_at=future_start,
            end_at=future_end,
        )
        
        # Elección Abierta (OPEN) - NO permite añadir/modificar candidatos
        self.open_election = Election.objects.create(
            owner=self.staff_user,
            title='Elección Abierta',
            status=Election.Status.OPEN,
            start_at=timezone.now() - timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1),
        )

        # 3. Candidato inicial
        self.candidate = Candidate.objects.create(
            election=self.draft_election,
            user=self.normal_user,
            name='Candidato Base',
            bio='Mi biografía.',
            image='http://example.com/base.jpg'
        )
        
        # 4. URLs con PKs
        self.list_create_url = reverse(
            'candidates:list-create', 
            kwargs={'election_pk': self.draft_election.pk}
        )
        self.detail_url = reverse(
            'candidates:detail-update-delete', 
            kwargs={'election_pk': self.draft_election.pk, 'pk': self.candidate.pk}
        )
        self.open_election_list_url = reverse(
            'candidates:list-create', 
            kwargs={'election_pk': self.open_election.pk}
        )
        
        # 5. Datos para la creación
        self.valid_data = {
            'user': self.other_user.pk, # El ID del usuario que se postula
            'name': 'Nuevo Candidato',
            'bio': 'Propuesta del nuevo candidato.',
            'image': 'http://new.example.com/photo.png'
        }

    # =============================================================
    # TESTS: LISTADO (GET /elections/<election_pk>/candidates/)
    # =============================================================

    def test_list_candidates_success(self):
        """Prueba que cualquier usuario autenticado pueda listar candidatos (200)."""
        # Crear un segundo candidato para asegurar que el listado funciona
        Candidate.objects.create(
            election=self.draft_election,
            user=self.other_user,
            name='Candidato Dos'
        )
        
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.list_create_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['election'], self.draft_election.pk)

    def test_list_candidates_unauthenticated_forbidden(self):
        """Prueba que un usuario no autenticado no puede listar candidatos (401)."""
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    # =============================================================
    # TESTS: CREACIÓN (POST /elections/<election_pk>/candidates/)
    # =============================================================

    def test_create_candidate_by_owner_success(self):
        """Prueba que el dueño de la elección puede añadir un candidato (201)."""
        self.client.force_authenticate(user=self.staff_user) # Dueño de la elección
        initial_count = Candidate.objects.count()
        
        response = self.client.post(self.list_create_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Candidate.objects.count(), initial_count + 1)
        self.assertEqual(response.data['user'], self.other_user.pk)
        self.assertEqual(response.data['election'], self.draft_election.pk)

    def test_create_candidate_by_non_owner_forbidden(self):
        """Prueba que un usuario que no es dueño no puede añadir candidatos (403)."""
        self.client.force_authenticate(user=self.normal_user) # No es dueño
        initial_count = Candidate.objects.count()
        
        response = self.client.post(self.list_create_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Solo el administrador de la elección', response.data['detail'])
        self.assertEqual(Candidate.objects.count(), initial_count)

    def test_create_candidate_election_open_forbidden(self):
        """Prueba que no se puede añadir candidatos a una elección abierta (403)."""
        self.client.force_authenticate(user=self.staff_user) # Dueño de la elección
        
        response = self.client.post(self.open_election_list_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No se pueden añadir candidatos a una elección que está en curso o finalizada', response.data['detail'])

    def test_create_candidate_duplicate_user_in_election(self):
        """Prueba que no se puede crear un candidato duplicado para la misma elección (400)."""
        self.client.force_authenticate(user=self.staff_user) # Dueño de la elección
        
        # Datos duplicados: mismo user (self.normal_user) en misma election (self.draft_election)
        duplicate_data = {
            'user': self.normal_user.pk, # Este usuario ya es self.candidate
            'name': 'Duplicado',
            'bio': 'Intento duplicado',
        }
        
        # El test debe capturar el error de unicidad (unique_together) del modelo
        response = self.client.post(self.list_create_url, duplicate_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # El error en DRF puede ser genérico por el unique_together
        self.assertIn('must make a unique set', str(response.data))
        
    # =============================================================
    # TESTS: DETALLE (GET /elections/<pk>/candidates/<pk>/)
    # =============================================================

    def test_get_candidate_detail_success(self):
        """Prueba obtener los detalles de un candidato (200)."""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.candidate.pk)
        self.assertEqual(response.data['user_name'], self.normal_user.name)
        self.assertEqual(response.data['election_title'], self.draft_election.title)

    def test_get_candidate_detail_not_found(self):
        """Prueba obtener un candidato inexistente (404)."""
        self.client.force_authenticate(user=self.normal_user)
        bad_url = reverse(
            'candidates:detail-update-delete', 
            kwargs={'election_pk': self.draft_election.pk, 'pk': 999}
        )
        response = self.client.get(bad_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    # =============================================================
    # TESTS: ACTUALIZACIÓN (PUT / DELETE)
    # =============================================================

    def test_update_candidate_by_owner_success(self):
        """Prueba que el dueño de la elección puede actualizar al candidato (200)."""
        self.client.force_authenticate(user=self.staff_user) # Dueño de la elección
        new_bio = {'bio': 'Biografía actualizada con PATCH'}
        
        response = self.client.put(self.detail_url, new_bio)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.bio, new_bio['bio'])

    def test_update_candidate_by_non_owner_forbidden(self):
        """Prueba que un usuario que no es dueño no puede actualizar (403)."""
        self.client.force_authenticate(user=self.normal_user) # No es dueño
        original_bio = self.candidate.bio
        new_bio = {'bio': 'Intento de hackeo'}
        
        response = self.client.put(self.detail_url, new_bio)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No tienes permiso', response.data['detail'])
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.bio, original_bio) # Sin cambios

    def test_delete_candidate_by_owner_success(self):
        """Prueba que el dueño de la elección puede eliminar al candidato (204)."""
        self.client.force_authenticate(user=self.staff_user) # Dueño de la elección
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Candidate.objects.filter(pk=self.candidate.pk).exists())

    def test_delete_candidate_election_open_forbidden(self):
        """Prueba que no se puede eliminar un candidato si la elección está abierta (403)."""
        # Crear un candidato en la elección abierta para la prueba
        open_candidate = Candidate.objects.create(
            election=self.open_election,
            user=self.other_user,
            name='Candidato Abierto',
        )
        open_detail_url = reverse(
            'candidates:detail-update-delete', 
            kwargs={'election_pk': self.open_election.pk, 'pk': open_candidate.pk}
        )
        
        self.client.force_authenticate(user=self.staff_user) # Dueño de la elección
        
        response = self.client.delete(open_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No se puede modificar ni eliminar una candidatura en una elección en curso o finalizada', response.data['detail'])
        self.assertTrue(Candidate.objects.filter(pk=open_candidate.pk).exists()) # Debe seguir existiendo