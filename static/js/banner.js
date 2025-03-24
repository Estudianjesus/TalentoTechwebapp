document.addEventListener("DOMContentLoaded", function() {
    const banner = document.querySelector('.banner-container');
    const header = document.querySelector('.main-header');

    function ajustarHeader() {
        if (banner.classList.contains('hidden')) {
            header.style.marginTop = "0px"; // Ajusta el header cuando el banner no está
        } else {
            header.style.marginTop = `${banner.offsetHeight}px`; // Ajusta según el tamaño real del banner
        }
    }

    window.addEventListener('scroll', function() {
        if (window.scrollY > 0) {
            banner.classList.add('hidden');
        } else {
            banner.classList.remove('hidden');
        }
        ajustarHeader();
    });

    // Ajustar el header al cargar la página
    ajustarHeader();
});
