import re

app_path = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN\planos_luan_app.py'
with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove anything between ======= and >>>>>>> inclusive
content = re.sub(r'=======\n.*?>>>>>>> [a-f0-9]+\n', '', content, flags=re.DOTALL)
# Remove <<<<<<< HEAD markers
content = re.sub(r'<<<<<<< HEAD\n', '', content)

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)
