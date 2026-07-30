# -*- coding: utf-8 -*-
from core.lib.metodologia import _frases_por_contexto


TECNICAS = {
    "abertura": "Virem e conversem",
    "registro": "Todo mundo escreve",
    "sintese": "Com suas palavras",
    "verificacao": "Pause e responda",
}


def _frases(perfil, tipo, *, tema="Tema da aula", conceito="Conceito da aula", recursos=None):
    return _frases_por_contexto(
        perfil=perfil,
        tipo=tipo,
        tema=tema,
        conceito=conceito,
        turma="1º ANO A",
        tecnicas=TECNICAS,
        recursos_detectados=recursos or [],
    )


def test_frases_educacao_financeira_preservam_credito_e_simulacao():
    frases = _frases(
        "educacao_financeira",
        "credito_endividamento",
        tema="Uso consciente do crédito",
        conceito="Crédito responsável",
    )

    assert "valor à vista, juros, parcelas e custo total" in frases["para_comecar"]
    assert "juros, parcelas, custo total, riscos de endividamento" in frases["foco"]
    assert frases["pratica"] == frases["simulacao"]
    assert "informações financeiras pessoais" in frases["encerramento"]


def test_frases_tecnologia_preservam_comandos_do_startlab():
    frases = _frases(
        "tecnologia_inovacao",
        "programacao_inicial",
        tema="Primeiros comandos",
        conceito="Programação em blocos",
    )

    assert "teclado, o mouse ou botoes de inicio" in frases["para_comecar"]
    assert "StartLab" in frases["foco"]
    assert "bandeira verde" in frases["foco"]
    assert "ambiente de programacao" in frases["pratica"]


def test_frases_orientacao_estudos_preservam_leitura_de_grafico():
    frases = _frases(
        "orientacao_estudos",
        "simples",
        tema="Leitura de gráficos",
        conceito="Análise de dados",
        recursos=["analise_grafico"],
    )

    assert "titulo, legendas, linhas, colunas, valores e comparacoes" in frases["foco"]
    assert "leitura dos dados em etapas" in frases["pratica"]


def test_frases_quimica_preservam_abordagem_investigativa():
    frases = _frases(
        "quimica",
        "simples",
        tema="Transformações químicas",
        conceito="Reações químicas",
    )

    assert "situação-problema, imagem, dado ou exemplo do cotidiano" in frases["para_comecar"]
    assert "observação, hipótese e conceito científico" in frases["foco"]
    assert "evidências usadas pelos estudantes" in frases["pratica"]


def test_frases_sociologia_preservam_estranhamento_e_analise_critica():
    frases = _frases(
        "sociologia",
        "simples",
        tema="Desigualdade social",
        conceito="Estratificação social",
    )

    assert "provocando estranhamento e questionamentos iniciais" in frases["para_comecar"]
    assert "superar leituras baseadas apenas no senso comum" in frases["foco"]
