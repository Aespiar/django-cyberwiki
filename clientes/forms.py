from django import forms
from .models import SeccionCliente, Cliente

class SeccionClienteForm(forms.ModelForm):
    """
    Formulario para crear y editar secciones.
    """
    class Meta:
        model = SeccionCliente
        fields = ['titulo', 'contenido']  # Campos a mostrar en el formulario

class ExcelUploadForm(forms.Form):
    cliente_id = forms.ModelChoiceField(queryset=Cliente.objects.all(), label="Seleccionar Cliente")
    excel_file = forms.FileField(label="Seleccionar archivo Excel")
