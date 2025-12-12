from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """
    Manager personalizado para autenticación mediante Email en lugar de Username.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El usuario debe tener una dirección de correo electrónico'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('El superusuario debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('El superusuario debe tener is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Modelo de usuario personalizado para el sistema de votación.
    Hereda de AbstractUser pero utiliza email como identificador único.
    """
    username = None  # Eliminamos el campo username
    email = models.EmailField(_('email address'), unique=True)
    
    # Campos específicos definidos en tu tesis
    name = models.CharField(_('full name'), max_length=255)
    
    # Configuraciones de autenticación
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']  # Campos obligatorios al crear superusuario por consola (además de email/pass)

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email
