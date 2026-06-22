"""Referencias DOCX para CDP Ensino Fundamental/Medio em fluxo contextual."""

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


def _normalizar_numero_aula(valor: Any) -> str:
    texto = str(valor or "").strip()
    match = re.search(r"(?:^|[_\s-])AULA[_\s-]*(\d{1,2}(?:[.,]\d+)?)", texto, flags=re.I)
    if not match:
        match = re.search(r"(?<!\d)(\d{1,2}(?:[.,]\d+)?)(?!\d)", texto)
    if not match:
        return ""
    numero = match.group(1).replace(",", ".")
    if "." in numero:
        inteiro, decimal = numero.split(".", 1)
        return f"{int(inteiro)}.{decimal.rstrip('0') or '0'}"
    return str(int(numero))


def _numero_aula_por_nome_pdf(caminho_pdf: str | Path) -> str:
    nome = Path(caminho_pdf).stem
    match_aula = re.search(r"(?:^|[_\s-])AULA[_\s-]*(\d{1,2}(?:[.,]\d+)?)", nome, flags=re.I)
    if match_aula:
        return _normalizar_numero_aula(match_aula.group(1))
    return _normalizar_numero_aula(nome)


def _tokens_titulo(texto: str) -> set[str]:
    ignorar = {
        "a",
        "o",
        "as",
        "os",
        "e",
        "de",
        "do",
        "da",
        "dos",
        "das",
        "em",
        "no",
        "na",
        "nos",
        "nas",
        "para",
        "por",
        "com",
        "aula",
        "tema",
        "parte",
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
    except Exception:
        return []

    try:
        doc = Document(caminho_docx)
    except Exception:
        return []

    paragrafos: list[str] = []
    for paragrafo in doc.paragraphs:
        texto = _normalizar_espacos(paragrafo.text)
        if texto:
            paragrafos.append(texto)
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


def _finalizar_aula(aula: dict[str, Any] | None, aulas: dict[str, dict[str, Any]]) -> None:
    if not aula:
        return
    numero = _normalizar_numero_aula(aula.get("numero"))
    if not numero:
        return
    if aula.get("metodologia") and len(aula.get("acompanhamento") or []) >= 3 and len(aula.get("acessibilidade") or []) >= 3:
        chave = numero
        if chave in aulas:
            repeticoes = sum(1 for chave_existente in aulas if chave_existente == numero or chave_existente.startswith(f"{numero}#"))
            chave = f"{numero}#{repeticoes + 1}"
        aulas[chave] = aula


@lru_cache(maxsize=32)
def _carregar_referencias_docx(caminho_docx: str) -> dict[str, dict[str, Any]]:
    paragrafos = _paragrafos_docx(caminho_docx)
    aulas: dict[str, dict[str, Any]] = {}
    aula_atual: dict[str, Any] | None = None
    secao = ""

    for texto in paragrafos:
        match_aula = re.match(r"^AULA\s+(\d{1,2}(?:[.,]\d+)?)\s*[-–—]\s*(.+)$", texto, flags=re.I)
        if match_aula:
            _finalizar_aula(aula_atual, aulas)
            aula_atual = {
                "numero": _normalizar_numero_aula(match_aula.group(1)),
                "titulo": _normalizar_espacos(match_aula.group(2)),
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
                aula_atual["metodologia"][-1]["texto"] = _normalizar_espacos(
                    f"{aula_atual['metodologia'][-1]['texto']} {texto}"
                )
        elif secao in {"acompanhamento", "acessibilidade"}:
            aula_atual[secao].extend(_itens_com_check(texto))

    _finalizar_aula(aula_atual, aulas)
    return aulas


def _score_docx_referencia(caminho: Path) -> tuple[int, float, str]:
    nome = _normalizar_busca(caminho.name)
    prioridade_nome = 0
    if "metodologias" in nome:
        prioridade_nome += 3
    if any(token in nome for token in ("corrigido", "atualizado", "novo", "2026")):
        prioridade_nome += 1
    try:
        modificado = caminho.stat().st_mtime
    except OSError:
        modificado = 0.0
    return prioridade_nome, modificado, caminho.name.lower()


def localizar_docx_referencia_cdp_contextual(caminho_pdf: str | Path) -> Path | None:
    caminho = Path(caminho_pdf)
    if not caminho_pdf or not caminho.parent.exists():
        return None

    candidatos = list(caminho.parent.glob("metodologias*.docx"))
    candidatos.extend(caminho.parent.glob("Metodologias*.docx"))
    candidatos.extend(caminho.parent.glob("*CDP*Metodologia*.docx"))
    candidatos.extend(caminho.parent.glob("*Metodologia*.docx"))
    candidatos_unicos = {candidato.resolve(): candidato for candidato in candidatos}.values()
    candidatos_validos = [candidato for candidato in candidatos_unicos if not candidato.name.startswith("~$")]
    if not candidatos_validos:
        return None
    return max(candidatos_validos, key=_score_docx_referencia)


def titulos_referencia_cdp_contextual_por_docx(caminho_docx: str | Path) -> dict[str, str]:
    referencias = _carregar_referencias_docx(str(caminho_docx))
    return {
        str(numero): str(referencia.get("titulo") or "").strip()
        for numero, referencia in referencias.items()
        if str(referencia.get("titulo") or "").strip()
    }


def _selecionar_referencia(
    referencias: dict[str, dict[str, Any]],
    numero_aula: str,
    tema: str = "",
) -> dict[str, Any] | None:
    referencia_numerica = referencias.get(numero_aula)
    if not tema:
        return referencia_numerica

    tokens_tema = _tokens_titulo(tema)
    melhor_numero = ""
    melhor_pontuacao = 0.0
    for numero, referencia in referencias.items():
        pontuacao = _pontuar_titulo(tema, referencia.get("titulo", ""))
        if pontuacao > melhor_pontuacao:
            melhor_numero = numero
            melhor_pontuacao = pontuacao

    pontuacao_numerica = _pontuar_titulo(tema, (referencia_numerica or {}).get("titulo", ""))
    if melhor_numero and melhor_pontuacao >= 0.50 and melhor_pontuacao > pontuacao_numerica + 0.15:
        return referencias.get(melhor_numero)
    if referencia_numerica and tokens_tema and pontuacao_numerica < 0.25:
        return None
    return referencia_numerica or (referencias.get(melhor_numero) if melhor_pontuacao >= 0.70 else None)


def referencia_cdp_contextual_por_pdf(caminho_pdf: str | Path, numero_aula: Any, tema: str = "") -> dict[str, Any] | None:
    docx = localizar_docx_referencia_cdp_contextual(caminho_pdf)
    if not docx:
        return None

    numero_nome = _numero_aula_por_nome_pdf(caminho_pdf)
    numero = numero_nome or _normalizar_numero_aula(numero_aula)
    if not numero:
        return None

    referencias = _carregar_referencias_docx(str(docx))
    referencia = _selecionar_referencia(referencias, numero, tema)
    if not referencia:
        return None

    return {
        "numero": referencia.get("numero") or numero,
        "titulo": referencia.get("titulo", ""),
        "metodologia": list(referencia.get("metodologia") or []),
        "acompanhamento": list(referencia.get("acompanhamento") or [])[:3],
        "acessibilidade": list(referencia.get("acessibilidade") or [])[:3],
        "fonte": str(docx),
        "referencia_pedagogica_aplicada": True,
    }
