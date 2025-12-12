import os
import sys
import django
import random
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from datetime import timedelta

# ------------------- CONFIGURACIÓN DE ENTORNO -------------------
PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
sys.path.insert(0, PROJECT_BASE_DIR) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'validvote.settings') 

try:
    django.setup()
except Exception as e:
    print(f"ERROR: Fallo al inicializar Django para Mockchain mocks: {e}")
    sys.exit(1)
# ---------------------------------------------------------------

from apps.mockchain.models import MockchainTx
from apps.elections.models import Election

# Función auxiliar para generar un hash aleatorio
def generate_random_hash():
    """Genera una cadena hexadecimal simulando un hash de transacción."""
    return ''.join(random.choices('0123456789abcdef', k=64))

def create_mockchain_transactions():
    """Crea registros de transacciones simuladas para la elección cerrada."""
    print("--- Iniciando creación de Mocks para MOCKCHAIN TX ---")

    try:
        # 1. Obtener la ELECCIÓN CERRADA
        elec_corp = Election.objects.get(title__icontains="Presupuesto Corporativo")
    except Election.DoesNotExist as e:
        print(f"!!! ERROR: No se encontró la elección corporativa: {e}")
        return

    # Definir la estructura de las transacciones a crear (7 en total)
    # Estas 7 transacciones corresponden a los 7 votos que queremos simular.
    NUM_TRANSACTIONS = 7
    transactions_to_create = []
    
    # Payload base, solo con metadatos de voto simulados
    base_payload = {
        "voter_id_sim": "N/A", # Será actualizado en el siguiente mock
        "choice_id": None, 
        "timestamp": None,
        "signature_sim": generate_random_hash(),
    }
    
    # Simulamos 5 votos A FAVOR y 2 EN CONTRA (basado en el mock de VoteRecord)
    simulated_choices = [
        # 5 A FAVOR
        {"choice_id": "CANDIDATE_FAVOR"}, {"choice_id": "CANDIDATE_FAVOR"}, 
        {"choice_id": "CANDIDATE_FAVOR"}, {"choice_id": "CANDIDATE_FAVOR"}, 
        {"choice_id": "CANDIDATE_FAVOR"}, 
        # 2 EN CONTRA
        {"choice_id": "CANDIDATE_CONTRA"}, {"choice_id": "CANDIDATE_CONTRA"},
    ]

    for i in range(NUM_TRANSACTIONS):
        tx_hash_base = generate_random_hash()
        
        # 1. Crear el Payload con detalles del voto
        payload = base_payload.copy()
        payload['choice_id'] = simulated_choices[i]['choice_id']
        payload['timestamp'] = str(elec_corp.start_at + timedelta(minutes=(i + 1) * 5))
        
        # 2. Definir los datos de la transacción Mockchain
        transactions_to_create.append({
            "tx_id": tx_hash_base, 
            "payload": payload,
            "payload_hash": generate_random_hash(),
            "block_number": 1, # Todos en el primer bloque simulado
        })

    # -----------------------------------------------------------
    # CREACIÓN FINAL
    # -----------------------------------------------------------
    for data in transactions_to_create:
        try:
            # Usamos update_or_create para manejar re-ejecuciones
            mockchain_tx, tx_created = MockchainTx.objects.update_or_create(
                tx_id=data['tx_id'], 
                defaults={
                    "payload": data['payload'],
                    "payload_hash": data['payload_hash'],
                    "block_number": data['block_number'],
                }
            )
            if tx_created:
                choice = data['payload']['choice_id']
                print(f"[+] TX {mockchain_tx.tx_id[:10]}... creada (Payload: {choice})")
            else:
                choice = data['payload']['choice_id']
                print(f"[-] TX {mockchain_tx.tx_id[:10]}... actualizada (Payload: {choice})")

        except (IntegrityError, ValidationError, Exception) as e:
            print(f"!!! Error al crear MockchainTx para {data['tx_id'][:10]}...: {e}")


    print("--- Fin de creación de Mockchain TX ---")

if __name__ == '__main__':
    create_mockchain_transactions()