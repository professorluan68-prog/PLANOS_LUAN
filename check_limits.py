import docx

doc_path = r'C:\Users\LuanDias\PLANOS_LUAN_DADOS\PDF_AULAS\HISTÓRIACDP\EM\1_2_3_ANO\METODOLOGIA_HISTORIACDP_1_2_3_ANO_3_B.docx'
doc = docx.Document(doc_path)

prefixes = ['Para começar:', 'Foco no conteúdo:', 'Na prática:', 'Encerramento:']
for i, p in enumerate(doc.paragraphs):
    if any(p.text.startswith(prefix) for prefix in prefixes):
        if len(p.text) > 350:
            print(f"ALERTA: Linha {i+1} com {len(p.text)} caracteres -> {p.text}")
print("Verificação concluída!")
