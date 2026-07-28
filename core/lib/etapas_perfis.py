"""Etapas metodológicas especializadas por perfil disciplinar.

Cada função preserva a ordem e as chaves usadas pelo motor legado.
"""

from __future__ import annotations


def etapas_educacao_financeira(tipo: str) -> list[tuple[str, str]]:
    if tipo == "aula_pratica_continuidade":
        return [
            ("Para começar", "retomada_conceitual"),
            ("Foco no conteúdo", "contextualizacao_pratica"),
            ("Na prática", "atividade_central"),
            ("Encerramento", "encerramento_reflexivo"),
        ]

    etapas = [
        ("Para começar", "para_comecar"),
        ("Análise de caso", "analise_caso"),
        ("Foco no conteúdo", "foco"),
        ("Pause e responda", "pause"),
    ]
    if tipo in {
        "credito_endividamento",
        "investimento_poupanca",
        "analise_percentuais_noticias",
    }:
        etapas.extend(
            [
                ("Cálculos financeiros", "calculos"),
                ("Na prática", "pratica"),
            ]
        )
    elif tipo == "orcamento_planejamento":
        etapas.append(("Planejamento orçamentário", "planejamento"))
    elif tipo == "empreendedorismo":
        etapas.append(("Projeto empreendedor", "projeto"))
    else:
        etapas.append(("Na prática", "pratica"))
    etapas.append(("Encerramento", "encerramento"))
    return etapas
