from django.db import models

class Archivo(models.Model):
    nombre = models.CharField(max_length=100)
    archivo = models.FileField(upload_to='uploads/')  # Los archivos se guardarán en 'media/uploads/'
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
