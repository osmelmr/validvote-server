# users/tests/views_tests.py
# py manage.py test apps.users.tests.views_tests

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

# Obtenemos el modelo de usuario activo
User = get_user_model()

class UserAuthTests(APITestCase):
    
    def setUp(self):
        """
        Configuración inicial que se ejecuta antes de cada test.
        """
        # Definimos las URLs. 
        # Asegúrate de que los 'name' en tu urls.py coincidan con estos 
        self.register_url = reverse('users:register') 
        self.login_url = reverse('users:login')
        self.profile_url = reverse('users:profile')
        
        # Datos de usuario de prueba
        self.user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'securepassword123'
        }
        
        # Creamos un usuario en la DB para testear login y perfil
        self.user = User.objects.create_user(**self.user_data)

    # --- TESTS DE REGISTRO ---

    def test_register_user_success(self):
        """Prueba que un usuario se puede registrar correctamente."""
        data = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'password': 'newpassword123'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)  
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], data['email'])

    def test_register_user_missing_data(self):
        """Prueba que el registro falla si faltan datos requeridos."""
        data = {
            'name': 'Incomplete User'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- TESTS DE LOGIN ---

    def test_login_success(self):
        """Prueba login exitoso con credenciales correctas."""
        data = {
            'email': 'test@example.com',
            'password': 'securepassword123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_invalid_password(self):
        """Prueba login fallido con contraseña incorrecta."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- TESTS DE PERFIL ---

    def test_profile_get_authenticated(self):
        """Prueba obtener el perfil estando autenticado."""
        # Forzamos la autenticación del cliente
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_profile_update_authenticated(self):
        """Prueba actualizar el perfil (PUT) estando autenticado."""
        self.client.force_authenticate(user=self.user)
        
        new_data = {'name': 'Updated Name'}
        response = self.client.put(self.profile_url, new_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')

    def test_profile_unauthenticated(self):
        """Prueba que no se puede acceder al perfil sin token."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)