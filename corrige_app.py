import sys
import re

app_path = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN\planos_luan_app.py'
with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'("Conferência\s+Mensal"\])', r'"Conferência Mensal", "PEI Inclusão"]', content)
content = re.sub(r'("Conferência Mensal"\])', r'"Conferência Mensal", "PEI Inclusão"]', content)

if 'modo_pei = modo_tela ==' not in content:
    content = re.sub(r'(modo_conferencia_mensal\s*=\s*modo_tela\s*==\s*"Conferência\s+Mensal")', r'\1\nmodo_pei = modo_tela == "PEI Inclusão"', content)

if 'if modo_pei:' not in content:
    content = re.sub(r'(if modo_conferencia_mensal:[^\n]+\n)', r'\1if modo_pei: _renderizar_pei(PROFESSORES_DB); st.stop()\n', content)

if 'def _renderizar_pei' not in content and 'from ui.pei import' not in content:
    content = content.replace('from ui.shared import (', 'from ui.pei import _renderizar_pei\nfrom ui.shared import (')

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)
