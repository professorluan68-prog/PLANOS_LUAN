import os
import pdfplumber
import glob

pdf_dir = r"C:\Users\Luan Dias\Documents\PDF_AULAS\QUIMICA\EM\3_BIMESTRE\2_ANO"
pdfs = glob.glob(os.path.join(pdf_dir, "*.pdf"))

results = []
for pdf in pdfs:
    try:
        with pdfplumber.open(pdf) as p:
            primeira_pagina = p.pages[0].extract_text()
            linhas = primeira_pagina.split('\n')[:10]
            # Tentar achar "AULA X" ou título principal
            texto = " | ".join([linha.strip() for linha in linhas if linha.strip()])
            results.append((os.path.basename(pdf), texto))
    except Exception as e:
        results.append((os.path.basename(pdf), f"Erro: {e}"))

for name, text in results:
    print(f"{name}: {text[:150]}...")
