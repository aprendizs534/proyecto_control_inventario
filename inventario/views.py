from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .models import (
    Producto, Sede, InventarioSede, Movimiento,
    EstadoProducto, Ubicacion, TipoMovimiento, Usuario,
)


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

@login_required
def asignaciones(request):
    return render(request, 'inventario/base_subpage.html', {'titulo': 'Asignaciones'})

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