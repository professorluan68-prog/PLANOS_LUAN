import os
from pathlib import Path

# ==========================================
# DOCUMENTACAO E CONFIGURACAO DE CAMINHOS
# ==========================================

# 1. Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent

# 2. Caminhos de trabalho externos (com fallback se D: não existir)
_D_DRIVE_EXISTS = Path(r"D:\\").exists()

PASTA_PRINCIPAL_TRABALHO = Path(r"D:\PLANOS DE JUNHO") if _D_DRIVE_EXISTS else BASE_DIR / "planos_de_junho"
PASTA_BACKUP = Path(r"D:\BACKUPS_PLANOS_LUAN") if _D_DRIVE_EXISTS else BASE_DIR / "backups_planos_luan"

# 3. Compatibilidade com o sistema existente
PASTA_PLANOS_PROFESSORES = Path(
    os.getenv("PLANOS_DIR", str(PASTA_PRINCIPAL_TRABALHO))
)
TEMPLATES_DOCX_DIR = BASE_DIR / "templates"
LEGACY_PLANOS_FEITOS_DIR = BASE_DIR / "Planos feitos"
MODELOS_LEGADOS_QUARENTENA_DIR = (
    PASTA_PLANOS_PROFESSORES / "_MODELOS_LEGADOS_PARA_EXCLUIR"
)

_padrao_finalizados = r"D:\PLANOS-FINALIZADOS" if _D_DRIVE_EXISTS else str(BASE_DIR / "planos_finalizados")
PLANOS_FINALIZADOS_DIR = Path(
    os.getenv("PLANOS_FINALIZADOS_DIR", _padrao_finalizados)
)
DB_PATH = BASE_DIR / "planos_luan.db"

# Arquivos de dados especificos
ESCOPO_PROJETO_VIDA_PATH = BASE_DIR / "EM Escopo-sequencia 2026 (1).ods"

# 4. Configuracoes de Inteligencia Artificial
MODELO_OPENAI_PADRAO = "gpt-4o-mini"
MODELO_GEMINI_PADRAO = "gemini-2.5-flash"
IA_TIMEOUT_SEGUNDOS = 120

# 5. Limites e regras de leitura
PDF_TEXTO_LIMITE_CHARS = 100000
MAX_CHARS_WORD = 15000

# 6. Criacao automatica de pastas
def inicializar_pastas():
    os.makedirs(PLANOS_FINALIZADOS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DOCX_DIR, exist_ok=True)
    os.makedirs(PASTA_BACKUP, exist_ok=True)

