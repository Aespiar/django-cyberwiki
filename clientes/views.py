from django.shortcuts import render, get_object_or_404, redirect
from .models import Cliente, ControlActivo,SeccionCliente, TablaCliente, FilaTabla
from django.contrib import messages
from simple_history.utils import update_change_reason
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from .forms import SeccionClienteForm, ExcelUploadForm
import pandas as pd
import json
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from .utils import procesar_archivo_y_guardar
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# Vista para listar clientes
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/clientes.html', {'clientes': clientes})

# Vista para el detalle de cada cliente
def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    return render(request, 'clientes/detalle_cliente.html', {'cliente': cliente})

# Vista para el control de activos
def control_activos(request):
    cliente_id = request.GET.get("cliente_id", None)
    clientes = Cliente.objects.all()  # Lista de clientes para el dropdown

    # Filtra los activos según el cliente seleccionado
    if cliente_id:
        activos = ControlActivo.objects.filter(cliente_id=cliente_id)
    else:
        activos = ControlActivo.objects.all()

    return render(request, 'clientes/control_activo.html', {
        'activos': activos,
        'clientes': clientes,
        'cliente_id': cliente_id,  # Esto mantiene la selección en el dropdown
    })

def cargar_excel(request):
    if request.method == "POST":
        cliente_id = request.POST.get("cliente_id")
        archivo_excel = request.FILES.get("archivo_excel")

        if not cliente_id or not archivo_excel:
            messages.error(request, "Selecciona un cliente y un archivo Excel.")
            return redirect("control_activos")

        try:
            # Verifica que el cliente existe
            cliente = Cliente.objects.get(id=cliente_id)

            df = pd.read_excel(request.FILES['archivo_excel'])

            # Renombrar columnas si es necesario
            df = df.rename(columns={
                'Ubicación': 'ubicacion',
                'IP': 'ip',
                'Nombre': 'nombre_activo',
                'Marca': 'marca',
                'Modelo': 'modelo',
                'Tipo de HW': 'tipo_hw',
                'Número de Serie': 'numero_serie',
                'Requiere Upgrade': 'requiere_upgrade',
                'Requiere Mantenimiento': 'requiere_mantenimiento',
                'N° de Mantenimientos': 'numero_mantenimientos',
                'Modelo Vigente': 'modelo_vigente',
                'Descripción': 'descripcion',
            })

            # Validar y cargar cada registro
            for _, row in df.iterrows():
                ControlActivo.objects.create(
                    cliente=Cliente.objects.get(id=request.POST['cliente_id']),
                    nombre_activo=row['nombre_activo'],
                    ubicacion=row['ubicacion'],
                    ip=row['ip'],
                    marca=row['marca'],
                    modelo=row['modelo'],
                    tipo_hw=row['tipo_hw'],
                    numero_serie=row['numero_serie'],
                    requiere_upgrade=row['requiere_upgrade'],
                    requiere_mantenimiento=row['requiere_mantenimiento'],
                    numero_mantenimientos=row['numero_mantenimientos'],
                    modelo_vigente=row['modelo_vigente'],
                    descripcion=row['descripcion'],
                )

            messages.success(request, "Archivo Excel cargado correctamente.")
            return redirect("control_activos")
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {e}")
            return redirect("control_activos")
        
def filtrar_activos(request):
    cliente_id = request.GET.get("cliente_id")
    if not cliente_id:
        return JsonResponse([], safe=False)

    activos = ControlActivo.objects.filter(cliente_id=cliente_id).values(
        "ubicacion", "ip", "nombre_activo", "marca", "modelo",
        "tipo_hw", "numero_serie", "requiere_upgrade", 
        "requiere_mantenimiento", "numero_mantenimientos",
        "modelo_vigente", "descripcion"
    )
    return JsonResponse(list(activos), safe=False)


@login_required
def detalle_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    secciones = cliente.secciones.all()
    es_supervisor = request.user.rol == 'Supervisor'

    return render(request, 'clientes/detalle_cliente.html', {
        'cliente': cliente,
        'secciones': secciones,
        'es_supervisor': es_supervisor,
    })

def generar_rowspan(filas, columna_clave):
    """
    Combina filas con valores repetidos en una columna específica, añadiendo rowspan.
    """
    valores_vistos = {}
    for i, fila in enumerate(filas):
        valor = fila[columna_clave]
        if valor in valores_vistos:
            # Incrementar el rowspan en la fila principal
            valores_vistos[valor]['rowspan'] += 1
            # Marcar esta fila con rowspan=0 para omitirla en el template
            fila[columna_clave] = {"text": None, "rowspan": None}
        else:
            # Primera vez que encontramos este valor
            valores_vistos[valor] = {"text": valor, "rowspan": 1}
            fila[columna_clave] = valores_vistos[valor]
    return filas

@login_required
def historial_seccion(request, cliente_id, seccion_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    seccion = get_object_or_404(SeccionCliente, id=seccion_id, cliente=cliente)
    historial = seccion.history.all().order_by('-history_date')
    return render(request, 'clientes/historial_seccion.html', {
        'cliente': cliente,
        'seccion': seccion,
        'historial': historial,
        'es_supervisor' : request.user.rol == 'Supervisor'
    })

def editar_seccion(request, cliente_id, seccion_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    seccion = get_object_or_404(SeccionCliente, id=seccion_id)

    if request.method == 'POST':
        form = SeccionClienteForm(request.POST, instance=seccion)
        if form.is_valid():
            # Verifica si el modelo tiene historial habilitado
            if hasattr(seccion, 'history') and hasattr(seccion, 'history_change_reason'):
                update_change_reason(seccion, "Edición manual desde la interfaz")
            else:
                messages.error(request, "No se pudo registrar el motivo del cambio.")
            form.save()  # Guarda los cambios
            messages.success(request, "Sección actualizada correctamente.")
            return redirect('detalle_cliente', cliente_id=cliente.id)
    else:
        form = SeccionClienteForm(instance=seccion)

    return render(request, 'clientes/editar_seccion.html', {'form': form, 'cliente': cliente})

def restaurar_seccion(request, cliente_id, seccion_id, historial_id):
    # Obtener la sección principal
    seccion = get_object_or_404(SeccionCliente, id=seccion_id, cliente_id=cliente_id)

    # Buscar el historial específico
    historial = seccion.history.filter(history_id=historial_id).first()

    # Validar si el historial existe
    if not historial:
        messages.error(request, f"No se encontró un historial con el ID {historial_id}.")
        return redirect('detalle_cliente', cliente_id=cliente_id)

    # Restaurar los datos desde el historial
    seccion.titulo = historial.titulo
    seccion.contenido = historial.contenido
    seccion.archivo = historial.archivo

    # Registrar el cambio con la razón "Restauración"
    update_change_reason(seccion, f"Restauración a versión anterior (ID Historial: {historial_id})")
    seccion.save()

    # Confirmar el éxito
    messages.success(request, "Sección restaurada correctamente.")
    return redirect('detalle_cliente', cliente_id=cliente_id)

def obtener_secciones(request, cliente_id):
    """
    Vista que devuelve las secciones de un cliente en formato JSON.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    secciones = cliente.secciones.values('titulo', 'contenido', 'ultima_actualizacion')
    return JsonResponse({'secciones': list(secciones)})



def agregar_seccion(request, cliente_id):
    """
    Vista para agregar una nueva sección a un cliente específico.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        form = SeccionClienteForm(request.POST)
        if form.is_valid():
            seccion = form.save(commit=False)
            seccion.cliente = cliente  # Asocia la sección al cliente
            seccion.save()
            return redirect('detalle_cliente', cliente_id=cliente.id)  # Redirige al detalle del cliente
    else:
        form = SeccionClienteForm()
    return render(request, 'clientes/agregar_seccion.html', {'form': form, 'cliente': cliente})

def editar_fila(request, fila_id):
    if request.method == "POST":
        fila = get_object_or_404(FilaTabla, id=fila_id)
        # Actualizar datos en la fila
        for key, value in request.POST.items():
            if key.startswith(f"fila_{fila_id}_"):
                column_name = key.replace(f"fila_{fila_id}_", "")
                fila.datos[column_name] = value
        fila.save()
        return JsonResponse({"success": True, "message": "Fila actualizada correctamente."})
    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

@csrf_exempt
def eliminar_fila(request):
    if request.method == "POST":
        fila_id = request.POST.get('fila_id')

        if not fila_id:
            return JsonResponse({"success": False, "message": "ID de fila no proporcionado."}, status=400)

        try:
            fila = FilaTabla.objects.get(id=fila_id)
            fila.delete()
            return JsonResponse({"success": True, "message": "Fila eliminada correctamente."})
        except FilaTabla.DoesNotExist:
            return JsonResponse({"success": False, "message": "Fila no encontrada."}, status=404)

    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

@csrf_exempt
def guardar_tabla(request):
    if request.method == "POST":
        try:
            # Registra lo que se recibe
            print("Datos recibidos en guardar_tabla:", request.POST)
            
            filas = json.loads(request.POST.get('filas', '[]'))
            tabla_id = request.POST.get('tabla_id')

            if not tabla_id:
                return JsonResponse({"success": False, "message": "ID de tabla no proporcionado."}, status=400)

            tabla = TablaCliente.objects.filter(id=tabla_id).first()
            if not tabla:
                return JsonResponse({"success": False, "message": "Tabla no encontrada."}, status=404)

            for fila in filas:
                fila_id = fila.get('id')
                datos = {key: value for key, value in fila.items() if key != 'id'}

                if fila_id == "new":
                    datos = {key: fila.get(key, "None") for key in fila.keys() if key != 'id'}
                    FilaTabla.objects.create(tabla=tabla, datos=datos)
                else:
                    # Procesar filas existentes
                    datos = {key: fila.get(key, "None") for key in fila.keys() if key != 'id'}
                    try:
                        fila_obj = FilaTabla.objects.get(id=fila_id, tabla=tabla)
                        fila_obj.datos = datos
                        fila_obj.save()
                    except FilaTabla.DoesNotExist:
                        return JsonResponse({"success": False, "message": f"Fila {fila_id} no encontrada."}, status=404)

            return JsonResponse({"success": True, "message": "Cambios guardados correctamente."})

        except Exception as e:
            print("Error al guardar la tabla:", e)
            return JsonResponse({"success": False, "message": "Error interno."}, status=500)

    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)


def exportar_excel(request, tabla_id):
    tabla = get_object_or_404(TablaCliente, id=tabla_id)
    filas = tabla.filas.all()
    data = [fila.datos for fila in filas]
    df = pd.DataFrame(data)

    # Crear respuesta de Excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="tabla_procesada.xlsx"'
    df.to_excel(response, index=False)
    return response

def exportar_pdf(request, tabla_id):
    tabla = get_object_or_404(TablaCliente, id=tabla_id)
    filas = tabla.filas.all()
    data = [list(fila.datos.values()) for fila in filas]
    headers = list(filas.first().datos.keys()) if filas.exists() else []

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    table_data = [headers] + data
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))

    elements = [table]
    doc.build(elements)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

def normalizar_datos_fila(datos):
    claves_vistas = set()
    datos_normalizados = {}

    for key, value in datos.items():
        if key not in claves_vistas:
            datos_normalizados[key] = value  # Mantener valores, incluidos `None`
            claves_vistas.add(key)
        else:
            print(f"Clave duplicada detectada y conservada: {key} - Valor existente: {datos_normalizados[key]}")
    return datos_normalizados


def detalle_seccion(request, cliente_id, seccion_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    seccion = get_object_or_404(SeccionCliente, id=seccion_id, cliente=cliente)
    tabla = TablaCliente.objects.filter(cliente=cliente, seccion=seccion).last()

    # Crear tabla por defecto si no existe
    if not tabla:
        tabla = TablaCliente.objects.create(
            cliente=cliente,
            seccion=seccion,
            nombre_tabla=f"Tabla por defecto para Sección {seccion.id}"
        )
        FilaTabla.objects.bulk_create([
            FilaTabla(tabla=tabla, datos={"columna_1": "Valor 1", "columna_2": "Valor 2"}),
            FilaTabla(tabla=tabla, datos={"columna_1": "Valor 3", "columna_2": "Valor 4"}),
        ])
        messages.info(request, "Se generó una tabla por defecto para esta sección.")

    # Manejo de archivos
    if request.method == 'POST':
        if 'eliminar_archivo' in request.POST:
            if seccion.archivo:
                seccion.archivo.delete()
                seccion.archivo = None
                seccion.save()
                tabla.filas.all().delete()
                messages.success(request, "Archivo y tabla eliminados correctamente.")
            return redirect('detalle_seccion', cliente_id=cliente.id, seccion_id=seccion.id)

        if 'archivo' in request.FILES:
            archivo = request.FILES['archivo']
            if not archivo.name.endswith(('.pdf', '.xlsx', '.txt')):
                messages.error(request, "Solo se permiten archivos PDF, Excel o TXT.")
            else:
                if seccion.archivo:
                    seccion.archivo.delete()
                seccion.archivo = archivo
                seccion.save()

                # Procesar archivo
                tabla.filas.all().delete()
                tabla = procesar_archivo_y_guardar(seccion.archivo.path, cliente.id, seccion.id)
                messages.success(request, "Archivo procesado y tabla generada correctamente.")
            return redirect('detalle_seccion', cliente_id=cliente.id, seccion_id=seccion.id)

    contexto = {
        'cliente': cliente,
        'seccion': seccion,
        'tabla': tabla,
        'es_supervisor': request.user.rol=="Supervisor",
    }
    return render(request, 'clientes/detalle_seccion.html', contexto)