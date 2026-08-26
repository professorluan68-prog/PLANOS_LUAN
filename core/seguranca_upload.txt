from __future__ import annotations

import os
import re
import secrets
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Callable


PREFIXO_PDF_TEMPORARIO = "planos_luan_upload_"


def _limite_inteiro(nome: str, padrao: int) -> int:
    try:
        valor = int(os.getenv(nome, str(padrao)) or str(padrao))
    except (TypeError, ValueError):
        valor = padrao
    return max(1, valor)


LIMITE_PDF_MB = _limite_inteiro("PLANOS_LUAN_PDF_MAX_MB", 200)
LIMITE_PDF_BYTES = LIMITE_PDF_MB * 1024 * 1024
LIMITE_PDF_PAGINAS = _limite_inteiro("PLANOS_LUAN_PDF_MAX_PAGES", 500)


class ArquivoPDFInvalido(ValueError):
    """Erro seguro e compreensível para PDFs recusados antes do processamento."""


def _nome_pdf_seguro(nome_original: str) -> str:
    nome = Path(str(nome_original or "aula.pdf")).name
    nome = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", nome).strip(" .")
    return nome or "aula.pdf"


def nome_pdf_upload_temporario(nome_original: str, token: str) -> str:
    token_seguro = re.sub(r"[^A-Za-z0-9_-]", "", str(token or ""))[:24]
    if not token_seguro:
        token_seguro = "upload"
    return f"{PREFIXO_PDF_TEMPORARIO}{token_seguro}__{_nome_pdf_seguro(nome_original)}"


def nomes_pdf_original_possiveis(nome_temporario: str) -> list[str]:
    nome = Path(str(nome_temporario or "")).name
    candidatos = [nome] if nome else []

    padrao_atual = re.match(
        rf"^{re.escape(PREFIXO_PDF_TEMPORARIO)}[A-Za-z0-9_-]+?__(.+\.pdf)$",
        nome,
        flags=re.I,
    )
    if padrao_atual:
        candidatos.append(padrao_atual.group(1))

    padrao_legado = re.match(r"^[A-Za-z0-9_-]{4}_(.+\.pdf)$", nome, flags=re.I)
    if padrao_legado:
        candidatos.append(padrao_legado.group(1))

    return list(dict.fromkeys(candidatos))


def _validar_nome_pdf(nome: str) -> None:
    if Path(str(nome or "")).suffix.casefold() != ".pdf":
        raise ArquivoPDFInvalido("O arquivo enviado precisa ter a extensão .pdf.")


def _validar_tamanho_pdf(tamanho: int, nome: str, limite_bytes: int) -> None:
    if tamanho <= 0:
        raise ArquivoPDFInvalido(f'O PDF "{nome}" está vazio.')
    if tamanho > limite_bytes:
        limite_mb = limite_bytes / (1024 * 1024)
        raise ArquivoPDFInvalido(
            f'O PDF "{nome}" ultrapassa o limite de {limite_mb:g} MB.'
        )


def _validar_assinatura_pdf(cabecalho: bytes, nome: str) -> None:
    if not bytes(cabecalho or b"").startswith(b"%PDF-"):
        raise ArquivoPDFInvalido(
            f'O arquivo "{nome}" não possui uma assinatura PDF válida.'
        )


def _contar_paginas_pdf_bytes(conteudo: bytes) -> int:
    import pdfplumber

    with pdfplumber.open(BytesIO(conteudo)) as pdf:
        return len(pdf.pages)


def _contar_paginas_pdf_caminho(caminho: Path) -> int:
    import pdfplumber

    with pdfplumber.open(caminho) as pdf:
        return len(pdf.pages)


def _validar_quantidade_paginas(
    nome: str,
    limite_paginas: int,
    contar_paginas: Callable[[], int],
) -> int:
    try:
        quantidade = int(contar_paginas())
    except ArquivoPDFInvalido:
        raise
    except Exception as exc:
        raise ArquivoPDFInvalido(
            f'O PDF "{nome}" está corrompido, protegido por senha ou não pôde ser lido.'
        ) from exc
    if quantidade <= 0:
        raise ArquivoPDFInvalido(f'O PDF "{nome}" não contém páginas válidas.')
    if quantidade > limite_paginas:
        raise ArquivoPDFInvalido(
            f'O PDF "{nome}" possui {quantidade} páginas e ultrapassa o limite de '
            f"{limite_paginas}."
        )
    return quantidade


def validar_pdf_bytes(
    conteudo: bytes,
    nome: str,
    *,
    limite_bytes: int = LIMITE_PDF_BYTES,
    limite_paginas: int = LIMITE_PDF_PAGINAS,
    contador_paginas: Callable[[bytes], int] | None = None,
) -> int:
    _validar_nome_pdf(nome)
    _validar_tamanho_pdf(len(conteudo), nome, limite_bytes)
    _validar_assinatura_pdf(conteudo[:8], nome)
    contador = contador_paginas or _contar_paginas_pdf_bytes
    return _validar_quantidade_paginas(
        nome,
        limite_paginas,
        lambda: contador(conteudo),
    )


def validar_pdf_caminho(
    caminho_pdf: str | Path,
    *,
    limite_bytes: int = LIMITE_PDF_BYTES,
    limite_paginas: int = LIMITE_PDF_PAGINAS,
    contador_paginas: Callable[[Path], int] | None = None,
) -> int:
    caminho = Path(caminho_pdf)
    _validar_nome_pdf(caminho.name)
    try:
        tamanho = caminho.stat().st_size
        with caminho.open("rb") as arquivo:
            cabecalho = arquivo.read(8)
    except OSError as exc:
        raise ArquivoPDFInvalido(
            f'O PDF "{caminho.name}" não pôde ser acessado.'
        ) from exc
    _validar_tamanho_pdf(tamanho, caminho.name, limite_bytes)
    _validar_assinatura_pdf(cabecalho, caminho.name)
    contador = contador_paginas or _contar_paginas_pdf_caminho
    return _validar_quantidade_paginas(
        caminho.name,
        limite_paginas,
        lambda: contador(caminho),
    )


def salvar_pdf_upload_temporario(
    conteudo: bytes,
    nome_original: str,
    *,
    raiz_temporaria: str | Path | None = None,
    limite_bytes: int = LIMITE_PDF_BYTES,
    limite_paginas: int = LIMITE_PDF_PAGINAS,
    contador_paginas: Callable[[bytes], int] | None = None,
) -> Path:
    """Valida e grava um upload em diretório temporário exclusivo."""
    conteudo = bytes(conteudo or b"")
    nome_original = _nome_pdf_seguro(nome_original)
    validar_pdf_bytes(
        conteudo,
        nome_original,
        limite_bytes=limite_bytes,
        limite_paginas=limite_paginas,
        contador_paginas=contador_paginas,
    )

    raiz = Path(raiz_temporaria or tempfile.gettempdir())
    raiz.mkdir(parents=True, exist_ok=True)
    diretorio = Path(
        tempfile.mkdtemp(prefix=PREFIXO_PDF_TEMPORARIO, dir=str(raiz))
    )
    token = secrets.token_urlsafe(6)
    caminho_pdf = diretorio / nome_pdf_upload_temporario(nome_original, token)
    try:
        caminho_pdf.write_bytes(conteudo)
        return caminho_pdf
    except Exception:
        shutil.rmtree(diretorio, ignore_errors=True)
        raise


def limpar_upload_temporario(
    caminho_pdf: str | Path,
    *,
    raiz_temporaria: str | Path | None = None,
) -> bool:
    """Remove o diretório exclusivo do upload e todos os auxiliares gerados nele."""
    if not caminho_pdf:
        return False

    raiz = Path(raiz_temporaria or tempfile.gettempdir()).resolve()
    caminho = Path(caminho_pdf).resolve(strict=False)
    diretorio = caminho.parent
    if (
        diretorio.parent != raiz
        or not diretorio.name.startswith(PREFIXO_PDF_TEMPORARIO)
    ):
        return False

    try:
        shutil.rmtree(diretorio)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return not diretorio.exists()
