"""Referencias prontas de Biologia a partir de DOCX na pasta dos PDFs."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.referencias_base import (
    carregar_referencias_docx,
    finalizar_aula as _finalizar_aula,
    normalizar_busca as _normalizar_busca,
    normalizar_espacos as _normalizar_espacos,
    normalizar_numero_aula as _normalizar_numero_aula,
    paragrafos_docx as _paragrafos_docx,
    parte_titulo as _parte_titulo,
    pontuar_titulo as _pontuar_titulo,
    score_docx_referencia as _score_docx_referencia,
    selecionar_referencia as _selecionar_referencia,
    tokens_titulo as _tokens_titulo,
)


















@lru_cache(maxsize=16)
def _carregar_referencias_docx(caminho_docx: str) -> dict[int, dict[str, Any]]:
    return carregar_referencias_docx(caminho_docx,
        padrao_aula=r"^AULA(?:\s+|_)(\d{1,2})\s*[-\u2013\u2014]\s*(.+)$",
        remover_espaco_antes_pontuacao=True,
    )




def localizar_docx_referencia_biologia(caminho_pdf: str | Path) -> Path | None:
    caminho = Path(caminho_pdf)
    if not caminho_pdf or not caminho.parent.exists():
        return None

    candidatos = list(caminho.parent.glob("Metodologias_Biologia*.docx"))
    candidatos.extend(caminho.parent.glob("*Biologia*Metodologia*.docx"))
    candidatos.extend(caminho.parent.glob("*Metodologia*.docx"))
    candidatos_unicos = {candidato.resolve(): candidato for candidato in candidatos}.values()
    candidatos_validos = [candidato for candidato in candidatos_unicos if not candidato.name.startswith("~$")]
    if not candidatos_validos:
        return None
    return max(candidatos_validos, key=_score_docx_referencia)


def titulos_referencia_biologia_por_docx(caminho_docx: str | Path) -> dict[int, str]:
    referencias = _carregar_referencias_docx(str(caminho_docx))
    return {
        int(numero): str(referencia.get("titulo") or "").strip()
        for numero, referencia in referencias.items()
        if str(referencia.get("titulo") or "").strip()
    }




def referencia_biologia_por_pdf(caminho_pdf: str | Path, numero_aula: Any, tema: str = "") -> dict[str, Any] | None:
    docx = localizar_docx_referencia_biologia(caminho_pdf)
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
        "titulo": referencia.get("titulo", ""),
        "metodologia": list(referencia.get("metodologia") or []),
        "acompanhamento": list(referencia.get("acompanhamento") or [])[:3],
        "acessibilidade": list(referencia.get("acessibilidade") or [])[:3],
        "fonte": str(docx),
        "referencia_pedagogica_aplicada": True,
    }
