from pathlib import Path
import os


# Configuracoes centralizadas do projeto

BASE_DIR = Path(__file__).resolve().parent
PDFS_ORGANIZADOS_DIR = BASE_DIR / "PDFs_Organizados"
MODELOS_DOCX_DIR = BASE_DIR / "modelos_docx"
TEMPLATES_DOCX_DIR = BASE_DIR / "templates"
LEGACY_PLANOS_FEITOS_DIR = BASE_DIR / "Planos feitos"

# Usar variáveis de ambiente com fallback para caminhos padrão
PASTA_PLANOS_PROFESSORES = Path(
    os.getenv("PLANOS_DIR", r"D:\PLANOS DE JUNHO")
)
MODELOS_LEGADOS_QUARENTENA_DIR = PASTA_PLANOS_PROFESSORES / "_MODELOS_LEGADOS_PARA_EXCLUIR"

PLANOS_FINALIZADOS_DIR = Path(
    os.getenv("PLANOS_FINALIZADOS_DIR", r"D:\PLANOS-FINALIZADOS")
)

ESCOPO_PROJETO_VIDA_PATH = BASE_DIR / "EM Escopo-sequência 2026 (1).ods"

REDACAO_DIR = PDFS_ORGANIZADOS_DIR / "Redação e Leitura"
REDACAO_PLANILHA_FUNDAMENTAL = REDACAO_DIR / "PLANILHA.xlsx"
REDACAO_PLANILHA_MEDIO = REDACAO_DIR / "PLANILHAENSINOMEDIO.xlsx"
REDACAO_TITULOS_XLSX = REDACAO_DIR / "TÍTULO.xlsx"

FORMATO_REFERENCIA_DOCX = MODELOS_DOCX_DIR / "modelo.docx"

# IA
MODELO_OPENAI_PADRAO = "gpt-4o-mini"
MODELO_GEMINI_PADRAO = "gemini-2.0-flash"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/chat/completions"
IA_TIMEOUT_SEGUNDOS = 45

# Limites de caracteres no DOCX
MAX_CELL_CHARS = 8000

MAX_DESENVOLVIMENTO_CHARS: dict[str, int] = {
    "default": 4500,
    "biologia": 4800,
    "ciencias": 4800,
    "lingua portuguesa": 5200,
}

MAX_ITEM_LISTA_CHARS: dict[str, int] = {
    "default": 550,
    "ciencias": 650,
    "lingua portuguesa": 650,
}

MAX_LISTA_TOTAL_CHARS: dict[str, int] = {
    "default": 1650,
    "ciencias": 1800,
    "lingua portuguesa": 1800,
}

# PDF
PDF_MAX_PAGINAS = 400
PDF_OCR_DPI = 200
PDF_OCR_LANG = "por"
PDF_SLIDE_LIMITE_CHARS = 2200
PDF_TEXTO_LIMITE_CHARS = 14000
