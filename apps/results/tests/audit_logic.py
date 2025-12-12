import os
import sys
import django
import json

# ------------------- CONFIGURACIÓN DE ENTORNO -------------------
PROJECT_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) 
sys.path.insert(0, PROJECT_BASE_DIR) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'validvote.settings') 

try:
    django.setup()
except Exception as e:
    print(f"ERROR: Fallo al inicializar Django para la lógica de auditoría: {e}")
    sys.exit(1)
# ---------------------------------------------------------------

from apps.votes.models import VoteRecord
from apps.mockchain.models import MockchainTx

def verify_single_vote_integrity(tx_id: str):
    """
    Verifica la integridad y el registro de un voto individual.
    Concilia el hash registrado localmente (VoteRecord.hash) con el hash
    almacenado en la Mockchain (MockchainTx.payload_hash).
    """
    print(f"--- Iniciando Auditoría para TX: {tx_id[:10]}... ---")
    
    audit_data = {
        'tx_id': tx_id,
        'status': 'PENDING',
        'local_hash': None,
        'chain_hash': None,
        'match': False,
        'details': {}
    }

    try:
        # 1. Buscar el registro local (VoteRecord)
        vote_record = VoteRecord.objects.get(tx_id=tx_id)
        audit_data['local_hash'] = vote_record.hash
        audit_data['details']['local_user'] = vote_record.user.email if vote_record.user else "Votante Externo/Anónimo"
        audit_data['details']['local_election'] = vote_record.election.title
        
    except VoteRecord.DoesNotExist:
        audit_data['status'] = 'FAIL_LOCAL'
        audit_data['details']['error'] = "ERROR: No se encontró el registro de auditoría local (VoteRecord)."
        print(f"!!! Error de auditoría: {audit_data['details']['error']}")
        return audit_data

    try:
        # 2. Buscar la transacción inmutable (MockchainTx)
        mockchain_tx = MockchainTx.objects.get(tx_id=tx_id)
        audit_data['chain_hash'] = mockchain_tx.payload_hash
        
    except MockchainTx.DoesNotExist:
        audit_data['status'] = 'FAIL_CHAIN'
        audit_data['details']['error'] = "ERROR: No se encontró la transacción en la Mockchain."
        print(f"!!! Error de auditoría: {audit_data['details']['error']}")
        return audit_data
    
    # 3. Conciliar los hashes
    if audit_data['local_hash'] == audit_data['chain_hash']:
        audit_data['match'] = True
        audit_data['status'] = 'SUCCESS'
        audit_data['details']['message'] = "✅ INTEGRIDAD CONFIRMADA: El voto local coincide con el registro inmutable de la Mockchain."
    else:
        audit_data['match'] = False
        audit_data['status'] = 'FAIL_HASH'
        audit_data['details']['message'] = "🚨 ALERTA DE INTEGRIDAD: Los hashes no coinciden. Posible manipulación o error de registro."

    print(f"--- Auditoría Completada: {audit_data['status']} ---")
    return audit_data

# ----------------------------------------------------------------------
# PRUEBA DE EJECUCIÓN CON MOCKS CREADOS
# ----------------------------------------------------------------------

if __name__ == '__main__':
    # Obtener un TX ID de éxito (el primer TX que creamos)
    try:
        # Usamos el TX ID de un voto a favor (de la Mockchain)
        tx_to_test = MockchainTx.objects.first()
        
        # 1. Prueba de Éxito (Transacción Válida)
        result_success = verify_single_vote_integrity(tx_to_test.tx_id)
        print("\nResultado JSON de Prueba Exitosa:")
        print(json.dumps(result_success, indent=4))
        
        # 2. Prueba de TX ID Inexistente (Error en la cadena)
        print("\n" + "="*50 + "\n")
        fake_tx_id = "fffeeecccbbaaa111222333444555666777888999000aaabbbcccdddeeefff"
        result_fail_chain = verify_single_vote_integrity(fake_tx_id)
        print("\nResultado JSON de Prueba con TX Inexistente:")
        print(json.dumps(result_fail_chain, indent=4))
        
    except MockchainTx.DoesNotExist:
        print("\n!!! ERROR: Asegúrate de que MockchainTx.objects.first() retorna una transacción para la prueba.")
        print("Ejecuta apps/mockchain/mocks.py y apps/votes/mocks.py antes de esta prueba.")
    except Exception as e:
        print(f"\n!!! Error inesperado durante la ejecución de pruebas: {e}")

"""
================================================================================
LÓGICA DE AUDITORÍA INDIVIDUAL (FASE 5: VERIFICACIÓN)
================================================================================

Esta función implementa la transparencia y auditoría individual del sistema.
Permite a cualquier usuario (votante o auditor) verificar que su voto fue 
registrado correctamente y no ha sido alterado.

### Mecanismo de Conciliación

1.  **Búsqueda Local (VoteRecord):** Busca el registro local de auditoría usando el 'tx_id'. 
    Obtiene el hash del voto registrado localmente (VoteRecord.hash).
2.  **Búsqueda Inmutable (MockchainTx):** Busca la transacción en la Mockchain 
    utilizando el mismo 'tx_id'. Obtiene el hash almacenado en la cadena (MockchainTx.payload_hash).
3.  **Verificación de Integridad:** Compara ambos hashes. Si son idénticos, 
    la integridad del voto está confirmada. Si difieren, hay una alerta.

### Pruebas de Ejecución (if __name__ == '__main__':)

- **Prueba de Éxito:** Utiliza el primer TX ID existente para confirmar que los hashes 
  coinciden, validando la integridad (Status: SUCCESS).
- **Prueba de Fallo:** Utiliza un TX ID inexistente para simular que el voto nunca fue 
  registrado localmente, verificando que el sistema maneje el error de búsqueda 
  correctamente (Status: FAIL_LOCAL/FAIL_CHAIN).

### Confirma
- Que el sistema puede conciliar el estado local del voto con la fuente de verdad inmutable.
- Que el 'tx_id' es la clave de unión entre el registro local y la cadena.
"""