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

"""Estado operativo de una unidad física individual."""
class EstatusElemento(models.TextChoices):
    DISPONIBLE = 'DISPONIBLE', 'Disponible en Almacén'
    ASIGNADO = 'ASIGNADO', 'Asignado a Trabajador/Montaje'
    MANTENIMIENTO = 'MANTENIMIENTO', 'En Mantenimiento'
    DADO_DE_BAJA = 'DADO_DE_BAJA', 'Dado de Baja / Perdido'

#Eliminado Estado prestamo
#Se agrega un nuevo estado

"""Estado global del acta de asignación."""
class EstadoAsignacion(models.TextChoices):
    ACTIVA = 'ACTIVA', 'Activa'
    CERRADA = 'CERRADA', 'Cerrada / Completada'

#Eliminado Estado consumible
#Se agrega un nuevo estado

"""Estado de cada ítem individual entregado en la asignación."""
class EstadoDetalleAsignacion(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente de Devolución'
    DEVUELTO = 'DEVUELTO', 'Devuelto a Almacén'
    DADO_DE_BAJA = 'DADO_DE_BAJA', 'Perdido / Dañado'
    CONSUMIDO = 'CONSUMIDO', 'Consumido (Material/Aseo)'

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
    tipo_producto = models.CharField(
        max_length=20, choices=TipoProducto.choices,
        default=TipoProducto.NA, blank=True
    )

    es_serializado = models.BooleanField(
        default=False,
        help_text="Marcar si requiere control de serial individual (Ej: Equipos y Máquinas)"
    )
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

# ElementoFísico

"""Unidad física individual y rastreable de un producto serializado (Ej: La pulidora PU-08-223)"""

class ElementoFisico(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='elementos_fisicos'
    )
    serial_interno = models.CharField(
        max_length=50, unique=True,
        help_text="Serial o Código interno (Ej: PU-08-223)"
    )
    sede_actual = models.ForeignKey(
        Sede, on_delete=models.PROTECT, related_name='elementos_sede'
    )
    ubicacion = models.ForeignKey(
        Ubicacion, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='elementos_ubicacion'
    )
    estado_fisico = models.ForeignKey(
        EstadoProducto, on_delete=models.PROTECT, related_name='elementos_estados'
    )
    estatus = models.CharField(
        max_length=20, choices=EstatusElemento.choices, default=EstatusElemento.DISPONIBLE
    )
    fecha_ingreso = models.DateField(auto_now_add=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.producto.descripcion} - {self.serial_interno} ({self.get_estatus_display()})"


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


"""Incrementa las existencias totales y disponibles.

        Delega la operación matemática a la base de datos utilizando expresiones F()
        para mitigar de manera absoluta condiciones de carrera concurrentes.

        Args:
            cantidad (int): Volumen físico de artículos que ingresan.
            estado (EstadoProducto): Instancia del estado físico actual del lote.
            ubicacion (Ubicacion, opcional): Posición en estante asignada. Defaults to None.
        """


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
#Eliminado
#  PrestamoConsumible 
#Eliminado

#  Módulo de Asignaciones 

"""Cabecera: Acta que agrupa la entrega de varias herramientas o equipos a un operario."""
class Asignacion(models.Model):
    responsable_recibe = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name='asignaciones_recibidas'
    )
    responsable_entrega = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name='asignaciones_entregadas'
    )
    sede = models.ForeignKey(
        Sede, on_delete=models.PROTECT, related_name='asignaciones'
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, choices=EstadoAsignacion.choices, default=EstadoAsignacion.ACTIVA
    )
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Asignación #{self.id} - {self.responsable_recibe.descripcion} ({self.get_estado_display()})"


"""Detalle: Cada línea dentro del acta (Ej: 1 Pulidora Serial X, 2 Macetas sin serial)."""
class AsignacionDetalle(models.Model):
    asignacion = models.ForeignKey(
        Asignacion, on_delete=models.CASCADE, related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='detalles_asignacion'
    )
    elemento_fisico = models.ForeignKey(
        ElementoFisico, on_delete=models.PROTECT, null=True, blank=True,
        related_name='historial_asignaciones',
        help_text="Obligatorio solo si el producto es serializado (equipos, máquinas, etc.)"
    )
    cantidad = models.IntegerField(default=1)
    cantidad_devuelta = models.IntegerField(default=0)
    estado_devolucion = models.CharField(
        max_length=20, choices=EstadoDetalleAsignacion.choices, default=EstadoDetalleAsignacion.PENDIENTE
    )
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.elemento_fisico:
            return f"{self.cantidad}x {self.producto.descripcion} (Serial: {self.elemento_fisico.serial_interno})"
        return f"{self.cantidad}x {self.producto.descripcion}"
    