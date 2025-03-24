document.getElementById('form_editar_paciente').addEventListener('submit', function(event) {
    event.preventDefault();

    let data = {
        primer_nombre: document.getElementById('primer_nombre').value,
        segundo_nombre: document.getElementById('segundo_nombre').value,
        primer_apellido: document.getElementById('primer_apellido').value,
        segundo_apellido: document.getElementById('segundo_apellido').value,
        tipo_documento: document.getElementById('tipo_documento').value,
        numero_documento: document.getElementById('numero_documento').value,  // Mantén el numero_documento
        correo: document.getElementById('correo').value,
        fecha_expedicion:document.getElementById('fecha_expedicion').value,
        fecha_nacimiento:document.getElementById('fecha_nacimiento').value,
        telefono: document.getElementById('telefono').value,
        direccion: document.getElementById('direccion').value,
        zona: document.getElementById('zona').value,
        departamento: document.getElementById('departamento').value,
        sexo: document.getElementById('sexo').value,
        ficha_sisben: document.getElementById('ficha_sisben').value,
        contraseña: document.getElementById('contraseña').value,
        activo: document.getElementById('activo').value
    };

    // Usamos el id del paciente directamente en la URL
    fetch(`/admin/paciente/actualizar/${document.getElementById('paciente_id').value}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            mostrarMensaje('Paciente actualizado correctamente', 'success');
        } else {
            mostrarMensaje('Hubo un error al actualizar', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarMensaje('Hubo un problema con la actualización.', 'error');
    });
});

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
