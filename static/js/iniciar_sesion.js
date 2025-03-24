

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("loginForm").addEventListener("submit", async function (event) {
        event.preventDefault();

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!username || !password) {
            mostrarMensaje("⚠️ Por favor, ingrese usuario y contraseña.", "warning");
            return;
        }

        try {
            const response = await fetch('/login_admin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    usuario: username,
                    password: password
                })
            });

            const data = await response.json();  // Asegurar que la respuesta es JSON

            if (response.ok && data.status === "success") {
                mostrarMensaje("✅ Inicio de sesión exitoso.", "success");

                setTimeout(() => {
                    window.location.href = data.redirect_url;  // Redirigir al usuario
                }, 2000);  // Esperar 2 segundos antes de redirigir

                document.getElementById('loginForm').reset();
            } else {
                // Mostrar mensaje de error recibido desde el backend
                mostrarMensaje(`❌ ${data.message}`, "error");

                // Limpiar los campos si el backend lo indica
                if (data.clear_fields) {
                    document.getElementById("password").value = "";
                }
            }
        } catch (error) {
            mostrarMensaje("⚠️ Error de conexión con el servidor.", "error");
            console.error("Error en la solicitud:", error);
        }
    });



    document.getElementById("togglePassword").addEventListener("click", function () {
        const passwordInput = document.getElementById("password");
        const eyeIcon = document.getElementById("eyeIcon");

        passwordInput.type = (passwordInput.type === "password") ? "text" : "password";
        eyeIcon.className = (passwordInput.type === "password") ? "bi bi-eye" : "bi bi-eye-slash";
    });
});
    

  function limpiarCampos() {
        document.getElementById("login-form").reset();
    }
// Función para mostrar mensajes con Toastify
function mostrarMensaje(mensaje, tipo) {
    Toastify({
        text: mensaje,
        duration: 3000,
        gravity: "top",
        position: "right",
        style: {
            background: tipo === "success" ? "#28a745" :
                        tipo === "warning" ? "#ffc107" :
                        "#dc3545"
        }
    }).showToast();
}
