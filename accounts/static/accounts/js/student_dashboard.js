/* =========================================
SIDEBAR TOGGLE
========================================= */

function toggleSidebar(){

    document
        .getElementById('sidebar')
        .classList
        .toggle('active');
}

/* =========================================
CARD ANIMATION
========================================= */

document.addEventListener(

    'DOMContentLoaded',

    function(){

        const cards = document.querySelectorAll(

            '.feature-card, .summary-card'
        );

        cards.forEach(

            function(card, index){

                card.style.opacity = '0';

                card.style.transform =
                    'translateY(20px)';

                setTimeout(

                    function(){

                        card.style.transition =
                            'all 0.4s ease';

                        card.style.opacity = '1';

                        card.style.transform =
                            'translateY(0)';
                    },

                    index * 100
                );
            }
        );
    }
);