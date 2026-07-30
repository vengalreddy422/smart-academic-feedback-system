import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEWS_FILE = os.path.join(BASE_DIR, 'accounts', 'views.py')
VIEWS_DIR = os.path.join(BASE_DIR, 'accounts', 'views')

if not os.path.exists(VIEWS_DIR):
    os.makedirs(VIEWS_DIR)

with open(VIEWS_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the imports to put at the top of each file
COMMON_IMPORTS = """from tracemalloc import start
from forms_engine.models import DynamicForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from accounts.models import User, StudentProfile, TeacherProfile, Department, Section
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from forms_engine.models import DynamicForm, FormQuestion, QuestionOption, FormResponse, PublicFormResponse, PublicFormAnswer, FormAnswer
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_protect
from collections import Counter
from io import BytesIO
import qrcode
from django.core.files import File
from functools import wraps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import update_session_auth_hash

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            user_role = getattr(request.user, 'role', None)
            if user_role not in roles:
                return HttpResponse('Unauthorized', status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

"""

# Define which functions belong to which file
FILE_MAPPING = {
    'auth_views.py': ['information_page', 'user_login', 'user_logout', 'UserPasswordChangeView'],
    'student_views.py': ['student_dashboard', 'completed_forms', 'upcoming_forms', 'pending_forms', 'expired_forms'],
    'teacher_views.py': ['teacher_dashboard', 'teacher_form_detail', 'student_response_detail', 'teacher_forms', 'active_forms', 'teacher_completed_forms', 'teacher_active_forms', 'teacher_upcoming_forms', 'teacher_students'],
    'admin_views.py': ['admin_dashboard', 'manage_users', 'teachers_list', 'students_list', 'add_student', 'edit_student', 'delete_student', 'add_teacher', 'edit_teacher', 'delete_teacher'],
    'form_management_views.py': ['private_forms', 'public_forms', 'public_form_qr', 'public_form_users', 'public_form_detail', 'edit_form', 'delete_form', 'add_question', 'get_form_questions', 'delete_question', 'delete_option', 'preview_form', 'public_active_forms', 'public_future_forms', 'public_expired_forms', 'public_forms_dashboard']
}

# Regex to split the file by function/class definitions
blocks = re.split(r'\n(?=@login_required|@csrf_protect|@role_required|def |class )', content)

files_content = {filename: COMMON_IMPORTS for filename in FILE_MAPPING.keys()}
files_content['__init__.py'] = ""

for block in blocks:
    block = block.strip()
    if not block: continue
    
    # Identify the function or class name
    match = re.search(r'(?:def|class)\s+([a-zA-Z0-9_]+)', block)
    if match:
        name = match.group(1)
        if name == 'role_required':
            continue # Already in COMMON_IMPORTS
            
        placed = False
        for filename, names in FILE_MAPPING.items():
            if name in names:
                files_content[filename] += "\n" + block + "\n"
                if f"from .{filename[:-3]} import *" not in files_content['__init__.py']:
                    files_content['__init__.py'] += f"from .{filename[:-3]} import *\n"
                placed = True
                break
        
        if not placed:
            print(f"Warning: {name} not mapped to any file! Adding to admin_views.py")
            files_content['admin_views.py'] += "\n" + block + "\n"
            if "from .admin_views import *" not in files_content['__init__.py']:
                files_content['__init__.py'] += f"from .admin_views import *\n"

# Write out the new files
for filename, text in files_content.items():
    path = os.path.join(VIEWS_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

# Backup and remove the old views.py
if os.path.exists(VIEWS_FILE):
    shutil.move(VIEWS_FILE, VIEWS_FILE + '.bak')
    
print("Successfully split views.py into accounts/views/ package!")
