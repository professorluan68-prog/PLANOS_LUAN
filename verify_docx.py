import docx

doc_path = r'C:\Users\LuanDias\PLANOS_LUAN_DADOS\PDF_AULAS\LIDERANCA_E_ORATORIA\EM\3_BIMESTRE\2_ANO\METODOLOGIA_LIDERANCA_E_ORATORIA_2_ANO_3_B.docx'
doc = docx.Document(doc_path)
for p in doc.paragraphs:
    if p.text.startswith(('Para começar:', 'Foco no conteúdo:', 'Na prática:', 'Encerramento:')):
        print(f'{p.text[:20]}... -> {len(p.text)}')
