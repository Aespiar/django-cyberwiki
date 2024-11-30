from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_clientes, name='lista_clientes'),
    path('<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('control_activos/', views.control_activos, name='control_activos'),
    path('<int:cliente_id>/seccion/<int:seccion_id>/', views.detalle_seccion, name='detalle_seccion'),
    path('<int:cliente_id>/agregar_seccion/', views.agregar_seccion, name='agregar_seccion'),
    path('clientes/<int:cliente_id>/secciones/agregar/', views.agregar_seccion, name='agregar_seccion'),
    path('<int:cliente_id>/secciones/', views.obtener_secciones, name='obtener_secciones'),
    path('clientes/<int:cliente_id>/secciones/<int:seccion_id>/editar/', views.editar_seccion, name='editar_seccion'),
    path('eliminar-fila/', views.eliminar_fila, name='eliminar_fila'),
    path('guardar-tabla/', views.guardar_tabla, name='guardar_tabla'),
    path("cargar-excel/", views.cargar_excel, name="cargar_excel"),
    path("filtrar-activos/", views.filtrar_activos, name="filtrar_activos"),
    path('exportar-excel/<int:tabla_id>/', views.exportar_excel, name='exportar_excel'),
    path('exportar-pdf/<int:tabla_id>/', views.exportar_pdf, name='exportar_pdf'),
    path('clientes/<int:cliente_id>/seccion/<int:seccion_id>/historial/', views.historial_seccion, name='historial_seccion'),
    path('clientes/<int:cliente_id>/seccion/<int:seccion_id>/historial/<int:historial_id>/restaurar/',views.restaurar_seccion, name='restaurar_seccion'),
]