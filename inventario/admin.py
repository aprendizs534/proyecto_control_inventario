from django.contrib import admin
from .models import (
    Sede, Categoria, Marca, EstadoProducto, Ubicacion, RolUsuario, 
    Usuario, Producto, Movimiento, Prestamo, PrestamoConsumible,
    InventarioSede,
)

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('id', 'descripcion')
    search_fields = ('descripcion',)

@admin.register(InventarioSede)
class InventarioSedeAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'sede', 'cantidad_total', 'cantidad_disponible', 'estado')
    list_filter = ('sede', 'estado')
    search_fields = ('producto__descripcion', 'sede__descripcion')
    list_select_related = ('producto', 'sede')


admin.site.register(Categoria)
admin.site.register(Marca)
admin.site.register(EstadoProducto)
admin.site.register(Ubicacion)
admin.site.register(RolUsuario)
admin.site.register(Usuario)
admin.site.register(Producto)
admin.site.register(Movimiento)
admin.site.register(Prestamo)
admin.site.register(PrestamoConsumible)
