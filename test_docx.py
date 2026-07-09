import docx
doc = docx.Document(r'C:\Users\Luan Dias\PLANOS_LUAN\PLANOS_FEITOS\SILVANA_MARIANO\QUÍMICA\Plano_2_Ano_D_Quimica.in.docx')
with open('temp_docx_out.txt', 'w', encoding='utf-8') as f:
    for t in doc.tables:
        for row in t.rows:
            if len(row.cells) >= 6:
                f.write(' | '.join([c.text.replace('\n', ' ') for c in row.cells]) + '\n')
