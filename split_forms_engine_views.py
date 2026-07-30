import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEWS_FILE = os.path.join(BASE_DIR, 'forms_engine', 'views.py')
VIEWS_DIR = os.path.join(BASE_DIR, 'forms_engine', 'views')

if not os.path.exists(VIEWS_DIR):
    os.makedirs(VIEWS_DIR)

with open(VIEWS_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

COMMON_IMPORTS = """from email import errors
from urllib import request
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from accounts.models import StudentProfile
from forms_engine.models import DynamicForm, FormAnswer, FormQuestion, FormResponse, PublicFormAnswer, PublicFormResponse
from forms_engine.field_registry import validate_field

def _attach_options_list(questions):
    for question in questions:
        question.options_list = question.question_options.all().order_by('id')
    return questions

"""

FILE_MAPPING = {
    'form_rendering.py': ['open_form'],
    'form_submission.py': ['submit_form', 'public_form']
}

blocks = re.split(r'\n(?=@login_required|def )', content)

files_content = {filename: COMMON_IMPORTS for filename in FILE_MAPPING.keys()}
files_content['__init__.py'] = ""

for block in blocks:
    block = block.strip()
    if not block: continue
    
    match = re.search(r'def\s+([a-zA-Z0-9_]+)', block)
    if match:
        name = match.group(1)
        if name == '_attach_options_list':
            continue
            
        for filename, names in FILE_MAPPING.items():
            if name in names:
                files_content[filename] += "\n" + block + "\n"
                files_content['__init__.py'] += f"from .{filename[:-3]} import *\n"
                break

for filename, text in files_content.items():
    path = os.path.join(VIEWS_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

if os.path.exists(VIEWS_FILE):
    shutil.move(VIEWS_FILE, VIEWS_FILE + '.bak')
