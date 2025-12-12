# apps/mockextusers/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class TestUser(models.Model):
    """
    Simula un registro de usuario en un sistema externo de padrón.
    Contiene campos complejos para permitir filtros avanzados.
    """
    
    # 1. Información de Identificación
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(_('full name'), max_length=255)
    
    # 2. Roles y Categorías
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', _('Estudiante')
        PROFESSOR = 'PROFESSOR', _('Profesor')
        EXECUTIVE = 'EXECUTIVE', _('Ejecutivo')

    role = models.CharField(
        _('rol'),
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )
    
    # 3. Campos Específicos por Rol (Para filtros)
    # Estudiantes
    student_class = models.CharField(_('clase/sección'), max_length=100, blank=True, null=True)
    school_year = models.PositiveIntegerField(_('año escolar'), blank=True, null=True)
    
    # Profesores
    subjects_taught = models.JSONField(
        _('asignaturas'), 
        default=list, 
        blank=True, 
        help_text=_('Lista de asignaturas que imparte.')
    )
    # Grados: Licenciatura, Maestría, Doctorado
    degree = models.CharField(
        _('grado académico'), 
        max_length=50, 
        blank=True, 
        null=True,
        choices=[('Bachelor', 'Licenciatura'), ('Master', 'Maestría'), ('Doctor', 'Doctorado')]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('usuario de prueba')
        verbose_name_plural = _('usuarios de prueba')
        ordering = ['email']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
