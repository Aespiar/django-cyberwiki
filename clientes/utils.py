import pdfplumber
import pandas as pd
import json
from .models import Cliente, TablaCliente, FilaTabla, SeccionCliente, ControlActivo


def procesar_archivo(file_path):
    data = []
    columnas_requeridas = [
        'Ubicación', 'IP', 'Nombre', 'Marca', 'Modelo', 'Tipo de HW',
        'Número de Serie', 'Requiere Upgrade', 'Requiere Mantenimiento',
        'N° de Mantenimientos', 'Modelo Vigente', 'Descripción'
    ]

    column_mapping = {
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
        'Descripción': 'descripcion'
    }

    try:
        if file_path.endswith('.xlsx'):
            # Leer archivo Excel
            df = pd.read_excel(file_path, header=0)

            # Normalizar nombres de columnas
            df.columns = df.columns.str.strip()

            # Verificar columnas faltantes
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            for col in columnas_faltantes:
                df[col] = None  # Añadir columnas faltantes con valores nulos

            # Renombrar columnas según el mapeo
            df.rename(columns=column_mapping, inplace=True)

            # Rellenar valores nulos según el tipo de columna
            for col in df.columns:
                if df[col].dtype == 'object':  # Si es una columna de texto
                    df[col].fillna("Valor no definido", inplace=True)
                else:  # Si es una columna numérica
                    df[col].fillna(0, inplace=True)

            # Convertir DataFrame a lista de diccionarios
            data = df.to_dict(orient='records')

    except Exception as e:
        print(f"Error al procesar archivo: {e}")
    return data

def validar_datos_excel(df):
    # Validación personalizada para columnas clave
    if 'Password' in df.columns:
        df['Password'] = df['Password'].apply(lambda x: x if isinstance(x, str) else "Contraseña no válida")
    return df

def descomponer_filas_combinadas(df):
    for column in df.columns:
        df[column] = df[column].ffill()  # Llenar valores combinados con el anterior
    return df

def validar_datos(datos):
    for fila in datos:
        if not isinstance(fila, dict):
            raise ValueError(f"Fila no válida (no es un diccionario): {fila}")
        # Verifica si cada valor en la fila es JSON serializable
        for key, value in fila.items():
            if not isinstance(value, (str, int, float)):
                raise ValueError(f"Valor no válido en {key}: {value}")
        # Intenta serializar toda la fila como JSON
        try:
            json.dumps(fila)
        except TypeError as e:
            raise ValueError(f"Fila no serializable como JSON: {fila} - Error: {e}")

def normalizar_datos(datos):
    datos_normalizados = []
    for fila in datos:
        fila_normalizada = {}
        for key, value in fila.items():
            if value is None:
                fila_normalizada[key] = "Valor no definido"  # Rellena nulos
            elif not isinstance(value, (str, int, float)):
                fila_normalizada[key] = str(value)  # Convierte otros tipos a cadena
            else:
                fila_normalizada[key] = value
        datos_normalizados.append(fila_normalizada)
    return datos_normalizados

def procesar_archivo_y_guardar(file_path, cliente_id, seccion_id, nombre_tabla=None):
    """
    Procesa un archivo subido y guarda los datos en una tabla asociada a una sección.
    
    Args:
        file_path (str): Ruta del archivo a procesar.
        cliente_id (int): ID del cliente asociado.
        seccion_id (int): ID de la sección asociada.
        nombre_tabla (str, opcional): Nombre personalizado para la tabla. 
                                       Por defecto, se genera un nombre automático.
    Returns:
        tabla (TablaCliente): La tabla procesada y actualizada.
    Raises:
        Exception: Si ocurre un error al procesar el archivo o guardar datos.
    """
    if not file_path:
        raise ValueError("La ruta del archivo no puede estar vacía.")

    try:
        # Procesar el archivo en formato DataFrame o similar
        datos_procesados = procesar_archivo(file_path)
        datos_procesados = normalizar_datos(datos_procesados)  # Normaliza los datos
        validar_datos(datos_procesados)  # Valida los datos

        cliente = Cliente.objects.get(id=cliente_id)

        # Generar un nombre de tabla predeterminado si no se proporciona uno
        if not nombre_tabla:
            nombre_tabla = f"Tabla procesada para Sección {seccion_id}"

        # Procesar datos para ControlActivo (sin sección asociada)
        if not seccion_id:
            # Borrar activos existentes para evitar duplicados
            ControlActivo.objects.filter(cliente=cliente).delete()

            # Crear nuevos registros
            for fila in datos_procesados:
                ControlActivo.objects.create(cliente=cliente, **fila)
            return None

        # Procesar datos para TablaCliente (si se proporciona seccion_id)
        seccion = SeccionCliente.objects.get(id=seccion_id)

        # Crear o actualizar tabla asociada
        tabla, created = TablaCliente.objects.get_or_create(
            cliente=cliente,
            seccion=seccion,
            defaults={'nombre_tabla': nombre_tabla or f"Tabla procesada para Sección {seccion_id}"}
        )

        # Borrar filas existentes si la tabla ya existía
        if not created:
            tabla.filas.all().delete()

        # Crear nuevas filas en la tabla
        filas = [FilaTabla(tabla=tabla, datos=fila) for fila in datos_procesados]
        FilaTabla.objects.bulk_create(filas)

        return tabla

    except FileNotFoundError:
        print(f"El archivo no se encontró: {file_path}")
        raise

    except Exception as e:
        print(f"Error al procesar y guardar el archivo: {e}")
        raise


