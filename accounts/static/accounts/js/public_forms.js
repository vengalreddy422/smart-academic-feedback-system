// ==========================================
// EXPLORE OPTIONS
// ==========================================

function toggleActions(id){

    const panel = document.getElementById(id);

    if(panel.style.display === 'grid'){

        panel.style.display = 'none';
    }

    else{

        panel.style.display = 'grid';
    }
}

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
// DOWNLOAD MENU
// ==========================================

function toggleDownload(id){

    const menu = document.getElementById(
        'download' + id
    );

    document.querySelectorAll('.download-menu')
    .forEach(item => {

        if(item !== menu){

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