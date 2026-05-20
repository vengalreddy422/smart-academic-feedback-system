// ==========================================
// TOGGLE DEPARTMENT
// ==========================================

function toggleDepartment(id){

    const section = document.getElementById(id);

    if(section.style.display === 'block'){

        section.style.display = 'none';
    }

    else{

        section.style.display = 'block';
    }
}

// ==========================================
// TOGGLE SECTION
// ==========================================

function toggleSection(id){

    const section = document.getElementById(id);

    if(section.style.display === 'grid'){

        section.style.display = 'none';
    }

    else{

        section.style.display = 'grid';
    }
}

// ==========================================
// TOGGLE STUDENT ACTIONS
// ==========================================

function toggleStudent(id){

    const panel = document.getElementById(id);

    if(panel.style.display === 'flex'){

        panel.style.display = 'none';
    }

    else{

        panel.style.display = 'flex';
    }
}