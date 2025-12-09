# apps/results/services.py
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
# Importaciones necesarias para la lógica segura
from apps.elections.models import Election, Election
from apps.mockchain.models import MockchainTx
from apps.candidates.models import Candidate
from apps.voter.models import Voter # Para el total de votantes elegibles
from apps.votes.models import VoteRecord # CRÍTICO: La fuente de la auditoría y unicidad
import json

def calculate_election_results(election_id):
    """
    Calcula los resultados finales de una elección de manera segura,
    basándose únicamente en los registros de auditoría (VoteRecord) 
    que han pasado la verificación de elegibilidad y unicidad.
    """
    try:
        election = Election.objects.get(pk=election_id)
    except Election.DoesNotExist:
        return None, _("Elección no encontrada.")

    # 1. Aplicar la Restricción de Negocio (Proceso P7)
    if election.status != Election.Status.CLOSED:
        return {
            'status': election.status,
            'title': election.title,
            'message': _('Los resultados solo están disponibles después de que la elección ha finalizado y cerrado.')
        }, _('Resultados no disponibles.') # Se usa 'Resultados no disponibles' como mensaje de error

    # 2. Obtener los registros de voto auditados (FUENTE DE SEGURIDAD)
    # Solo contamos los votos que fueron registrados exitosamente en el Proceso P6.
    audited_vote_records = VoteRecord.objects.filter(election_id=election_id)
    
    # Obtener los TX_ID de todos los votos auditados
    tx_ids = [record.tx_id for record in audited_vote_records]
    
    # 3. Consultar las transacciones inmutables de la Mockchain basadas en los TX_ID auditados
    # Utilizamos el tx_id para asegurar la trazabilidad.
    mockchain_txs = MockchainTx.objects.filter(tx_id__in=tx_ids)

    results_count = {}
    
    # 4. Pre-cargar los candidatos de la elección
    candidates_in_election = Candidate.objects.filter(election=election).values('id', 'name')
    candidate_names = {c['id']: c['name'] for c in candidates_in_election}
    candidate_ids = set(candidate_names.keys())

    # 5. Sumar votos por candidato
    for tx in mockchain_txs:
        payload = tx.payload
        
        # Asumimos el formato: {"election_id": 1, "candidates": [101, 105], "proof": "..."}
        candidates_voted = payload.get('candidates', [])
        
        # Recorrer las selecciones del votante (Permite max_sel > 1)
        for candidate_id in candidates_voted:
            # Ignorar si el ID del candidato no pertenece a la elección (capa de seguridad extra)
            if candidate_id not in candidate_ids:
                continue

            candidate_id_str = str(candidate_id)
            results_count[candidate_id_str] = results_count.get(candidate_id_str, 0) + 1
            
    # El total de votos es el número de VoteRecords únicos
    total_votes_cast = len(audited_vote_records)
    total_eligible_voters = Voter.objects.filter(election=election, allowed=True).count()
    
    # 6. Formatear resultados
    formatted_results = []
    for id_str, count in results_count.items():
        candidate_id = int(id_str)
        formatted_results.append({
            'candidate_id': candidate_id,
            'candidate_name': candidate_names.get(candidate_id, _('Candidato Desconocido')),
            'vote_count': count
        })

    return {
        'election_id': election.id,
        'title': election.title,
        'status': election.status,
        'total_eligible_voters': total_eligible_voters,
        'total_voters_cast': total_votes_cast, # Votos únicos (un VoteRecord por persona)
        'results': sorted(formatted_results, key=lambda x: x['vote_count'], reverse=True)
    }, None