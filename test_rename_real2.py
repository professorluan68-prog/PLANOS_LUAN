import os
import re
import unicodedata
import pdfplumber
import glob

def clean_filename(name):
    # Remove accents
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    # Remove invalid characters
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def process_directory(dir_path):
    print(f"Processing directory: {dir_path}")
    pdf_files = glob.glob(os.path.join(dir_path, "*.pdf"))
    for pdf_path in pdf_files:
        if "AULA_" in os.path.basename(pdf_path):
            continue
            
        new_name = None
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
                    if 'Lngua Portuguesa' in line or 'Língua Portuguesa' in line or 'Lngua Portuguesa' in line:
                        started = True
                        continue
                    if 'bimestre' in line.lower() or 'Ensino' in line:
                        break
                    if started and line.strip():
                        title_lines.append(line.strip())
                
                if not title_lines and len(lines) > 1:
                    title_lines = [lines[1]]
                
                title = " - ".join(title_lines)
                
                # Replace the missing character representation explicitly if present
                title = title.replace('\ufffd', '-')
                
                title = clean_filename(title)
                # Replace multiple dashes or spaces
                title = re.sub(r'\s+', ' ', title)
                title = re.sub(r'-\s*-', '-', title)
                title = title.strip(' -')
                
                new_name = f"{aula_str} - {title}.pdf"
                
        except Exception as e:
            print(f"Error extracting {pdf_path}: {e}")
            
        if new_name:
            try:
                new_path = os.path.join(dir_path, new_name)
                print(f"{os.path.basename(pdf_path)} -> {new_name}")
                os.rename(pdf_path, new_path)
            except Exception as e:
                print(f"Error renaming {pdf_path}: {e}")

base_dir = r"D:\PDF novos\LINGUA_PORTUGUESA\EM\3_BIMESTRE"
for folder in ["1_ANO", "2_ANO", "3_ANO"]:
    process_directory(os.path.join(base_dir, folder))
