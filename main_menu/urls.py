from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_menu, name='main_menu'),  # URL para la página principal
    path('actualizar_personal/<int:personal_id>/', views.actualizar_personal, name='actualizar_personal'),  # URL para editar
    path('agregar_personal/', views.agregar_personal, name='agregar_personal'),
    path('editar_personal/<int:personal_id>/', views.editar_personal, name='editar_personal'),
    path('eliminar_personal/<int:personal_id>/', views.eliminar_personal, name='eliminar_personal'),
]