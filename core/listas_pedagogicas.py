"""Regras compartilhadas para listas pedagogicas do plano."""

import re

from core.qualidade_metodologica import corrigir_mojibake, limitar_texto_natural


def itens_lista_pedagogica(valor) -> list[str]:
    if not isinstance(valor, list):
        return []
    return [str(item).strip() for item in valor if str(item).strip()]


def problemas_lista_exatamente_tres(
    nome_campo: str,
    itens: list[str],
    prefixo: str = "",
) -> list[str]:
    problemas = []
    if len(itens) != 3:
        problemas.append(
            f"{prefixo}{nome_campo} deve ter exatamente 3 itens; "
            f"foram encontrados {len(itens)}."
        )
    if itens and any(not item.startswith("☑") for item in itens):
        problemas.append(f"{prefixo}{nome_campo} deve ter todos os itens iniciando com ☑.")
    return problemas


def normalizar_lista_exatamente_tres(
    itens,
    fallbacks,
    max_chars: int = 220,
) -> list[str]:
    """Formata listas pedagogicas com exatamente 3 itens iniciados por ☑."""
    saida = []
    candidatos = list(itens or []) + list(fallbacks or [])

    for texto in candidatos:
        txt = corrigir_mojibake(re.sub(r"\s+", " ", str(texto or "")).strip())
        if not txt:
            continue
        txt = re.sub(r"^(?:[☑☒☐✓•*+\-]|\[[ xX]\])+\s*", "", txt).strip()
        if not txt:
            continue
        if len(txt) > max_chars:
            txt = limitar_texto_natural(txt, max_chars)
        item = f"☑ {txt}"
        if item not in saida:
            saida.append(item)
        if len(saida) == 3:
            return saida

    while len(saida) < 3:
        saida.append("☑ Acompanhar a realização da atividade com mediação do professor e retomadas conforme as necessidades da turma.")

    return saida[:3]
