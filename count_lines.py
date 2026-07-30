import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

counts = []
for root, dirs, files in os.walk(BASE_DIR):
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    counts.append((lines, os.path.relpath(path, BASE_DIR)))
            except Exception:
                pass

counts.sort(reverse=True)
with open(os.path.join(BASE_DIR, 'line_counts.txt'), 'w', encoding='utf-8') as f:
    for lines, path in counts:
        f.write(f"{lines} : {path}\n")
