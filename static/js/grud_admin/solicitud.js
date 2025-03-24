$(document).ready(function() {
    // Cargar las solicitudes inmediatamente cuando la página carga
    cargarSolicitudes();

    // Configurar el intervalo para que se actualicen cada 10 segundos
    setInterval(cargarSolicitudes, 15000);
});

function cargarSolicitudes() {
    $.ajax({
        url: '/admin/solicitudes',  // Ruta de Flask
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            if (response.status === 'success') {
                let tabla = $('.table tbody');
                tabla.empty(); // Limpiar la tabla antes de agregar nuevos datos

                response.solicitudes.forEach(solicitud => {
                    let estadoClass = solicitud.estado === 'Pendiente' ? 'estado-pendiente' :
                                      solicitud.estado === 'Aprobada' ? 'estado-aprobado' :
                                      solicitud.estado === 'Rechazada' ? 'estado-rechazado' : '';

                    let acciones = '';
                    if (solicitud.estado === 'Pendiente') {
                        acciones = `
                            <button class="btn-aceptar" onclick="aceptarSolicitud(${solicitud.id})">Aceptar</button>
                            <button class="btn-rechazar" onclick="rechazarSolicitud(${solicitud.id})">Rechazar</button>
                        `;
                    } else if (solicitud.estado === 'Rechazada') {
                        acciones = `<button class="btn-restaurar" onclick="restaurarSolicitud(${solicitud.id})">Restaurar</button>`;
                    } else {
                        acciones = `<span class="text-muted">No se pueden cambiar</span>`;
                    }

                    let fila = ` 
                        <tr id="solicitud-${solicitud.id}">
                            <td>${solicitud.primer_nombre} ${solicitud.primer_apellido}</td>
                            <td>${solicitud.tipo_documento}</td>
                            <td>${solicitud.numero_documento}</td>
                            <td>${solicitud.zona}</td>
                            <td><span class="${estadoClass}">${solicitud.estado}</span></td>
                            <td class="acciones">${acciones}</td>
                        </tr>
                    `;
                    tabla.append(fila);
                });
            } else {
                alert('No se pudieron cargar las solicitudes');
            }
        },
        error: function() {
            alert('Hubo un error al cargar las solicitudes');
        }
    });
}

function aceptarSolicitud(solicitudId) {
    $.ajax({
        url: `/admin/solicitudes/aceptar/${solicitudId}`,
        type: 'POST',
        dataType: 'json',
        success: function(response) {
            if (response.status === 'success') {
                $('#solicitud-' + solicitudId).fadeOut(500, function() {
                    $(this).remove();
                });
                mostrarMensaje(response.message, 'success');
            } else {
                mostrarMensaje(response.message, 'error');
            }
        },
        error: function() {
            mostrarMensaje('Hubo un error al aceptar la solicitud.', 'error');
        }
    });
}

function rechazarSolicitud(solicitudId) {
    $.ajax({
        url: `/admin/solicitudes/rechazar/${solicitudId}`,
        type: 'POST',
        dataType: 'json',
        success: function(response) {
            if (response.status === 'success') {
                // Cambiar el estado visualmente
                let fila = $('#solicitud-' + solicitudId);
                fila.find('td:nth-child(5)').html('<span class="estado-rechazado">Rechazada</span>');

                // Reemplazar los botones con el de restaurar
                fila.find('.acciones').html(
                    `<button class="btn-restaurar" onclick="restaurarSolicitud(${solicitudId})">Restaurar</button>`
                );

                mostrarMensaje(response.message, 'success');
            } else {
                mostrarMensaje(response.message, 'error');
            }
        },
        error: function() {
            mostrarMensaje('Hubo un error al rechazar la solicitud.', 'error');
        }
    });
}

function restaurarSolicitud(solicitudId) {
    $.ajax({
        url: `/admin/solicitudes/restaurar/${solicitudId}`,
        type: 'POST',
        dataType: 'json',
        success: function(response) {
            if (response.status === 'success') {
                // Restaurar estado visualmente
                let fila = $('#solicitud-' + solicitudId);
                fila.find('td:nth-child(5)').html('<span class="estado-pendiente">Pendiente</span>');

                // Reponer los botones originales
                fila.find('.acciones').html(
                    `<button class="btn-aceptar" onclick="aceptarSolicitud(${solicitudId})">Aceptar</button>
                     <button class="btn-rechazar" onclick="rechazarSolicitud(${solicitudId})">Rechazar</button>`
                );

                mostrarMensaje(response.message, 'success');
            } else {
                mostrarMensaje(response.message, 'error');
            }
        },
        error: function() {
            mostrarMensaje('Hubo un error al restaurar la solicitud.', 'error');
        }
    });
}

function mostrarMensaje(mensaje, tipo) {
    let alerta = $('<div class="alert"></div>').text(mensaje);
    alerta.addClass(tipo === 'success' ? 'alert-success' : 'alert-danger');
    
    $('.container').prepend(alerta);
    setTimeout(() => {
        alerta.fadeOut(500, function() { $(this).remove(); });
    }, 3000);
}