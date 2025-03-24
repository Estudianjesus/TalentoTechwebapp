document.addEventListener("DOMContentLoaded", function () {
    let primerNombre = sessionStorage.getItem("primer_nombre");
    let primerApellido = sessionStorage.getItem("primer_apellido");

    function capitalizarIniciales(texto) {
        return texto ? texto.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase()) : "";
    }

    let nombremayu = capitalizarIniciales(primerNombre);
    let apellidomayus = capitalizarIniciales(primerApellido);

    document.getElementById("elemento").textContent = nombremayu + " " + apellidomayus;

    const token = localStorage.getItem("token");

    if (token) {
        function verificarServidor() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "http://192.168.1.3:5003/verificar_usuario", true);
            xhr.setRequestHeader("Authorization", "Bearer " + token);
            xhr.timeout = 5000;

            xhr.onload = function () {
                if (xhr.status >= 200 && xhr.status < 300) {
                    const data = JSON.parse(xhr.responseText);
                    if (data.documento) {
                        document.getElementById("tipo_documento").value = data.tipo_documento;
                        document.getElementById("documentNumber").value = data.documento;
                        document.getElementById("nombre").value = data.nombre;
                        document.getElementById("segundo_nombre").value = data.segundo_nombre || "";
                        document.getElementById("apellido").value = data.apellido;
                        document.getElementById("segundo_apellido").value = data.segundo_apellido || "";
                    }
                } else {
                    console.error("Error al obtener el usuario:", xhr.statusText);
                    cerrarSesion();
                }
            };

            xhr.onerror = function () {
                console.error("Error en la solicitud AJAX");
                cerrarSesion();
            };

            xhr.ontimeout = function () {
                console.error("El servidor no responde a tiempo.");
                cerrarSesion();
            };

            xhr.send();
        }

        function cerrarSesion() {
            sessionStorage.clear();
            localStorage.clear();
            window.location.replace("login.html");
        }

        if (!window.verificacionIniciada) {
            window.verificacionIniciada = true;
            verificarServidor();
            setInterval(verificarServidor, 60000);
        }
    }
});


