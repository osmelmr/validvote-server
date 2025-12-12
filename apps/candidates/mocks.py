import os
import sys
import django
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q 

# ------------------- CONFIGURACIÓN DE ENTORNO -------------------
# Mantenemos la configuración de ruta robusta que funcionó
PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
sys.path.insert(0, PROJECT_BASE_DIR) 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'validvote.settings') 

try:
    django.setup()
except Exception as e:
    print(f"ERROR: Fallo al inicializar Django para Candidate mocks: {e}")
    sys.exit(1)
# ---------------------------------------------------------------

from apps.candidates.models import Candidate
from apps.elections.models import Election
from apps.users.models import User

# URLs de ejemplo para las imágenes de los candidatos
IMAGE_URLS = [
    "https://example.com/images/avatar_blue.jpg",
    "https://example.com/images/avatar_red.jpg",
    "https://example.com/images/avatar_green.jpg",
    "https://example.com/images/avatar_yellow.jpg",
    "https://example.com/images/avatar_purple.jpg",
]

def create_candidates():
    """Crea candidatos asociados a las elecciones Abiertas y Cerradas."""
    print("--- Iniciando creación de Mocks para CANDIDATES ---")

    try:
        # Obtener las elecciones
        elec_student = Election.objects.get(title__icontains="Estudiantiles")
        elec_corp = Election.objects.get(title__icontains="Presupuesto Corporativo")
        
        # Obtener usuarios (para vincular candidatos con cuentas existentes)
        user_votante1 = User.objects.get(email="votante1@student.edu")
        user_profesor1 = User.objects.get(email="profesor1@university.edu")
        user_empleado1 = User.objects.get(email="empleado1@company.com")

    except (Election.DoesNotExist, User.DoesNotExist):
        print("!!! ERROR: No se pudieron encontrar las elecciones o los usuarios base. Asegúrate de ejecutar los mocks de User y Election primero.")
        return

    candidates_to_create = []

    # -----------------------------------------------------------
    # CANDIDATOS PARA ELECCIÓN ESTUDIANTIL (Elección Abierta)
    # -----------------------------------------------------------
    candidates_to_create.extend([
        # Candidato vinculado a un usuario
        {
            "election": elec_student,
            "user": user_votante1, 
            "name": "Frente de Innovación 'Alpha'",
            "bio": "Propuesta de reforma académica y horarios flexibles.",
            "image": IMAGE_URLS[0]
        },
        # Candidato sin vínculo de usuario (ej. lista independiente o partido)
        {
            "election": elec_student,
            "user": None, 
            "name": "Candidato Independiente: Voto Joven",
            "bio": "Comprometidos con la transparencia y el uso de blockchain en la universidad.",
            "image": IMAGE_URLS[1]
        },
        # Tercer candidato para la elección estudiantil
        {
            "election": elec_student,
            "user": user_profesor1, # Un profesor que postula como candidato estudiantil (caso raro, pero posible)
            "name": "Lista 'El Buen Gobernar'",
            "bio": "Experiencia en gestión, buscando eficiencia administrativa.",
            "image": IMAGE_URLS[2]
        }
    ])

    # -----------------------------------------------------------
    # CANDIDATOS PARA ELECCIÓN CORPORATIVA (Elección Cerrada, de Resultados)
    # -----------------------------------------------------------
    # Esta elección es de voto único (max_sel=1)
    candidates_to_create.extend([
        {
            "election": elec_corp,
            "user": user_empleado1,
            "name": "Moción 'A Favor' (Presupuesto)",
            "bio": "Votar Sí asegura inversión en I+D.",
            "image": IMAGE_URLS[3]
        },
        {
            "election": elec_corp,
            "user": None,
            "name": "Moción 'En Contra' (Presupuesto)",
            "bio": "Votar No requiere una auditoría previa.",
            "image": IMAGE_URLS[4]
        }
    ])

    # -----------------------------------------------------------
    # CREACIÓN
    # -----------------------------------------------------------
    for data in candidates_to_create:
        try:
            # Usamos unique_together = ['election', 'user'] para get_or_create
            candidate, created = Candidate.objects.get_or_create(
                election=data['election'],
                user=data['user'],
                defaults=data
            )
            if created:
                print(f"[+] Candidato creado: {candidate.name} en {candidate.election.title}")
            else:
                # Si ya existe, lo actualizamos si es necesario (solo actualiza si el user/election es el mismo)
                Candidate.objects.filter(election=data['election'], user=data['user']).update(**data)
                print(f"[-] Candidato ya existe: {candidate.name} en {candidate.election.title}")

        except (IntegrityError, ValidationError) as e:
            print(f"!!! Error al crear Candidato '{data['name']}': {e}")


    print("--- Fin de creación de candidatos ---")

if __name__ == '__main__':
    create_candidates()