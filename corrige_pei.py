import sys

app_path = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN\ui\pei.py'
with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('disciplina = ? AND bimestre = ?\n            ''\', conn, params=(professor, disciplina, f"{bimestre}º Bimestre"))', 'disciplina = ? AND bimestre = ?\n            ''\', conn, params=(professor, disciplina.upper(), f"{bimestre}º Bimestre"))')

content = content.replace('disciplina = ? AND bimestre = ? AND turma = ?\n        ''\', conn, params=(professor, disciplina, f"{bimestre}º Bimestre", turma_selecionada))', 'disciplina = ? AND bimestre = ? AND turma = ?\n        ''\', conn, params=(professor, disciplina.upper(), f"{bimestre}º Bimestre", turma_selecionada))')

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Consultas SQL corrigidas para uppercase na disciplina!")
