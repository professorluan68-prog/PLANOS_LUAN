from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


STATUS_DOCX_LITERAL = "docx_literal"
STATUS_DOCX_REFINADO_IA = "docx_refinado_ia"
STATUS_AULA_AUSENTE_OU_INCOMPLETA = "aula_ausente_ou_incompleta"
STATUS_DOCX_AUSENTE = "docx_ausente"

_STATUS_FALLBACK = {
    STATUS_AULA_AUSENTE_OU_INCOMPLETA,
    STATUS_DOCX_AUSENTE,
}


def _primeiro_valor(aula: Mapping[str, Any], *campos: str) -> Any:
    for campo in campos:
        valor = aula.get(campo)
        if valor not in (None, ""):
            return valor
    return ""


def _nome_arquivo_referencia(aula: Mapping[str, Any]) -> str:
    caminho = _primeiro_valor(
        aula,
        "arquivo_referencia_docx",
        "fonte_referencia_metodologia",
        "caminho_referencia_docx",
    )
    if not caminho:
        return ""
    return Path(str(caminho)).name


def resumir_proveniencia_docx(
    turmas_processadas: Iterable[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Resume a origem DOCX das aulas sem modificar os dados recebidos.

    O resumo expõe somente o nome dos arquivos de referência. Caminhos absolutos
    guardados nas aulas nunca são devolvidos pela função.
    """

    resumo: dict[str, Any] = {
        "total_aulas": 0,
        STATUS_DOCX_LITERAL: 0,
        STATUS_DOCX_REFINADO_IA: 0,
        "fallback": 0,
        "arquivos": [],
        "falhas": [],
    }
    arquivos_vistos: set[str] = set()

    for turma_processada in turmas_processadas or []:
        turma = turma_processada.get("turma") or ""
        for aula in turma_processada.get("aulas") or []:
            resumo["total_aulas"] += 1
            status = aula.get("status_referencia_docx") or ""

            if status == STATUS_DOCX_LITERAL:
                resumo[STATUS_DOCX_LITERAL] += 1
            elif status == STATUS_DOCX_REFINADO_IA:
                resumo[STATUS_DOCX_REFINADO_IA] += 1
            elif status in _STATUS_FALLBACK:
                resumo["fallback"] += 1
                resumo["falhas"].append(
                    {
                        "turma": turma,
                        "numero_aula": aula.get("numero_aula") or "",
                        "tema": aula.get("tema") or "",
                        "status": status,
                        "motivo": _primeiro_valor(
                            aula,
                            "motivo_referencia_docx",
                            "motivo",
                        ),
                    }
                )

            nome_arquivo = _nome_arquivo_referencia(aula)
            chave_arquivo = nome_arquivo.casefold()
            if nome_arquivo and chave_arquivo not in arquivos_vistos:
                arquivos_vistos.add(chave_arquivo)
                resumo["arquivos"].append(nome_arquivo)

    return resumo
