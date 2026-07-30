import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def split_admin_file(app_name):
    ADMIN_FILE = os.path.join(BASE_DIR, app_name, 'admin.py')
    ADMIN_DIR = os.path.join(BASE_DIR, app_name, 'admin')

    if not os.path.exists(ADMIN_FILE):
        return

    if not os.path.exists(ADMIN_DIR):
        os.makedirs(ADMIN_DIR)

    with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = re.split(r'\n(?=@admin\.register|class )', content)
    
    common_imports = blocks[0]
    
    init_content = ""
    for idx, block in enumerate(blocks[1:]):
        block = block.strip()
        if not block: continue
        
        match = re.search(r'class\s+([a-zA-Z0-9_]+)', block)
        if match:
            class_name = match.group(1)
            # e.g., StudentProfileAdmin -> student_profile_admin.py
            file_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower() + ".py"
            
            with open(os.path.join(ADMIN_DIR, file_name), 'w', encoding='utf-8') as f:
                f.write(common_imports + "\n\n" + block + "\n")
                
            init_content += f"from .{file_name[:-3]} import *\n"

    with open(os.path.join(ADMIN_DIR, '__init__.py'), 'w', encoding='utf-8') as f:
        f.write(init_content)

    shutil.move(ADMIN_FILE, ADMIN_FILE + '.bak')

split_admin_file('accounts')
split_admin_file('forms_engine')
