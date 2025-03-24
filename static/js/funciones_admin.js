document.addEventListener("DOMContentLoaded", function () {
    // Toggle del sidebar
    document.querySelector('[data-bs-target="#sidebarCollapse"]').addEventListener("click", function () {
        document.getElementById("sidebar").classList.toggle("show");
    });

    // Manejo de dropdowns
    document.querySelectorAll(".dropdown-toggle").forEach(toggle => {
        toggle.addEventListener("click", function (event) {
            let dropdownMenu = this.nextElementSibling;
            dropdownMenu.classList.toggle("show");
            event.stopPropagation(); // Evita que el evento de document lo cierre inmediatamente
        });
    });

    // Cerrar dropdowns y sidebar al hacer clic fuera
    document.addEventListener("click", function (event) {
        // Cierra todos los dropdowns abiertos
        document.querySelectorAll(".dropdown-menu.show").forEach(menu => {
            if (!menu.previousElementSibling.contains(event.target) && !menu.contains(event.target)) {
                menu.classList.remove("show");
            }
        });

        // Cierra el sidebar si se hace clic fuera de él
        let sidebar = document.getElementById("sidebar");
        if (sidebar.classList.contains("show") && !sidebar.contains(event.target) && !event.target.closest('[data-bs-target="#sidebarCollapse"]')) {
            sidebar.classList.remove("show");
        }
    });
});