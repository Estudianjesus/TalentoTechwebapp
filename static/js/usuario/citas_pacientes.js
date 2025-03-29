document.addEventListener('DOMContentLoaded', function () {
    // Verificar si estamos en la página "Mis Citas"
    if (window.location.href.includes('/mis_citas')) {
        cargarCitas();
    }

    // Evento para cargar citas cuando se hace clic en la pestaña
    const appointmentsTab = document.getElementById('appointments-tab');
    if (appointmentsTab) {
        appointmentsTab.addEventListener('click', cargarCitas);
    }
});

function cargarCitas() {
    console.log("Cargando citas...");
    
    const contenedorCitas = document.getElementById("contenedor-citas");
    if (contenedorCitas) {
        contenedorCitas.innerHTML = '<div class="loader-container">Cargando...</div>';
    }
    
    // Usar fetch para obtener citas
    fetch('/api/citas_paciente')
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al obtener citas');
            }
            return response.json();
        })
        .then(data => {
            mostrarCitas(data);
        })
        .catch(error => {
            if (contenedorCitas) {
                contenedorCitas.innerHTML = '<div class="error-container">Error al cargar las citas</div>';
            }
        });
}

function mostrarCitas(respuesta) {
    const contenedorCitas = document.getElementById("contenedor-citas");
    if (!contenedorCitas) return;

    // Verificar que la respuesta tiene el formato correcto
    let citas = [];
    
    // Manejo flexible de diferentes formatos de respuesta API
    if (Array.isArray(respuesta)) {
        citas = respuesta;
    } else if (respuesta && Array.isArray(respuesta.citas)) {
        citas = respuesta.citas;
    } else if (respuesta && respuesta.data && Array.isArray(respuesta.data.citas)) {
        citas = respuesta.data.citas;
    } else if (respuesta && respuesta.data && Array.isArray(respuesta.data)) {
        citas = respuesta.data;
    } else {
        contenedorCitas.innerHTML = '<div class="error-container">Formato de datos incorrecto</div>';
        return;
    }

    contenedorCitas.innerHTML = '';

    if (citas.length === 0) {
        contenedorCitas.innerHTML = `
            <div class="empty-state">
                <h3>No tiene citas programadas</h3>
                <a href="/programar_cita" class="btn-primary">Programar nueva cita</a>
            </div>
        `;
        return;
    }

    // Agrupar citas por fecha
    const citasPorFecha = agruparCitasPorFecha(citas);
    
    // Contenedor para todas las citas
    const citasContainer = document.createElement('div');
    citasContainer.classList.add('citas-container');
    
    // Procesar cada grupo de fecha
    Object.keys(citasPorFecha).forEach(fecha => {
        const citasDelDia = citasPorFecha[fecha];
        
        // Crear sección para el día
        const seccionDia = document.createElement('div');
        seccionDia.classList.add('day-section');
        
        // Encabezado del día
        const dayHeader = document.createElement('div');
        dayHeader.classList.add('day-header');
        dayHeader.innerHTML = `<div class="date-badge">${fecha}</div>`;
        seccionDia.appendChild(dayHeader);
        
        // Contenedor para tarjetas de citas
        const citasGrid = document.createElement('div');
        citasGrid.classList.add('citas-grid');
        
        // Crear tarjetas para cada cita
        citasDelDia.forEach(cita => {
            const citaCard = document.createElement('div');
            citaCard.classList.add('cita-card');
            citaCard.innerHTML = `
                <div class="cita-header">
                 <h3>${cita.tipo_servicio }${cita.especialidad ? ` - ${cita.especialidad}` : ''}</h3>
                 <span>${cita.estado || 'Confirmada'}</span>
                 </div>
                <div class="cita-body">
                    <div>Hora: ${cita.hora || 'No disponible'}</div>
                    ${cita.motivo ? `<div>Motivo: ${cita.motivo}</div>` : ''}
                    ${cita.codigo_confirmacion ? `<div>Codigo: ${cita.codigo_confirmacion}</div>` : ''}
                </div>
                <div class="cita-footer">
                    ${cita.estado?.toLowerCase() !== 'cancelada' ? 
                    `<button onclick="confirmarCancelacion(${cita.id})">Cancelar cita</button>` : ''}
                </div>
            `;
            citasGrid.appendChild(citaCard);
        });
        
        seccionDia.appendChild(citasGrid);
        citasContainer.appendChild(seccionDia);
    });
    
    contenedorCitas.appendChild(citasContainer);
}


function confirmarCancelacion(idCita) {
    if (confirm("¿Estás seguro de que quieres cancelar esta cita?")) {
        cancelarCita(idCita);
    }
}

function cancelarCita(idCita) {
    console.log("Intentando cancelar cita con ID:", idCita);

    const btnCancelar = $(`button[data-id="${idCita}"]`);
    if (btnCancelar.length) {
        btnCancelar.html('<span class="spinner-border spinner-border-sm"></span> Cancelando...');
        btnCancelar.prop("disabled", true);
    }

    $.ajax({
        url: `/api/cancelar_cita/${idCita}`,
        type: "DELETE",
        dataType: "json",
        success: function (data, textStatus, xhr) {
            console.log("Respuesta de cancelación:", textStatus, xhr.status);
            if (xhr.status === 204 || (data && data.success)) {
                alert("Cita cancelada con éxito.");
                $(`#cita-${idCita}`).fadeOut(500, function () {
                    $(this).remove();
                });
            } else {
                alert("Error al cancelar la cita.");
            }
        },
        error: function (xhr) {
            console.error("Error al cancelar la cita:", xhr.responseText);
            alert("No se pudo cancelar la cita. Intente nuevamente.");
        },
        complete: function () {
            $(`button[data-id="${idCita}"]`).html("Cancelar cita").prop("disabled", false);
        }
    });

}



// Función para agrupar citas por fecha
function agruparCitasPorFecha(citas) {
    const citasPorFecha = {};
    
    citas.forEach(cita => {
        const fecha = cita.fecha || 'Sin fecha';
        
        if (!citasPorFecha[fecha]) {
            citasPorFecha[fecha] = [];
        }
        
        citasPorFecha[fecha].push(cita);
    });
    
    return citasPorFecha;
}
