document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Auto-completar datos del operario seleccionado
    const selectResponsable = document.getElementById('select-responsable');
    if (selectResponsable) {
        selectResponsable.addEventListener('change', function() {
            let opt = this.options[this.selectedIndex];
            document.getElementById('info-cedula').value = opt.getAttribute('data-cedula') || '';
            document.getElementById('info-cargo').value = opt.getAttribute('data-cargo') || '';
            document.getElementById('info-ubicacion').value = opt.getAttribute('data-ubicacion') || '';
        });
    }

    // 2. Búsqueda de elementos vía AJAX en el Modal
    const btnBusqueda = document.getElementById('btn-ejecutar-busqueda');
    if (btnBusqueda) {
        btnBusqueda.addEventListener('click', function() {
            let input = document.getElementById('input-modal-busqueda');
            let q = input ? input.value.trim() : '';
            
            fetch(`/asignaciones/api/buscar/?q=${encodeURIComponent(q)}`)
                .then(res => res.json())
                .then(data => {
                    let tbody = document.getElementById('resultados-busqueda-modal');
                    tbody.innerHTML = '';
                    
                    if (!data.resultados || data.resultados.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No se encontraron elementos disponibles.</td></tr>';
                        return;
                    }
                    
                    data.resultados.forEach((item, index) => {
                        // Mapeo seguro de atributos según la API de Django
                        let itemNormalizado = {
                            id_producto: item.id_producto || item.id,
                            id_elemento: item.id_elemento || (item.tipo === 'SERIALIZADO' ? item.id : ''),
                            tipo: item.tipo || 'GENERAL',
                            es_serializado: item.es_serializado || (item.tipo === 'SERIALIZADO'),
                            categoria: item.categoria || 'N/A',
                            descripcion: item.descripcion || 'Sin descripción',
                            marca: item.marca || 'N/A',
                            serial: item.serial || 'N/A (Lote)',
                            estado: item.estado || item.estatus || 'Disponible',
                            ubicacion: item.ubicacion || 'N/A',
                            max_cantidad: item.max_cantidad || 1
                        };

                        let itemJson = JSON.stringify(itemNormalizado).replace(/'/g, "&apos;");
                        
                        // Generación estricta de las 8 columnas del <thead>
                        let row = `<tr>
                            <td>${index + 1}</td>
                            <td>${itemNormalizado.categoria}</td>
                            <td>${itemNormalizado.descripcion}</td>
                            <td>${itemNormalizado.marca}</td>
                            <td><strong>${itemNormalizado.serial}</strong></td>
                            <td><span class="badge bg-secondary">${itemNormalizado.estado}</span></td>
                            <td>${itemNormalizado.ubicacion}</td>
                            <td>
                                <button type="button" class="btn btn-sm btn-success fw-bold" onclick='agregarItemTabla(${itemJson})'>
                                    + ASIGNAR
                                </button>
                            </td>
                        </tr>`;
                        tbody.innerHTML += row;
                    });
                })
                .catch(err => console.error("Error consultando la API:", err));
        });
    }
});

// 3. Función global para agregar ítems a la tabla principal de asignación
let contadorItems = 0;

function agregarItemTabla(item) {
    contadorItems++;
    let tbody = document.getElementById('body-tabla-asignacion');
    if (!tbody) return;

    let row = document.createElement('tr');
    row.id = `item-row-${contadorItems}`;

    row.innerHTML = `
        <td>${contadorItems}</td>
        <td>${item.categoria}</td>
        <td>
            ${item.descripcion}
            <input type="hidden" name="productos_ids[]" value="${item.id_producto}">
            <input type="hidden" name="elementos_fisicos_ids[]" value="${item.id_elemento}">
        </td>
        <td>${item.marca}</td>
        <td><strong>${item.serial}</strong></td>
        <td>${item.estado}</td>
        <td>${item.ubicacion}</td>
        <td style="width: 80px;">
            <input type="number" name="cantidades[]" value="1" min="1" max="${item.max_cantidad}" 
                   class="form-control form-control-sm" ${item.es_serializado ? 'readonly' : ''}>
        </td>
        <td>
            <input type="text" name="observaciones[]" placeholder="Opcional..." 
                   class="form-control form-control-sm">
        </td>
        <td class="text-center">
            <button type="button" class="btn btn-danger btn-sm" 
                    onclick="document.getElementById('${row.id}').remove();">
                X
            </button>
        </td>
    `;
    tbody.appendChild(row);
}