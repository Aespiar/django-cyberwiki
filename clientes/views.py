from django.shortcuts import render, get_object_or_404, redirect
from PIL import Image
from .models import Cliente, ControlActivo,SeccionCliente, TablaCliente, FilaTabla
from django.contrib import messages
from simple_history.utils import update_change_reason
from django.conf import settings
from rapidfuzz import process, fuzz
from django.http import JsonResponse, HttpResponse
from .forms import SeccionClienteForm, ExcelUploadForm
from django.templatetags.static import static
import pandas as pd
import json,os,tempfile
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from .utils import procesar_archivo_y_guardar, procesar_archivo
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# Vista para listar clientes
def lista_clientes(request):
    clientes = Cliente.objects.all()
    for cliente in clientes:
        # Si el logo es vacío o None, usar el valor predeterminado
        if not cliente.logo or cliente.logo == '':
            cliente.logo = 'logos/default_logo.jpg'
    return render(request, 'clientes/clientes.html', {'clientes': clientes})

# Vista para agregar un cliente
def agregar_cliente(request):
    if request.method == 'POST':
        nombre_cliente = request.POST['nombre_cliente']
        informacion_general = request.POST['informacion_general']
        logo = request.FILES.get('logo', None)
        Cliente.objects.create(nombre_cliente=nombre_cliente, informacion_general=informacion_general, logo=logo)
        return redirect('lista_clientes')
    return render(request, 'clientes/agregar_cliente.html')

@receiver(pre_save, sender=Cliente)
def convertir_logo(sender, instance, **kwargs):
    if instance.logo:
        filepath = instance.logo.path
        if filepath.endswith('.jfif'):
            img = Image.open(filepath)
            rgb_im = img.convert('RGB')
            new_filepath = filepath.replace('.jfif', '.jpg')
            rgb_im.save(new_filepath, format='JPEG')
            os.remove(filepath)  # Elimina el archivo original
            instance.logo.name = instance.logo.name.replace('.jfif', '.jpg')

# Vista para editar un cliente
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        cliente.nombre_cliente = request.POST['nombre_cliente']
        cliente.informacion_general = request.POST['informacion_general']
        if 'logo' in request.FILES:
            cliente.logo = request.FILES['logo']
        cliente.save()
        return redirect('lista_clientes')
    return render(request, 'clientes/editar_cliente.html', {'cliente': cliente})

# Vista para listar los activos
def control_activos(request):
    cliente_id = request.GET.get("cliente_id", None)
    clientes = Cliente.objects.all()  # Lista de clientes para el dropdown

    if cliente_id:
        activos = ControlActivo.objects.filter(cliente_id=cliente_id)
    else:
        activos = ControlActivo.objects.all()

    print(f"Activos encontrados: {activos.count()}")
    return render(request, 'clientes/control_activo.html', {
        'activos': activos,
        'clientes': clientes,
        'cliente_id': cliente_id,
    })

# Cargar archivo Excel para actualizar activos
@login_required
def cargar_excel(request):
    if request.method == "POST":
        cliente_id = request.POST.get("cliente_id")
        archivo_excel = request.FILES.get("archivo_excel")

        if not cliente_id or not archivo_excel:
            messages.error(request, "Selecciona un cliente y un archivo Excel.")
            return redirect("control_activos")

        try:
            # Guardar temporalmente el archivo para procesarlo
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                for chunk in archivo_excel.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # Procesar archivo
            datos_procesados = procesar_archivo(temp_file_path)

            # Registrar los datos en la base de datos
            cliente = Cliente.objects.get(id=cliente_id)
            for fila in datos_procesados:
                ControlActivo.objects.create(
                    cliente=cliente,
                    nombre_activo=fila.get('nombre_activo'),
                    ubicacion=fila.get('ubicacion'),
                    ip=fila.get('ip'),
                    marca=fila.get('marca'),
                    modelo=fila.get('modelo'),
                    tipo_hw=fila.get('tipo_hw'),
                    numero_serie=fila.get('numero_serie'),
                    requiere_upgrade=fila.get('requiere_upgrade'),
                    requiere_mantenimiento=fila.get('requiere_mantenimiento'),
                    numero_mantenimientos=fila.get('numero_mantenimientos'),
                    modelo_vigente=fila.get('modelo_vigente'),
                    descripcion=fila.get('descripcion'),
                )

            os.remove(temp_file_path)  # Eliminar archivo temporal
            messages.success(request, "Archivo Excel procesado y datos registrados correctamente.")
        except Exception as e:
            print(f"Error al procesar el archivo: {e}")
            messages.error(request, "Hubo un problema al procesar el archivo.")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)  # Asegurarse de eliminar el archivo temporal

        return redirect("control_activos")

def descomponer_celdas_combinadas(df):
    """
    Rellena las celdas vacías con el último valor no vacío en cada columna.
    Esto asegura que los datos combinados en Excel se propaguen correctamente.
    """
    for column in df.columns:
        df[column] = df[column].fillna(method="ffill")  # Rellenar hacia adelante
    return df

@login_required
@csrf_exempt
def procesar_archivo_control_activo(request):
    if request.method == "POST":
        cliente_id = request.POST.get("cliente_id")
        archivo_excel = request.FILES.get("archivo_excel")

        if not cliente_id or not archivo_excel:
            return JsonResponse({"success": False, "message": "Cliente o archivo no proporcionado."})

        try:
            # Guardar el archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
                for chunk in archivo_excel.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # Leer el archivo Excel
            df = pd.read_excel(temp_file_path)

            # Descomponer celdas combinadas
            df = descomponer_celdas_combinadas(df)

            # Rellenar valores nulos en todas las columnas
            for column in df.columns:
                df[column] = df[column].fillna(method="ffill")  # Rellenar hacia adelante

            # Mapeo flexible de columnas
            columnas_requeridas = {
                "ubicacion": ["Ubicación"],
                "ip": ["IP"],
                "nombre_activo": ["Nombre"],
                "marca": ["Marca"],
                "modelo": ["Modelo"],
                "tipo_hw": ["Tipo de HW"],
                "numero_serie": ["Número de Serie"],
                "requiere_upgrade": ["Requiere Upgrade"],
                "requiere_mantenimiento": ["Requiere Mantenimiento"],
                "numero_mantenimientos": ["N° de Mantenimientos"],
                "modelo_vigente": ["Modelo Vigente"],
                "descripcion": ["Descripción"],
            }

            # Renombrar columnas según el mapeo
            mapeo_columnas = {v[0]: k for k, v in columnas_requeridas.items()}
            df.rename(columns=mapeo_columnas, inplace=True)

            # Validar columnas requeridas
            for col in columnas_requeridas.keys():
                if col not in df.columns:
                    df[col] = None

            # Limpiar y normalizar valores
            df["nombre_activo"] = df["nombre_activo"].fillna("Nombre no definido")  # Reemplazo para valores nulos
            df["numero_mantenimientos"] = pd.to_numeric(df["numero_mantenimientos"], errors="coerce").fillna(0).astype(int)

            # Crear registros
            registros = []
            for _, row in df.iterrows():
                registros.append(ControlActivo(
                    cliente_id=cliente_id,
                    ubicacion=row["ubicacion"],
                    ip=row["ip"],
                    nombre_activo=row["nombre_activo"],
                    marca=row["marca"],
                    modelo=row["modelo"],
                    tipo_hw=row["tipo_hw"],
                    numero_serie=row["numero_serie"],
                    requiere_upgrade=row["requiere_upgrade"],
                    requiere_mantenimiento=row["requiere_mantenimiento"],
                    numero_mantenimientos=row["numero_mantenimientos"],
                    modelo_vigente=row["modelo_vigente"],
                    descripcion=row["descripcion"],
                ))

            # Guardar en la base de datos
            ControlActivo.objects.bulk_create(registros)
            os.remove(temp_file_path)

            return JsonResponse({"success": True, "message": "Archivo procesado y datos cargados correctamente."})

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error al procesar el archivo: {str(e)}"})

    return JsonResponse({"success": False, "message": "Método no permitido."})

# Filtrar activos por cliente
@login_required
def filtrar_activos(request):
    cliente_id = request.GET.get("cliente_id")
    activos = ControlActivo.objects.filter(cliente_id=cliente_id).values() if cliente_id else []
    return JsonResponse(list(activos), safe=False)

# Agregar un activo manualmente
@login_required
@csrf_exempt
def agregar_activo(request):
    if request.method == "POST":
        data = request.POST
        cliente_id = data.get("cliente_id")
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            ControlActivo.objects.create(
                cliente=cliente,
                nombre_activo=data.get("nombre_activo", ""),
                ubicacion=data.get("ubicacion", ""),
                ip=data.get("ip", ""),
                marca=data.get("marca", ""),
                modelo=data.get("modelo", ""),
                tipo_hw=data.get("tipo_hw", ""),
                numero_serie=data.get("numero_serie", ""),
                requiere_upgrade=data.get("requiere_upgrade", ""),
                requiere_mantenimiento=data.get("requiere_mantenimiento", ""),
                numero_mantenimientos=data.get("numero_mantenimientos", 0),
                modelo_vigente=data.get("modelo_vigente", ""),
                descripcion=data.get("descripcion", "")
            )
            return JsonResponse({"success": True, "message": "Activo agregado correctamente."})
        except Cliente.DoesNotExist:
            return JsonResponse({"success": False, "message": "Cliente no encontrado."})
    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

# Editar un activo existente
@login_required
@csrf_exempt
def editar_activo(request, activo_id):
    activo = get_object_or_404(ControlActivo, id=activo_id)

    if request.method == "GET":
        # Devuelve los datos del activo en formato JSON
        return JsonResponse({
            'id': activo.id,
            'nombre_activo': activo.nombre_activo,
            'ubicacion': activo.ubicacion,
            'ip': activo.ip,
            'marca': activo.marca,
            'modelo': activo.modelo,
            'tipo_hw': activo.tipo_hw,
            'numero_serie': activo.numero_serie,
            'requiere_upgrade': activo.requiere_upgrade,
            'requiere_mantenimiento': activo.requiere_mantenimiento,
            'numero_mantenimientos': activo.numero_mantenimientos,
            'modelo_vigente': activo.modelo_vigente,
            'descripcion': activo.descripcion,
        })

    elif request.method == "POST":
        # Actualiza los datos del activo
        data = request.POST
        try:
            activo.nombre_activo = data.get("nombre_activo", activo.nombre_activo)
            activo.ubicacion = data.get("ubicacion", activo.ubicacion)
            activo.ip = data.get("ip", activo.ip)
            activo.marca = data.get("marca", activo.marca)
            activo.modelo = data.get("modelo", activo.modelo)
            activo.tipo_hw = data.get("tipo_hw", activo.tipo_hw)
            activo.numero_serie = data.get("numero_serie", activo.numero_serie)
            activo.requiere_upgrade = data.get("requiere_upgrade", activo.requiere_upgrade)
            activo.requiere_mantenimiento = data.get("requiere_mantenimiento", activo.requiere_mantenimiento)
            activo.numero_mantenimientos = data.get("numero_mantenimientos", activo.numero_mantenimientos)
            activo.modelo_vigente = data.get("modelo_vigente", activo.modelo_vigente)
            activo.descripcion = data.get("descripcion", activo.descripcion)
            activo.save()

            return JsonResponse({"success": True, "message": "Activo actualizado correctamente."})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

# Eliminar un activo
@csrf_exempt
def eliminar_activo(request, activo_id):
    if request.method == 'POST':
        try:
            activo = get_object_or_404(ControlActivo, id=activo_id)
            activo.delete()
            return JsonResponse({'success': True, 'message': 'Activo eliminado correctamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

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

# Vista para eliminar un cliente
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    cliente.delete()
    return redirect('lista_clientes')


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

@login_required
def agregar_seccion(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = SeccionClienteForm(request.POST, request.FILES)
        if form.is_valid():
            seccion = form.save(commit=False)
            seccion.cliente = cliente
            seccion.save()
            return JsonResponse({"success": True, "message": "Sección agregada correctamente."})
        return JsonResponse({"success": False, "message": "Formulario inválido."})

    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

@login_required
@csrf_exempt
def editar_seccion(request, cliente_id, seccion_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    seccion = get_object_or_404(SeccionCliente, id=seccion_id)

    if request.method == 'POST':
        # Incluye tanto request.POST como request.FILES para manejar archivos
        form = SeccionClienteForm(request.POST, request.FILES, instance=seccion)
        if form.is_valid():
            archivo = form.cleaned_data.get('archivo')

            if archivo:
                # Guardar temporalmente el archivo para procesarlo
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo.name)[1]) as temp_file:
                    for chunk in archivo.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name

                try:
                    # Procesar el archivo usando la ruta temporal
                    procesar_archivo_y_guardar(
                        file_path=temp_file_path,
                        cliente_id=cliente_id,
                        seccion_id=seccion_id,
                        nombre_tabla=f"Datos actualizados para {seccion.titulo}"
                    )

                    # Asignar el archivo procesado al campo 'archivo' de la sección
                    seccion.archivo.save(archivo.name, archivo, save=True)

                finally:
                    # Asegurarse de eliminar el archivo temporal
                    os.remove(temp_file_path)
            else:
                # Si no hay archivo, simplemente guarda la sección
                form.save()

            return JsonResponse({"success": True, "message": "Sección actualizada correctamente."})
        else:
            print("Errores del formulario:", form.errors)
            return JsonResponse({"success": False, "message": "Formulario inválido.", "errors": form.errors.as_json()})

    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

@csrf_exempt
def eliminar_seccion(request, cliente_id, seccion_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    seccion = get_object_or_404(SeccionCliente, id=seccion_id, cliente=cliente)

    if request.method == 'POST':
        seccion.delete()
        return JsonResponse({"success": True, "message": "Sección eliminada correctamente."})

    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

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