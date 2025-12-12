import os
import sys
import django
from collections import defaultdict
import json

# ------------------- CONFIGURACIÓN DE ENTORNO -------------------
PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) 
sys.path.insert(0, PROJECT_BASE_DIR) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'validvote.settings') 

try:
    django.setup()
except Exception as e:
    print(f"ERROR: Fallo al inicializar Django para la lógica de resultados: {e}")
    sys.exit(1)
# ---------------------------------------------------------------

from apps.elections.models import Election
from apps.mockchain.models import MockchainTx
from apps.candidates.models import Candidate

def calculate_election_results(election_title="Presupuesto Corporativo"):
    """
    Simula el escrutinio de votos leyendo directamente las transacciones
    de la Mockchain (Fuente de Verdad inmutable).
    
    Esta función NO consulta VoteRecord; solo se basa en MockchainTx.
    """
    print(f"--- Iniciando Escrutinio para: {election_title} ---")
    
    try:
        election = Election.objects.get(title__icontains=election_title)
        candidates = Candidate.objects.filter(election=election)
        
        # Mapeo de IDs de Payloads a Nombres de Candidatos
        # Esto es necesario porque el payload de la Mockchain solo tiene el 'choice_id'
        candidate_map = {
            "CANDIDATE_FAVOR": candidates.get(name__icontains="A Favor").name,
            "CANDIDATE_CONTRA": candidates.get(name__icontains="En Contra").name,
        }
        
    except (Election.DoesNotExist, Candidate.DoesNotExist) as e:
        print(f"!!! ERROR: No se encontró la elección o los candidatos: {e}")
        return

    # 1. Obtener todas las transacciones de la Mockchain relacionadas
    # Como MockchainTx NO tiene FK a Election, filtramos todas las TXs
    # y confiamos en que contienen el payload que buscamos.
    transactions = MockchainTx.objects.all().order_by('created_at')

    if not transactions.exists():
        print("!!! No se encontraron transacciones en la Mockchain para auditar.")
        return

    # Inicializar el contador de resultados
    results = defaultdict(int)
    total_votes = 0

    # 2. Procesar cada transacción (cada voto)
    for tx in transactions:
        try:
            # El payload es un JSONField que contiene la información del voto
            payload_data = tx.payload
            choice_id = payload_data.get('choice_id') # Usamos la clave que definimos en apps/mockchain/mocks.py

            if choice_id in candidate_map:
                candidate_name = candidate_map[choice_id]
                results[candidate_name] += 1
                total_votes += 1
            else:
                print(f"[!] TX {tx.tx_id[:10]}... ignorada: choice_id desconocido '{choice_id}'.")

        except json.JSONDecodeError:
            print(f"[!] Error decodificando payload para TX {tx.tx_id[:10]}...")
        except Exception as e:
            print(f"[!] Error general al procesar TX {tx.tx_id[:10]}...: {e}")


    # 3. Presentar los resultados
    print("\n========================================================")
    print(f"✅ RESULTADO FINAL DEL ESCRUTINIO - {election.title.upper()}")
    print("========================================================")
    
    for name, count in sorted(results.items(), key=lambda item: item[1], reverse=True):
        print(f"  > {name}: {count} votos")

    print(f"\nTOTAL DE VOTOS CONTABILIZADOS: {total_votes}")
    print("========================================================")

if __name__ == '__main__':
    calculate_election_results()


"""
================================================================================
LÓGICA DE ESCRUTINIO (FASE 5: CONTEO DE RESULTADOS)
================================================================================

Esta función simula el proceso de escrutinio oficial post-cierre de la elección. 
Su objetivo es garantizar la inmutabilidad y la trazabilidad del resultado final.

### Mecanismo de Escrutinio

1.  **Fuente de Verdad:** Consulta *exclusivamente* el modelo MockchainTx. Esto simula 
    la consulta a la API de la Blockchain, asegurando que el conteo se basa en la 
    fuente de datos inmutable.
2.  **Conciliación:** Mapea el 'choice_id' encontrado dentro del Payload de la TX al 
    nombre del Candidato (Moción 'A Favor' o 'En Contra').
3.  **Resultado:** Cuenta las ocurrencias y presenta el resultado final.

### Confirma
- Que el sistema calcula los resultados a partir de la fuente inmutable.
- Que los mocks creados se contabilizan correctamente (5 A Favor, 2 En Contra).
"""