import os
import glob
from pathlib import Path

base_dir = Path(r"C:\Users\LuanDias\OneDrive\PLANOS_LUAN")
out_dir = base_dir / "ESTRUTURAS_SISTEMA_TXT"
out_dir.mkdir(exist_ok=True)

# Limpar o diretório se já existir
for f in out_dir.glob("*.txt"):
    f.unlink()

# Arquivos críticos que merecem um arquivo .txt exclusivo
arquivos_principais = [
    "planos_luan_app.py",
    "config.py",
    "core/database.py",
    "core/models.py",
    "core/engine.py",
    "core/ia.py",
    "core/ia_client.py",
    "core/gerador_pei.py",
    "core/leitor_lista_pei.py",
    "core/gestao_aulas.py",
    "core/calendario.py",
    "ui/pei.py",
    "ui/shared.py",
    "ui/historico.py",
    "ui/geracao_lote.py",
    "docx_generator/preencher.py",
    "docx_generator/preencher_cdp.py",
    "docx_generator/utils.py",
    "AGENTS.md",
    "GEMINI.md",
    "AUDITORIA_SISTEMA_2026-10-03.md",
    "core/lib/metodologia.py",
    "core/lib/progressao.py",
    "core/lib/extrator_pdf.py",
    "core/lib/classificador.py",
    "core/lib/higienizador_pedagogico.py"
]

# Total acima: 26 arquivos. Faltam 2 para 28.
# Vamos agrupar todo o resto da pasta "core/" em um "27_core_outros.txt"
# E todo o resto da pasta "ui/" em "28_ui_outros.txt"

def ler_arquivo(caminho_relativo):
    p = base_dir / caminho_relativo
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return f"\n\n{'='*50}\nARQUIVO: {caminho_relativo}\n{'='*50}\n" + f.read()
    return ""

# Exportar os 26 arquivos 1 para 1
for i, caminho in enumerate(arquivos_principais, 1):
    conteudo = ler_arquivo(caminho)
    if conteudo:
        nome_safe = caminho.replace("/", "_").replace("\\", "_").replace(".py", "").replace(".md", "")
        with open(out_dir / f"{i:02d}_{nome_safe}.txt", "w", encoding="utf-8") as out:
            out.write(conteudo)

# Exportar core_outros (tudo do core e subpastas que não está na lista)
core_outros = []
for p in base_dir.rglob("core/**/*.py"):
    rel = p.relative_to(base_dir).as_posix()
    if rel not in arquivos_principais:
        core_outros.append(rel)

with open(out_dir / "27_core_outros_agrupados.txt", "w", encoding="utf-8") as out:
    for rel in core_outros:
        out.write(ler_arquivo(rel))

# Exportar ui_outros (tudo do ui que não está na lista)
ui_outros = []
for p in base_dir.rglob("ui/**/*.py"):
    rel = p.relative_to(base_dir).as_posix()
    if rel not in arquivos_principais:
        ui_outros.append(rel)

with open(out_dir / "28_ui_outros_agrupados.txt", "w", encoding="utf-8") as out:
    for rel in ui_outros:
        out.write(ler_arquivo(rel))

print(f"Exportados {len(list(out_dir.glob('*.txt')))} arquivos .txt com sucesso!")
