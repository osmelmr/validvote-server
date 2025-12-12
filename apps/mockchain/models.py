from django.db import models
from django.utils.translation import gettext_lazy as _

class MockchainTx(models.Model):
    """
    Simulación de un registro de transacción inmutable en la blockchain.
    Contiene la carga útil (payload) del voto y los datos de la transacción (tx_id).
    """

    # Identificador de Transacción
    tx_id = models.CharField(
        _('ID de transacción simulada'),
        max_length=255,
        unique=True,
        help_text=_('Identificador único que simula el hash de la transacción en la red.')
    )
    
    # Hash del Contenido (Vote Hash)
    payload_hash = models.CharField(
        _('hash de la carga útil'),
        max_length=64, # SHA-256
        unique=True,
        help_text=_('Hash del contenido del voto, utilizado para verificación externa.')
    )
    
    # Contenido Inmutable
    payload = models.JSONField(
        _('carga útil del voto'),
        help_text=_('Contenido JSON estructurado y firmado del voto (simulación de datos on-chain).')
    )
    
    # Metadatos del Bloque
    block_number = models.PositiveIntegerField(
        _('número de bloque'),
        default=0,
        help_text=_('Número de bloque simulado en el que se "minó" la transacción.')
    )

    # Trazabilidad
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('transacción mockchain')
        verbose_name_plural = _('transacciones mockchain')
        ordering = ['-created_at']

    def __str__(self):
        return f"Mock TX: {self.tx_id[:10]}... | Hash: {self.payload_hash[:10]}..."
