import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resplit_views_file(app_name, file_mapping):
    BAK_FILE = os.path.join(BASE_DIR, app_name, 'views.py.bak')
    VIEWS_DIR = os.path.join(BASE_DIR, app_name, 'views')

    if not os.path.exists(BAK_FILE):
        return

    # Clear existing broken directory
    if os.path.exists(VIEWS_DIR):
        shutil.rmtree(VIEWS_DIR)
    os.makedirs(VIEWS_DIR)

    with open(BAK_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    common_imports = []
    blocks = []
    current_block = []
    
    in_imports = True
    
    for line in lines:
        if in_imports:
            if line.startswith('def ') or line.startswith('class ') or line.startswith('@') or line.startswith('# ==='):
                in_imports = False
            else:
                if line.startswith('from .models'):
                    line = line.replace('from .models', f'from {app_name}.models')
                elif line.startswith('from .field_registry'):
                    line = line.replace('from .field_registry', f'from {app_name}.field_registry')
                common_imports.append(line)
                continue
                
        if line.startswith('@') or (line.startswith('def ') and not any(l.startswith('@') for l in current_block)) or (line.startswith('class ') and not any(l.startswith('@') for l in current_block)):
            if current_block:
                blocks.append("".join(current_block))
            current_block = [line]
        else:
            current_block.append(line)
            
    if current_block:
        blocks.append("".join(current_block))

    common_imports_text = "".join(common_imports).strip()
    
    # ensure role_required is in common imports if defined
    if app_name == 'accounts':
        if 'def role_required' not in common_imports_text:
            common_imports_text += """
from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponse

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('user_login')
            user_role = getattr(request.user, 'role', None)
            if user_role not in roles:
                return HttpResponse('Unauthorized', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
"""

    files_content = {filename: common_imports_text + "\n" for filename in file_mapping.keys()}
    files_content['__init__.py'] = ""

    for block_text in blocks:
        block_text = block_text.strip()
        if not block_text: continue
        
        match = re.search(r'(?:def|class)\s+([a-zA-Z0-9_]+)', block_text)
        if match:
            func_name = match.group(1)
            
            if func_name == 'role_required':
                continue
            
            placed = False
            for filename, names in file_mapping.items():
                if func_name in names:
                    files_content[filename] += "\n" + block_text + "\n"
                    if f"from .{filename[:-3]} import *" not in files_content['__init__.py']:
                        files_content['__init__.py'] += f"from .{filename[:-3]} import *\n"
                    placed = True
                    break
            
            if not placed:
                print(f"Warning: {func_name} not mapped! Putting in utils_views.py")
                if 'utils_views.py' not in files_content:
                    files_content['utils_views.py'] = common_imports_text + "\n"
                files_content['utils_views.py'] += "\n" + block_text + "\n"
                if f"from .utils_views import *" not in files_content['__init__.py']:
                    files_content['__init__.py'] += f"from .utils_views import *\n"

    for filename, text in files_content.items():
        if filename == '__init__.py' or text.strip() != common_imports_text.strip():
            with open(os.path.join(VIEWS_DIR, filename), 'w', encoding='utf-8') as f:
                f.write(text)


ACCOUNTS_MAPPING = {
    'auth_views.py': ['information_page', 'user_login', 'user_logout', 'UserPasswordChangeView'],
    'student_views.py': ['student_dashboard', 'completed_forms', 'upcoming_forms', 'pending_forms', 'expired_forms'],
    'teacher_views.py': ['teacher_dashboard', 'teacher_form_detail', 'student_response_detail', 'teacher_forms', 'active_forms', 'teacher_completed_forms', 'teacher_active_forms', 'teacher_upcoming_forms', 'teacher_students'],
    'admin_views.py': ['admin_dashboard', 'manage_users', 'teachers_list', 'students_list', 'add_student', 'edit_student', 'delete_student', 'add_teacher', 'edit_teacher', 'delete_teacher'],
    'form_management_views.py': ['private_forms', 'public_forms', 'public_form_qr', 'public_form_users', 'public_form_detail', 'edit_form', 'delete_form', 'add_question', 'get_form_questions', 'delete_question', 'delete_option', 'preview_form', 'public_active_forms', 'public_future_forms', 'public_expired_forms', 'public_forms_dashboard']
}

FORMS_ENGINE_MAPPING = {
    'public_views.py': ['public_form_view', 'submit_public_form', 'submit_success', '_attach_options_list'],
    'private_views.py': ['open_form', 'submit_form']
}

resplit_views_file('accounts', ACCOUNTS_MAPPING)
resplit_views_file('forms_engine', FORMS_ENGINE_MAPPING)

# Self-cleanup
manage_path = os.path.join(BASE_DIR, 'manage.py')
if os.path.exists(manage_path):
    with open(manage_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'import resplit_views\n' in content:
        content = content.replace('import resplit_views\n', '')
        with open(manage_path, 'w', encoding='utf-8') as f:
            f.write(content)
