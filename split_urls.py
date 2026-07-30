import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URLS_FILE = os.path.join(BASE_DIR, 'accounts', 'urls.py')
URLS_DIR = os.path.join(BASE_DIR, 'accounts', 'urls')

if not os.path.exists(URLS_DIR):
    os.makedirs(URLS_DIR)

with open(URLS_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# We will split content based on the comments
# Example: # ==========================================
# ADMIN MODULE

sections = re.split(r'\n\s*# ==========================================\n\s*# (.*?)\n\s*# ==========================================\n', content)

header = sections[0]
admin_content = "from django.urls import path\nfrom . import views\n\nurlpatterns = [\n"
teacher_content = "from django.urls import path\nfrom . import views\n\nurlpatterns = [\n"
student_content = "from django.urls import path\nfrom . import views\n\nurlpatterns = [\n"
base_content = header

for i in range(1, len(sections), 2):
    title = sections[i].strip()
    body = sections[i+1]
    
    if 'ADMIN' in title or 'FORMS' in title or 'QR' in title:
        admin_content += body
    elif 'TEACHER' in title:
        teacher_content += body
    elif 'STUDENT' in title:
        student_content += body
    else:
        base_content += body

# Close the brackets and remove trailing commas if necessary, though it's python, trailing commas are fine.
# Wait, the last item in body might end without a bracket if the file ends.
if base_content.endswith(']'):
    pass # we can just let it be

# Let's not risk breaking urls.py with naive regex since it's an array.
# I will just write a simpler script: rename urls.py to base_urls.py, and import it from __init__.py.
