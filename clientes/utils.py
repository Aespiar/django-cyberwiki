import pdfplumber
import pandas as pd
import json
from .models import Cliente, TablaCliente, FilaTabla, SeccionCliente


def procesar_archivo(file_path):
    data = []
    try:
        if file_path.endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        headers = table[0]  # Primera fila como encabezados
                        rows = table[1:]    # Las siguientes filas son datos
                        for row in rows:
                            data.append(dict(zip(headers, row)))
        elif file_path.endswith('.xlsx'):
            # Leer archivo Excel
            df = pd.read_excel(file_path, header=0)  # Primera fila como cabecera
            
            # Descomponer filas combinadas (función personalizada)
            df = descomponer_filas_combinadas(df)
            
            # Eliminar columnas con nombres no definidos ('Unnamed')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            # Renombrar columnas 'Unnamed' o sin nombre con nombres genéricos
            df.columns = [
                f"Columna_{i}" if "Unnamed" in str(col) else col
                for i, col in enumerate(df.columns)
            ]

            # Rellenar valores nulos con un texto genérico
            df.fillna("Valor no definido", inplace=True)
            
            # Convertir el DataFrame a una lista de diccionarios
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
        seccion = SeccionCliente.objects.get(id=seccion_id)

        # Generar un nombre de tabla predeterminado si no se proporciona uno
        if not nombre_tabla:
            nombre_tabla = f"Tabla procesada para Sección {seccion_id}"

        # Obtener o crear la tabla asociada
        tabla, created = TablaCliente.objects.get_or_create(
            cliente=cliente,
            seccion=seccion,
            defaults={'nombre_tabla': nombre_tabla}
        )

        # Limpiar las filas existentes si la tabla ya existía
        if not created:
            tabla.filas.all().delete()

        # Guardar las nuevas filas en la tabla
        filas = [FilaTabla(tabla=tabla, datos=fila) for fila in datos_procesados]
        FilaTabla.objects.bulk_create(filas)

        return tabla

    except FileNotFoundError:
        print(f"El archivo no se encontró: {file_path}")
        raise

    except Exception as e:
        print(f"Error al procesar y guardar el archivo: {e}")
        raise


