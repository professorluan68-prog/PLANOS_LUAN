"""Contrato de preservacao quando a IA aprimora uma referencia em DOCX."""

from __future__ import annotations

from core.lib.classificador import normalizar_texto


def _etapas_validas(valor: object) -> list[dict]:
    return [item for item in (valor or []) if isinstance(item, dict)]


def validar_refino_ia_do_docx(
    referencia_docx: dict | None,
    plano_ia: dict | None,
) -> tuple[bool, str]:
    """Garante que a IA preserve a estrutura pedagogica cadastrada no DOCX."""
    etapas_docx = _etapas_validas((referencia_docx or {}).get("metodologia"))
    etapas_ia = _etapas_validas((plano_ia or {}).get("metodologia"))
    if not etapas_docx:
        return True, ""
    if len(etapas_ia) != len(etapas_docx):
        return False, "A IA alterou a quantidade de etapas do DOCX."

    for indice, (etapa_docx, etapa_ia) in enumerate(zip(etapas_docx, etapas_ia), start=1):
        titulo_docx = normalizar_texto(etapa_docx.get("titulo", ""))
        titulo_ia = normalizar_texto(etapa_ia.get("titulo", ""))
        if not titulo_docx or titulo_ia != titulo_docx:
            return False, f"A IA alterou o titulo ou a ordem da etapa {indice} do DOCX."
        if not str(etapa_ia.get("texto", "")).strip():
            return False, f"A IA deixou a etapa {indice} do DOCX sem texto."

    for chave, rotulo in (
        ("acompanhamento", "acompanhamento da aprendizagem"),
        ("acessibilidade", "acessibilidade"),
    ):
        itens_docx = [item for item in (referencia_docx or {}).get(chave, []) if str(item).strip()]
        itens_ia = [item for item in (plano_ia or {}).get(chave, []) if str(item).strip()]
        if itens_docx and len(itens_ia) < len(itens_docx):
            return False, f"A IA removeu item(ns) de {rotulo} do DOCX."
    return True, ""
