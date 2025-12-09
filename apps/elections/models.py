from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Election(models.Model):
    """
    Representa un proceso electoral completo.
    Define las reglas de tiempo, tipo de acceso y configuración de la votación.
    """

    # Definición de Estados (Enumeración)
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Borrador')
        OPEN = 'OPEN', _('Abierta')
        CLOSED = 'CLOSED', _('Finalizada')
        ARCHIVED = 'ARCHIVED', _('Archivada')

    # Definición de Tipos de Elección
    class Type(models.TextChoices):
        PUBLIC = 'PUBLIC', _('Pública')
        PRIVATE = 'PRIVATE', _('Privada')
        INTERNAL = 'INTERNAL', _('Interna / Institucional')

    # Relación con el creador (Owner)
    # Usamos settings.AUTH_USER_MODEL para referenciar al modelo de Usuario personalizado
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='elections',
        verbose_name=_('propietario')
    )

    # Campos descriptivos
    title = models.CharField(_('título'), max_length=255)
    desc = models.TextField(_('descripción'), blank=True)

    # Ventana temporal
    start_at = models.DateTimeField(_('fecha de inicio'))
    end_at = models.DateTimeField(_('fecha de fin'))

    # Configuración
    type = models.CharField(
        _('tipo'),
        max_length=20,
        choices=Type.choices,
        default=Type.PRIVATE
    )
    
    max_sel = models.PositiveIntegerField(
        _('selecciones máximas'),
        default=1,
        help_text=_('Número máximo de candidatos que se pueden seleccionar en un solo voto.')
    )

    status = models.CharField(
        _('estado'),
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    ext_validation_url = models.URLField(
        _('URL de Validación Externa'), 
        max_length=500, 
        blank=True, 
        null=True,
        help_text=_('URL del servicio que valida la elegibilidad del votante si no está en el padrón local.')
    )
    # Trazabilidad
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('elección')
        verbose_name_plural = _('elecciones')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def clean(self):
        """
        Validación de reglas de negocio a nivel de modelo.
        """
        # Regla: La fecha de fin no puede ser anterior a la fecha de inicio
        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValidationError({
                'end_at': _('La fecha de fin debe ser posterior a la fecha de inicio.')
            })
        
        # Regla: max_sel debe ser al menos 1
        if self.max_sel < 1:
            raise ValidationError({
                'max_sel': _('Debe permitirse seleccionar al menos un candidato.')
            })

    def save(self, *args, **kwargs):
        self.full_clean()  # Asegura que se ejecute clean() antes de guardar
        super().save(*args, **kwargs)