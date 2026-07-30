import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resplit_admin_file(app_name):
    BAK_FILE = os.path.join(BASE_DIR, app_name, 'admin.py.bak')
    ADMIN_DIR = os.path.join(BASE_DIR, app_name, 'admin')

    if not os.path.exists(BAK_FILE):
        return

    # Clear existing broken directory
    if os.path.exists(ADMIN_DIR):
        shutil.rmtree(ADMIN_DIR)
    os.makedirs(ADMIN_DIR)

    with open(BAK_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    common_imports = []
    blocks = []
    current_block = []
    
    in_imports = True
    
    for line in lines:
        if in_imports:
            # We assume imports end when we see the first class or @admin
            if line.startswith('class ') or line.startswith('@admin.register') or line.startswith('# ==='):
                in_imports = False
            else:
                common_imports.append(line)
                continue
                
        if line.startswith('@admin.register') or (line.startswith('class ') and not any(l.startswith('@admin.register') for l in current_block)):
            if current_block:
                blocks.append("".join(current_block))
            current_block = [line]
        else:
            current_block.append(line)
            
    if current_block:
        blocks.append("".join(current_block))

    common_imports_text = "".join(common_imports).strip()

    init_content = ""
    for block_text in blocks:
        block_text = block_text.strip()
        if not block_text: continue
        
        match = re.search(r'class\s+([a-zA-Z0-9_]+)', block_text)
        if match:
            class_name = match.group(1)
            file_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower() + ".py"
            
            # Fix imports for accounts package
            fixed_block = block_text
            fixed_imports = common_imports_text.replace('from .models', f'from {app_name}.models').replace('from .forms', f'from {app_name}.forms')
            
            with open(os.path.join(ADMIN_DIR, file_name), 'w', encoding='utf-8') as f:
                f.write(fixed_imports + "\n\n" + fixed_block + "\n")
                
            init_content += f"from .{file_name[:-3]} import *\n"

    with open(os.path.join(ADMIN_DIR, '__init__.py'), 'w', encoding='utf-8') as f:
        f.write(init_content)

resplit_admin_file('accounts')
resplit_admin_file('forms_engine')
