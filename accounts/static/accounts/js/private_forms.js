// ==========================================
// SEARCH FORMS
// ==========================================

function searchForms(){

    const input = document.getElementById(
        'formSearch'
    ).value.toLowerCase();

    const cards = document.querySelectorAll(
        '.form-card'
    );

    cards.forEach(card => {

        const title = card.querySelector(
            '.form-title'
        ).innerText.toLowerCase();

        if(title.includes(input)){

            card.style.display = 'block';
        }

        else{

            card.style.display = 'none';
        }
    });
}

// ==========================================
// TOGGLE ACTIONS
// ==========================================

function toggleActions(id){

    const panel = document.getElementById(id);

    if(panel.style.display === 'block'){

        panel.style.display = 'none';
    }

    else{

        panel.style.display = 'block';
    }
}

// ==========================================
// TOGGLE STUDENTS
// ==========================================

function toggleStudents(id){

    event.stopPropagation();

    const panel = document.getElementById(id);

    if(panel.style.display === 'flex'){

        panel.style.display = 'none';
    }

    else{

        panel.style.display = 'flex';
    }
}

// ==========================================
// FILTER FORMS
// ==========================================

function filterForms(status, button){

    const cards = document.querySelectorAll(
        '.form-card'
    );

    cards.forEach(card => {

        if(

            status === 'all'

            ||

            card.dataset.status.includes(status)
        ){

            card.style.display = 'block';
        }

        else{

            card.style.display = 'none';
        }
    });

    document.querySelectorAll(
        '.filter-btn'
    ).forEach(btn => {

        btn.classList.remove(
            'active-filter'
        );
    });

    button.classList.add(
        'active-filter'
    );
}

// ==========================================
// TOGGLE DOWNLOAD
// ==========================================

function toggleDownload(id){

    event.stopPropagation();

    const menu = document.getElementById(id);

    document.querySelectorAll(
        '.download-menu'
    ).forEach(item => {

        if(item.id !== id){

            item.style.display = 'none';
        }
    });

    if(menu.style.display === 'block'){

        menu.style.display = 'none';
    }

    else{

        menu.style.display = 'block';
    }
}

// ==========================================
// CLOSE OUTSIDE
// ==========================================

document.addEventListener(
    'click',

    function(e){

        if(
            !e.target.closest(
                '.download-wrapper'
            )
        ){

            document.querySelectorAll(
                '.download-menu'
            ).forEach(menu => {

                menu.style.display = 'none';
            });
        }
    }
);