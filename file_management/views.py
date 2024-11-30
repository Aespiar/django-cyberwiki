from django.shortcuts import render,redirect
import pandas as pd
import pdfplumber
from .forms import ArchivoForm
from .models import Archivo
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

def upload_file(request):
    if request.method == 'POST':
        form = ArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('archivo_list')
    else:
        form = ArchivoForm()
    return render(request, 'file_management/upload.html', {'form': form})
def archivo_list(request):
    archivos = Archivo.objects.all()  # Recupera todos los archivos de la base de datos
    return render(request, 'file_management/archivo_list.html', {'archivos': archivos})

def upload_file_view(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_url = fs.url(filename)

        if filename.endswith('.pdf'):
            # Extraer datos de PDF
            extracted_data = extract_pdf_table(fs.path(filename))
        elif filename.endswith('.xlsx'):
            # Leer Excel
            extracted_data = extract_excel_table(fs.path(filename))
        
        return render(request, 'edit_data.html', {'data': extracted_data, 'file_url': file_url})

    return render(request, 'upload.html')

def extract_pdf_table(file_path):
    data = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                data.extend(table)
    return data

def limpiar_datos(data):
    """
    Reemplaza valores None por 'No especificado'.
    """
    return [
        {k: (v if v is not None else "No especificado") for k, v in row.items()}
        for row in data
    ]

def extract_excel_table(file_path):
    df = pd.read_excel(file_path)
    return df.to_dict(orient='records')
