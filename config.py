import os
from pathlib import Path

# ==========================================
# DOCUMENTAÇÃO E CONFIGURAÇÃO DE CAMINHOS
# ==========================================

# 1. Caminho Base do Projeto
BASE_DIR = Path(__file__).resolve().parent

# 2. Caminhos de Trabalho Externos (Centralizados)
PASTA_PRINCIPAL_TRABALHO = Path(r"D:\PLANOS DE JUNHO")
PASTA_BACKUP = Path(r"D:\BACKUPS_PLANOS_LUAN")

# 3. Compatibilidade com o sistema existente
PASTA_PLANOS_PROFESSORES = Path(
    os.getenv("PLANOS_DIR", str(PASTA_PRINCIPAL_TRABALHO))
)
TEMPLATES_DOCX_DIR = BASE_DIR / "templates"
LEGACY_PLANOS_FEITOS_DIR = BASE_DIR / "Planos feitos"
MODELOS_LEGADOS_QUARENTENA_DIR = PASTA_PLANOS_PROFESSORES / "_MODELOS_LEGADOS_PARA_EXCLUIR"
PLANOS_FINALIZADOS_DIR = Path(
    os.getenv("PLANOS_FINALIZADOS_DIR", r"D:\PLANOS-FINALIZADOS")
)
DB_PATH = BASE_DIR / "core" / "planos_luan.db"

# Arquivos de dados específicos
ESCOPO_PROJETO_VIDA_PATH = BASE_DIR / "EM Escopo-sequência 2026 (1).ods"

# 4. Configurações de Inteligência Artificial
MODELO_OPENAI_PADRAO = "gpt-4o-mini"
MODELO_GEMINI_PADRAO = "gemini-1.5-flash"
IA_TIMEOUT_SEGUNDOS = 120

# 5. Limites e Regras de Leitura
PDF_TEXTO_LIMITE_CHARS = 100000
MAX_CHARS_WORD = 15000

# 6. Criação Automática de Pastas
os.makedirs(PLANOS_FINALIZADOS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DOCX_DIR, exist_ok=True)
os.makedirs(PASTA_BACKUP, exist_ok=True)

print(f"[CONFIG] Definições carregadas. Pasta principal: {PASTA_PRINCIPAL_TRABALHO}")
