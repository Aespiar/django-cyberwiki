from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('list/', views.archivo_list, name='archivo_list'),  # Nueva URL para la lista de archivos
]