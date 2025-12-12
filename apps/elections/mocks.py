import os
import sys
import django
from datetime import datetime, timedelta
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q # Necesario para buscar al owner

# ------------------- CONFIGURACIÓN DE ENTORNO -------------------
# 1. Obtenemos la ruta de la raíz del proyecto (la carpeta 'validvote')
PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 

# 2. Añadimos la raíz del proyecto al path
sys.path.insert(0, PROJECT_BASE_DIR) 

# 3. Módulo de configuración: validvote.settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'validvote.settings') 

try:
    django.setup()
except Exception as e:
    print(f"ERROR: Fallo al inicializar Django para Election mocks: {e}")
    sys.exit(1)
# ---------------------------------------------------------------

from apps.elections.models import Election
from apps.users.models import User

def create_elections():
    """Crea diversas instancias de elecciones para pruebas."""
    print("--- Iniciando creación de Mocks para ELECTIONS ---")

    # 1. Buscar a los organizadores (Owners)
    try:
        owner_uni = User.objects.get(email="organizador1@university.edu")
        owner_corp = User.objects.get(email="organizador2@company.com")
    except User.DoesNotExist:
        print("!!! ERROR: Los organizadores no existen. Ejecuta apps/users/mocks.py primero.")
        return

    # Definir fechas clave
    now = timezone.now()
    
    # Elección 1: Abierta (Para votar inmediatamente)
    election1_data = {
        "title": "Elección de Representantes Estudiantiles (ABIERTA)",
        "desc": "Votación para elegir a los 3 representantes del alumnado.",
        "owner": owner_uni,
        "start_at": now - timedelta(days=1), # Empezó ayer
        "end_at": now + timedelta(days=5),   # Termina en 5 días
        "type": Election.Type.PUBLIC,
        "status": Election.Status.OPEN,
        "max_sel": 3, # Permite selección múltiple
    }
    
    # Elección 2: Cerrada/Finalizada (Para probar resultados)
    election2_data = {
        "title": "Votación de Presupuesto Corporativo 2024 (CERRADA)",
        "desc": "Aprobación de la moción de presupuesto. Voto único.",
        "owner": owner_corp,
        "start_at": now - timedelta(days=30), # Empezó hace un mes
        "end_at": now - timedelta(days=2),    # Terminó hace 2 días
        "type": Election.Type.INTERNAL,
        "status": Election.Status.CLOSED,
        "max_sel": 1,
    }

    # Elección 3: Borrador (Para configuración y prueba de validación externa)
    election3_data = {
        "title": "Renovación del Comité Directivo (BORRADOR)",
        "desc": "Solo profesores y ejecutivos pueden postular y votar.",
        "owner": owner_uni,
        "start_at": now + timedelta(days=10), # Empieza en 10 días
        "end_at": now + timedelta(days=15),
        "type": Election.Type.PRIVATE,
        "status": Election.Status.DRAFT,
        "max_sel": 1,
        # Simula una URL de validación externa (usaremos esto en los mocks de Voter)
        "ext_validation_url": "https://api.external-validation.edu/check"
    }

    elections_to_create = [election1_data, election2_data, election3_data]

    for data in elections_to_create:
        try:
            election, created = Election.objects.get_or_create(
                title=data['title'],
                defaults=data
            )
            if created:
                print(f"[+] Elección creada: {election.title} | Estado: {election.get_status_display()}")
            else:
                print(f"[-] Elección ya existe: {election.title}")

        except (IntegrityError, ValidationError) as e:
            print(f"!!! Error al crear Elección '{data['title']}': {e}")


    print("--- Fin de creación de elecciones ---")

if __name__ == '__main__':
    create_elections()