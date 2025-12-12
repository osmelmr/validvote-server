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
    print(f"ERROR: Fallo al inicializar Django para Voter mocks: {e}")
    sys.exit(1)
# ---------------------------------------------------------------

from apps.voter.models import Voter
from apps.elections.models import Election
from apps.users.models import User

def create_voters():
    """Crea registros de votantes para las elecciones."""
    print("--- Iniciando creación de Mocks para VOTER (Padrón Local) ---")

    try:
        # Obtener las elecciones
        elec_student = Election.objects.get(title__icontains="Estudiantiles") # ABIERTA
        elec_corp = Election.objects.get(title__icontains="Presupuesto Corporativo") # CERRADA
        
        # Obtener usuarios del sistema (User)
        user_votante1 = User.objects.get(email="votante1@student.edu")
        user_votante2 = User.objects.get(email="votante2@student.edu")
        user_profesor1 = User.objects.get(email="profesor1@university.edu")
        user_empleado1 = User.objects.get(email="empleado1@company.com")
        user_externo = User.objects.get(email="externo@gmail.com") # No debería ser elegible

    except (Election.DoesNotExist, User.DoesNotExist) as e:
        print(f"!!! ERROR: No se pudieron encontrar las elecciones o los usuarios base: {e}. Asegúrate de ejecutar los mocks anteriores.")
        return

    voters_to_create = []

    # -----------------------------------------------------------
    # Padrón para ELECCIÓN ABIERTA (Estudiantil)
    # -----------------------------------------------------------
    # Votante1 (Elegible, no ha votado)
    voters_to_create.append({
        "user": user_votante1,
        "election": elec_student,
        "is_eligible": True,
        "has_voted": False,
    })
    # Votante2 (Elegible, no ha votado)
    voters_to_create.append({
        "user": user_votante2,
        "election": elec_student,
        "is_eligible": True,
        "has_voted": False,
    })
    # Profesor1 (No Elegible en esta elección)
    voters_to_create.append({
        "user": user_profesor1,
        "election": elec_student,
        "is_eligible": False,
        "has_voted": False,
    })
    # Empleado1 (Elegible, no ha votado)
    voters_to_create.append({
        "user": user_empleado1,
        "election": elec_student,
        "is_eligible": True,
        "has_voted": False,
    })
    # Externo (No Elegible)
    voters_to_create.append({
        "user": user_externo,
        "election": elec_student,
        "is_eligible": False,
        "has_voted": False,
    })

    # -----------------------------------------------------------
    # Padrón para ELECCIÓN CERRADA (Corporativa)
    # Estos usuarios ya DEBEN haber votado para probar resultados
    # -----------------------------------------------------------
    # Empleado1 (Ya votó)
    voters_to_create.append({
        "user": user_empleado1,
        "election": elec_corp,
        "is_eligible": True,
        "has_voted": True, # Clave para el mock de votos
    })
    # Votante1 (Ya votó)
    voters_to_create.append({
        "user": user_votante1,
        "election": elec_corp,
        "is_eligible": True,
        "has_voted": True, # Clave para el mock de votos
    })

# -----------------------------------------------------------
    # CREACIÓN (FINAL: Usando 'allowed' y 'voted')
    # -----------------------------------------------------------
    for data in voters_to_create:
        
        # Parámetros de BÚSQUEDA
        search_kwargs = {
            'user': data['user'],
            'election': data['election'],
        }

        # Parámetros de CREACIÓN/ACTUALIZACIÓN (RENOMBRADOS)
        update_kwargs = {
            # Mapeo: is_eligible -> allowed
            'allowed': data['is_eligible'], 
            # Mapeo: has_voted -> voted
            'voted': data['has_voted'],
        }
        
        # Opcional: Si tienes el campo 'ext_verified' en el mock, lo mapeamos también
        # Asumiendo que no está en el diccionario 'data' de tu mock, lo omitimos por ahora.
        # Si quisieras usarlo:
        # update_kwargs['ext_verified'] = True 

        try:
            # 1. Intentar obtener el registro
            voter = Voter.objects.get(**search_kwargs)
            
            # 2. Si existe, actualizarlo
            Voter.objects.filter(pk=voter.pk).update(**update_kwargs)
            voter.refresh_from_db()
            
            print(f"[-] Voter actualizado: {voter.user.email} en {voter.election.title} (Allowed: {voter.allowed}, Voted: {voter.voted})")
            
        except Voter.DoesNotExist:
            # 3. Si no existe, crearlo
            try:
                voter = Voter.objects.create(
                    **search_kwargs,
                    **update_kwargs 
                )
                print(f"[+] Voter creado: {voter.user.email} en {voter.election.title} (Allowed: {voter.allowed}, Voted: {voter.voted})")
                
            except (IntegrityError, ValidationError) as create_e:
                print(f"!!! Error al crear Voter para '{data['user'].email}' (Creación Fallida): {create_e}")

        except (IntegrityError, ValidationError) as e:
            print(f"!!! Error general al procesar Voter para '{data['user'].email}': {e}")


    print("--- Fin de creación de Voters ---")

if __name__ == '__main__':
    create_voters()