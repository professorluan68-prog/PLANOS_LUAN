"""Referencias prontas de Orientacao de Estudos a partir de DOCX na pasta dos PDFs."""

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


def _normalizar_numero_aula(valor: Any) -> int:
    if isinstance(valor, int):
        return valor
    match = re.search(r"\d{1,2}", str(valor or ""))
    return int(match.group(0)) if match else 0


def _normalizar_habilidade(texto: str) -> str:
    texto = _normalizar_espacos(texto)
    texto = re.sub(r"^[\s.,;:–—-]+", "", texto).strip()
    texto = re.sub(r"\be\.\s+(?=(?:LP|EF|EM)\d)", "e ", texto)
    return texto


def _separar_titulo_habilidade(texto: str) -> tuple[str, str]:
    texto = _normalizar_espacos(texto)
    match = re.search(r"\bHABILIDADE\s*:\s*", texto, flags=re.I)
    if not match:
        return texto, ""
    titulo = _normalizar_espacos(texto[: match.start()])
    habilidade = _normalizar_habilidade(texto[match.end() :])
    return titulo, habilidade


def _paragrafos_docx(caminho_docx: str) -> list[str]:
    try:
        from docx import Document
    except Exception:
        return []

    try:
        doc = Document(caminho_docx)
    except Exception:
        return []

    return [_normalizar_espacos(paragrafo.text) for paragrafo in doc.paragraphs if _normalizar_espacos(paragrafo.text)]


def _finalizar_aula(aula: dict[str, Any] | None, aulas: dict[int, dict[str, Any]]) -> None:
    if not aula:
        return
    numero = _normalizar_numero_aula(aula.get("numero"))
    if not numero:
        return
    if aula.get("metodologia") and len(aula.get("acompanhamento") or []) >= 3 and len(aula.get("acessibilidade") or []) >= 3:
        aulas[numero] = aula


@lru_cache(maxsize=16)
def _carregar_referencias_docx(caminho_docx: str) -> dict[int, dict[str, Any]]:
    paragrafos = _paragrafos_docx(caminho_docx)
    aulas: dict[int, dict[str, Any]] = {}
    aula_atual: dict[str, Any] | None = None
    secao = ""

    for texto in paragrafos:
        match_aula = re.match(r"^AULA\s+(\d{1,2})[\s\-–—.:]*(.+)$", texto, flags=re.I)
        if match_aula:
            _finalizar_aula(aula_atual, aulas)
            titulo, habilidade = _separar_titulo_habilidade(match_aula.group(2))
            aula_atual = {
                "numero": int(match_aula.group(1)),
                "titulo": titulo,
                "habilidade": habilidade,
                "metodologia": [],
                "acompanhamento": [],
                "acessibilidade": [],
            }
            secao = ""
            continue

        if not aula_atual:
            continue

        texto_norm = _normalizar_busca(texto)
        if texto_norm.startswith("habilidade "):
            _, habilidade = _separar_titulo_habilidade(texto)
            aula_atual["habilidade"] = habilidade
            continue
        if texto_norm == "metodologia":
            secao = "metodologia"
            continue
        if texto_norm == "acompanhamento da aprendizagem":
            secao = "acompanhamento"
            continue
        if texto_norm == "acessibilidade":
            secao = "acessibilidade"
            continue

        if not secao and aula_atual.get("habilidade"):
            aula_atual["habilidade"] = _normalizar_habilidade(
                f"{aula_atual['habilidade']} {texto}"
            )
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
    if any(token in nome for token in ("corrigido", "atualizado", "novo", "2026")):
        prioridade_nome = 1
    try:
        modificado = caminho.stat().st_mtime
    except OSError:
        modificado = 0.0
    return prioridade_nome, modificado, caminho.name.lower()


def localizar_docx_referencia_orientacao_estudos(caminho_pdf: str | Path) -> Path | None:
    caminho = Path(caminho_pdf)
    if not caminho_pdf or not caminho.parent.exists():
        return None

    candidatos = list(caminho.parent.glob("Metodologias_Orientacao_de_Estudos*.docx"))
    candidatos.extend(caminho.parent.glob("*Orientacao*Estudos*Metodologia*.docx"))
    candidatos.extend(caminho.parent.glob("*Orientação*Estudos*Metodologia*.docx"))
    candidatos.extend(caminho.parent.glob("*Metodologia*.docx"))
    candidatos_unicos = {candidato.resolve(): candidato for candidato in candidatos}.values()
    candidatos_validos = [candidato for candidato in candidatos_unicos if not candidato.name.startswith("~$")]
    if not candidatos_validos:
        return None
    return max(candidatos_validos, key=_score_docx_referencia)


def titulos_referencia_orientacao_estudos_por_docx(caminho_docx: str | Path) -> dict[int, str]:
    referencias = _carregar_referencias_docx(str(caminho_docx))
    return {
        int(numero): str(referencia.get("titulo") or "").strip()
        for numero, referencia in referencias.items()
        if str(referencia.get("titulo") or "").strip()
    }


def _arquivo_parece_referencia_nao_aula(caminho: Path) -> bool:
    nome = _normalizar_busca(caminho.stem)
    marcadores = (
        "matriz de referencia",
        "matriz referencia",
        "referencial curricular",
    )
    return any(marcador in nome for marcador in marcadores)


def _numero_por_ordem_na_pasta(caminho_pdf: Path, referencias: dict[int, dict[str, Any]]) -> int:
    if not referencias or not caminho_pdf.exists():
        return 0
    try:
        pdfs = [
            item
            for item in caminho_pdf.parent.glob("*.pdf")
            if item.is_file() and not _arquivo_parece_referencia_nao_aula(item)
        ]
    except OSError:
        return 0
    pdfs = sorted(pdfs, key=lambda item: item.name.lower())
    try:
        posicao = pdfs.index(caminho_pdf) + 1
    except ValueError:
        return 0
    return posicao if posicao in referencias else 0


def referencia_orientacao_estudos_por_pdf(caminho_pdf: str | Path, numero_aula: Any, tema: str = "") -> dict[str, Any] | None:
    docx = localizar_docx_referencia_orientacao_estudos(caminho_pdf)
    if not docx:
        return None
    referencias = _carregar_referencias_docx(str(docx))
    caminho = Path(caminho_pdf)
    nome_busca = _normalizar_busca(caminho.stem)
    numero_por_ordem = _numero_por_ordem_na_pasta(caminho, referencias)

    numero = _normalizar_numero_aula(numero_aula)
    if numero not in referencias and numero_por_ordem:
        numero = numero_por_ordem
    elif numero_por_ordem and "aula" not in nome_busca:
        numero = numero_por_ordem
    if not numero:
        numero = _normalizar_numero_aula(caminho.stem)
    if numero not in referencias and numero_por_ordem:
        numero = numero_por_ordem
    if not numero:
        return None
    referencia = referencias.get(numero)
    if not referencia:
        return None
    return {
        "numero": numero,
        "titulo": referencia.get("titulo", ""),
        "habilidade": referencia.get("habilidade", ""),
        "metodologia": list(referencia.get("metodologia") or []),
        "acompanhamento": list(referencia.get("acompanhamento") or [])[:3],
        "acessibilidade": list(referencia.get("acessibilidade") or [])[:3],
        "fonte": str(docx),
        "referencia_pedagogica_aplicada": True,
    }
