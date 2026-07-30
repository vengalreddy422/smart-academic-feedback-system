import os
import sys
import traceback

def test_django_imports():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartacademic.settings')
    import django
    try:
        django.setup()
        with open('import_errors.txt', 'w', encoding='utf-8') as f:
            f.write("SUCCESS\n")
    except Exception as e:
        with open('import_errors.txt', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())

test_django_imports()
