import os
import sys
import django
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

# ------------------- CONFIGURACIÓN DE ENTORNO -------------------
# Mantenemos la configuración de ruta robusta que funcionó
PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
sys.path.insert(0, PROJECT_BASE_DIR) 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'validvote.settings') 

try:
    django.setup()
except Exception as e:
    print(f"ERROR: Fallo al inicializar Django para TestUser mocks: {e}")
    sys.exit(1)
# ---------------------------------------------------------------

from apps.mockextusers.models import TestUser

def create_test_users():
    """Crea registros de usuarios simulados de un padrón externo."""
    print("--- Iniciando creación de Mocks para TEST USERS (Padrón Externo) ---")

    test_users_data = [
        # Usuario Estudiante (coincide con votante1, votante2)
        {
            "email": "votante1@student.edu",
            "full_name": "Juan Perez - Test Student",
            "role": TestUser.Role.STUDENT,
            "student_class": "A-2025",
            "school_year": 2,
        },
        {
            "email": "votante2@student.edu",
            "full_name": "Maria Garcia - Test Student",
            "role": TestUser.Role.STUDENT,
            "student_class": "B-2024",
            "school_year": 3,
        },
        # Usuario Profesor (coincide con profesor1)
        {
            "email": "profesor1@university.edu",
            "full_name": "Dr. Roberto Gomez - Test Professor",
            "role": TestUser.Role.PROFESSOR,
            "subjects_taught": ["Criptografía", "Sistemas Distribuidos"],
            "degree": "Doctor",
        },
        # Usuario Ejecutivo (coincide con organizador2, empleado1)
        {
            "email": "empleado1@company.com",
            "full_name": "Ana Torres - Test Executive",
            "role": TestUser.Role.EXECUTIVE,
            "degree": "Master",
        },
        # Usuario que NO tiene una cuenta en el sistema principal (User)
        {
            "email": "unregistered@external.net",
            "full_name": "Visitante No Registrado",
            "role": TestUser.Role.EXECUTIVE,
            "degree": "Bachelor",
        },
    ]

    for data in test_users_data:
        try:
            # Quitamos los campos específicos del diccionario de datos para el defaults
            role_specific_fields = {}
            if data['role'] == TestUser.Role.STUDENT:
                role_specific_fields = {'student_class': data.pop('student_class'), 'school_year': data.pop('school_year')}
            elif data['role'] == TestUser.Role.PROFESSOR or data['role'] == TestUser.Role.EXECUTIVE:
                role_specific_fields = {'subjects_taught': data.pop('subjects_taught', []), 'degree': data.pop('degree', None)}

            
            user, created = TestUser.objects.get_or_create(
                email=data['email'],
                defaults={
                    "full_name": data['full_name'],
                    "role": data['role'],
                    **role_specific_fields # Añade los campos específicos
                }
            )
            if created:
                print(f"[+] Test User creado: {user.email} | Rol: {user.get_role_display()}")
            else:
                print(f"[-] Test User ya existe: {user.email}")

        except (IntegrityError, ValidationError) as e:
            print(f"!!! Error al crear Test User '{data['email']}': {e}")


    print("--- Fin de creación de Test Users ---")

if __name__ == '__main__':
    create_test_users()