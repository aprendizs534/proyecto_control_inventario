// inventario/static/js/script.js

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
                    
                    if (data.resultados.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No se encontraron elementos disponibles.</td></tr>';
                        return;
                    }
                    
                    data.resultados.forEach((item, index) => {
                        let itemJson = JSON.stringify(item).replace(/'/g, "&apos;");
                        let row = `<tr>
                            <td>${index + 1}</td>
                            <td>${item.descripcion}</td>
                            <td><strong>${item.serial}</strong></td>
                            <td><span class="badge bg-secondary">${item.estado}</span></td>
                            <td>${item.ubicacion}</td>
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

// 3. Función global para agregar ítems a la tabla de la asignación
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
            <input type="hidden" name="elementos_fisicos_ids[]" value="${item.id_elemento || ''}">
        </td>
        <td><strong>${item.serial}</strong></td>
        <td>${item.estado}</td>
        <td>${item.ubicacion}</td>
        <td>
            <input type="number" name="cantidades[]" value="1" min="1" ${item.es_serializado ? 'readonly' : ''} class="form-control form-control-sm text-center">
        </td>
        <td class="text-center">
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="document.getElementById('item-row-${contadorItems}').remove()">
                &times;
            </button>
        </td>
    `;
    tbody.appendChild(row);
}