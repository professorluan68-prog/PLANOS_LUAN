import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
from pathlib import Path
import re

def process_guia(pdf_path, output_pdf_dir, output_excel_base_dir, is_em=False):
    pdf_path = Path(pdf_path)
    output_pdf_dir = Path(output_pdf_dir)
    output_pdf_dir.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    
    # Mapping of series to list of page numbers
    pages_by_serie = {}
    
    for i in range(len(doc)):
        page = doc.load_page(i)
        text = page.get_text().upper()
        
        # Find which serie it belongs to
        serie = None
        if is_em:
            if "1ªSÉRIE" in text or "1ª SÉRIE" in text or "1º ANO" in text:
                serie = "1_ANO"
            elif "2ªSÉRIE" in text or "2ª SÉRIE" in text or "2º ANO" in text:
                serie = "2_ANO"
            elif "3ªSÉRIE" in text or "3ª SÉRIE" in text or "3º ANO" in text:
                serie = "3_ANO"
        else:
            if "6º ANO" in text or "6ºANO" in text:
                serie = "6_ANO"
            elif "7º ANO" in text or "7ºANO" in text:
                serie = "7_ANO"
            elif "8º ANO" in text or "8ºANO" in text:
                serie = "8_ANO"
            elif "9º ANO" in text or "9ºANO" in text:
                serie = "9_ANO"
                
        if serie:
            if serie not in pages_by_serie:
                pages_by_serie[serie] = []
            pages_by_serie[serie].append(i)
            
    print(f"[{pdf_path.name}] Found series mapping:", {k: len(v) for k, v in pages_by_serie.items()})
    
    # Now create new PDFs and extract tables
    for serie, pages in pages_by_serie.items():
        if not pages: continue
        
        # 1. Create PDF part
        new_pdf_path = output_pdf_dir / f"GUIA_{serie}_3_BIMESTRE.pdf"
        new_doc = fitz.open()
        for p in pages:
            new_doc.insert_pdf(doc, from_page=p, to_page=p)
        new_doc.save(new_pdf_path)
        new_doc.close()
        print(f"Created PDF part: {new_pdf_path}")
        
        # 2. Extract tables from this new PDF
        all_rows = []
        headers = None
        
        with pdfplumber.open(new_pdf_path) as pdf_plumb:
            for page in pdf_plumb.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table: continue
                    
                    # Remove empty columns if they exist
                    clean_table = []
                    for row in table:
                        clean_row = [str(cell).strip() if cell else "" for cell in row]
                        clean_table.append(clean_row)
                    
                    first_row = clean_table[0]
                    
                    if "AULA" in str(first_row[0]).upper():
                        headers = first_row
                        rows = clean_table[1:]
                    else:
                        rows = clean_table
                        
                    for row in rows:
                        if len(row) > 0 and str(row[0]).strip().isdigit():
                            all_rows.append(row)
        
        if not all_rows:
            print(f"  WARNING: No tables found for {serie}")
            continue
            
        if not headers or len(headers) < 6:
            headers = ['AULA', 'TÍTULO', 'Conteúdo', 'Objetivos de aprendizagem', 'Habilidades', 'Aprendizagem Essencial']
            
        df = pd.DataFrame(all_rows, columns=headers[:len(all_rows[0])])
        
        # 3. Save Excel
        out_excel_dir = Path(output_excel_base_dir) / serie
        out_excel_dir.mkdir(parents=True, exist_ok=True)
        
        out_excel_file = out_excel_dir / f"GUIA_{serie}_3_BIMESTRE.xlsx"
        df.to_excel(out_excel_file, index=False)
        print(f"  Saved Excel: {out_excel_file}")

# Process AF
print("=== Processing AF ===")
process_guia(
    "D:/GUIA_PRIORIZADO/MATEMÁTICA_AF/MAT_AF_3_BIMESTRE.pdf",
    "D:/GUIA_PRIORIZADO/MATEMÁTICA_AF/3_BIMESTRE",
    "D:/PDF novos/MATEMATICA/AF/3_BIMESTRE",
    is_em=False
)

# Process EM
print("=== Processing EM ===")
process_guia(
    "D:/GUIA_PRIORIZADO/MATEMÁTICA_EM/MAT_EM_3_BIMESTRE.pdf",
    "D:/GUIA_PRIORIZADO/MATEMÁTICA_EM/3_BIMESTRE",
    "D:/PDF novos/MATEMATICA/EM/3_BIMESTRE",
    is_em=True
)

print("Done!")
