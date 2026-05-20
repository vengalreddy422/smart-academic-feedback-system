const studentCards = document.querySelectorAll(
    '.student-card'
);

studentCards.forEach(card => {

    card.addEventListener('click', () => {

        card.classList.toggle('active');

    });

});