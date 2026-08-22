from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse

from .models import (
    Asignacion, AsignacionDetalle, ElementoFisico, Producto,
    InventarioSede, Usuario, EstatusElemento, EstadoAsignacion, EstadoDetalleAsignacion, Sede, Movimiento, TipoMovimiento,
)

#-----------------------------------------------------------------------------------------

def gestion_asignaciones(request):
    """Vista principal con las tres pestañas: Crear, Activas e Historial."""
    pestana_activa = request.GET.get('tab', 'activas')

    
    # 1. Asignaciones Activas
    asignaciones_activas = Asignacion.objects.filter(
        estado=EstadoAsignacion.ACTIVA
    ).select_related('responsable_recibe').prefetch_related('detalles__producto', 'detalles__elemento_fisico')

    # 2. Historial de Cierres / Devoluciones
    historial_asignaciones = Asignacion.objects.filter(
        estado=EstadoAsignacion.CERRADA
    ).select_related('responsable_recibe').order_by('-fecha_asignacion')

    # Listado de trabajadores para la cabecera
    usuarios = Usuario.objects.all()

    context = {
        'titulo': 'ASIGNACIONES',
        'pestana_activa': pestana_activa,
        'asignaciones_activas': asignaciones_activas,
        'historial_asignaciones': historial_asignaciones,
        'usuarios': usuarios,
    }
    return render(request, 'inventario/asignaciones.html', context)

def buscar_elementos_api(request):
    q = request.GET.get('q', '').strip()
    resultados = []

    if q:
        # 1. Elementos Físicos (Serializados)
        elementos = ElementoFisico.objects.filter(
            Q(serial_interno__icontains=q) | 
            Q(producto__descripcion__icontains=q) | 
            Q(producto__codigo__icontains=q)
        ).filter(
            Q(estatus__icontains='Dispon')
        )[:15]

        for elem in elementos:
            p = elem.producto
            sede = str(elem.sede_actual) if elem.sede_actual else ''
            ubi = str(elem.ubicacion) if elem.ubicacion else ''
            ubicacion_str = f"{sede} - {ubi}" if (sede and ubi) else (sede or ubi or 'N/A')
            estatus_fmt = str(elem.estatus).capitalize() if elem.estatus else 'Disponible'

            # Obtener Categoría y Marca con fallback a N/A
            cat_nombre = str(p.categoria) if getattr(p, 'categoria', None) else 'N/A'
            marca_nombre = str(p.marca) if getattr(p, 'marca', None) else 'N/A'

            resultados.append({
                'id': elem.id,
                'tipo': 'SERIALIZADO',
                'categoria': cat_nombre,
                'descripcion': p.descripcion,
                'marca': marca_nombre,
                'serial': elem.serial_interno,
                'estatus': estatus_fmt,
                'estado': estatus_fmt,
                'ubicacion': ubicacion_str,
                'max_cantidad': 1
            })

        # 2. Inventario por Sede (No Serializados / Lotes)
        inventario_lotes = InventarioSede.objects.filter(
            Q(producto__descripcion__icontains=q) | Q(producto__codigo__icontains=q),
            cantidad_disponible__gt=0
        )[:15]

        for inv in inventario_lotes:
            p = inv.producto
            sede_lote = str(inv.sede) if getattr(inv, 'sede', None) else ''
            ubi_lote = str(inv.ubicacion) if hasattr(inv, 'ubicacion') and inv.ubicacion else ''
            ubicacion_lote_str = f"{sede_lote} - {ubi_lote}" if (sede_lote and ubi_lote) else (sede_lote or ubi_lote or 'N/A')

            cat_nombre = str(p.categoria) if getattr(p, 'categoria', None) else 'N/A'
            marca_nombre = str(p.marca) if getattr(p, 'marca', None) else 'N/A'

            resultados.append({
                'id': inv.id,
                'tipo': 'LOTE',
                'categoria': cat_nombre,
                'descripcion': p.descripcion,
                'marca': marca_nombre,
                'serial': 'N/A (Lote)',
                'estatus': 'Disponible',
                'estado': 'Disponible',
                'ubicacion': ubicacion_lote_str,
                'max_cantidad': inv.cantidad_disponible
            })

    return JsonResponse({'resultados': resultados})

@transaction.atomic
def guardar_asignacion(request):
    """Procesa el guardado del acta de asignación completa."""
    if request.method == 'POST':
        usuario_recibe_id = request.POST.get('responsable_recibe')
        usuario_entrega = getattr(request.user, 'usuario_profile', None)
        
        elementos_fisicos_ids = request.POST.getlist('elementos_fisicos_ids[]')
        productos_ids = request.POST.getlist('productos_ids[]')
        cantidades = request.POST.getlist('cantidades[]')

        if not usuario_recibe_id or not productos_ids:
            messages.error(request, "Debe seleccionar un responsable y al menos un ítem para asignar.")
            return redirect('inventario:gestion_asignaciones')

        usuario_recibe = get_object_or_404(Usuario, id=usuario_recibe_id)

        # Crear Cabecera
        asignacion = Asignacion.objects.create(
            responsable_recibe=usuario_recibe,
            responsable_entrega=usuario_entrega,
            sede=getattr(usuario_recibe, 'sede', Sede.objects.first()),
            estado=EstadoAsignacion.ACTIVA
        )

        # Crear Detalle y Actualizar Inventario
        for i in range(len(productos_ids)):
            prod_id = productos_ids[i]
            elem_id = elementos_fisicos_ids[i] if i < len(elementos_fisicos_ids) and elementos_fisicos_ids[i] != '' else None
            cantidad = int(cantidades[i]) if i < len(cantidades) else 1

            producto = get_object_or_404(Producto, id=prod_id)
            elemento_fisico = get_object_or_404(ElementoFisico, id=elem_id) if elem_id else None

            AsignacionDetalle.objects.create(
                asignacion=asignacion,
                producto=producto,
                elemento_fisico=elemento_fisico,
                cantidad=cantidad,
                estado_devolucion=EstadoDetalleAsignacion.PENDIENTE
            )

            # Actualizar estado según tipo de producto
            if elemento_fisico:
                elemento_fisico.estatus = EstatusElemento.ASIGNADO
                elemento_fisico.save()
            else:
                inv_sede = InventarioSede.objects.get(producto=producto, sede=asignacion.sede)
                inv_sede.cantidad_disponible -= cantidad
                inv_sede.save()

        messages.success(request, f"Asignación #{asignacion.id} registrada a {usuario_recibe.descripcion}.")
        return redirect('inventario:gestion_asignaciones')

#------------------------------------------------------------------------------------------


# Dashboard 

@login_required  
def dashboard(request):
    return render(request, 'dashboard.html')


#  Registrar Entrada 

from .forms import EntradaInventarioForm

@login_required
def registrar_entrada(request):
    
    if request.method == 'POST':
        form = EntradaInventarioForm(request.POST)

        if form.is_valid():
            # cleaned_data ya contiene los objetos Django, no IDs crudos
            # Django hizo todos los get_object_or_404 internamente
            producto   = form.cleaned_data['producto']
            sede       = form.cleaned_data['sede']
            cantidad   = form.cleaned_data['cantidad']
            estado     = form.cleaned_data['estado']
            ubicacion  = form.cleaned_data['ubicacion']
            observaciones = form.cleaned_data['observaciones']

            try:
                perfil_usuario = request.user.perfil_inventario
            except Usuario.DoesNotExist:
                messages.error(
                    request,
                    "Tu cuenta no tiene un perfil de inventario asignado. "
                    "Contacta al administrador."
                )
                return render(request, 'inventario/registrar_entrada.html', {'form': form})

            try:
                with transaction.atomic():
                    inventario_sede, _ = InventarioSede.objects.get_or_create(
                        producto=producto,
                        sede=sede,
                        defaults={
                            'cantidad_total': 0,
                            'cantidad_disponible': 0,
                            'estado': estado,
                            'ubicacion': ubicacion,
                        }
                    )
                    inventario_sede.aplicar_entrada(cantidad, estado, ubicacion)

                    Movimiento.objects.create(
                        producto=producto,
                        sede=sede,
                        tipo_movimiento=TipoMovimiento.ENTRADA,
                        cantidad=cantidad,
                        usuario=perfil_usuario,
                        usuario_almacen=perfil_usuario,
                        observaciones=observaciones,
                    )

            except Exception:
                messages.error(request, "Error al registrar la entrada. Intenta de nuevo.")
                return render(request, 'inventario/registrar_entrada.html', {'form': form})

            messages.success(
                request,
                f"Entrada de {cantidad} unidad(es) registrada para "
                f"'{producto.descripcion}' en {sede.descripcion}."
            )
            return redirect('inventario:registrar_entrada')

    else:
        # GET: formulario vacío
        form = EntradaInventarioForm()

    return render(request, 'inventario/registrar_entrada.html', {'form': form})


#  Vistas stub del Dashboard 

#@login_required
#def asignaciones(request):
#    return render(request, 'inventario/base_subpage.html', {'titulo': 'Asignaciones'})

@login_required
def herramientas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Herramientas'})

@login_required
def maquinas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Máquinas'})

@login_required
def equipos(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Equipos'})

@login_required
def materiales(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Materiales'})

@login_required
def pinturas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Pinturas'})

@login_required
def insumos(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Insumos'})

@login_required
def epps(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'EPPs'})

@login_required
def dotaciones(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Dotaciones'})

@login_required
def aseo_cafeteria(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Aseo y Cafetería'})


# Vistas stub del Menú Lateral 

@login_required
def menu_entradas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Entradas'})

@login_required
def menu_salidas(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Salidas'})

@login_required
def ubicaciones(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Ubicaciones'})

@login_required
def estado_productos(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Estado de Productos'})

@login_required
def categorias(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Categorías'})

