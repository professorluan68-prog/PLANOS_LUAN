import os
import shutil

src_dir = r"C:\Users\Luan Dias\Documents\PDF_AULAS\QUIMICA\EM\3_BIMESTRE\2_ANO"
dest_dir = r"C:\Users\Luan Dias\PLANOS_LUAN\Alteracoes_remover\QUIMICA_EM_3B_2ANO_PDFS"

# Criar a pasta de destino
os.makedirs(dest_dir, exist_ok=True)

map_arquivos = {
    "1650794.pdf": "AULA 1.pdf",
    "1650799.pdf": "AULA 2.pdf",
    "1650812.pdf": "AULA 3.pdf",
    "1619453.pdf": "AULA 4.pdf",
    "1650829.pdf": "AULA 5.pdf",
    "1650852.pdf": "AULA 6.pdf",
    "1650865.pdf": "AULA 7.pdf",
    "1650870.pdf": "AULA 8.pdf",
    "1650880.pdf": "AULA 9.pdf",
    "1650888.pdf": "AULA 10.pdf",
    "1650906.pdf": "AULA 11.pdf",
    "1650925.pdf": "AULA 12.pdf"
}

for velho, novo in map_arquivos.items():
    src_path = os.path.join(src_dir, velho)
    dest_path = os.path.join(dest_dir, novo)
    
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"Copiado: {velho} -> {novo}")
    else:
        print(f"Aviso: Arquivo {velho} não encontrado na origem.")

print(f"\nTodos os arquivos foram copiados e renomeados para: {dest_dir}")
