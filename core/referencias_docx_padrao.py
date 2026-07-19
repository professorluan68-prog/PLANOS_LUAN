"""Leitor central de referencias pedagogicas em DOCX padronizado.

O arquivo auxiliar deve ficar na mesma pasta do PDF e conter blocos numerados
no formato ``AULA N - Titulo``. A selecao da referencia e feita somente pelo
numero da aula; o tema nao e usado como alternativa de correspondencia.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any


_CABECALHO_AULA = re.compile(
    r"^AULA\s+(\d{1,3})\s*[-\u2013\u2014]\s*(.+)$",
    flags=re.IGNORECASE,
)


def _normalizar_espacos_separacao(texto: Any) -> str:
    """Remove espacos acidentais sem reescrever o conteudo pedagogico."""
    return re.sub(r"\s+", " ", str(texto or "")).strip()


def _normalizar_para_comparacao(texto: Any) -> str:
    normalizado = unicodedata.normalize("NFD", str(texto or "").casefold())
    normalizado = "".join(
        caractere
        for caractere in normalizado
        if unicodedata.category(caractere) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", normalizado).strip()


def _separar_titulo_habilidade(texto: Any) -> tuple[str, str]:
    texto_normalizado = _normalizar_espacos_separacao(texto)
    marcador = re.search(r"\bHABILIDADE\s*:\s*", texto_normalizado, flags=re.I)
    if not marcador:
        return texto_normalizado, ""
    titulo = _normalizar_espacos_separacao(texto_normalizado[: marcador.start()])
    habilidade = _normalizar_espacos_separacao(texto_normalizado[marcador.end() :])
    return titulo, habilidade


def _eh_candidato_docx(caminho: Path) -> bool:
    if not caminho.is_file() or caminho.suffix.casefold() != ".docx":
        return False
    if caminho.name.startswith("~$"):
        return False
    return "backup" not in _normalizar_para_comparacao(caminho.stem)


def localizar_docx_referencia_padrao(
    caminho_pdf: str | Path,
) -> Path | None:
    """Localiza o DOCX auxiliar padronizado na mesma pasta do PDF.

    Nomes iniciados por ``METODOLOGIA_`` (no singular) tem prioridade. Na
    ausencia deles, e aceito qualquer DOCX cujo nome contenha ``metodologia``
    ou ``metodologias``. Arquivos temporarios do Word e backups sao ignorados.
    """
    if not str(caminho_pdf or "").strip():
        return None

    pasta = Path(caminho_pdf).parent
    if not pasta.is_dir():
        return None

    try:
        candidatos = [
            caminho
            for caminho in pasta.iterdir()
            if _eh_candidato_docx(caminho)
        ]
    except OSError:
        return None

    candidatos_singulares = [
        caminho
        for caminho in candidatos
        if caminho.name.casefold().startswith("metodologia_")
    ]
    if candidatos_singulares:
        return min(candidatos_singulares, key=lambda item: item.name.casefold())

    candidatos_genericos = [
        caminho
        for caminho in candidatos
        if "metodologia" in _normalizar_para_comparacao(caminho.stem)
    ]
    if not candidatos_genericos:
        return None
    return min(candidatos_genericos, key=lambda item: item.name.casefold())


def _extrair_paragrafos(caminho_docx: str | Path) -> list[str]:
    try:
        from docx import Document
    except ImportError:
        return []

    try:
        documento = Document(str(caminho_docx))
    except Exception:
        return []

    paragrafos: list[str] = []
    for paragrafo in documento.paragraphs:
        texto = _normalizar_espacos_separacao(paragrafo.text)
        if texto:
            paragrafos.append(texto)
    return paragrafos


def _finalizar_aula(
    aula: dict[str, Any] | None,
    referencias: dict[int, dict[str, Any]],
) -> None:
    if not aula:
        return

    metodologia = [
        dict(item)
        for item in aula.get("metodologia") or []
        if item.get("titulo") and item.get("texto")
    ]
    acompanhamento = list(aula.get("acompanhamento") or [])
    acessibilidade = list(aula.get("acessibilidade") or [])
    if not metodologia or len(acompanhamento) < 3 or len(acessibilidade) < 3:
        return

    numero = int(aula["numero"])
    referencias[numero] = {
        "numero": numero,
        "titulo": aula["titulo"],
        "habilidade": aula.get("habilidade", ""),
        "metodologia": metodologia,
        "acompanhamento": acompanhamento[:3],
        "acessibilidade": acessibilidade[:3],
    }


def carregar_referencias_docx_padrao(
    caminho_docx: str | Path,
) -> dict[int, dict[str, Any]]:
    """Le as aulas validas de um DOCX padronizado, sem adaptar seus textos."""
    referencias: dict[int, dict[str, Any]] = {}
    aula_atual: dict[str, Any] | None = None
    secao = ""

    for texto in _extrair_paragrafos(caminho_docx):
        cabecalho = _CABECALHO_AULA.match(texto)
        if cabecalho:
            _finalizar_aula(aula_atual, referencias)
            titulo, habilidade = _separar_titulo_habilidade(cabecalho.group(2))
            aula_atual = {
                "numero": int(cabecalho.group(1)),
                "titulo": titulo,
                "habilidade": habilidade,
                "metodologia": [],
                "acompanhamento": [],
                "acessibilidade": [],
            }
            secao = ""
            continue

        if aula_atual is None:
            continue

        titulo_secao = _normalizar_para_comparacao(texto)
        if titulo_secao.startswith("habilidade "):
            _, habilidade = _separar_titulo_habilidade(texto)
            aula_atual["habilidade"] = habilidade
            continue
        if titulo_secao == "metodologia":
            secao = "metodologia"
            continue
        if titulo_secao == "acompanhamento da aprendizagem":
            secao = "acompanhamento"
            continue
        if titulo_secao == "acessibilidade":
            secao = "acessibilidade"
            continue

        if secao == "metodologia":
            if ":" in texto:
                titulo, conteudo = texto.split(":", 1)
                titulo = _normalizar_espacos_separacao(titulo)
                conteudo = _normalizar_espacos_separacao(conteudo)
                if titulo and conteudo:
                    aula_atual["metodologia"].append(
                        {"titulo": titulo, "texto": conteudo}
                    )
            elif aula_atual["metodologia"]:
                etapa = aula_atual["metodologia"][-1]
                etapa["texto"] = _normalizar_espacos_separacao(
                    f"{etapa['texto']} {texto}"
                )
        elif secao in {"acompanhamento", "acessibilidade"}:
            aula_atual[secao].append(texto)

    _finalizar_aula(aula_atual, referencias)
    return referencias


def _normalizar_numero_aula(numero_aula: Any) -> int:
    if isinstance(numero_aula, bool):
        return 0
    if isinstance(numero_aula, int):
        return numero_aula if numero_aula > 0 else 0
    correspondencia = re.search(r"\d{1,3}", str(numero_aula or ""))
    if not correspondencia:
        return 0
    numero = int(correspondencia.group(0))
    return numero if numero > 0 else 0


def referencia_docx_padrao_por_pdf(
    caminho_pdf: str | Path,
    numero_aula: Any,
    tema: str = "",
) -> dict[str, Any] | None:
    """Retorna a referencia que corresponde exatamente ao numero da aula."""
    del tema  # Mantido na API apenas por compatibilidade; nunca orienta a busca.

    caminho_docx = localizar_docx_referencia_padrao(caminho_pdf)
    numero = _normalizar_numero_aula(numero_aula)
    if caminho_docx is None or not numero:
        return None

    referencia = carregar_referencias_docx_padrao(caminho_docx).get(numero)
    if referencia is None:
        return None

    return {
        "numero": referencia["numero"],
        "titulo": referencia["titulo"],
        "habilidade": referencia.get("habilidade", ""),
        "metodologia": [dict(item) for item in referencia["metodologia"]],
        "acompanhamento": list(referencia["acompanhamento"]),
        "acessibilidade": list(referencia["acessibilidade"]),
        "fonte": str(caminho_docx),
        "referencia_pedagogica_aplicada": True,
    }
