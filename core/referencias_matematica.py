"""Referencias prontas de Matematica a partir de DOCX na pasta dos PDFs."""

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
    paragrafos_docx as _paragrafos_docx,
    parte_titulo as _parte_titulo,
    pontuar_titulo as _pontuar_titulo,
    selecionar_referencia as _selecionar_referencia,
    tokens_titulo as _tokens_titulo,
)












def _normalizar_numero_aula(valor: Any) -> int:
    if isinstance(valor, int):
        return valor
    match = re.search(r"\d{1,3}", str(valor or ""))
    return int(match.group(0)) if match else 0






@lru_cache(maxsize=16)
def _carregar_referencias_docx(caminho_docx: str) -> dict[int, dict[str, Any]]:
    return carregar_referencias_docx(caminho_docx,
        normalizar_secoes=True,
    )


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
