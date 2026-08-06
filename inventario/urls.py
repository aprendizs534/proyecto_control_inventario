from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # Página de inicio (Dashboard)
    path('', views.dashboard, name='dashboard'),

    # Botones del Dashboard
    path('asignaciones/', views.asignaciones, name='asignaciones'),
    path('herramientas/', views.herramientas, name='herramientas'),
    path('maquinas/', views.maquinas, name='maquinas'),
    path('equipos/', views.equipos, name='equipos'),
    path('materiales/', views.materiales, name='materiales'),
    path('pinturas/', views.pinturas, name='pinturas'),
    path('insumos/', views.insumos, name='insumos'),
    path('epps/', views.epps, name='epps'),
    path('dotaciones/', views.dotaciones, name='dotaciones'),
    path('aseo-cafeteria/', views.aseo_cafeteria, name='aseo_cafeteria'),

    # Menú lateral (Offcanvas)
    path('menu/entradas/', views.menu_entradas, name='menu_entradas'),
    path('menu/salidas/', views.menu_salidas, name='menu_salidas'),
    path('menu/ubicaciones/', views.ubicaciones, name='ubicaciones'),
    path('menu/estado-productos/', views.estado_productos, name='estado_productos'),
    path('menu/categorias/', views.categorias, name='categorias'),
]