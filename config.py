import os
from pathlib import Path

# ==========================================
# DOCUMENTACAO E CONFIGURACAO DE CAMINHOS
# ==========================================

# 1. Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent

# 2. Caminhos de trabalho externos (com fallback se D: não existir)
_D_DRIVE_EXISTS = Path(r"D:\\").exists()

PASTA_PRINCIPAL_TRABALHO = Path(os.getenv("PLANOS_TRABALHO_DIR", r"D:\PLANOS DE JUNHO" if _D_DRIVE_EXISTS else str(BASE_DIR / "planos_de_junho")))
PASTA_BACKUP = Path(os.getenv("PLANOS_BACKUP_DIR", r"D:\BACKUPS_PLANOS_LUAN" if _D_DRIVE_EXISTS else str(BASE_DIR / "backups_planos_luan")))

# 3. Compatibilidade com o sistema existente
PASTA_PLANOS_PROFESSORES = Path(
    os.getenv("PLANOS_DIR", str(PASTA_PRINCIPAL_TRABALHO))
)
TEMPLATES_DOCX_DIR = BASE_DIR / "templates"
LEGACY_PLANOS_FEITOS_DIR = BASE_DIR / "Planos feitos"
MODELOS_LEGADOS_QUARENTENA_DIR = (
    PASTA_PLANOS_PROFESSORES / "_MODELOS_LEGADOS_PARA_EXCLUIR"
)

_padrao_finalizados = str(BASE_DIR / "planos_finalizados")
PLANOS_FINALIZADOS_DIR = Path(
    os.getenv("PLANOS_FINALIZADOS_DIR", _padrao_finalizados)
)
PLANOS_FEITOS_DIR = BASE_DIR / "Planos feitos"
DB_PATH = BASE_DIR / "planos_luan.db"
HISTORICO_DOCX_DIR = BASE_DIR / "historico_docx"

# 3.1 Fonte pedagogica oficial
#
# Os PDFs operacionais ficam fora do repositorio Git, em uma unica raiz
# controlada. Nao ha fallback automatico para OneDrive, Documents/Documentos
# ou instalacoes antigas: isso evita que uma pasta legada seja escolhida apenas
# porque ainda existe no computador.
PLANOS_LUAN_DADOS_DIR = BASE_DIR.parent / "PLANOS_LUAN_DADOS"
PDF_AULAS_DIR = PLANOS_LUAN_DADOS_DIR / "PDF_AULAS"
# Referencias gerais usadas como apoio pela IA. Quando nao existirem, o
# gerador continua usando o PDF/DOCX da aula e registra o aviso no plano.
REFERENCIAS_METODOLOGICAS_DIR = (
    PLANOS_LUAN_DADOS_DIR / "REFERENCIAS_METODOLOGICAS"
)


# Arquivos de dados especificos
ESCOPO_PROJETO_VIDA_PATH = BASE_DIR / "EM Escopo-sequencia 2026 (1).ods"
REGISTRO_PROXIMA_GERACAO_PATH = os.getenv(
    "REGISTRO_PROXIMA_GERACAO_PATH",
    str(BASE_DIR / "registro_proxima_geracao.json"),
)
# 4. Configuracoes de Inteligencia Artificial
MODELO_OPENAI_PADRAO = "gpt-4o-mini"
MODELO_GEMINI_PADRAO = "gemini-2.5-flash"
IA_TIMEOUT_SEGUNDOS = 120

# 4.1 Fluxos temporariamente desabilitados
# Fluxo de revisão pós-geração (etapa de edição das aulas geradas antes do DOCX).
# Mantido False intencionalmente: a UI usa este flag em 3 pontos (linhas ~1856, 2890 e 3016
# de planos_luan_app.py) para suprimir a tela de revisão intermediária e ir direto ao DOCX.
# Antes de reabilitar, validar o fluxo completo de revisão com a UI.
HABILITAR_REVISAO_POS_GERACAO = False

# 5. Limites e regras de leitura
PDF_TEXTO_LIMITE_CHARS = 100000
MAX_CHARS_WORD = 15000
HABILITAR_PDF2DOCX = False

# 6. Criacao automatica de pastas
def inicializar_pastas():
    os.makedirs(PLANOS_FINALIZADOS_DIR, exist_ok=True)
    os.makedirs(PLANOS_FEITOS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DOCX_DIR, exist_ok=True)
    os.makedirs(PASTA_BACKUP, exist_ok=True)
    os.makedirs(HISTORICO_DOCX_DIR, exist_ok=True)
