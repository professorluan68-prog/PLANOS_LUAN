from core.normalizacao import normalizar as normalizar_texto_lote

def _linha_instrucao_matematica(linha: str) -> bool:
    normalizada = normalizar_texto_lote(linha)
    inicios_instrucao = (
        "resolva",
        "calcule",
        "determine",
        "registre",
        "complete",
        "observe",
        "assinale",
        "responda",
        "explique",
        "justifique",
        "copie",
        "escreva",
        "analise",
    )
    return normalizada.startswith(inicios_instrucao)
