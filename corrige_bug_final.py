import sys

app_path = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN\planos_luan_app.py'
with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if 'modo_conferencia_mensal =' in line and 'modo_tela ==' in line:
        if 'modo_pei = modo_tela ==' not in ''.join(lines):
            new_lines.append('modo_pei = modo_tela == "PEI Inclusão"\n')

with open(app_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
