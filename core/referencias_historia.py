"""Referencias prontas de Historia a partir de arquivos DOCX unificados."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.referencias_base import (
    normalizar_busca as _normalizar_busca,
    normalizar_espacos,
    paragrafos_docx,
    tokens_titulo as _tokens_titulo,
)


def _normalizar_espacos(texto: str) -> str:
    return normalizar_espacos(texto, remover_espaco_antes_pontuacao=True)






def _pontuar_titulo(tema: str, titulo_referencia: str) -> float:
    tokens_tema = _tokens_titulo(tema)
    tokens_ref = _tokens_titulo(titulo_referencia)
    if not tokens_tema or not tokens_ref:
        return 0.0
    return len(tokens_tema & tokens_ref) / len(tokens_tema | tokens_ref)


def _paragrafos_docx(caminho_docx: str) -> list[str]:
    return paragrafos_docx(caminho_docx, remover_espaco_antes_pontuacao=True)


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


def _finalizar_aula(
    aula: dict[str, Any] | None,
    aulas: dict[tuple[int, int], dict[str, Any]],
) -> None:
    if not aula:
        return
    grade = aula.get("grade")
    numero = aula.get("numero")
    if not grade or not numero:
        return
    if (
        aula.get("metodologia")
        and len(aula.get("acompanhamento") or []) >= 3
        and len(aula.get("acessibilidade") or []) >= 3
    ):
        aulas[(grade, numero)] = aula


@lru_cache(maxsize=8)
def _carregar_referencias_historia_docx(
    caminho_docx: str,
) -> dict[tuple[int, int], dict[str, Any]]:
    """Carrega as referencias de Historia estruturadas por (grade, numero_aula)."""
    paragrafos = _paragrafos_docx(caminho_docx)
    aulas: dict[tuple[int, int], dict[str, Any]] = {}
    aula_atual: dict[str, Any] | None = None
    secao = ""

    padrao_header = re.compile(
        r"^(?:(\d{1,2})(?:º|o|a)?\s*(?:ANO|S[EÉ]RIE(?:\s*\(EM\))?)\s*[-–—]\s*)?AULA\s*(\d{1,2})\s*[-–—]\s*(.+)$",
        re.I,
    )

    # Extract default grade from path
    default_grade = 0
    from pathlib import Path
    caminho = Path(caminho_docx)
    for part in [caminho.parent.name, caminho.name]:
        part_clean = part.replace("_", " ").replace("-", " ")
        match_grade = re.search(r"(\d)\s*(?:º|o|a)?\s*ano", part_clean, re.I)
        if match_grade:
            default_grade = int(match_grade.group(1))
            break
    if not default_grade:
        for parent in caminho.parents:
            parent_clean = parent.name.replace("_", " ").replace("-", " ")
            match_grade = re.search(r"(\d)\s*(?:º|o|a)?\s*ano", parent_clean, re.I)
            if match_grade:
                default_grade = int(match_grade.group(1))
                break

    for texto in paragrafos:
        match_aula = padrao_header.match(texto)
        if match_aula:
            _finalizar_aula(aula_atual, aulas)
            grade_parsed = match_aula.group(1)
            grade_val = int(grade_parsed) if grade_parsed else default_grade
            if not grade_val:
                import logging
                logging.getLogger(__name__).warning("Aula '%s' ignorada pois nao foi possivel determinar a serie.", match_aula.group(3))
                aula_atual = None
                continue
            aula_atual = {
                "grade": grade_val,
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
                        "texto": _normalizar_espacos(match_etapa.group(2)),
                    }
                )
            elif aula_atual["metodologia"]:
                aux = _normalizar_espacos(
                    f"{aula_atual['metodologia'][-1]['texto']} {texto}"
                )
                aula_atual["metodologia"][-1]["texto"] = aux
        elif secao in {"acompanhamento", "acessibilidade"}:
            aula_atual[secao].extend(_itens_com_check(texto))

    _finalizar_aula(aula_atual, aulas)
    return aulas


def _obter_grade_e_aula_do_pdf(
    caminho_pdf: str | Path,
    numero_aula: Any,
) -> tuple[int, int]:
    caminho = Path(caminho_pdf)
    grade = 0
    for part in [caminho.parent.name, caminho.name]:
        part_clean = part.replace("_", " ").replace("-", " ")
        match_grade = re.search(r"(\d)\s*(?:º|o|a)?\s*ano", part_clean, re.I)
        if match_grade:
            grade = int(match_grade.group(1))
            break

    if not grade:
        for parent in caminho.parents:
            parent_clean = parent.name.replace("_", " ").replace("-", " ")
            match_grade = re.search(r"(\d)\s*(?:º|o|a)?\s*ano", parent_clean, re.I)
            if match_grade:
                grade = int(match_grade.group(1))
                break

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
            else:
                match_num = re.match(
                    r"^\s*(\d{1,3})(?:\s*[-_.]|\s+)",
                    caminho.stem,
                )
                if match_num:
                    numero = int(match_num.group(1))

    return grade, numero


def _selecionar_referencia(
    referencias: dict[tuple[int, int], dict[str, Any]],
    grade: int,
    numero_aula: int,
    tema: str = "",
) -> dict[str, Any] | None:
    referencia_exata = referencias.get((grade, numero_aula))
    if referencia_exata:
        return referencia_exata

    if not tema:
        return None

    melhor_num = 0
    melhor_pontuacao = 0.0
    for (g, n), ref in referencias.items():
        if g != grade:
            continue
        pontuacao = _pontuar_titulo(tema, ref.get("titulo", ""))
        if pontuacao > melhor_pontuacao:
            melhor_num = n
            melhor_pontuacao = pontuacao

    if melhor_num and melhor_pontuacao >= 0.60:
        return referencias.get((grade, melhor_num))
    return None


def _localizar_docx_historia_generico(
    caminho_pdf: str | Path,
    *,
    incluir: list[str],
    excluir: list[str],
) -> Path | None:
    caminho = Path(caminho_pdf)
    if not caminho_pdf:
        return None

    candidatos = []
    folders = [caminho.parent, caminho.parent.parent]
    for folder in folders:
        if not folder.exists():
            continue
        for padrao in incluir:
            candidatos.extend(folder.glob(padrao))

    vistos: set[Path] = set()
    candidatos_filtrados = []
    for candidato in candidatos:
        try:
            resolvido = candidato.resolve()
        except Exception:
            continue
        nome_normalizado = _normalizar_busca(candidato.name)
        if candidato.name.startswith("~$"):
            continue
        if any(token in nome_normalizado for token in excluir):
            continue
        if resolvido in vistos:
            continue
        vistos.add(resolvido)
        candidatos_filtrados.append(candidato)

    if not candidatos_filtrados:
        return None
    return candidatos_filtrados[0]


def localizar_docx_referencia_historia(caminho_pdf: str | Path) -> Path | None:
    return _localizar_docx_historia_generico(
        caminho_pdf,
        incluir=[
            "Metodologias_Historia_Ensino_Regular*.docx",
            "*Historia*Ensino*Regular*.docx",
            "Metodologias_Historia*.docx",
            "*Historia*.docx",
        ],
        excluir=["cdp"],
    )


def localizar_docx_referencia_historia_cdp(caminho_pdf: str | Path) -> Path | None:
    return _localizar_docx_historia_generico(
        caminho_pdf,
        incluir=[
            "Metodologias_Historia_CDP*.docx",
            "*Historia*CDP*.docx",
        ],
        excluir=[],
    )


def referencia_historia_por_pdf(
    caminho_pdf: str | Path,
    numero_aula: Any,
    tema: str = "",
) -> dict[str, Any] | None:
    docx = localizar_docx_referencia_historia(caminho_pdf)
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
        "habilidade": "",
        "metodologia": list(referencia.get("metodologia") or []),
        "acompanhamento": list(referencia.get("acompanhamento") or [])[:3],
        "acessibilidade": list(referencia.get("acessibilidade") or [])[:3],
        "fonte": str(docx),
        "referencia_pedagogica_aplicada": True,
    }


def referencia_historia_cdp_por_pdf(
    caminho_pdf: str | Path,
    numero_aula: Any,
    tema: str = "",
) -> dict[str, Any] | None:
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
