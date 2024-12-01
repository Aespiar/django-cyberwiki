from django.urls import path
from . import views

urlpatterns = [
    # Clientes
    path('', views.lista_clientes, name='lista_clientes'),
    path('agregar/', views.agregar_cliente, name='agregar_cliente'),
    path('<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),

    # Control de activos
    path('control_activos/', views.control_activos, name='control_activos'),
    path('cargar_excel/', views.cargar_excel, name='cargar_excel'),
    path('filtrar_activos/', views.filtrar_activos, name='filtrar_activos'),
    path('control_activos/eliminar/<int:activo_id>/', views.eliminar_activo, name='eliminar_activo'),
    path("control_activos/agregar/", views.agregar_activo, name="agregar_activo"),
    path('control_activos/editar/<int:activo_id>/', views.editar_activo, name='editar_activo'),
    path('procesar_archivo_control_activo/', views.procesar_archivo_control_activo, name='procesar_archivo_control_activo'),

    # Secciones del cliente
    path('<int:cliente_id>/agregar_seccion/', views.agregar_seccion, name='agregar_seccion'),
    path('<int:cliente_id>/secciones/<int:seccion_id>/editar/', views.editar_seccion, name='editar_seccion'),
    path('<int:cliente_id>/secciones/<int:seccion_id>/eliminar/', views.eliminar_seccion, name='eliminar_seccion'),

    # Detalle de secciones
    path('<int:cliente_id>/seccion/<int:seccion_id>/', views.detalle_seccion, name='detalle_seccion'),
    path('<int:cliente_id>/seccion/<int:seccion_id>/historial/', views.historial_seccion, name='historial_seccion'),

    # Exportación
    path('exportar-excel/<int:tabla_id>/', views.exportar_excel, name='exportar_excel'),
    path('exportar-pdf/<int:tabla_id>/', views.exportar_pdf, name='exportar_pdf'),

    # Tablas relacionadas con las secciones
    path('guardar-tabla/', views.guardar_tabla, name='guardar_tabla'),
    path('eliminar-fila/', views.eliminar_fila, name='eliminar_fila'),
    path('editar-fila/<int:fila_id>/', views.editar_fila, name='editar_fila'),
]