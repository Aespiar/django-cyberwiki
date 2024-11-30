from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        print("Formulario enviado")  # Verifica si el formulario se envía correctamente
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('main_menu')  # Redirigir al menú principal
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'login/login.html')  # Redirige / Muestra la interfaz de login