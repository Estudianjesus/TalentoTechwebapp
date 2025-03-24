document.getElementById("registroForm").addEventListener("submit", async function (e) {
    e.preventDefault(); 

    const formData = new FormData();
    formData.append("tipoDocumento", document.getElementById("tipo_documento").value);
    formData.append("documentNumber", document.getElementById("documentNumber").value);
    formData.append("fechaExpedicion", document.getElementById("fecha_expedicion").value);
    formData.append("fechaNacimiento", document.getElementById("fecha_nacimiento").value);
    formData.append("primerApellido", document.getElementById("primer_apellido").value);
    formData.append("segundoApellido", document.getElementById("segundo_apellido").value);
    formData.append("primerNombre", document.getElementById("primer_nombre").value);
    formData.append("segundoNombre", document.getElementById("segundo_nombre").value);
    formData.append("departamento", document.getElementById("departamento").value);
    formData.append("direccion", document.getElementById("direccion").value);
    formData.append("telefono", document.getElementById("telefono").value);
    formData.append("email", document.getElementById("email").value);
    formData.append("zona", document.querySelector('input[name="zona"]:checked')?.value || "");
    formData.append("sexo", document.querySelector('input[name="sexo"]:checked')?.value || "");
    formData.append("sisben", document.getElementById("sisben").value);
    formData.append("estado", "pendiente"); // Nuevo estado

    const archivoInput = document.getElementById("archivo").files[0];
    if (archivoInput) {
        formData.append("imagen", archivoInput);
    }

    try {
        const response = await fetch("http://192.168.1.3:5003/regisafiliado", {
            method: "POST",
            body: formData,
            mode: "cors"
        });

        const resultado = await response.json();
        console.log("Respuesta del servidor:", resultado);

        if (response.ok) {
            alert("✅ Solicitud enviada correctamente. Pendiente de aprobación.");
        } else {
            alert(`⚠ Error: ${resultado.error}`);
        }
    } catch (error) {
        console.error("❌ Error al enviar los datos:", error);
        alert("Hubo un error en la conexión con el servidor");
    }
});
