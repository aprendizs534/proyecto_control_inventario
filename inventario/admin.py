from django.contrib import admin
from .models import (
    Categoria, Marca, EstadoProducto, Ubicacion, RolUsuario,
    Usuario, Producto, Movimiento, Prestamo, PrestamoConsumible
)

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
