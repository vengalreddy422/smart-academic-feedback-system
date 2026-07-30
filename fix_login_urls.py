import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIEWS_DIRS = [
    os.path.join(BASE_DIR, 'accounts', 'views'),
    os.path.join(BASE_DIR, 'forms_engine', 'views')
]

for d in VIEWS_DIRS:
    if not os.path.exists(d): continue
    for filename in os.listdir(d):
        if not filename.endswith('.py'): continue
        
        filepath = os.path.join(d, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        modified = False
        if "redirect('user_login')" in content:
            content = content.replace("redirect('user_login')", "redirect('login')")
            modified = True
        
        if "login_url='user_login'" in content:
            content = content.replace("login_url='user_login'", "login_url='login'")
            modified = True
            
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

print("Fixed login URLs!")
