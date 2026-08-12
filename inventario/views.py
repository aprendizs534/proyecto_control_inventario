from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Producto, Sede, InventarioSede, Movimiento, EstadoProducto, Ubicacion, TipoMovimiento, Usuario, RolUsuario;
from django.contrib.auth.decorators import login_required


# Create your views here.
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def registrar_entrada(request):
    productos = Producto.objects.filter(activo=True)
    sedes = Sede.objects.all()
    estados = EstadoProducto.objects.all()
    ubicaciones = Ubicacion.objects.all()

    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        sede_id = request.POST.get('sede')
        cantidad = int(request.POST.get('cantidad', 0))
        estado_id = request.POST.get('estado')
        ubicacion_id = request.POST.get('ubicacion')
        observaciones = request.POST.get('observaciones', '')
    
        if cantidad <= 0:
            messages.error(request, "La cantidad debe ser mayor a 0.")
            return redirect('inventario:registrar_entrada')

        producto = get_object_or_404(Producto, id=producto_id)
        sede = get_object_or_404(Sede, id=sede_id)
        estado = get_object_or_404(EstadoProducto, id=estado_id)
        ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id) if ubicacion_id else None

        # 1. Lógica del inventario por sede
        inventario_sede, created = InventarioSede.objects.get_or_create(
            producto=producto,
            sede=sede,
            defaults={
                'estado': estado,
                'ubicacion': ubicacion
            }
        )
         # Si ya existía, actualizamos los campos y sumamos la cantidad
        if not created:
            inventario_sede.estado = estado
            if ubicacion:
                inventario_sede.ubicacion = ubicacion
            inventario_sede.cantidad_total += cantidad
            inventario_sede.cantidad_disponible += cantidad
        else:
            # Si es nuevo, asignamos la cantidad inicial
            inventario_sede.cantidad_total = cantidad
            inventario_sede.cantidad_disponible = cantidad

        inventario_sede.save()
    try:
        perfil_usuario = request.user.perfil_inventario
    except Usuario.DoesNotExist:
        perfil_usuario = Usuario.objects.create(
                descripcion=request.user.username,
                user=request.user,
                rol=RolUsuario.objects.first()  # Le asignamos el primer rol disponible de la tabla
            )


        # 2. Crear el registro de Movimiento
        Movimiento.objects.create(
            producto=producto,
            sede=sede,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=cantidad,
            usuario=perfil_usuario, # <-- Esto asume que el usuario está logueado y tiene un perfil Usuario
            usuario_almacen=perfil_usuario, # <-- Por simplicidad usamos el mismo
            observaciones=observaciones
        )

        messages.success(request, f"Entrada registrada exitosamente para {producto.descripcion} en {sede.descripcion}.")
        return redirect('inventario:registrar_entrada')

    context = {
        'productos': productos,
        'sedes': sedes,
        'estados': estados,
        'ubicaciones': ubicaciones,
    }
    return render(request, 'inventario/registrar_entrada.html', context)

#-----------------------------------------------------------------------------------------------------------

# --- Vistas para los botones del Dashboard ---
def asignaciones(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Asignaciones'})

def herramientas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Herramientas'})

def maquinas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Máquinas'})

def equipos(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Equipos'})

def materiales(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Materiales'})

def pinturas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Pinturas'})

def insumos(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Insumos'})

def epps(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'EPPs'})

def dotaciones(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Dotaciones'})

def aseo_cafeteria(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Aseo y Cafetería'})

# --- Vistas para el Menú Lateral ---
def menu_entradas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Entradas'})

def menu_salidas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Salidas'})

def ubicaciones(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Ubicaciones'})

def estado_productos(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Estado de Productos'})

def categorias(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Categorías'})

