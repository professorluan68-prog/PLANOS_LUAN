"""Valida o contrato minimo das etapas pedagogicas de uma metodologia."""

from __future__ import annotations

from core.lib.classificador import normalizar_texto


_ETAPAS_OBRIGATORIAS = (
    ("Para começar ou Relembre", ("para comecar", "relembre")),
    ("Foco no conteúdo", ("foco no conteudo",)),
    ("Na prática", ("na pratica",)),
    ("Encerramento", ("encerramento",)),
)


def eh_titulo_etapa_obrigatoria(titulo: object) -> bool:
    titulo_normalizado = normalizar_texto(titulo)
    return any(
        titulo_normalizado.startswith(alternativa)
        for _, alternativas in _ETAPAS_OBRIGATORIAS
        for alternativa in alternativas
    )


def validar_etapas_obrigatorias(metodologia: object) -> tuple[bool, str]:
    """Exige apenas as quatro etapas mínimas, sem impor ordem ou quantidade."""
    titulos = [
        normalizar_texto(item.get("titulo", ""))
        for item in (metodologia or [])
        if isinstance(item, dict) and str(item.get("texto", "")).strip()
    ]
    ausentes = [
        rotulo
        for rotulo, alternativas in _ETAPAS_OBRIGATORIAS
        if not any(any(titulo.startswith(alternativa) for alternativa in alternativas) for titulo in titulos)
    ]
    if not ausentes:
        return True, ""
    return False, "Metodologia sem etapa(s) obrigatória(s): " + ", ".join(ausentes) + "."
