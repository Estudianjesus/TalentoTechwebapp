document.getElementById('registroForm').addEventListener('submit', async function(event) {
    event.preventDefault();  

    const formData = {
        tipo_documento: document.getElementById('tipo_documento').value,
        documentNumber: document.getElementById('documentNumber').value,
        fecha_expedicion: document.getElementById('fecha_expedicion').value,
        fecha_nacimiento: document.getElementById('fecha_nacimiento').value,
        primer_apellido: document.getElementById('primer_apellido').value,
        segundo_apellido: document.getElementById('segundo_apellido').value,
        primer_nombre: document.getElementById('primer_nombre').value,
        segundo_nombre: document.getElementById('segundo_nombre').value,
        departamento: document.getElementById('departamento').value,
        direccion: document.getElementById('direccion').value,
        telefono: document.getElementById('telefono').value,
        email: document.getElementById('email').value,
        zona: document.querySelector('input[name="zona"]:checked')?.value,
        sexo: document.querySelector('input[name="sexo"]:checked')?.value,
        sisben: document.getElementById('sisben').value
    };

    if (!document.getElementById('aceptarTerminos').checked) {
        Toastify({
            text: "Debe aceptar los términos y condiciones.",
            duration: 3000,
            backgroundColor: "red"
        }).showToast();
        return;
    }

    try {
        const response = await fetch('/portal_usuarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        if (response.ok) {
            Toastify({
                text: "Solicitud exitosa",
                duration: 3000,
                backgroundColor: "green"
            }).showToast();

            // Limpiar el formulario 
            document.getElementById('registroForm').reset();

        } else {
            if (response.status === 409) {
                Toastify({
                    text: "Error: El número de documento ya está registrado.",
                    duration: 3000,
                    backgroundColor: "red"
                }).showToast();
            } else {
                Toastify({
                    text: 'Error: ' + (result.error || 'Ocurrió un error desconocido'),
                    duration: 3000,
                    backgroundColor: "red"
                }).showToast();
            }
        }
    } catch (error) {
        console.error('Error al enviar los datos:', error);
        Toastify({
            text: 'Hubo un problema al enviar los datos. Intenta nuevamente.',
            duration: 3000,
            backgroundColor: "red"
        }).showToast();
    }
});
