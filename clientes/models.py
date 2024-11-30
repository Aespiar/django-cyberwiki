from django.db import models
from django import forms
from simple_history.models import HistoricalRecords
from simple_history.utils import update_change_reason

class Cliente(models.Model):
    nombre_cliente = models.CharField(max_length=100)
    informacion_general = models.TextField()
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)  # Campo para el logo de cada cliente

    def __str__(self):
        return self.nombre_cliente


class InformacionCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='informacion')
    tipo_informacion = models.CharField(
        max_length=50,
        choices=[
            ('credenciales_servicio', 'Credenciales de Servicio'),
            ('informacion_enlaces', 'Información Enlaces'),
            ('esquema_conectividad', 'Esquema de Conectividad'),
            ('casos_uso', 'Casos de Uso - CyberSOC')
        ]
    )
    contenido = models.TextField()

    def __str__(self):
        return f"{self.get_tipo_informacion_display()} - {self.cliente.nombre_cliente}"


class CasoUso(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='casos_uso')
    descripcion = models.TextField()
    fecha_implementacion = models.DateField()

    def __str__(self):
        return f"Caso de Uso {self.id} - {self.cliente.nombre_cliente}"

class ControlActivo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='activos')
    nombre_activo = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=255, null=True, blank=True)
    ip = models.CharField(max_length=100, null=True, blank=True)
    marca = models.CharField(max_length=100, null=True, blank=True)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    tipo_hw = models.CharField(max_length=100, null=True, blank=True)
    numero_serie = models.CharField(max_length=100, null=True, blank=True)
    requiere_upgrade = models.CharField(max_length=50, null=True, blank=True)
    requiere_mantenimiento = models.CharField(max_length=50, null=True, blank=True)
    numero_mantenimientos = models.IntegerField(null=True, blank=True)
    modelo_vigente = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    fecha_registro = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.nombre_activo} ({self.cliente.nombre_cliente})"
    
class SeccionCliente(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='secciones')
    titulo = models.CharField(max_length=100)
    contenido = models.TextField(null=True, blank=True)
    archivo = models.FileField(upload_to='secciones_archivos/', null=True, blank=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()  # Para registrar el historial

    def __str__(self):
        return f"{self.cliente.nombre_cliente} - {self.titulo}"

class SeccionClienteForm(forms.ModelForm):
    class Meta:
        model = SeccionCliente
        fields = ['titulo', 'contenido', 'archivo']
        

class TablaCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='tablas')
    seccion = models.ForeignKey(SeccionCliente, on_delete=models.CASCADE, related_name='tablas', default=1)  # Asegura relación con sección
    nombre_tabla = models.CharField(max_length=100)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_tabla} - Sección: {self.seccion.id}"

class FilaTabla(models.Model):
    tabla = models.ForeignKey(TablaCliente, on_delete=models.CASCADE, related_name="filas")
    datos = models.JSONField()  # Almacenar cada fila como un JSON (clave-valor)

    def __str__(self):
        return f"Fila de {self.tabla.nombre_tabla}"
