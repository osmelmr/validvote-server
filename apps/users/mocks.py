import os
import sys
import django
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

# ------------------- CONFIGURACIÓN DE ENTORNO CORREGIDA V3 -------------------
# 1. Obtenemos la ruta de la raíz del proyecto (la carpeta 'validvote' que contiene 'apps' y el settings)
# __file__ está en .../validvote/apps/users/mocks.py
# Subimos tres niveles para llegar a la carpeta raíz C:\Users\Osmel\Projects\tesis\validvote
PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 

# 2. Añadimos la raíz del proyecto al path
# Usamos insert(0) para darle máxima prioridad
sys.path.insert(0, PROJECT_BASE_DIR) 

# 3. Módulo de configuración: validvote.settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'validvote.settings') 

try:
    django.setup()
except Exception as e:
    # Si el error persiste, muestra el error de importación específico
    print(f"ERROR: Fallo al inicializar Django. Asegúrate de que 'validvote.settings' es correcto y que las carpetas 'apps' y 'apps/core' tienen el archivo __init__.py.")
    print(f"Detalle del error: {e}")
    sys.exit(1)
# -----------------------------------------------------------------------------

from apps.users.models import User

def create_users():
    """Crea un superusuario, organizadores y votantes regulares."""
    print("--- Iniciando creación de Mocks para USERS ---")

    # 1. Crear Superusuario (Admin)
    admin_email = "admin@validvote.com"
    try:
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                name="Administrador del Sistema",
                password="adminpassword123"
            )
            print(f"[+] Superusuario creado: {admin_email} | Password: adminpassword123")
        else:
            print(f"[-] El superusuario {admin_email} ya existe.")
    except (IntegrityError, ValidationError) as e:
        print(f"!!! Error al crear Superusuario: {e}")
        
    # 2. Crear Organizadores de Elecciones (Election Owners)
    organizers = [
        {"email": "organizador1@university.edu", "name": "Comité Electoral Ingeniería"},
        {"email": "organizador2@company.com", "name": "RRHH Corporativo"},
    ]

    for org in organizers:
        try:
            user, created = User.objects.get_or_create(
                email=org["email"],
                defaults={
                    "name": org["name"],
                    "is_staff": False, 
                    "is_active": True
                }
            )
            if created:
                user.set_password("orgpassword123")
                user.save()
                print(f"[+] Organizador creado: {org['email']} | Password: orgpassword123")
            else:
                 # Asegura que el usuario tiene password si ya existía
                if not user.has_usable_password():
                    user.set_password("orgpassword123")
                    user.save()
                print(f"[-] Organizador ya existe: {org['email']}")
        except (IntegrityError, ValidationError) as e:
            print(f"!!! Error al crear Organizador {org['email']}: {e}")
            
    # 3. Crear Votantes (Usuarios regulares)
    voters = [
        {"email": "votante1@student.edu", "name": "Juan Perez (Estudiante)"},
        {"email": "votante2@student.edu", "name": "Maria Garcia (Estudiante)"},
        {"email": "profesor1@university.edu", "name": "Dr. Roberto Gomez"},
        {"email": "empleado1@company.com", "name": "Ana Torres"},
        {"email": "externo@gmail.com", "name": "Pedro Visitante"}, 
    ]

    for voter in voters:
        try:
            user, created = User.objects.get_or_create(
                email=voter["email"],
                defaults={
                    "name": voter["name"],
                    "is_active": True
                }
            )
            if created:
                user.set_password("userpassword123")
                user.save()
                print(f"[+] Votante creado: {voter['email']} | Password: userpassword123")
            else:
                if not user.has_usable_password():
                    user.set_password("userpassword123")
                    user.save()
                print(f"[-] Votante ya existe: {voter['email']}")
        except (IntegrityError, ValidationError) as e:
            print(f"!!! Error al crear Votante {voter['email']}: {e}")


    print("--- Fin de creación de usuarios ---")

if __name__ == '__main__':
    create_users()