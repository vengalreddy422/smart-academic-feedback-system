const menuToggle = document.getElementById('menuToggle');

const sidebar = document.querySelector('.sidebar');

menuToggle.addEventListener('click', () => {

    sidebar.classList.toggle('active');

});