document.addEventListener("DOMContentLoaded", function () {
    const userMenuTrigger = document.getElementById("userMenuTrigger");
    const userDropdown = document.querySelector(".user-dropdown");

    if (userMenuTrigger && userDropdown) {
        userMenuTrigger.addEventListener("click", function (event) {
            event.stopPropagation();
            userDropdown.classList.toggle("show");
        });

        document.addEventListener("click", function (event) {
            if (!userMenuTrigger.contains(event.target) && !userDropdown.contains(event.target)) {
                userDropdown.classList.remove("show");
            }
        });
    } else {
        console.error("❌ No se encontraron elementos");
    }
});