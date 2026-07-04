"""Referências prontas de História a partir de arquivos DOCX unificados."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


def _normalizar_espacos(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    return re.sub(r"\s+([.,;:!?])", r"\1", texto)


def _normalizar_busca(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def _tokens_titulo(texto: str) -> set[str]:
    ignorar = {
        "a", "o", "as", "os", "e", "de", "do", "da", "dos", "das",
        "um", "uma", "para", "por", "que", "em", "no", "na", "nos", "nas",
        "aula", "parte", "ano"
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _normalizar_busca(texto))
        if token not in ignorar and len(token) > 1
    }


def _pontuar_titulo(tema: str, titulo_referencia: str) -> float:
    tokens_tema = _tokens_titulo(tema)
    tokens_ref = _tokens_titulo(titulo_referencia)
    if not tokens_tema or not tokens_ref:
        return 0.0
    return len(tokens_tema & tokens_ref) / len(tokens_tema | tokens_ref)


def _paragrafos_docx(caminho_docx: str) -> list[str]:
    try:
        from docx import Document
    except ImportError:
        return []

    try:
        doc = Document(caminho_docx)
    except Exception:
        return []

    paragrafos = []
    for p in doc.paragraphs:
        txt = _normalizar_espacos(p.text)
        if txt:
            paragrafos.append(txt)
    return paragrafos


def _itens_com_check(texto: str) -> list[str]:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not texto:
        return []
    partes = [
        parte.strip(" -;")
        for parte in re.split(r"\s*(?:☑|•|\u2022)\s*", texto)
        if parte.strip(" -;")
    ]
    if len(partes) <= 1:
        partes = [
            parte.strip(" -;")
            for parte in re.split(r"\s*;\s+|\n+", texto)
            if parte.strip(" -;")
        ]
    itens = []
    for parte in partes:
        parte = parte.lstrip("☑• ").strip()
        if parte:
            itens.append(_normalizar_espacos(f"☑ {parte}"))
    return itens


def _finalizar_aula(aula: dict[str, Any] | None, aulas: dict[tuple[int, int], dict[str, Any]]) -> None:
    if not aula:
        return
    grade = aula.get("grade")
    numero = aula.get("numero")
    if not grade or not numero:
        return
    if aula.get("metodologia") and len(aula.get("acompanhamento") or []) >= 3 and len(aula.get("acessibilidade") or []) >= 3:
        aulas[(grade, numero)] = aula


@lru_cache(maxsize=8)
def _carregar_referencias_historia_docx(caminho_docx: str) -> dict[tuple[int, int], dict[str, Any]]:
    """Carrega as referências de História estruturadas por (grade, numero_aula)."""
    paragrafos = _paragrafos_docx(caminho_docx)
    aulas: dict[tuple[int, int], dict[str, Any]] = {}
    aula_atual: dict[str, Any] | None = None
    secao = ""

    # Matches "6º ANO - AULA 1 - As pólis gregas" or "1º SÉRIE (EM) - AULA 1 - ..."
    padrao_header = re.compile(r"^(\d{1,2})(?:º|o|a)?\s*(?:ANO|S[EÉ]RIE(?:\s*\(EM\))?)\s*[-–—]\s*AULA\s*(\d{1,2})\s*[-–—]\s*(.+)$", re.I)

    for texto in paragrafos:
        match_aula = padrao_header.match(texto)
        if match_aula:
            _finalizar_aula(aula_atual, aulas)
            aula_atual = {
                "grade": int(match_aula.group(1)),
                "numero": int(match_aula.group(2)),
                "titulo": _normalizar_espacos(match_aula.group(3)),
                "metodologia": [],
                "acompanhamento": [],
                "acessibilidade": [],
            }
            secao = ""
            continue

        if not aula_atual:
            continue

        texto_norm = _normalizar_busca(texto)
        if texto_norm == "metodologia":
            secao = "metodologia"
            continue
        if texto_norm == "acompanhamento da aprendizagem":
            secao = "acompanhamento"
            continue
        if texto_norm == "acessibilidade":
            secao = "acessibilidade"
            continue

        if secao == "metodologia":
            match_etapa = re.match(r"^([^:]{2,80}):\s*(.+)$", texto)
            if match_etapa:
                aula_atual["metodologia"].append(
                    {
                        "titulo": _normalizar_espacos(match_etapa.group(1)),
                        "text": _normalizar_espacos(match_etapa.group(2)), # Use "text" to be compatible with normalizer/generator schema
                        "texto": _normalizar_espacos(match_etapa.group(2)),
                    }
                )
            elif aula_atual["metodologia"]:
                aux = _normalizar_espacos(f"{aula_atual['metodologia'][-1]['texto']} {texto}")
                aula_atual["metodologia"][-1]["texto"] = aux
                aula_atual["metodologia"][-1]["text"] = aux
        elif secao in {"acompanhamento", "acessibilidade"}:
            aula_atual[secao].extend(_itens_com_check(texto))

    _finalizar_aula(aula_atual, aulas)
    return aulas


def _obter_grade_e_aula_do_pdf(caminho_pdf: str | Path, numero_aula: Any) -> tuple[int, int]:
    # Extract grade (e.g. "6_ANO" or "6" from path)
    caminho = Path(caminho_pdf)
    grade = 0
    for part in [caminho.parent.name, caminho.name]:
        part_clean = part.replace("_", " ").replace("-", " ")
        match_grade = re.search(r"(\d)\s*(?:º|o|a)?\s*ano", part_clean, re.I)
        if match_grade:
            grade = int(match_grade.group(1))
            break
            
    # Fallback checking parent paths
    if not grade:
        for parent in caminho.parents:
            parent_clean = parent.name.replace("_", " ").replace("-", " ")
            match_grade = re.search(r"(\d)\s*(?:º|o|a)?\s*ano", parent_clean, re.I)
            if match_grade:
                grade = int(match_grade.group(1))
                break

    # Extract lesson number
    numero = 0
    if isinstance(numero_aula, int):
        numero = numero_aula
    else:
        match_num = re.search(r"\d+", str(numero_aula or ""))
        if match_num:
            numero = int(match_num.group(0))
        else:
            match_num = re.search(r"AULA_(\d+)", caminho.stem, re.I)
            if match_num:
                numero = int(match_num.group(1))

    return grade, numero


def _selecionar_referencia(
    referencias: dict[tuple[int, int], dict[str, Any]],
    grade: int,
    numero_aula: int,
    tema: str = "",
) -> dict[str, Any] | None:
    # Try exact match first
    referencia_exata = referencias.get((grade, numero_aula))
    if referencia_exata:
        return referencia_exata

    # Fallback to title matching within the same grade
    if not tema:
        return None

    melhor_num = 0
    melhor_pontuacao = 0.0
    for (g, n), ref in referencias.items():
        if g == grade:
            pontuacao = _pontuar_titulo(tema, ref.get("titulo", ""))
            if pontuacao > melhor_pontuacao:
                melhor_num = n
                melhor_pontuacao = pontuacao

    if melhor_num and melhor_pontuacao >= 0.60:
        return referencias.get((grade, melhor_num))
    return None


def localizar_docx_referencia_historia(caminho_pdf: str | Path) -> Path | None:
    # AJUSTE: Desativado a pedido do usuário. A metodologia de História agora vem 100% da IA.
    return None


def localizar_docx_referencia_historia_cdp(caminho_pdf: str | Path) -> Path | None:
    caminho = Path(caminho_pdf)
    if not caminho_pdf:
        return None
        
    candidatos = []
    folders = [caminho.parent, caminho.parent.parent]
    for folder in folders:
        if folder.exists():
            candidatos.extend(folder.glob("Metodologias_Historia_CDP*.docx"))
            candidatos.extend(folder.glob("*Historia*CDP*.docx"))
            
    candidatos_unicos = {c.resolve(): c for c in candidatos if not c.name.startswith("~$")}.values()
    if not candidatos_unicos:
        return None
    return list(candidatos_unicos)[0]


def referencia_historia_por_pdf(caminho_pdf: str | Path, numero_aula: Any, tema: str = "") -> dict[str, Any] | None:
    # AJUSTE: Forçar o retorno vazio para que o sistema use as regras da IA, ignorando os DOCXs antigos
    return None


def referencia_historia_cdp_por_pdf(caminho_pdf: str | Path, numero_aula: Any, tema: str = "") -> dict[str, Any] | None:
    docx = localizar_docx_referencia_historia_cdp(caminho_pdf)
    if not docx:
        return None

    grade, numero = _obter_grade_e_aula_do_pdf(caminho_pdf, numero_aula)
    if not grade or not numero:
        return None

    referencias = _carregar_referencias_historia_docx(str(docx))
    referencia = _selecionar_referencia(referencias, grade, numero, tema)
    if not referencia:
        return None

    return {
        "numero": str(referencia.get("numero") or numero),
        "titulo": referencia.get("titulo", ""),
        "metodologia": list(referencia.get("metodologia") or []),
        "acompanhamento": list(referencia.get("acompanhamento") or [])[:3],
        "acessibilidade": list(referencia.get("acessibilidade") or [])[:3],
        "fonte": str(docx),
        "referencia_pedagogica_aplicada": True,
    }
