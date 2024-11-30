from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Personal

@login_required
def main_menu(request):
    usuario_actual = request.user
    
    if usuario_actual.rol == 'Supervisor':
        # Los supervisores tienen acceso completo, incluida la edición
        personales = Personal.objects.all()
        editable = True
    else:   
        # Los analistas solo tienen acceso de visualización
        personales = Personal.objects.all()
        editable = False

    return render(request, 'main_menu/main_menu.html', {
        'personales': personales,
        'usuario_actual': usuario_actual,
        'editable': editable
    })

def actualizar_personal(request, personal_id):
    # Solo permite la actualización si el usuario es Supervisor y el método es POST
    if request.method == 'POST' and request.user.rol == 'Supervisor':
        personal = get_object_or_404(Personal, id=personal_id)
        # Actualizamos los campos con los datos enviados en el formulario
        personal.nombre = request.POST.get('nombre')
        personal.turno = request.POST.get('turno')
        personal.rol = request.POST.get('rol')
        personal.save()  # Guardamos los cambios en la base de datos
        return redirect('main_menu')  # Redirige de nuevo al menú principal
    else:
        return HttpResponseForbidden("No tienes permisos para editar esta información.")

@login_required
def agregar_personal(request):
    if request.method == 'POST':
        # Solo los usuarios con rol de Supervisor pueden agregar personal
        if request.user.rol == 'Supervisor':
            # Obtener los datos del formulario
            nombre = request.POST.get('nombre')
            turno = request.POST.get('turno')
            rol = request.POST.get('rol')

            # Verificar si se cargó una imagen o usar el valor predeterminado
            if 'imagen' in request.FILES:
                imagen = request.FILES['imagen']  # Se utiliza la imagen cargada
            else:
                imagen = 'avatars/avatar.png'  # Valor predeterminado si no se cargó una imagen

            # Crear el objeto de personal
            Personal.objects.create(
                nombre=nombre,
                turno=turno,
                rol=rol,
                imagen=imagen
            )
            return redirect('main_menu')
        else:
            return HttpResponseForbidden("No tienes permisos para agregar personal.")
    else:
        # Renderizar la plantilla para agregar personal
        if request.user.rol == 'Supervisor':
            return render(request, 'main_menu/agregar_personal.html')
        else:
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
    
@login_required
def editar_personal(request, personal_id):
    personal = get_object_or_404(Personal, id=personal_id)
    if request.method == 'POST':
        personal.nombre = request.POST.get('nombre', personal.nombre)
        personal.turno = request.POST.get('turno', personal.turno)
        personal.rol = request.POST.get('rol', personal.rol)

        if 'imagen' in request.FILES:
            personal.imagen = request.FILES['imagen']
        personal.save()
        
        return JsonResponse({'status': 'success'})  # Respuesta JSON para el fetch
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def eliminar_personal(request, personal_id):
    if request.method == 'POST' and request.user.rol == 'Supervisor':
        personal = get_object_or_404(Personal, id=personal_id)
        personal.delete()
        return redirect('main_menu')
    else:
        return HttpResponseForbidden("No tienes permisos para eliminar personal.")