from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.elections.models import Election
# Asumimos que la app 'voter' ya existe para la FK
from apps.voter.models import Voter 


class VoteRecord(models.Model):
    """
    Registro inmutable en la base de datos local que apunta a la transacción 
    real del voto almacenada en la blockchain. 
    Contiene datos de auditoría, no el contenido secreto del voto.
    """
    
    # Relación con la Elección (Para qué elección se emitió)
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='vote_records',
        verbose_name=_('elección')
    )

    # Relación con el Usuario (Para control interno y trazabilidad administrativa)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Si el usuario se borra, el registro del voto local (auditable) NO debe borrarse.
        related_name='votes_cast',
        null=True, # Permite que el FK se establezca a NULL si el usuario se elimina
        verbose_name=_('usuario votante')
    )

    # Restricción Lógica del Negocio (Voto Único)
    # Se recomienda que la lógica de negocio se fuerce aquí también, aunque la app Voter ya lo hace.
    # Podemos referenciar el registro de Voter si queremos, pero la restricción de unicidad es más limpia en el hash.
    
    # Campo Crítico 1: Prueba de Integridad
    hash = models.CharField(
        _('hash del voto (vote_hash)'),
        max_length=64, # SHA-256 (64 caracteres)
        unique=True, # CRÍTICO: Asegura que el mismo contenido de voto nunca se registre dos veces.
        help_text=_('Hash criptográfico del contenido del voto (publicado en blockchain).')
    )
    
    # Campo Crítico 2: Localizador en la Red
    tx_id = models.CharField(
        _('ID de transacción'),
        max_length=255,
        unique=True, # CRÍTICO: Asegura que la misma transacción no se registre dos veces.
        help_text=_('Identificador de la transacción en la blockchain (hash de la transacción).')
    )

    # Trazabilidad Temporal
    published_at = models.DateTimeField(
        _('fecha de publicación en blockchain'),
        help_text=_('Fecha en la que la transacción fue confirmada y registrada en la blockchain.')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('registro de voto')
        verbose_name_plural = _('registros de votos')
        # Restricción de unicidad adicional: Un usuario solo puede votar una vez por elección.
        # Esta restricción refuerza la lógica ya definida en el modelo Voter.
        unique_together = ['election', 'user']
        ordering = ['-published_at']

    def __str__(self):
        return f"Voto en {self.election.title} | TX: {self.tx_id[:10]}..."