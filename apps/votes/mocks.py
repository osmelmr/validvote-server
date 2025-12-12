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
    print(f"ERROR: Fallo al inicializar Django para Vote mocks: {e}")
    sys.exit(1)
# ---------------------------------------------------------------

from apps.votes.models import VoteRecord
from apps.mockchain.models import MockchainTx
from apps.elections.models import Election
from apps.voter.models import Voter
from apps.candidates.models import Candidate

# Función auxiliar para generar un hash aleatorio
def generate_random_hash():
    """Genera una cadena hexadecimal simulando un hash de transacción."""
    return ''.join(random.choices('0123456789abcdef', k=64))

def create_votes():
    """Crea registros de votos asociándolos a las transacciones de Mockchain existentes."""
    print("--- Iniciando creación de Mocks para VOTES (Asociación a Mockchain) ---")

    try:
        # 1. Obtener la ELECCIÓN CERRADA y los CANDIDATOS
        elec_corp = Election.objects.get(title__icontains="Presupuesto Corporativo")
        candidate_favor = Candidate.objects.get(election=elec_corp, name__icontains="A Favor")
        candidate_contra = Candidate.objects.get(election=elec_corp, name__icontains="En Contra")

        # 2. Obtener las TRANSACCIONES CREADAS PREVIAMENTE
        mockchain_txs = MockchainTx.objects.all().order_by('created_at') 
        if not mockchain_txs.exists():
            print("!!! ERROR: No se encontraron transacciones en MockchainTx. Ejecuta apps/mockchain/mocks.py primero.")
            return

        # 3. Obtener los VOTANTES LOCALES que YA VOTARON
        voter_records = Voter.objects.filter(election=elec_corp, voted=True)
        voters_in_mock = list(voter_records) 
        
    except (Election.DoesNotExist, Candidate.DoesNotExist, Voter.DoesNotExist) as e:
        print(f"!!! ERROR: No se encontraron los objetos base necesarios: {e}")
        return
    
    # Mapeo de TXs a Votos (7 votos en total, 5 a favor, 2 en contra)
    vote_associations = [
        # Votos A FAVOR (5)
        {'voter': voters_in_mock[0], 'candidate': candidate_favor, 'tx_index': 0}, 
        {'voter': voters_in_mock[1], 'candidate': candidate_favor, 'tx_index': 1}, 
        {'voter': None, 'candidate': candidate_favor, 'tx_index': 2},              
        {'voter': None, 'candidate': candidate_favor, 'tx_index': 3},              
        {'voter': None, 'candidate': candidate_favor, 'tx_index': 4},              
        # Votos EN CONTRA (2)
        {'voter': None, 'candidate': candidate_contra, 'tx_index': 5},             
        {'voter': None, 'candidate': candidate_contra, 'tx_index': 6},             
    ]
    
    
    for association in vote_associations:
        voter_record = association['voter']
        candidate = association['candidate']
        tx = mockchain_txs[association['tx_index']] # Obtiene la TX correspondiente
        
        # 1. Crear el Registro de Voto (VoteRecord)
        try:
            # 🚨 CORRECCIÓN: Usamos 'tx_id' en lugar de 'transaction_hash'
            vote_record_obj, vr_created = VoteRecord.objects.update_or_create(
                tx_id=tx.tx_id, 
                defaults={
                    "election": elec_corp, 
                    "user": voter_record.user if voter_record else None, 
                    "hash": tx.payload_hash, 
                    "published_at": tx.created_at + timedelta(seconds=1), # 🚨 CAMBIO FINAL: Usamos 'published_at'
                    # El campo 'is_counted' parece no existir o es un método, lo dejamos fuera.
                }
            )
            if vr_created:
                voter_email = voter_record.user.email if voter_record else "Votante Externo (Tx-Linked)"
                print(f"[+] Voto registrado para: {voter_email} a favor de {candidate.name} (TX: {tx.tx_id[:10]}...)")
            else:
                print(f"[-] Voto ya existe para TX: {tx.tx_id[:10]}...")

        except (IntegrityError, ValidationError) as e:
            print(f"!!! Error al crear VoteRecord para '{candidate.name}' (TX: {tx.tx_id[:10]}...): {e}")

    print("--- Fin de creación de Votes (Asociados a Mockchain) ---")

if __name__ == '__main__':
    create_votes()