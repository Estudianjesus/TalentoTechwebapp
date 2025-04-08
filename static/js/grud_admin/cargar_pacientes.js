$(document).ready(function() {
    cargarPacientes();
    setInterval(cargarPacientes, 15000); 
});

function cargarPacientes() {
    fetch('/admin/pacientes', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                let tableBody = document.getElementById("pacientes-table");

                data.pacientes.forEach(paciente => {
                    if (!document.getElementById(`paciente-${paciente.id}`)) {
                        let row = document.createElement("tr");
                        row.id = `paciente-${paciente.id}`;
                        row.innerHTML = `
                            <td contenteditable="true" onblur="actualizarPaciente(${paciente.id}, 'primer_nombre', this.textContent)">${paciente.primer_nombre} ${paciente.primer_apellido}</td>
                            <td>${paciente.tipo_documento}</td>
                            <td>${paciente.numero_documento}</td>
                            <td>${paciente.zona}</td>
                            <td>
                               <a href="/admin/paciente/${paciente.id}" class="btn btn-info btn-sm">Ver</a>
                                <a href="/admin/paciente/editar/${paciente.id}" class="btn btn-warning btn-sm">Editar</a>
                                <button class="btn btn-danger btn-sm" onclick="eliminarPaciente(${paciente.id})">Eliminar</button>
                            </td>
                        `;
                        tableBody.appendChild(row);
                    }
                });
                 filtrarPacientes()
            }
        })
        .catch(error => console.error("Error al cargar pacientes:", error));
}
    
function filtrarPacientes() {
    let input = document.getElementById("busqueda").value.toLowerCase();
    let filas = document.querySelectorAll("#pacientes-table tr");

    filas.forEach(fila => {
        let textoFila = "";  
        fila.querySelectorAll("td").forEach(td => {
            textoFila += td.innerText.toLowerCase() + " "; // Concatenar contenido de todas las celdas
        });

        fila.style.display = textoFila.includes(input) ? "" : "none";
    });
}


// Ejecutar el filtro cada vez que se presiona una tecla en el input de búsqueda
document.getElementById("busqueda").addEventListener("keyup", filtrarPacientes);
    

function eliminarPaciente(id) {
    if (!confirm("¿Estás seguro de que deseas eliminar este paciente?")) return;

    fetch(`/admin/paciente/eliminar/${id}`, {
        method: "DELETE",
        headers: { 
            "X-Requested-With": "XMLHttpRequest" 
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Respuesta del servidor:', data); // Log para depuración
        if (data.status === "success") {
            document.getElementById(`paciente-${id}`).remove();  // Eliminar la fila en la tabla
            mostrarMensaje("Paciente eliminado correctamente.", "success"); // Mostrar mensaje de éxito
        } else {
            mostrarMensaje("Error: " + data.message, "danger"); // Mostrar mensaje de error
        }
    })
    .catch(error => {
        console.error("Error al eliminar paciente:", error);
        mostrarMensaje("Se produjo un error inesperado.", "danger"); // Mostrar mensaje de error inesperado
    });
}

function mostrarMensaje(mensaje, tipo) {
    let alerta = $('<div class="alert"></div>').text(mensaje);
    alerta.addClass(tipo === 'success' ? 'alert-success' : 'alert-danger');

    // Especifica el contenedor donde aparecerá la alerta
    $('#mensaje_alerta').html(alerta);  // Reemplaza el contenido anterior

  
    $('html, body').animate({
        scrollTop: $('#mensaje_alerta').offset().top - ($(window).height() / 2) + ($('#mensaje_alerta').outerHeight() / 2)
    }, 800); 

    setTimeout(() => {
        alerta.fadeOut(500, function() { $(this).remove(); });
    }, 3000);
}