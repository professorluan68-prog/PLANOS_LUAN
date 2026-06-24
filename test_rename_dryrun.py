import os
import re
import pdfplumber
import glob

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def process_directory(dir_path):
    print(f"Processing directory: {dir_path}")
    pdf_files = glob.glob(os.path.join(dir_path, "*.pdf"))
    for pdf_path in pdf_files[:3]:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = pdf.pages[0].extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                
                aula_match = re.search(r'Aula\s+(\d+)', text, re.IGNORECASE)
                if not aula_match:
                    print(f"[{os.path.basename(pdf_path)}] NO AULA FOUND")
                    continue
                
                aula_num = int(aula_match.group(1))
                aula_str = f"AULA_{aula_num:02d}"
                
                title_lines = []
                started = False
                for line in lines:
                    # Ignore the subject line
                    if 'Língua Portuguesa' in line or 'Lngua Portuguesa' in line or 'Lngua Portuguesa' in line:
                        started = True
                        continue
                    if 'bimestre' in line.lower() or 'Ensino' in line:
                        break
                    if started and line.strip():
                        title_lines.append(line.strip())
                
                if not title_lines and len(lines) > 1:
                    title_lines = [lines[1]]
                
                title = " - ".join(title_lines)
                title = clean_filename(title)
                
                new_name = f"{aula_str} - {title}.pdf"
                print(f"{os.path.basename(pdf_path)} -> {new_name}")
                
        except Exception as e:
            print(f"Error {pdf_path}: {e}")

base_dir = r"D:\PDF novos\LINGUA_PORTUGUESA\AF\3_BIMESTRE"
for folder in ["6_ANO", "7_ANO", "8_ANO", "9_ANO"]:
    process_directory(os.path.join(base_dir, folder))
