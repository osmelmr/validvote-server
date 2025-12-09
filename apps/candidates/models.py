# apps/candidates/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.elections.models import Election

# NOTA: La función candidate_photo_path y su importación ya no son necesarias
# porque no estamos guardando archivos locales, solo una URL.

class Candidate(models.Model):
    """
    Representa a un candidato postulado en una elección específica.
    """
    
    # Relación con la Elección
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='candidates',
        verbose_name=_('elección')
    )

    # Relación con el Usuario
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # Si el usuario se elimina, el candidato permanece.
        null=True,                 # Permite NULL en la base de datos
        blank=True,                # Permite vacío en formularios de Django
        related_name='candidacies'
    )

    # Información pública para la boleta
    name = models.CharField(
        _('nombre en boleta'), 
        max_length=255,
        help_text=_('Nombre público que verán los votantes (puede diferir del nombre de usuario).')
    )
    
    bio = models.TextField(_('biografía/propuesta'), blank=True)
    
    # Campo Actualizado: image como URL
    image = models.URLField(
        _('URL de imagen/avatar'),
        max_length=500, # Aumentamos el máximo para URLS largas
        blank=True, 
        null=True,
        help_text=_('Enlace a la imagen del candidato, alojada externamente.')
    )
    
    # Campo eliminado: ext_id
    
    class Meta:
        verbose_name = _('candidato')
        verbose_name_plural = _('candidatos')
        unique_together = ['election', 'user']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.election.title}"