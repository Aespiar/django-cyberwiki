from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    ROLES = [
        ('Supervisor', 'Supervisor'),  # Tiene permisos de edición
        ('Analista', 'Analista')       # Solo puede visualizar
    ]
    rol = models.CharField(max_length=20, choices=ROLES)

    # Especifica un related_name para evitar conflictos entre tablas
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_groups',  # Nombre personalizado
        blank=True,
        help_text='Los grupos a los que pertenece este usuario.',
        verbose_name='grupos'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_user_permissions',  # Nombre personalizado
        blank=True,
        help_text='Permisos específicos para este usuario.',
        verbose_name='permisos de usuario'
    )