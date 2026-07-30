import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def fix_imports_in_dir(directory, package_name):
    if not os.path.exists(directory):
        return
        
    for filename in os.listdir(directory):
        if filename.endswith('.py') and filename != '__init__.py':
            path = os.path.join(directory, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Replace 'from .models' with 'from accounts.models' etc
            new_content = content.replace('from .models', f'from {package_name}.models')
            new_content = new_content.replace('from .forms', f'from {package_name}.forms')
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)

fix_imports_in_dir(os.path.join(BASE_DIR, 'accounts', 'admin'), 'accounts')
fix_imports_in_dir(os.path.join(BASE_DIR, 'forms_engine', 'admin'), 'forms_engine')
