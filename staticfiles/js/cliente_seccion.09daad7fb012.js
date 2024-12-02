document.getElementById('agregarSeccionForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(this);
    const clienteId = document.body.getAttribute('data-cliente-id');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(`/clientes/${clienteId}/agregar_seccion/`, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrfToken }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire('Éxito', data.message, 'success').then(() => location.reload());
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire('Error', 'No se pudo agregar la sección.', 'error');
        });
});

function mostrarModalEditar(clienteId, seccionId, titulo, contenido) {
    Swal.fire({
        title: 'Editar Sección',
        html: `
            <form id="editarSeccionForm" enctype="multipart/form-data">
                <label for="titulo">Título</label>
                <input id="titulo" name="titulo" class="form-control mb-3" value="${titulo || ''}" required>
                <label for="contenido">Contenido</label>
                <textarea id="contenido" name="contenido" class="form-control mb-3">${contenido || ''}</textarea>
                <label for="archivo">Archivo (opcional)</label>
                <input id="archivo" name="archivo" type="file" class="form-control">
            </form>
        `,
        confirmButtonText: 'Guardar',
        showCancelButton: true,
        preConfirm: () => {
            const form = document.getElementById('editarSeccionForm');
            const formData = new FormData(form);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            return fetch(`/clientes/${clienteId}/secciones/${seccionId}/editar/`, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrfToken },
            })
                .then(response => {
                    if (!response.ok) throw new Error('Error al editar la sección');
                    return response.json();
                })
                .catch(error => {
                    console.error('Error:', error);
                    Swal.showValidationMessage(`Error: ${error}`);
                });
        }
    }).then(result => {
        if (result.value && result.value.success) {
            Swal.fire('Éxito', 'Sección actualizada correctamente.', 'success').then(() => location.reload());
        } else if (result.value) {
            Swal.fire('Error', result.value.message, 'error');
        }
    });
}


function eliminarSeccion(clienteId, seccionId) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: 'No podrás deshacer esta acción.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/clientes/${clienteId}/secciones/${seccionId}/eliminar/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire('Eliminado', data.message, 'success').then(() => location.reload());
                    } else {
                        Swal.fire('Error', data.message, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    Swal.fire('Error', 'Ocurrió un error al eliminar la sección.', 'error');
                });
        }
    });
}