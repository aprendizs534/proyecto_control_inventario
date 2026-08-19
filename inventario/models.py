from django.db import models, transaction
from django.db.models import F
from django.contrib.auth.models import User

"""Opciones de rol de acceso y permisos dentro de la aplicación."""
class TipoUsuario(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrador'
    ALMACEN = 'ALMACEN', 'Almacenista'
    USUARIO = 'USUARIO', 'Usuario normal'

"""Clasificación física y operativa de los elementos en el inventario."""
class TipoProducto(models.TextChoices):
    EQUIPO = 'EQUIPO', 'Equipo'
    CONSUMIBLE = 'CONSUMIBLE', 'Consumible'
    HERRAMIENTA = 'HERRAMIENTA', 'Herramienta'
    MATERIALES = 'MATERIALES', 'Materiales'
    NA = 'N/A', 'N/A'

"""Naturaleza de la transacción física del inventario."""
class TipoMovimiento(models.TextChoices):
    ENTRADA = 'ENTRADA', 'Entrada'
    SALIDA = 'SALIDA', 'Salida'
    AJUSTE = 'AJUSTE', 'Ajuste'

"""Ciclo de vida operativo de un préstamo de equipo o herramienta."""
class EstadoPrestamo(models.TextChoices):
    ACTIVO = 'ACTIVO', 'Activo'
    DEVUELTO = 'DEVUELTO', 'Devuelto'
    VENCIDO = 'VENCIDO', 'Vencido'
    CANCELADO = 'CANCELADO', 'Cancelado'

"""Rastreo del destino o estado de materiales consumibles entregados."""
class EstadoConsumible(models.TextChoices):
    ENTREGADO = 'ENTREGADO', 'Entregado'
    DEVUELTO = 'DEVUELTO', 'Devuelto'
    PERDIDO = 'PERDIDO', 'Perdido'


#  Catálogos 
"""Catálogo de ubicaciones físicas o almacenes de la organización."""
class Sede(models.Model):
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

"""Estructura jerárquica (árbol) para clasificar los productos.
    Permite subcategorías apuntando a sí misma mediante 'categoria_padre'."""
class Categoria(models.Model):
    descripcion = models.CharField(max_length=50)
    categoria_padre = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='subcategorias'
    )

    def __str__(self):
        return self.descripcion

"""Catálogo de marcas de los artículos."""
class Marca(models.Model):
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

"""Define condiciones físicas del stock (ej: bueno, regular, malo)."""
class EstadoProducto(models.Model):
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

"""Espacio específico dentro de un almacén/sede."""
class Ubicacion(models.Model):
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

"""Roles de negocio internos complementarios a la autenticación estándar."""
class RolUsuario(models.Model):
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion


#  Usuario 
"""Perfil extendido que asocia el usuario de Django con la lógica del inventario."""
class Usuario(models.Model):
    descripcion = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    rol = models.ForeignKey(RolUsuario, on_delete=models.PROTECT, related_name='usuarios')
    tipo_usuario = models.CharField(
        max_length=20, choices=TipoUsuario.choices, default=TipoUsuario.USUARIO
    )
    fecha_registro = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    sede_por_defecto = models.ForeignKey(
        Sede, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='usuarios_sede'
    )
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='perfil_inventario'
    )

    def __str__(self):
        return self.descripcion


# Producto 
"""Ficha maestra de un artículo identificable en el catálogo global."""
class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name='productos')
    serial_ingemol = models.CharField(max_length=50, blank=True, null=True)
    tipo_producto = models.CharField(
        max_length=20, choices=TipoProducto.choices,
        default=TipoProducto.NA, blank=True
    )
    responsable = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='productos_responsable'
    )
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


#  InventarioSede 
""" Matriz de existencias físicas que consolida el stock por combinación Sede-Producto."""
class InventarioSede(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='inventarios_sede'
    )
    sede = models.ForeignKey(
        Sede, on_delete=models.PROTECT, related_name='inventarios_productos'
    )
    cantidad_total = models.IntegerField(default=0)
    cantidad_disponible = models.IntegerField(default=0)
    cantidad_prestada = models.IntegerField(default=0)
    estado = models.ForeignKey(
        EstadoProducto, on_delete=models.PROTECT, related_name='stock_estado'
    )
    ubicacion = models.ForeignKey(
        Ubicacion, on_delete=models.PROTECT, null=True, blank=True,
        related_name='stock_ubicacion'
    )

    class Meta:
        unique_together = ('producto', 'sede')

    def __str__(self):
        return (
            f"{self.producto.descripcion} - {self.sede.descripcion} "
            f"(Disp: {self.cantidad_disponible})"
        )

    # lógica de negocio en el modelo 
"""Incrementa las existencias totales y disponibles.

        Delega la operación matemática a la base de datos utilizando expresiones F()
        para mitigar de manera absoluta condiciones de carrera concurrentes.

        Args:
            cantidad (int): Volumen físico de artículos que ingresan.
            estado (EstadoProducto): Instancia del estado físico actual del lote.
            ubicacion (Ubicacion, opcional): Posición en estante asignada. Defaults to None.
        """

@transaction.atomic
def aplicar_entrada(self, cantidad: int, estado, ubicacion=None):
        self.estado = estado
        if ubicacion:
            self.ubicacion = ubicacion

        # F() delega la suma a la base de datos: seguro ante condiciones de carrera
        InventarioSede.objects.filter(pk=self.pk).update(
            cantidad_total=F('cantidad_total') + cantidad,
            cantidad_disponible=F('cantidad_disponible') + cantidad,
        )
        # Sincronizamos el estado y la ubicación por separado
        self.save(update_fields=['estado', 'ubicacion'])


#  Movimiento 
""" Kárdex / Historial de transacciones de inventario para fines de auditoría."""
class Movimiento(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='movimientos'
    )
    sede = models.ForeignKey(
        Sede, on_delete=models.PROTECT, related_name='movimientos_sede'
    )
    tipo_movimiento = models.CharField(max_length=20, choices=TipoMovimiento.choices)
    cantidad = models.IntegerField()
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name='movimientos_usuario'
    )
    usuario_almacen = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name='movimientos_almacen'
    )
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return (
            f"{self.tipo_movimiento} - {self.producto.codigo} "
            f"- {self.cantidad} - {self.sede.descripcion}"
        )


#  Prestamo 
""" Control operativo de préstamos temporales de activos no consumibles."""
class Prestamo(models.Model):
    movimiento = models.ForeignKey(
        Movimiento, on_delete=models.PROTECT, related_name='prestamos',
        null=True, blank=True
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='prestamos'
    )
    sede = models.ForeignKey(
        Sede, on_delete=models.PROTECT, related_name='prestamos_sede'
    )
    usuario_prestamo = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name='prestamos_solicitados'
    )
    fecha_prestamo = models.DateTimeField(auto_now_add=True)
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    cantidad_prestada = models.IntegerField()
    cantidad_devuelta = models.IntegerField(default=0)
    estado_prestamo = models.CharField(
        max_length=20, choices=EstadoPrestamo.choices, default=EstadoPrestamo.ACTIVO
    )
    responsable_entrega = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name='prestamos_entregados'
    )
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Préstamo #{self.id} - {self.producto.codigo}"


#  PrestamoConsumible 
""" Seguimiento de entrega y gasto de materiales consumibles desechables."""
class PrestamoConsumible(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='prestamos_consumibles'
    )
    sede = models.ForeignKey(
        Sede, on_delete=models.PROTECT, related_name='consumibles_prestados_sede'
    )
    usuario_prestamo = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name='consumibles_prestados'
    )
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    cantidad = models.IntegerField()
    estado = models.CharField(
        max_length=20, choices=EstadoConsumible.choices,
        default=EstadoConsumible.ENTREGADO
    )
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Consumible #{self.id} - {self.producto.codigo}"