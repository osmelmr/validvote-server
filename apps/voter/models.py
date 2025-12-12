from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.elections.models import Election

class Voter(models.Model):
    """
    Representa el registro de un votante habilitado para una elección específica.
    Controla si el usuario está autorizado a votar y si ya ha ejercido su voto.
    """
    
    # 1. Relación con la Elección (Padrón específico)
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='voters_register',
        verbose_name=_('elección')
    )

    # 2. Relación con el Usuario (Identidad del votante)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='voter_permissions',
        verbose_name=_('usuario votante')
    )

    # 3. Reglas de Negocio Centrales
    allowed = models.BooleanField(
        _('habilitado para votar'),
        default=False,
        help_text=_('Indica si el administrador ha autorizado a este usuario para votar en la elección.')
    )
    
    voted = models.BooleanField(
        _('voto emitido'),
        default=False,
        help_text=_('Indica si el usuario ya emitió su voto. Si es True, bloquea nuevos intentos.')
    )

    # 4. Datos de Auditoría
    ext_verified = models.BooleanField(
        _('verificado externamente'),
        default=False,
        help_text=_('Indica si la habilitación (allowed) proviene de un sistema de padrón oficial o externo.')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('votante habilitado')
        verbose_name_plural = _('votantes habilitados')
        # Restricción Crítica: Un usuario solo puede tener un registro de participación por elección
        unique_together = ['election', 'user']
        ordering = ['user__email']

    def __str__(self):
        status = "Votó" if self.voted else ("Habilitado" if self.allowed else "Pendiente")
        return f"[{self.election.title}] {self.user.email} ({status})"
