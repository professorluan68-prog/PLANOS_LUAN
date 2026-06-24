import os
import shutil

# Dicionário mapeando os caminhos relativos do projeto para as extensões de destino em D:\ESTRUTURAS_PLANOS_LUAN
# Alguns arquivos são copiados como '.py.txt' e também como '.txt'.
MAPPING = {
    "core/lib/acessibilidade.py": ["acessibilidade.py.txt", "acessibilidade.txt"],
    "core/lib/acessibilidade_perfis.py": ["acessibilidade_perfis.py.txt", "acessibilidade_perfis.txt"],
    "core/lib/acompanhamento.py": ["acompanhamento.py.txt", "acompanhamento.txt"],
    "core/lib/acompanhamento_perfis.py": ["acompanhamento_perfis.py.txt", "acompanhamento_perfis.txt"],
    "core/cdp_em_docx.py": ["cdp_em_docx.py.txt"],
    "core/cdp_legacy.py": ["cdp_legacy.py.txt"],
    "core/lib/classificador.py": ["classificador.py.txt", "classificador.txt"],
    "core/database.py": ["database.py.txt", "database.txt"],
    "core/disciplinas.py": ["disciplinas.py.txt"],
    "core/lib/extrator_pdf.py": ["extrator_pdf.py.txt"],
    "core/ia.py": ["ia.py.txt", "ia.txt"],
    "core/lote.py": ["lote.py.txt", "lote.txt"],
    "core/lib/metodologia.py": ["metodologia.py.txt", "metodologia.txt"],
    "docx_generator/preencher.py": ["preencher.py.txt"],
    "docx_generator/preencher_cdp.py": ["preencher_cdp.py.txt"],
    "core/professores_planos.py": ["professores_planos.py.txt"],
    "core/lib/progressao.py": ["progressao.py.txt"],
    "core/prompts_por_disciplina.py": ["prompts_por_disciplina.py.txt"],
    "core/qualidade_metodologica.py": ["qualidade_metodologica.py.txt"],
    "core/lib/tecnicas.py": ["tecnicas.py.txt"],
    "core/validador_plano.py": ["validador_plano.py.txt"]
}

SOURCE_DIR = r"d:\PLANOS_LUAN"
DEST_DIR = r"D:\ESTRUTURAS_PLANOS_LUAN"

def run_update():
    print(f"Iniciando a atualização das estruturas de {SOURCE_DIR} para {DEST_DIR}...")
    
    if not os.path.exists(DEST_DIR):
        print(f"Erro: O diretório de destino {DEST_DIR} não existe!")
        return

    copied_count = 0
    for rel_path, dest_filenames in MAPPING.items():
        src_path = os.path.join(SOURCE_DIR, rel_path.replace("/", os.sep))
        if not os.path.exists(src_path):
            print(f"Aviso: Arquivo de origem não encontrado: {src_path}")
            continue
            
        for dest_filename in dest_filenames:
            dest_path = os.path.join(DEST_DIR, dest_filename)
            try:
                # Copiar mantendo metadados ou conteúdo
                shutil.copy2(src_path, dest_path)
                print(f"Copiado: {rel_path} -> {dest_filename}")
                copied_count += 1
            except Exception as e:
                print(f"Erro ao copiar {rel_path} para {dest_filename}: {e}")
                
    print(f"\nAtualização concluída! Total de arquivos atualizados no destino: {copied_count}")

if __name__ == "__main__":
    run_update()
