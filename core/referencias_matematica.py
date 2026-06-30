"""Referencias prontas de Matematica a partir de DOCX na pasta dos PDFs."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


def _normalizar_espacos(texto: str) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip()


def _normalizar_busca(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


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
        "um",
        "uma",
        "para",
        "por",
        "que",
        "em",
        "no",
        "na",
        "nos",
        "nas",
        "aula",
        "parte",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _normalizar_busca(texto))
        if token not in ignorar and len(token) > 1
    }


def _parte_titulo(texto: str) -> str:
    match = re.search(r"\bparte\s*(\d{1,2})\b", _normalizar_busca(texto))
    return match.group(1) if match else ""


def _pontuar_titulo(tema: str, titulo_referencia: str) -> float:
    tokens_tema = _tokens_titulo(tema)
    tokens_ref = _tokens_titulo(titulo_referencia)
    if not tokens_tema or not tokens_ref:
        return 0.0

    pontuacao = len(tokens_tema & tokens_ref) / len(tokens_tema | tokens_ref)
    parte_tema = _parte_titulo(tema)
    parte_ref = _parte_titulo(titulo_referencia)
    if parte_tema and parte_ref:
        pontuacao += 0.25 if parte_tema == parte_ref else -0.25
    return pontuacao


def _normalizar_numero_aula(valor: Any) -> int:
    if isinstance(valor, int):
        return valor
    match = re.search(r"\d{1,3}", str(valor or ""))
    return int(match.group(0)) if match else 0


def _paragrafos_docx(caminho_docx: str) -> list[str]:
    try:
        from docx import Document
    except Exception:
        return []

    try:
        doc = Document(caminho_docx)
    except Exception:
        return []

    return [
        _normalizar_espacos(paragrafo.text)
        for paragrafo in doc.paragraphs
        if _normalizar_espacos(paragrafo.text)
    ]


def _finalizar_aula(
    aula: dict[str, Any] | None,
    aulas: dict[int, dict[str, Any]],
) -> None:
    if not aula:
        return
    numero = _normalizar_numero_aula(aula.get("numero"))
    if not numero:
        return
    if (
        aula.get("metodologia")
        and len(aula.get("acompanhamento") or []) >= 3
        and len(aula.get("acessibilidade") or []) >= 3
    ):
        aulas[numero] = aula


@lru_cache(maxsize=16)
def _carregar_referencias_docx(caminho_docx: str) -> dict[int, dict[str, Any]]:
    paragrafos = _paragrafos_docx(caminho_docx)
    aulas: dict[int, dict[str, Any]] = {}
    aula_atual: dict[str, Any] | None = None
    secao = ""

    for texto in paragrafos:
        match_aula = re.match(r"^AULA\s+(\d{1,2})\s*[-–—]\s*(.+)$", texto, flags=re.I)
        if match_aula:
            _finalizar_aula(aula_atual, aulas)
            aula_atual = {
                "numero": int(match_aula.group(1)),
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
            item = texto if texto.startswith("☑") else f"☑ {texto.lstrip('☑ ').strip()}"
            aula_atual[secao].append(_normalizar_espacos(item))

    _finalizar_aula(aula_atual, aulas)
    return aulas


def _score_docx_referencia(caminho: Path) -> tuple[int, float, str]:
    nome = _normalizar_busca(caminho.name)
    prioridade_nome = 0
    if "revisado" in nome:
        prioridade_nome = 3
    elif any(token in nome for token in ("corrigido", "atualizado", "novo", "2026")):
        prioridade_nome = 2
    elif "backup" in nome:
        prioridade_nome = -2
    try:
        modificado = caminho.stat().st_mtime
    except OSError:
        modificado = 0.0
    return prioridade_nome, modificado, caminho.name.lower()


def localizar_docx_referencia_matematica(caminho_pdf: str | Path) -> Path | None:
    caminho = Path(caminho_pdf)
    if not caminho_pdf or not caminho.parent.exists():
        return None

    candidatos: list[Path] = []
    padroes = [
        "Metodologias_Matematica*.docx",
        "Metodologias_Matemática*.docx",
        "Metodologia_Matematica*.docx",
        "Metodologia_Matemática*.docx",
    ]
    for padrao in padroes:
        candidatos.extend(caminho.parent.glob(padrao))

    candidatos_unicos = {candidato.resolve(): candidato for candidato in candidatos}.values()
    candidatos_validos = [
        candidato
        for candidato in candidatos_unicos
        if not candidato.name.startswith("~$")
    ]
    if not candidatos_validos:
        return None
    return max(candidatos_validos, key=_score_docx_referencia)


def titulos_referencia_matematica_por_docx(caminho_docx: str | Path) -> dict[int, str]:
    referencias = _carregar_referencias_docx(str(caminho_docx))
    return {
        int(numero): str(referencia.get("titulo") or "").strip()
        for numero, referencia in referencias.items()
        if str(referencia.get("titulo") or "").strip()
    }


def _selecionar_referencia(
    referencias: dict[int, dict[str, Any]],
    numero_aula: int,
    tema: str = "",
) -> dict[str, Any] | None:
    referencia_numerica = referencias.get(numero_aula)
    if not tema:
        return referencia_numerica

    melhor_numero = 0
    melhor_pontuacao = 0.0
    for numero, referencia in referencias.items():
        pontuacao = _pontuar_titulo(tema, referencia.get("titulo", ""))
        if pontuacao > melhor_pontuacao:
            melhor_numero = numero
            melhor_pontuacao = pontuacao

    pontuacao_numerica = _pontuar_titulo(
        tema,
        (referencia_numerica or {}).get("titulo", ""),
    )
    if (
        melhor_numero
        and melhor_pontuacao >= 0.50
        and melhor_pontuacao > pontuacao_numerica + 0.15
    ):
        return referencias.get(melhor_numero)
    return referencia_numerica or (
        referencias.get(melhor_numero) if melhor_pontuacao >= 0.70 else None
    )


def referencia_matematica_por_pdf(
    caminho_pdf: str | Path,
    numero_aula: Any,
    tema: str = "",
) -> dict[str, Any] | None:
    docx = localizar_docx_referencia_matematica(caminho_pdf)
    if not docx:
        return None
    numero = _normalizar_numero_aula(numero_aula)
    if not numero:
        numero = _normalizar_numero_aula(Path(caminho_pdf).stem)
    if not numero:
        return None

    referencias = _carregar_referencias_docx(str(docx))
    referencia = _selecionar_referencia(referencias, numero, tema)
    if not referencia:
        return None
    return {
        "numero": referencia.get("numero", numero),
        "titulo": referencia.get("titulo", ""),
        "metodologia": list(referencia.get("metodologia") or []),
        "acompanhamento": list(referencia.get("acompanhamento") or [])[:3],
        "acessibilidade": list(referencia.get("acessibilidade") or [])[:3],
        "fonte": str(docx),
        "referencia_pedagogica_aplicada": True,
    }
