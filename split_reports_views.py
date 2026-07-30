import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEWS_FILE = os.path.join(BASE_DIR, 'reports', 'views.py')
VIEWS_DIR = os.path.join(BASE_DIR, 'reports', 'views')

if not os.path.exists(VIEWS_DIR):
    os.makedirs(VIEWS_DIR)

with open(VIEWS_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

COMMON_IMPORTS = """from urllib import request
from django.shortcuts import get_object_or_404
from openpyxl import Workbook
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import styles
from accounts.models import TeacherProfile, StudentProfile
from forms_engine.models import DynamicForm, FormQuestion, FormResponse, FormAnswer, PublicFormResponse, PublicFormAnswer
from reports.exports.identified.summary_excel import export_identified_summary_excel
from reports.exports.identified.detailed_pdf import export_identified_detailed_pdf
from reports.exports.anonymous.detailed_pdf import export_anonymous_detailed_pdf
import openpyxl

"""

FILE_MAPPING = {
    'excel_exports.py': ['identified_summary_excel'],
    'pdf_exports.py': ['identified_detailed_pdf', 'anonymous_detailed_pdf']
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
