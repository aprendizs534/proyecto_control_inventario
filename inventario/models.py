from django.db import models
from django.contrib.auth.models import User

# Opciones para campos ENUM
class TipoUsuario(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrador'
    ALMACEN = 'ALMACEN', 'Almacenista'
    USUARIO = 'USUARIO', 'Usuario normal'

class TipoProducto(models.TextChoices):
    EQUIPO = 'EQUIPO', 'Equipo'
    CONSUMIBLE = 'CONSUMIBLE', 'Consumible'
    HERRAMIENTA = 'HERRAMIENTA', 'Herramienta'

class TipoMovimiento(models.TextChoices):
    ENTRADA = 'ENTRADA', 'Entrada'
    SALIDA = 'SALIDA', 'Salida'
    AJUSTE = 'AJUSTE', 'Ajuste'

class EstadoPrestamo(models.TextChoices):
    ACTIVO = 'ACTIVO', 'Activo'
    DEVUELTO = 'DEVUELTO', 'Devuelto'
    VENCIDO = 'VENCIDO', 'Vencido'
    CANCELADO = 'CANCELADO', 'Cancelado'

class EstadoConsumible(models.TextChoices):
    ENTREGADO = 'ENTREGADO', 'Entregado'
    DEVUELTO = 'DEVUELTO', 'Devuelto'
    PERDIDO = 'PERDIDO', 'Perdido'


# --- MODELOS AUXILIARES (Catálogos) ---
class Sede(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)  # Ej: Bogotá, Cartagena, Rio Claro

    def __str__(self):
        return self.descripcion

class Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)
    categoria_padre = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategorias'
    )

    def __str__(self):
        return self.descripcion

class Marca(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

class EstadoProducto(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

class Ubicacion(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

class RolUsuario(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion


# --- MODELO DE USUARIO ---
class Usuario(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100)  # Nombre o descripción
    telefono = models.CharField(max_length=20, blank=True, null=True)
    rol = models.ForeignKey(RolUsuario, on_delete=models.PROTECT, related_name='usuarios')
    tipo_usuario = models.CharField(max_length=20, choices=TipoUsuario.choices, default=TipoUsuario.USUARIO)
    fecha_registro = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    # NUEVO: Asignamos una sede por defecto al usuario (opcional)
    sede_por_defecto = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios_sede')

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='perfil_inventario')

    def __str__(self):
        return self.descripcion


# --- MODELO DE PRODUCTO ---
class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name='productos')
    serial_ingemol = models.CharField(max_length=50, blank=True, null=True)
    tipo_producto = models.CharField(max_length=20, choices=TipoProducto.choices, default=TipoProducto.EQUIPO)
    
    # Responsable general (quien tiene la custodia)
    responsable = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_responsable')
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


# --- NUEVO: INVENTARIO POR SEDE ---
class InventarioSede(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios_sede')
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name='inventarios_productos')
    
    cantidad_total = models.IntegerField(default=0)
    cantidad_disponible = models.IntegerField(default=0)
    cantidad_prestada = models.IntegerField(default=0)
    
    # El estado y la ubicación ahora dependen de la sede y el producto
    estado = models.ForeignKey(EstadoProducto, on_delete=models.PROTECT, related_name='stock_estado')
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, null=True, blank=True, related_name='stock_ubicacion')

    class Meta:
        # Garantiza que no existan dos registros del mismo producto en la misma sede
        unique_together = ('producto', 'sede')

    def __str__(self):
        return f"{self.producto.descripcion} - {self.sede.descripcion} (Disp: {self.cantidad_disponible})"


# --- MODELO DE MOVIMIENTO ---
class Movimiento(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name='movimientos_sede')  # Agregado: De qué sede fue el movimiento
    
    tipo_movimiento = models.CharField(max_length=20, choices=TipoMovimiento.choices)
    cantidad = models.IntegerField()
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='movimientos_usuario')
    usuario_almacen = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='movimientos_almacen')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.producto.codigo} - {self.cantidad} - {self.sede.descripcion}"


# --- MODELO DE PRÉSTAMO ---
class Prestamo(models.Model):
    id = models.AutoField(primary_key=True)
    movimiento = models.ForeignKey(Movimiento, on_delete=models.PROTECT, related_name='prestamos', null=True, blank=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='prestamos')
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name='prestamos_sede')  # Agregado: De qué sede salió
    
    usuario_prestamo = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='prestamos_solicitados')
    fecha_prestamo = models.DateTimeField(auto_now_add=True)
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    cantidad_prestada = models.IntegerField()
    cantidad_devuelta = models.IntegerField(default=0)
    estado_prestamo = models.CharField(max_length=20, choices=EstadoPrestamo.choices, default=EstadoPrestamo.ACTIVO)
    responsable_entrega = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='prestamos_entregados')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Préstamo #{self.id} - {self.producto.codigo}"


# --- MODELO DE PRÉSTAMO CONSUMIBLE ---
class PrestamoConsumible(models.Model):
    id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='prestamos_consumibles')
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name='consumibles_prestados_sede')  # Agregado
    
    usuario_prestamo = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='consumibles_prestados')
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    cantidad = models.IntegerField()
    estado = models.CharField(max_length=20, choices=EstadoConsumible.choices, default=EstadoConsumible.ENTREGADO)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Consumible #{self.id} - {self.producto.codigo}"