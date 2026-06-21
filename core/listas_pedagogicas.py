"""Regras compartilhadas para listas pedagogicas do plano."""


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
