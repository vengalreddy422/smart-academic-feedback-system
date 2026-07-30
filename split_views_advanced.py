import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEWS_DIR = os.path.join(BASE_DIR, 'accounts', 'views')
INIT_FILE = os.path.join(VIEWS_DIR, '__init__.py')

# Mappings for further splitting
SPLITS = {
    'form_management_views.py': {
        'private_form_views.py': ['private_forms'],
        'public_form_views.py': ['public_forms', 'public_form_qr', 'public_form_users', 'public_form_detail', 'public_active_forms', 'public_future_forms', 'public_expired_forms', 'public_forms_dashboard'],
        'form_builder_views.py': ['edit_form', 'delete_form', 'add_question', 'get_form_questions', 'delete_question', 'delete_option', 'preview_form']
    },
    'teacher_views.py': {
        'teacher_dashboard_views.py': ['teacher_dashboard'],
        'teacher_form_views.py': ['teacher_forms', 'active_forms', 'teacher_completed_forms', 'teacher_active_forms', 'teacher_upcoming_forms'],
        'teacher_student_views.py': ['teacher_form_detail', 'student_response_detail', 'teacher_students']
    },
    'admin_views.py': {
        'admin_dashboard_views.py': ['admin_dashboard', 'manage_users'],
        'admin_student_views.py': ['students_list', 'add_student', 'edit_student', 'delete_student'],
        'admin_teacher_views.py': ['teachers_list', 'add_teacher', 'edit_teacher', 'delete_teacher']
    },
    'student_views.py': {
        'student_dashboard_views.py': ['student_dashboard'],
        'student_forms_views.py': ['completed_forms', 'upcoming_forms', 'pending_forms', 'expired_forms']
    }
}

for source_file, target_mapping in SPLITS.items():
    source_path = os.path.join(VIEWS_DIR, source_file)
    if not os.path.exists(source_path):
        continue
        
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = re.split(r'\n(?=@login_required|@csrf_protect|@role_required|def |class )', content)
    
    # Extract COMMON_IMPORTS from the first block
    common_imports = blocks[0] if len(blocks) > 0 else ""
    
    for new_file, func_names in target_mapping.items():
        new_content = common_imports
        for block in blocks[1:]:
            block = block.strip()
            if not block: continue
            match = re.search(r'(?:def|class)\s+([a-zA-Z0-9_]+)', block)
            if match and match.group(1) in func_names:
                new_content += "\n\n" + block
        
        with open(os.path.join(VIEWS_DIR, new_file), 'w', encoding='utf-8') as f:
            f.write(new_content)
            
    os.remove(source_path)

# Rebuild __init__.py
all_files = [f for f in os.listdir(VIEWS_DIR) if f.endswith('.py') and f != '__init__.py']
init_content = ""
for f in all_files:
    init_content += f"from .{f[:-3]} import *\n"

with open(INIT_FILE, 'w', encoding='utf-8') as f:
    f.write(init_content)
