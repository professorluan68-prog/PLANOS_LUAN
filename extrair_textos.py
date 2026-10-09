import os
from docx import Document

auditorias_dir = r"C:\Users\LuanDias\OneDrive\PLANOS_LUAN_DADOS\AUDITORIAS"

def extract_docx_to_txt(docx_path, txt_path):
    if not os.path.exists(docx_path):
        print(f"Arquivo não encontrado: {docx_path}")
        return
    
    try:
        doc = Document(docx_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Extraído com sucesso: {txt_path}")
    except Exception as e:
        print(f"Erro ao extrair {docx_path}: {e}")

file1 = os.path.join(auditorias_dir, "Relatório Técnico e Arquitetural 360º.docx")
txt1 = os.path.join(auditorias_dir, "sparks_1.txt")

file2 = os.path.join(auditorias_dir, "AUDITORIA_TECNICA_360_PLANOS_LUAN.docx")
txt2 = os.path.join(auditorias_dir, "sparks_2.txt")

extract_docx_to_txt(file1, txt1)
extract_docx_to_txt(file2, txt2)

print("\nConcluído! O Antigravity agora pode ler os arquivos .txt")
