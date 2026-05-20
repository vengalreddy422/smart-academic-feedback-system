// ==========================================
// SIMPLE CARD HOVER ANIMATION
// ==========================================

document.querySelectorAll(

    '.action-card, .kpi-card'

).forEach(card => {

    card.addEventListener(

        'mouseenter',

        () => {

            card.style.transition =
                '0.3s';
        }
    );
});