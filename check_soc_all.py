import docx

doc_path = r'C:\Users\LuanDias\PLANOS_LUAN_DADOS\PDF_AULAS\SOCIOLOGIA\EM\3_BIMESTRE\1_ANO_2_ANO_3_ANO\METODOLOGIA_CDP_ENSINO_MEDIO_MULTISSERIADO_J_3_B.docx'
doc = docx.Document(doc_path)
for p in doc.paragraphs:
    if p.text.startswith(('Para começar:', 'Foco no conteúdo:', 'Pause e responda:', 'Na prática:', 'Encerramento:')):
        print(f'{p.text[:20]}... -> {len(p.text)}')
