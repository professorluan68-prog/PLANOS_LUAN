import os
import json
import docx
import pdfplumber
import glob

pdf_base_dir = r"D:\PDF novos\PROJETO_DE_VIDA"
doc_base_dir = r"D:\PLANOS-FINALIZADOS\AGOSTO\DANIELA CRISTINA AMARAL\Projeto de Vida"

grades_map = {
    "Aprof. Geo 3_ANO": r"APROFUNDAMENTO_EM_GEOGRAFIA\EM\3_BIMESTRE\3_ANO",
    "Geo 2_ANO": r"GEOGRAFIA\EM\3_BIMESTRE\2_ANO"
}
pdf_base_dir = r"D:\PDF novos"

def extract_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    return text

with open("scratch/analysis_report.md", "w", encoding="utf-8") as f:
    for grade_key, rel_path in grades_map.items():
        f.write(f"# Grade: {grade_key}\n")
        
        pdf_dir = os.path.join(pdf_base_dir, rel_path)
        if not os.path.exists(pdf_dir):
            f.write(f"PDF directory not found: {pdf_dir}\n\n")
            continue
            
        json_files = sorted(glob.glob(os.path.join(pdf_dir, "*.json")))
        
        f.write(f"Found {len(json_files)} lessons.\n\n")
        
        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as jfile:
                    data = json.load(jfile)
            except:
                with open(jf, "r", encoding="latin1") as jfile:
                    data = json.load(jfile)
            
            aula_num = data.get("numero_aula", "?")
            f.write(f"## Aula {aula_num}: {data.get('tema', '')}\n")
            f.write("### Extraído (DOCX/JSON):\n")
            
            # extract methodology properly
            metodologia = data.get("diagnostico_geracao", {}).get("metodologia_final", [])
            if not metodologia: metodologia = data.get("metodologia", [])
            metodologia_text = "\n".join([f"- **{m.get('titulo', '')}**: {m.get('texto', '')}" for m in metodologia])
            
            f.write(f"**Desenvolvimento:**\n{metodologia_text}\n")
            f.write(f"**Acompanhamento:** {data.get('acompanhamento', '')}\n")
            f.write(f"**Acessibilidade:** {data.get('acessibilidade', '')}\n\n")
            
            # Extract PDF text
            pdf_path = jf.replace(".json", ".pdf")
            if os.path.exists(pdf_path):
                f.write(f"### PDF Text:\n```\n{extract_pdf_text(pdf_path)}\n```\n\n")
            else:
                f.write("PDF not found.\n\n")
            
