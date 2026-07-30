import os

with open(r'e:\SMART_ACADEMIC_SYSTEM\SMART_ACADEMIC_SYSTEM\requirements.txt', 'r', encoding='utf-16le') as f:
    content = f.read()

with open(r'e:\SMART_ACADEMIC_SYSTEM\SMART_ACADEMIC_SYSTEM\requirements_utf8.txt', 'w', encoding='utf-8') as f:
    f.write(content)
