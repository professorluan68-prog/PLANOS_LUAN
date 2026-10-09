import os

target_dir = r"C:\Users\LuanDias\OneDrive\PLANOS_LUAN_DADOS\AUDITORIAS"
if os.path.exists(target_dir):
    files = os.listdir(target_dir)
    with open(r"C:\Users\LuanDias\OneDrive\PLANOS_LUAN_DADOS\AUDITORIAS\arquivos.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(files))
    print(f"Arquivos salvos em arquivos.txt: {files}")
else:
    print("Diretório não encontrado.")
