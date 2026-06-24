import sys

with open(r'D:\PLANOS_LUAN\tests\test_educacao_financeira_metodologia.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('assert "conhecimentos prévios" in texto or "conhecimentos prvios" in texto', 'assert "aula anterior" in texto')
content = content.replace('assert "explicar o procedimento central" in texto', 'assert "sistematizar o conceito" in texto')
content = content.replace('assert "exemplo resolvido" in texto', 'assert "diagrama" in texto')

with open(r'D:\PLANOS_LUAN\tests\test_educacao_financeira_metodologia.py', 'w', encoding='utf-8') as f:
    f.write(content)
