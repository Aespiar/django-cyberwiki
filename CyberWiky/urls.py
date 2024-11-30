"""
URL configuration for CyberWiky project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('login.urls')),  # Incluye las URLs de la app login
    path('main_menu/', include('main_menu.urls')),
    path('clientes/', include('clientes.urls')),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('files/', include('file_management.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)