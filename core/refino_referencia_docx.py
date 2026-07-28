"""Contrato de preservacao quando a IA aprimora uma referencia em DOCX."""

from __future__ import annotations

from core.estrutura_metodologia import validar_etapas_obrigatorias


def _etapas_validas(valor: object) -> list[dict]:
    return [item for item in (valor or []) if isinstance(item, dict)]


def validar_refino_ia_do_docx(
    referencia_docx: dict | None,
    plano_ia: dict | None,
) -> tuple[bool, str]:
    """Valida o refino da IA sem impor a ordem ou a contagem do DOCX."""
    etapas_docx = _etapas_validas((referencia_docx or {}).get("metodologia"))
    etapas_ia = _etapas_validas((plano_ia or {}).get("metodologia"))
    if not etapas_docx:
        return True, ""
    return validar_etapas_obrigatorias(etapas_ia)
