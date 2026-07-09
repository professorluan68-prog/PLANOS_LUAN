import os
import json
from docx import Document

bio_path = r"C:\Users\Luan Dias\PLANOS_LUAN\PLANOS_FEITOS\SILVANA_MARIANO\BIOLOGIA\Plano_2o_ANO_B_Biologia_In.docx"

def fallback_extract(doc_path):
    doc = Document(doc_path)
    textos = []
    for table in doc.tables:
        for i, row in enumerate(table.rows):
            if len(row.cells) > 0:
                for cell in row.cells:
                    if len(cell.text) > 200:
                        if cell.text not in textos:
                            textos.append(cell.text)
    return textos

results = {"biologia": []}

bio_texts = fallback_extract(bio_path)
for t in bio_texts:
    if "min" in t.lower() or "etapa" in t.lower():
        words = len(t.split())
        chars = len(t)
        results["biologia"].append({"chars": chars, "words": words, "exemplo": t[:100]})

with open("tamanhos.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
