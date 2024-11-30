from django.db import models

class Personal(models.Model):
    nombre = models.CharField(max_length=100)
    turno = models.CharField(max_length=100)
    rol = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='avatars/', default='avatars/avatar.png', blank=True, null=True)
    class Meta:
        db_table = 'main_menu_personal'