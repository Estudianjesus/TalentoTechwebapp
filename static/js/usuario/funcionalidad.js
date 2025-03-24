document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".edit-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            let section = this.getAttribute("data-section");
            let viewElement = document.getElementById(section + "-view");
            let formElement = document.getElementById(section + "-form");

            if (viewElement && formElement) {
                if (formElement.classList.contains("d-none")) {
                    viewElement.classList.add("d-none");
                    formElement.classList.remove("d-none");
                    this.innerHTML = '<i class="fas fa-save me-1"></i>GUARDAR';
                    this.classList.replace("btn-outline-warning", "btn-warning");
                } else {
                    let userId = formElement.dataset.id || formElement.querySelector("[name='id']")?.value;
                    if (!userId) {
                        alert("No se pudo obtener el ID del paciente.");
                        return;
                    }

                    let formData = new FormData();
                    formData.append("id", userId);
                    formData.append("telefono", formElement.querySelector("[name='telefono']")?.value.trim() || "");
                    formData.append("direccion", formElement.querySelector("[name='direccion']")?.value.trim() || "");
                    formData.append("correo", formElement.querySelector("[name='correo']")?.value.trim() || "");

                    let passwordField = formElement.querySelector("[name='password']");
                    if (passwordField && passwordField.value.trim() !== "") {
                        formData.append("password", passwordField.value.trim());
                    }

                    fetch("/actualizar_paciente", {
                        method: "POST",
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            mostrarMensaje("error", data.error);
                        } else {
                            mostrarMensaje("success", data.mensaje);
                            viewElement.classList.remove("d-none");
                            formElement.classList.add("d-none");
                            button.innerHTML = '<i class="fas fa-edit me-1"></i>EDITAR';
                            button.classList.replace("btn-warning", "btn-outline-warning");

                            document.getElementById("view-telefono").innerHTML = 
                                `<i class="fas fa-phone-alt me-2 text-warning"></i> ${formData.get("telefono")}`;
                            document.getElementById("view-direccion").innerHTML = 
                                `<i class="fas fa-map-marker-alt me-2 text-warning"></i> ${formData.get("direccion")}`;
                            document.getElementById("view-correo").innerHTML = 
                                `<i class="fas fa-envelope me-2 text-warning"></i> ${formData.get("correo")}`;

                            if (data.imagen_url) {
                                document.getElementById("avatarContainer").style.backgroundImage = `url(${data.imagen_url})`;
                            }
                        }
                    })
                    .catch(error => {
                        console.error("Error al actualizar:", error);
                        mostrarMensaje("error", "Ocurrió un error al actualizar los datos.");
                    });
                }
            }
        });
    });

});

document.addEventListener("DOMContentLoaded", function () {
    let fileInput = document.getElementById("fileInput");
    let previewImagen = document.getElementById("previewImagen");

    // Si existe la imagen, permite hacer clic para cambiarla
    if (previewImagen) {
        previewImagen.addEventListener("click", function () {
            fileInput.click();
        });
    }

    // Detectar cambio en el input file y subir la imagen automáticamente
    fileInput.addEventListener("change", async function(event) {
        let file = event.target.files[0];

        if (file) {
            let reader = new FileReader();
            reader.onload = function(e) {
                previewImagen.src = e.target.result;  // Muestra la imagen seleccionada
            };
            reader.readAsDataURL(file);

            let formData = new FormData(document.getElementById("uploadForm"));

            try {
                let response = await fetch("/actualizar_paciente", {
                    method: "POST",
                    body: formData
                });

                let data = await response.json();
                
                if (data.imagen_url) {
                    previewImagen.src = data.imagen_url + "?" + new Date().getTime(); // Evitar caché
                } else {
                    console.error("Error al subir la imagen:", data);
                }
            } catch (error) {
                console.error("Error en la subida:", error);
            }
        }
    });
});


function mostrarMensaje(tipo, mensaje) {
    let mensajeBox = document.getElementById("mensaje-box");
    mensajeBox.innerHTML = mensaje;
    mensajeBox.className = tipo === "success" ? "alert alert-success" : "alert alert-danger";
    mensajeBox.style.display = "block";

    setTimeout(() => {
        mensajeBox.style.display = "none";
    }, 3000);
}


