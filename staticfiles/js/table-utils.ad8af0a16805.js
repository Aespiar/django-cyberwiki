document.addEventListener("DOMContentLoaded", function () {
    const table = document.querySelector("table"); // Seleccionar la tabla
    if (!table) return; // Salir si no hay tabla

    const rows = table.querySelectorAll("tr");

    // Combinar celdas con contenido repetido en columnas específicas
    rows.forEach((row) => {
        let previousCell = null;
        let colspanCount = 1;

        row.querySelectorAll("td").forEach((cell) => {
            if (previousCell && previousCell.textContent === cell.textContent) {
                colspanCount++;
                previousCell.setAttribute("colspan", colspanCount);
                cell.remove();
            } else {
                previousCell = cell;
                colspanCount = 1;
            }
        });
    });

    // Centrar columnas específicas
    const columnsToCenter = [0, 2]; // Índices de columnas a centrar
    table.querySelectorAll("tr").forEach(row => {
        row.querySelectorAll("td, th").forEach((cell, index) => {
            if (columnsToCenter.includes(index)) {
                cell.style.textAlign = "center";
            }
        });
    });
});
