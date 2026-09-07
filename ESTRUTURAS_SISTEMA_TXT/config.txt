import os
import shutil
from pathlib import Path

# ==========================================
# DOCUMENTACAO E CONFIGURACAO DE CAMINHOS
# ==========================================

# 1. Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent

PLANOS_LUAN_DADOS_DIR = BASE_DIR.parent / "PLANOS_LUAN_DADOS"

# 2. Caminhos de trabalho externos
PASTA_PRINCIPAL_TRABALHO = Path(os.getenv("PLANOS_TRABALHO_DIR", str(PLANOS_LUAN_DADOS_DIR / "planos_de_junho")))
PASTA_BACKUP = Path(os.getenv("PLANOS_BACKUP_DIR", str(PLANOS_LUAN_DADOS_DIR / "backups_planos_luan")))

# 3. Compatibilidade com o sistema existente
PASTA_PLANOS_PROFESSORES = Path(
    os.getenv("PLANOS_DIR", str(PASTA_PRINCIPAL_TRABALHO))
)
TEMPLATES_DOCX_DIR = BASE_DIR / "templates"
LEGACY_PLANOS_FEITOS_DIR = BASE_DIR / "Planos feitos"
MODELOS_LEGADOS_QUARENTENA_DIR = (
    PASTA_PLANOS_PROFESSORES / "_MODELOS_LEGADOS_PARA_EXCLUIR"
)

# 3.1 Fonte pedagogica oficial
PDF_AULAS_DIR = PLANOS_LUAN_DADOS_DIR / "PDF_AULAS"
REFERENCIAS_METODOLOGICAS_DIR = PLANOS_LUAN_DADOS_DIR / "REFERENCIAS_METODOLOGICAS"

_padrao_finalizados = str(PLANOS_LUAN_DADOS_DIR / "planos_finalizados")
PLANOS_FINALIZADOS_DIR = Path(
    os.getenv("PLANOS_FINALIZADOS_DIR", _padrao_finalizados)
)
PLANOS_FEITOS_DIR = PLANOS_LUAN_DADOS_DIR / "Planos feitos"
DB_PATH = PLANOS_LUAN_DADOS_DIR / "planos_luan.db"
HISTORICO_DOCX_DIR = PLANOS_LUAN_DADOS_DIR / "historico_docx"

# Arquivos de dados especificos
ESCOPO_PROJETO_VIDA_PATH = BASE_DIR / "EM Escopo-sequencia 2026 (1).ods"
REGISTRO_PROXIMA_GERACAO_PATH = os.getenv(
    "REGISTRO_PROXIMA_GERACAO_PATH",
    str(PLANOS_LUAN_DADOS_DIR / "registro_proxima_geracao.json"),
)
# 4. Configuracoes de Inteligencia Artificial
MODELO_OPENAI_PADRAO = "gpt-4o-mini"
MODELO_GEMINI_PADRAO = "gemini-2.5-flash"
IA_TIMEOUT_SEGUNDOS = 120

# 4.1 Fluxos temporariamente desabilitados
HABILITAR_REVISAO_POS_GERACAO = False

# 5. Limites e regras de leitura
PDF_TEXTO_LIMITE_CHARS = 100000
MAX_CHARS_WORD = 15000
HABILITAR_PDF2DOCX = False

def _localizar_executavel(nome_variavel: str, candidatos: list[Path]) -> Path | None:
    configurado = os.getenv(nome_variavel)
    if configurado:
        caminho = Path(configurado)
        if caminho.is_file():
            return caminho

    for caminho in candidatos:
        if caminho.is_file():
            return caminho

    encontrado_no_path = shutil.which(candidatos[0].name)
    return Path(encontrado_no_path) if encontrado_no_path else None

TESSERACT_CMD = _localizar_executavel(
    "PLANOS_LUAN_TESSERACT_CMD",
    [Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")],
)
TESSDATA_DIR = BASE_DIR / "assets" / "tessdata"
LIBREOFFICE_CMD = _localizar_executavel(
    "PLANOS_LUAN_LIBREOFFICE_CMD",
    [Path(r"C:\Program Files\LibreOffice\program\soffice.exe")],
)

def _localizar_poppler_bin() -> Path | None:
    configurado = os.getenv("PLANOS_LUAN_POPPLER_DIR")
    if configurado and (Path(configurado) / "pdftoppm.exe").is_file():
        return Path(configurado)
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        return Path(pdftoppm).parent
    raiz_winget = Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "WinGet"
    atalhos_winget = raiz_winget / "Links"
    if (atalhos_winget / "pdftoppm.exe").is_file():
        return atalhos_winget
    try:
        for pacote in (raiz_winget / "Packages").glob("oschwartz10612.Poppler_*"):
            for versao in pacote.glob("poppler-*"):
                candidato = versao / "Library" / "bin"
                if (candidato / "pdftoppm.exe").is_file():
                    return candidato
    except OSError:
        pass
    return None

POPPLER_BIN_DIR = _localizar_poppler_bin()

def inicializar_pastas():
    os.makedirs(PLANOS_FINALIZADOS_DIR, exist_ok=True)
    os.makedirs(PLANOS_FEITOS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DOCX_DIR, exist_ok=True)
    os.makedirs(PASTA_BACKUP, exist_ok=True)
    os.makedirs(HISTORICO_DOCX_DIR, exist_ok=True)

