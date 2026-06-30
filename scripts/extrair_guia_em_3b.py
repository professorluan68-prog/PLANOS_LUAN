import pdfplumber
import pandas as pd
from pathlib import Path

# Paths
source_dir = Path("D:/GUIA_PRIORIZADO/PORTUGUÊS_EM/3_BIMESTRE")
dest_base = Path("D:/PDF novos/LINGUA_PORTUGUESA/EM/3_BIMESTRE")

# PDF mapping
pdfs = {
    "1_ANO": source_dir / "GUIA_1_ANO_3_BIMESTRE_1_a_4.pdf",
    "2_ANO": source_dir / "GUIA_2_ANO_3_BIMESTRE_5_a_8.pdf",
    "3_ANO": source_dir / "GUIA_3_ANO_3_BIMESTRE_9_a_12.pdf",
}

for serie, pdf_path in pdfs.items():
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        continue
    
    print(f"Processing {pdf_path.name}...")
    all_rows = []
    headers = None
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                
                # Check if first row is header
                first_row = table[0]
                if "Aula" in str(first_row[0]) or "Conteúdo" in str(first_row[2]):
                    headers = first_row
                    rows = table[1:]
                else:
                    rows = table
                    
                for row in rows:
                    if len(row) > 0 and str(row[0]).strip().isdigit():
                        all_rows.append(row)
    
    if not all_rows:
        print(f"No valid rows found in {pdf_path.name}")
        continue
        
    # Standard headers that the system expects
    # In AF, headers were: ['AULA', 'TÍTULO', 'Conteúdo', 'Objetivos de aprendizagem', 'Habilidades', 'Aprendizagem Essencial', ...]
    # We will use exactly what we extract from the PDF, with AE at the end.
    
    # Let's define headers based on the first extracted header, or fallback to default
    if not headers or len(headers) < 6:
        headers = ['AULA', 'TÍTULO', 'Conteúdo', 'Objetivos de aprendizagem', 'Habilidades', 'Aprendizagem Essencial']
        
    df = pd.DataFrame(all_rows, columns=headers[:len(all_rows[0])])
    
    # Save to the specific dest folder
    out_dir = dest_base / serie
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = out_dir / f"GUIA_{serie}_3_BIMESTRE.xlsx"
    df.to_excel(out_file, index=False)
    print(f"Saved {out_file}")

print("Done!")
