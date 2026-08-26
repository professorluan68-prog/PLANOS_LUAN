import docx
import os
import glob
import re

base_dir = r'C:\Users\LuanDias\OneDrive\PLANOS_LUAN_DADOS\PDF_AULAS\ARTE'
files = glob.glob(os.path.join(base_dir, 'Metodologias_Arte_*_Ano_Ensino_Fundamental.docx'))

for filepath in files:
    filename = os.path.basename(filepath)
    print(f'Processando {filename}...')
    
    # Extrair ano do nome do arquivo
    match = re.search(r'Arte_(\d+)_Ano', filename)
    if not match:
        continue
    ano = match.group(1)
    
    doc = docx.Document(filepath)
    modificado = False
    
    # Expressão regular para encontrar [Texto] e substituir por Texto: no início ou meio
    padrao = re.compile(r'\[(.*?)\]')
    
    for para in doc.paragraphs:
        if padrao.search(para.text):
            # Limpar formatações anteriores e refazer o texto
            # É mais seguro substituir texto diretamente no run se estiver contido,
            # ou limpar o parágrafo e reconstruir (mais fácil se formatação fina não for crítica)
            novo_texto = padrao.sub(r'\1:', para.text)
            para.text = novo_texto
            modificado = True
            
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if padrao.search(para.text):
                        novo_texto = padrao.sub(r'\1:', para.text)
                        para.text = novo_texto
                        modificado = True
                        
    if modificado:
        target_dir = os.path.join(base_dir, 'AF', '3_BIMESTRE', f'{ano}_ANO')
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        target_path = os.path.join(target_dir, filename)
        doc.save(target_path)
        print(f'Salvo em: {target_path}')
        os.remove(filepath)
    else:
        print('Nenhuma modificação necessária.')

