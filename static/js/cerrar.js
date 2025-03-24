document.getElementById("logoutBtn").addEventListener("click", function(event) {
    event.preventDefault(); // Prevenir recarga de la página

    console.log("Botón de logout presionado.");

    var xhr = new XMLHttpRequest();
    xhr.open("POST", 'http://192.168.1.3:5003/logout', true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            console.log("Respuesta del servidor en logout:", data); // Log para la respuesta del servidor
            Toastify({
                text: data.message || "Cierre de sesión exitoso.",
                duration: 3000,
                gravity: "top",
                position: "right",
                backgroundColor: "green",
                stopOnFocus: true
            }).showToast();

            sessionStorage.clear();  
            localStorage.clear();
            window.location.href = "login.html";  // Redirigir al login sin recargar la página
        } else {
            console.error('Error al cerrar sesión:', xhr.statusText);
            Toastify({
                text: "Hubo un error al cerrar sesión. Intenta nuevamente.",
                duration: 3000,
                gravity: "top",
                position: "right",
                backgroundColor: "red",
                stopOnFocus: true
            }).showToast();
        }
    };

    xhr.onerror = function() {
        console.error('Error en la solicitud de logout');
        Toastify({
            text: "Hubo un error en la solicitud de cierre de sesión. Intenta nuevamente.",
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: "red",
            stopOnFocus: true
        }).showToast();
    };

    xhr.send(JSON.stringify({}));  // Enviar la solicitud de logout
});

document.getElementById("formCita").addEventListener("submit", function (event) {
    event.preventDefault(); // Evita la recarga de la página

    console.log("Formulario de cita enviado.");

    // Recuperar el token almacenado
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    console.log("Token enviado:", token);
    if (!token) {
        console.error("Error: No hay token disponible");
        alert("No tienes una sesión activa. Inicia sesión primero.");
        return;
    }

    const datosCita = {
        tipo_documento: document.getElementById("tipo_documento").value,
        documentNumber: document.getElementById("documentNumber").value,
        nombre: document.getElementById("nombre").value,
        segundo_nombre: document.getElementById("segundo_nombre").value,
        apellido: document.getElementById("apellido").value,
        segundo_apellido: document.getElementById("segundo_apellido").value,
        tipo_cita: document.getElementById("tipo_cita").value,
        fecha: document.getElementById("fecha").value,
        hora: document.getElementById("hora").value,
        motivo: document.getElementById("motivo").value
    };

    console.log("Datos de la cita:", datosCita);

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://192.168.1.3:5004/agendar_cita", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            const data = JSON.parse(xhr.responseText);
            console.log("Respuesta de agendar_cita:", data);
            alert(data.message);
        } else {
            console.error("Error al agendar cita:", xhr.status, xhr.statusText);
            alert("Error al agendar cita: " + xhr.statusText);
        }
    };

    xhr.onerror = function() {
        console.error("Error en la solicitud de agendar cita");
        alert("Error de conexión con el servidor.");
    };

    xhr.send(JSON.stringify(datosCita)); 
});