"""Referencias prontas de Ciencias a partir de DOCX na pasta dos PDFs."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.referencias_base import (
    normalizar_busca as _normalizar_busca,
    normalizar_espacos,
    normalizar_numero_aula as _normalizar_numero_aula,
    paragrafos_docx,
    parte_titulo as _parte_titulo,
    pontuar_titulo as _pontuar_titulo,
    score_docx_referencia as _score_docx_referencia,
    selecionar_referencia as _selecionar_referencia,
    tokens_titulo as _tokens_titulo,
)

from core.padrao_mestre_metodologia import (
    extrair_paragrafos_docx,
    inferir_turma_de_caminho,
    normalizar_referencia_pedagogica,
)


def _normalizar_espacos(texto: str) -> str:
    return normalizar_espacos(texto, remover_espaco_antes_pontuacao=True)












def _paragrafos_docx(caminho_docx: str) -> list[str]:
    return paragrafos_docx(caminho_docx, remover_espaco_antes_pontuacao=True)


def _finalizar_aula(
    aula: dict[str, Any] | None,
    aulas: dict[int, dict[str, Any]],
    disciplina: str = "Ciências",
    turma: str = "",
) -> None:
    if not aula:
        return
    aula = normalizar_referencia_pedagogica(aula, disciplina=disciplina, turma=turma)
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
    turma = inferir_turma_de_caminho(caminho_docx)

    for texto in paragrafos:
        match_aula = re.match(r"^(?:📘\s*)?AULA\s+(\d{1,2})\s*[-–—]\s*(.+)$", texto, flags=re.I)
        if match_aula:
            _finalizar_aula(aula_atual, aulas, disciplina="Ciências", turma=turma)
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

        texto_norm = texto.lower()
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

    _finalizar_aula(aula_atual, aulas, disciplina="Ciências", turma=turma)
    return aulas




def localizar_docx_referencia_ciencias(caminho_pdf: str | Path) -> Path | None:
    caminho = Path(caminho_pdf)
    if not caminho_pdf or not caminho.parent.exists():
        return None

    candidatos = list(caminho.parent.glob("Metodologias_Ciencias*.docx"))
    candidatos.extend(caminho.parent.glob("*Ciencias*Metodologia*.docx"))
    candidatos.extend(caminho.parent.glob("*Metodologia*.docx"))
    candidatos_unicos = {candidato.resolve(): candidato for candidato in candidatos}.values()
    candidatos_validos = [candidato for candidato in candidatos_unicos if not candidato.name.startswith("~$")]
    if not candidatos_validos:
        return None
    return max(candidatos_validos, key=_score_docx_referencia)


def titulos_referencia_ciencias_por_docx(caminho_docx: str | Path) -> dict[int, str]:
    referencias = _carregar_referencias_docx(str(caminho_docx))
    return {
        int(numero): str(referencia.get("titulo") or "").strip()
        for numero, referencia in referencias.items()
        if str(referencia.get("titulo") or "").strip()
    }




def referencia_ciencias_por_pdf(caminho_pdf: str | Path, numero_aula: Any, tema: str = "") -> dict[str, Any] | None:
    docx = localizar_docx_referencia_ciencias(caminho_pdf)
    if not docx:
        return None
    numero = _normalizar_numero_aula(numero_aula)
    if not numero:
        numero = _normalizar_numero_aula(Path(caminho_pdf).name)
    if not numero:
        return None
    referencias = _carregar_referencias_docx(str(docx))
    referencia = _selecionar_referencia(referencias, numero, tema)
    if not referencia:
        return None
    return {
        "titulo": referencia.get("titulo", ""),
        "metodologia": list(referencia.get("metodologia") or []),
        "acompanhamento": list(referencia.get("acompanhamento") or [])[:3],
        "acessibilidade": list(referencia.get("acessibilidade") or [])[:3],
        "fonte": str(docx),
        "referencia_pedagogica_aplicada": True,
    }
