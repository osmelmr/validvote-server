# apps/voter/tests/views_tests.py
# py .\manage.py test apps.voter.tests.views_tests

from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.elections.models import Election
from apps.voter.models import Voter

User = get_user_model()

class VoterAPITests(APITestCase):
    
    def setUp(self):
        """Configuración inicial: usuarios, elecciones y URLs."""
        
        # 1. Usuarios
        self.owner_user = User.objects.create_user(
            email='owner@test.com', name='Owner', password='pass', is_staff=True
        )
        self.voter_user = User.objects.create_user(
            email='voter@test.com', name='Voter', password='pass', is_staff=False
        )
        self.non_owner_user = User.objects.create_user(
            email='nonowner@test.com', name='NonOwner', password='pass', is_staff=False
        )
        
        # 2. Elecciones
        future_start = timezone.now() + timedelta(days=1)
        future_end = future_start + timedelta(days=7)
        
        # Elección en borrador (DRAFT) - Permite modificar padrón
        self.draft_election = Election.objects.create(
            owner=self.owner_user,
            title='Elección Borrador',
            status=Election.Status.DRAFT,
            start_at=future_start,
            end_at=future_end,
        )
        
        # Elección Abierta (OPEN) - NO permite modificar padrón
        self.open_election = Election.objects.create(
            owner=self.owner_user,
            title='Elección Abierta',
            status=Election.Status.OPEN,
            start_at=timezone.now() - timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1),
        )

        # 3. Registro de Voter inicial en Draft Election
        self.voter_record = Voter.objects.create(
            election=self.draft_election,
            user=self.voter_user,
            allowed=True,
            voted=False
        )
        
        # 4. URLs con PKs
        self.list_create_url = reverse(
            'voter:list-create', 
            kwargs={'election_pk': self.draft_election.pk}
        )
        self.detail_url = reverse(
            'voter:detail-update-delete', 
            kwargs={'election_pk': self.draft_election.pk, 'pk': self.voter_record.pk}
        )
        self.open_election_list_url = reverse(
            'voter:list-create', 
            kwargs={'election_pk': self.open_election.pk}
        )
        
        # 5. Datos para la creación
        self.valid_data = {
            'user': self.non_owner_user.pk, # Usuario a agregar al padrón
            'allowed': True,
        }

    # =============================================================
    # TESTS: LISTADO (GET /elections/<pk>/voters/)
    # =============================================================

    def test_list_voters_by_owner_success(self):
        """Prueba que el dueño de la elección pueda listar el padrón (200)."""
        # Crear un segundo registro de votante
        Voter.objects.create(
            election=self.draft_election,
            user=self.non_owner_user,
            allowed=False,
        )
        
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(self.list_create_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Verifica que los campos de read_only se devuelvan
        self.assertIn('user_email', response.data[0])
        self.assertIn('election_title', response.data[0])

    def test_list_voters_by_non_owner_forbidden(self):
        """Prueba que un usuario que no es dueño no pueda listar el padrón (403)."""
        self.client.force_authenticate(user=self.non_owner_user)
        response = self.client.get(self.list_create_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Solo el administrador de la elección', response.data['detail'])

    # =============================================================
    # TESTS: CREACIÓN (POST /elections/<pk>/voters/)
    # =============================================================

    def test_create_voter_record_by_owner_success(self):
        """Prueba que el dueño de la elección puede agregar un usuario al padrón (201)."""
        self.client.force_authenticate(user=self.owner_user)
        initial_count = Voter.objects.count()
        
        response = self.client.post(self.list_create_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Voter.objects.count(), initial_count + 1)
        self.assertTrue(Voter.objects.filter(user=self.non_owner_user, election=self.draft_election).exists())

    def test_create_voter_record_duplicate_user_forbidden(self):
        """Prueba que no se puede agregar un usuario que ya existe en el padrón (400)."""
        self.client.force_authenticate(user=self.owner_user)
        
        # Intenta agregar el mismo usuario (self.voter_user) que ya existe
        duplicate_data = {
            'user': self.voter_user.pk, 
            'allowed': False, # No importa el valor, fallará por unicidad
        }
        
        response = self.client.post(self.list_create_url, duplicate_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # DRF devuelve este error para unique_together
        self.assertIn('must make a unique set', str(response.data)) 

    def test_create_voter_record_election_open_forbidden(self):
        """Prueba que no se puede modificar el padrón si la elección está OPEN (403)."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.post(self.open_election_list_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No se puede modificar el padrón de una elección que está en curso o finalizada', response.data['detail'])

    # =============================================================
    # TESTS: DETALLE y ACTUALIZACIÓN (GET / PUT / DELETE)
    # =============================================================

    def test_get_voter_detail_by_owner_success(self):
        """Prueba que el dueño puede obtener el detalle de un registro (200)."""
        self.client.force_authenticate(user=self.owner_user)
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.voter_record.pk)
        self.assertEqual(response.data['user_email'], self.voter_user.email)

    def test_update_voter_allowed_by_owner_success(self):
        """Prueba que el dueño puede cambiar el estado 'allowed' de un votante (PUT/PATCH)."""
        self.client.force_authenticate(user=self.owner_user)
        # Cambiar el estado a False
        update_data = {'allowed': False}
        
        response = self.client.put(self.detail_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.voter_record.refresh_from_db()
        self.assertFalse(self.voter_record.allowed)

    def test_update_voter_voted_forbidden(self):
        """Prueba que no se puede modificar el campo 'voted' manualmente (400)."""
        self.client.force_authenticate(user=self.owner_user)
        # Intenta marcar 'voted' como True
        update_data = {'voted': True}
        
        response = self.client.put(self.detail_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('El estado de voto (\'voted\') solo puede ser modificado por el sistema.', str(response.data))
        self.voter_record.refresh_from_db()
        self.assertFalse(self.voter_record.voted) # Sigue en False

    def test_delete_voter_record_by_owner_success(self):
        """Prueba que el dueño puede eliminar un registro del padrón (204)."""
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.delete(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Voter.objects.filter(pk=self.voter_record.pk).exists())

    def test_update_voter_election_open_forbidden(self):
        """Prueba que no se puede modificar un registro si la elección está abierta (403)."""
        # Crear un registro en la elección abierta para la prueba
        open_voter = Voter.objects.create(
            election=self.open_election,
            user=self.non_owner_user,
            allowed=True,
        )
        open_detail_url = reverse(
            'voter:detail-update-delete', 
            kwargs={'election_pk': self.open_election.pk, 'pk': open_voter.pk}
        )
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.put(open_detail_url, {'allowed': False})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No se puede modificar el padrón de una elección en curso o finalizada.', response.data['detail'])

    def test_delete_voter_election_open_forbidden(self):
        """Prueba que no se puede eliminar un registro si la elección está abierta (403)."""
        # Usamos el registro creado en el test anterior si es posible, o creamos uno nuevo
        open_voter = Voter.objects.create(
            election=self.open_election,
            user=self.voter_user,
            allowed=True,
        )
        open_detail_url = reverse(
            'voter:detail-update-delete', 
            kwargs={'election_pk': self.open_election.pk, 'pk': open_voter.pk}
        )
        
        self.client.force_authenticate(user=self.owner_user)
        
        response = self.client.delete(open_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No se puede modificar el padrón de una elección en curso o finalizada.', response.data['detail'])
        self.assertTrue(Voter.objects.filter(pk=open_voter.pk).exists()) # Debe seguir existiendo