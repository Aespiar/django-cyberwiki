// Espera a que el DOM esté completamente cargado
document.addEventListener("DOMContentLoaded", () => {
    const clienteSelect = document.getElementById("cliente-select");
    const formCargarExcel = document.getElementById("form-cargar-excel"); // Asegúrate de usar este ID en tu formulario HTML
    const tableBody = document.getElementById("table-body");

    // Filtrar activos al seleccionar un cliente
    if (clienteSelect) {
        clienteSelect.addEventListener("change", function () {
            const clienteId = this.value;
            fetch(`/clientes/filtrar-activos/?cliente_id=${clienteId}`)
                .then(response => response.json())
                .then(data => {
                    tableBody.innerHTML = ""; // Limpia la tabla actual
                    data.forEach((activo, index) => {
                        const row = `
                            <tr>
                                <td>${index + 1}</td>
                                <td>${activo.ubicacion || ""}</td>
                                <td>${activo.ip || ""}</td>
                                <td>${activo.nombre_activo || ""}</td>
                                <td>${activo.marca || ""}</td>
                                <td>${activo.modelo || ""}</td>
                                <td>${activo.tipo_hw || ""}</td>
                                <td>${activo.numero_serie || ""}</td>
                                <td>${activo.requiere_upgrade || ""}</td>
                                <td>${activo.requiere_mantenimiento || ""}</td>
                                <td>${activo.numero_mantenimientos || 0}</td>
                                <td>${activo.modelo_vigente || ""}</td>
                                <td>${activo.descripcion || ""}</td>
                            </tr>`;
                        tableBody.innerHTML += row;
                    });
                })
                .catch(error => console.error("Error al filtrar activos:", error));
        });
    } else {
        console.error("El elemento 'cliente-select' no existe en el DOM.");
    }

    // Procesar archivo y actualizar la tabla
    if (formCargarExcel) {
        formCargarExcel.addEventListener("submit", function (e) {
            e.preventDefault();

            const formData = new FormData(this);

            fetch("/clientes/procesar_archivo_control_activo/", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire("Éxito", data.message, "success");

                        // Actualizar la tabla con los nuevos datos
                        const clienteId = clienteSelect ? clienteSelect.value : null;
                        if (clienteId) {
                            fetch(`/clientes/filtrar-activos/?cliente_id=${clienteId}`)
                                .then(response => response.json())
                                .then(activos => {
                                    tableBody.innerHTML = ""; // Limpia la tabla
                                    activos.forEach((activo, index) => {
                                        const row = `
                                            <tr>
                                                <td>${index + 1}</td>
                                                <td>${activo.ubicacion || ""}</td>
                                                <td>${activo.ip || ""}</td>
                                                <td>${activo.nombre_activo || ""}</td>
                                                <td>${activo.marca || ""}</td>
                                                <td>${activo.modelo || ""}</td>
                                                <td>${activo.tipo_hw || ""}</td>
                                                <td>${activo.numero_serie || ""}</td>
                                                <td>${activo.requiere_upgrade || ""}</td>
                                                <td>${activo.requiere_mantenimiento || ""}</td>
                                                <td>${activo.numero_mantenimientos || 0}</td>
                                                <td>${activo.modelo_vigente || ""}</td>
                                                <td>${activo.descripcion || ""}</td>
                                            </tr>`;
                                        tableBody.innerHTML += row;
                                    });
                                })
                                .catch(error => console.error("Error al actualizar la tabla:", error));
                        }
                    } else {
                        Swal.fire("Error", data.message, "error");
                    }
                })
                .catch(error => {
                    console.error("Error al procesar el archivo:", error);
                    Swal.fire("Error", "Hubo un problema al procesar el archivo.", "error");
                });
        });
    } else {
        console.error("El formulario de carga de Excel ('form-cargar-excel') no existe en el DOM.");
    }
});

// Función para cargar datos del activo en el modal
function editarActivo(activoId) {
    fetch(`/clientes/control_activos/editar/${activoId}/`,{
        method: "GET", // Asegúrate de usar el método correcto
        headers: {
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                // Llenar el formulario con los datos del activo
                document.getElementById("edit-activo-id").value = data.id;
                document.getElementById("edit-nombre-activo").value = data.nombre_activo;
                document.getElementById("edit-ubicacion").value = data.ubicacion;
                document.getElementById("edit-ip").value = data.ip;
                document.getElementById("edit-marca").value = data.marca;
                document.getElementById("edit-modelo").value = data.modelo;
                document.getElementById("edit-tipo-hw").value = data.tipo_hw;
                document.getElementById("edit-numero-serie").value = data.numero_serie;
                document.getElementById("edit-requiere-upgrade").value = data.requiere_upgrade;
                document.getElementById("edit-requiere-mantenimiento").value = data.requiere_mantenimiento;
                document.getElementById("edit-numero-mantenimientos").value = data.numero_mantenimientos;
                document.getElementById("edit-modelo-vigente").value = data.modelo_vigente;
                document.getElementById("edit-descripcion").value = data.descripcion;

                // Mostrar el modal
                const editModal = new bootstrap.Modal(document.getElementById("editModal"));
                editModal.show();
            } else {
                Swal.fire("Error", "No se pudo cargar el activo.", "error");
            }
        })
        .catch(error => {
            console.error("Error al cargar el activo:", error);
            Swal.fire("Error", "Ocurrió un error al cargar los datos del activo.", "error");
        });
}

// Guardar cambios al enviar el formulario
document.getElementById("saveChanges").addEventListener("click", function () {
    const form = document.getElementById("editForm");
    const formData = new FormData(form);

    fetch(`/clientes/control_activos/editar/${formData.get("activo_id")}/`, {
        method: "POST", // Usar POST para actualizar datos
        body: formData,
        headers: {
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire("Éxito", data.message, "success").then(() => location.reload());
            } else {
                Swal.fire("Error", data.error || "No se pudo actualizar el activo.", "error");
            }
        })
        .catch(error => {
            console.error("Error al guardar cambios:", error);
            Swal.fire("Error", "Ocurrió un error al guardar los cambios.", "error");
        });
});

// Función para eliminar un activo
function eliminarActivo(activoId) {
    Swal.fire({
        title: "¿Está seguro?",
        text: "Esta acción no se puede deshacer.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "Sí, eliminar",
        cancelButtonText: "Cancelar",
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/clientes/control_activos/eliminar/${activoId}/`, {
                method: "POST", // Esto debe coincidir con la vista
                headers: {
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire("Eliminado", data.message, "success").then(() => location.reload());
                    } else {
                        Swal.fire("Error", data.error || "No se pudo eliminar el activo.", "error");
                    }
                })
                .catch(error => {
                    Swal.fire("Error", "Ocurrió un error inesperado.", "error");
                    console.error("Error al eliminar el activo:", error);
                });
        }
    });
}
document.addEventListener("DOMContentLoaded", () => {
    const clienteSelect = document.getElementById("cliente-select");
    const formAddActivo = document.getElementById("addForm");
    const saveAddButton = document.getElementById("saveAdd");
    const tableBody = document.getElementById("table-body");

    // Actualiza el cliente seleccionado en el formulario oculto para agregar un activo
    if (clienteSelect) {
        clienteSelect.addEventListener("change", function () {
            const clienteId = this.value;
            document.getElementById("add-cliente-id").value = clienteId;
        });
    }

    // Guardar un nuevo activo
    if (saveAddButton) {
        saveAddButton.addEventListener("click", function () {
            const formData = new FormData(formAddActivo);
            const clienteId = formData.get("cliente_id");
        
            // Validación básica para asegurarse de que un cliente esté seleccionado
            if (!clienteId) {
                Swal.fire("Error", "Selecciona un cliente antes de agregar un activo.", "error");
                return;
            }
        
            fetch("/clientes/control_activos/agregar/", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire("Éxito", data.message, "success").then(() => {
                            // Aquí actualizamos la tabla dinámicamente o recargamos la página.
                            fetch(`/clientes/filtrar-activos/?cliente_id=${clienteId}`)
                                .then(response => response.json())
                                .then(activos => {
                                    tableBody.innerHTML = ""; // Limpia la tabla
                                    activos.forEach((activo, index) => {
                                        const row = `
                                            <tr>
                                                <td>${index + 1}</td>
                                                <td>${activo.ubicacion || ""}</td>
                                                <td>${activo.ip || ""}</td>
                                                <td>${activo.nombre_activo || ""}</td>
                                                <td>${activo.marca || ""}</td>
                                                <td>${activo.modelo || ""}</td>
                                                <td>${activo.tipo_hw || ""}</td>
                                                <td>${activo.numero_serie || ""}</td>
                                                <td>${activo.requiere_upgrade || ""}</td>
                                                <td>${activo.requiere_mantenimiento || ""}</td>
                                                <td>${activo.numero_mantenimientos || 0}</td>
                                                <td>${activo.modelo_vigente || ""}</td>
                                                <td>${activo.descripcion || ""}</td>
                                                <td>
                                                    <button class="btn btn-sm btn-warning" onclick="editarActivo('${activo.id}')">Editar</button>
                                                    <button class="btn btn-sm btn-danger" onclick="eliminarActivo('${activo.id}')">Eliminar</button>
                                                </td>
                                            </tr>`;
                                        tableBody.innerHTML += row;
                                    });
        
                                    // Limpia el formulario
                                    formAddActivo.reset();
        
                                    // Oculta el modal después de agregar
                                    const addModal = bootstrap.Modal.getInstance(document.getElementById("addModal"));
                                    addModal.hide();
                                })
                                .catch(error => {
                                    console.error("Error al actualizar la tabla:", error);
                                    // Recargar la página si falla la actualización de la tabla
                                    location.reload();
                                });
                        });
                    } else {
                        Swal.fire("Error", data.message || "No se pudo agregar el activo.", "error");
                    }
                })
                .catch(error => {
                    console.error("Error al agregar el activo:", error);
                    Swal.fire("Error", "Ocurrió un error al agregar el activo.", "error");
                });
        });
    }
});
