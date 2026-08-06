from django.shortcuts import render

# Create your views here.
def dashboard(request):
    return render(request, 'dashboard.html')


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