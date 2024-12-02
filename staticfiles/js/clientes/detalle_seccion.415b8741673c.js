document.addEventListener("DOMContentLoaded", function () {
    const table = document.getElementById("data-table");

    if (table) {
        const rows = Array.from(table.rows);

        // Función para colapsar filas con valores repetidos en la primera columna
        function collapseTableRows() {
            let prevValue = null;
            let spanCount = 0;

            rows.forEach((row, index) => {
                const cell = row.cells[0]; // Primera columna
                if (cell) {
                    const currentValue = cell.innerText.trim();
                    if (currentValue === prevValue) {
                        spanCount++;
                        row.deleteCell(0); // Eliminar celda repetida
                        rows[index - spanCount].cells[0].rowSpan = spanCount + 1;
                    } else {
                        prevValue = currentValue;
                        spanCount = 0;
                    }
                }
            });
        }

        // Ejecutar colapso de filas
        collapseTableRows();
    }
});
document.addEventListener("DOMContentLoaded", function () {
    const table = document.getElementById("data-table");
    console.log("Tabla detectada:", table); // Verifica si la tabla está en el DOM

    if (table) {
        console.log("Tabla encontrada con filas:", table.rows.length);
    } else {
        console.error("Tabla no encontrada");
    }
});
