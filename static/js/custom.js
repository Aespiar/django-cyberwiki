$(document).ready(function () {
    // Función para inicializar DataTables
    function inicializarDataTable() {
        if ($.fn.dataTable.isDataTable('#data-table')) {
            $('#data-table').DataTable().destroy(); // Destruir instancia previa si existe
        }

        $('#data-table').DataTable({
            responsive: true,
            autoWidth: false, // Desactiva el cálculo automático de ancho
            scrollX: true, // Permite el desplazamiento horizontal si es necesario
            dom: '<"filters-container"lf>t<"pagination-container"ip>',
            paging: true,
            searching: true,
            ordering: true,
            language: {
                lengthMenu: "Mostrar _MENU_ registros por página",
                zeroRecords: "No se encontraron resultados",
                info: "Mostrando página _PAGE_ de _PAGES_",
                infoEmpty: "No hay datos disponibles",
                infoFiltered: "(filtrado de _MAX_ registros totales)",
                search: "Buscar:",
                paginate: {
                    first: "Primero",
                    last: "Último",
                    next: "Siguiente",
                    previous: "Anterior"
                }
            },
            columnDefs: [
                { targets: '_all', className: 'responsive-header' }, // Aplica clase a todas las columnas
                { targets: "_all", className: "dt-head-center dt-body-center" }, 
                { targets: -1, orderable: false } // Deshabilitar orden en la columna de acciones
            ]
        });
    }

    // Inicializar DataTables al cargar la página
    inicializarDataTable();

    // Botón para habilitar/deshabilitar edición
    document.getElementById("toggle-edit").addEventListener("click", function () {
        const inputs = document.querySelectorAll(".styled-table tbody tr td:not(:last-child)"); // Excluir columna de acciones
        const isEditable = inputs[0].querySelector("input") !== null; // Verificar si ya está en modo edición

        inputs.forEach((cell) => {
            if (isEditable) {
                // Convertir input a texto
                const input = cell.querySelector("input");
                if (input) {
                    cell.textContent = input.value.trim();
                }
            } else {
                // Convertir texto a input
                const text = cell.textContent.trim();
                cell.innerHTML = `<input type="text" value="${text}" class="form-control"/>`;
            }
        });

        this.textContent = isEditable ? "✏️ Edición" : "Deshabilitar Edición";
        this.classList.toggle("btn-warning", isEditable);
        this.classList.toggle("btn-danger", !isEditable);
    });

    // Guardar cambios en la tabla
    $('#guardar-tabla').on('click', function () {
        const url = $(this).data('url'); // URL del backend
        const tablaId = $('#data-table').data('tabla-id'); // ID de la tabla desde el atributo data
        if (!tablaId) {
            alert('No se pudo identificar la tabla. Verifica la configuración.');
            return;
        }
    
        const filas = [];
        $('#data-table tbody tr').each(function () {
            const fila = { id: $(this).data('id') }; // Captura el ID de la fila
            $(this).find('td.data-cell').each(function () {
                const key = $(this).data('key'); // Clave de la celda
                const value = $(this).find('input').length > 0
                    ? $(this).find('input').val().trim() // Valor desde el input
                    : $(this).text().trim(); // Valor desde el texto plano
    
                if (key) { // Solo añade claves válidas
                    fila[key] = value;
                }
            });
            filas.push(fila); // Añade la fila al array
        });
    
        console.log("Datos enviados al backend:", filas); // Verifica la estructura antes de enviarla
    
        $.ajax({
            url: url,
            type: 'POST',
            data: {
                tabla_id: tablaId,
                filas: JSON.stringify(filas), // Serializa las filas como JSON
                csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function (response) {
                if (response.success) {
                    alert(response.message);
                    location.reload(); // Recarga la página para reflejar los cambios
                } else {
                    alert(response.message);
                }
            },
            error: function (xhr) {
                alert('Error al guardar los cambios: ' + xhr.responseText);
            }
        });
    });

    // Botón para eliminar filas
    $(document).on('click', '.btn-delete', function () {
        const filaId = $(this).closest('tr').data('id');
        const url = '/clientes/eliminar-fila/'; // Ruta del backend para eliminar (ajústala si es necesario)

        if (filaId === "new") {
            // Si es una fila nueva, simplemente eliminarla del DOM
            $(this).closest('tr').remove();
            alert('Fila nueva eliminada.');
            inicializarDataTable(); // Actualizar DataTable
            return;
        }

        if (confirm('¿Estás seguro de que deseas eliminar este registro?')) {
            // Si tiene ID real, enviar solicitud al backend
            $.ajax({
                url: url,
                type: 'POST',
                data: { fila_id: filaId },
                headers: { 'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val() }, // Token CSRF
                success: function (response) {
                    if (response.success) {
                        alert(response.message || 'Registro eliminado correctamente.');
                        $(`tr[data-id="${filaId}"]`).remove(); // Eliminar del DOM
                        inicializarDataTable();
                        location.reload();
                    } else {
                        alert(response.message || 'Error al eliminar el registro.');
                    }
                },
                error: function (xhr, status, error) {
                    alert('Ocurrió un error al eliminar el registro.');
                    console.error('Error:', error);
                }
            });
        }
    });

    // Botón para añadir fila nueva
    $('#add-row').on('click', function () {
        console.log("Botón añadir fila presionado.");
    
        // Obtén las claves de las columnas del encabezado
        const headers = $('#data-table thead th').map(function () {
            return $(this).text().trim() || null;
        }).get();
    
        const nuevaFila = $('<tr data-id="new"></tr>');
    
        headers.forEach((header, index) => {
            if (header && index < headers.length - 1) { // Excluir columna de acciones
                nuevaFila.append(
                    `<td class="data-cell" data-key="${header}"><input type="text" class="form-control" value="None"></td>`
                );
            }
        });
    
        nuevaFila.append(
            `<td><button class="btn-delete btn btn-danger">🗑️</button></td>`
        );
    
        console.log("Nueva fila HTML generada:", nuevaFila.prop('outerHTML'));
    
        $('#data-table tbody').append(nuevaFila);
    });
});
