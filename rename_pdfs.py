import os
import pdfplumber
import glob
import re

pdf_dir = r"C:\Users\Luan Dias\Documents\PDF_AULAS\QUIMICA\EM\3_BIMESTRE\2_ANO"
pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf"))

to_rename = []

for pdf in pdfs:
    try:
        with pdfplumber.open(pdf) as p:
            primeira_pagina = p.pages[0].extract_text()
            match = re.search(r'Aula\s+(\d+)', primeira_pagina, re.IGNORECASE)
            if match:
                numero = int(match.group(1))
                novo_nome = f"AULA {numero}.pdf"
                novo_caminho = os.path.join(pdf_dir, novo_nome)
                to_rename.append((pdf, novo_caminho))
    except Exception as e:
        print(f"Erro em {os.path.basename(pdf)}: {e}")

# Agora que todos os PDFs estão fechados, renomeamos
for pdf, novo_caminho in to_rename:
    novo_nome = os.path.basename(novo_caminho)
    try:
        if not os.path.exists(novo_caminho):
            os.rename(pdf, novo_caminho)
            print(f"Renomeou: {os.path.basename(pdf)} -> {novo_nome}")
        else:
            print(f"O arquivo {novo_nome} já existe. Ignorando {os.path.basename(pdf)}.")
    except Exception as e:
        print(f"Erro ao renomear {os.path.basename(pdf)}: {e}")
