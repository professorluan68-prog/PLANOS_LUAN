from core.ia import _normalizar_saida_ia
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.qualidade_metodologica import sanitizar_texto_metodologico


def test_sanitiza_fragmentos_quebrados_de_tecnica_e_placeholder():
    texto = sanitizar_texto_metodologico(
        "Aplicar o para que os estudantes levantem hipoteses. "
        "Utilizar o em um exemplo pratico. "
        "Conduzir atividade com material impresso, quadro e registro no caderno. "
        "Incorporar uma etapa ao desenvolvimento da aula, articulando-a aos exemplos, registros e intervenções do professor."
    )

    texto_norm = texto.lower()
    assert "aplicar o para" not in texto_norm
    assert "utilizar o em um exemplo" not in texto_norm
    assert "material impresso, quadro e registro no caderno" not in texto_norm
    assert "ao desenvolvimento da aula, articulando-a" not in texto_norm


def test_ia_fallback_de_aprendizagem_para_portugues_fica_especifico():
    saida = _normalizar_saida_ia(
        {
            "tema": "AULA 2 - As origens do Trovadorismo",
            "aprendizagem": "Habilidade: (EM13LGG601) Desenvolver habilidades relacionadas ao tema da aula, com foco em As origens do Trovadorismo.",
            "metodologia": [
                {"titulo": "Para comecar", "texto": "Retomar uma cantiga medieval e levantar hipoteses sobre o contexto da aula."},
                {"titulo": "Foco no conteudo", "texto": "Conduzir leitura orientada das cantigas e discutir caracteristicas do trovadorismo."},
                {"titulo": "Encerramento", "texto": "Sistematizar o que foi observado nos textos lidos."},
            ],
        },
        texto_pdf="Lingua Portuguesa\nAs origens do Trovadorismo\nCantigas de Santa Maria e leitura de textos medievais.",
        disciplina="Lingua Portuguesa",
        turma="1o ano EM",
    )

    aprendizagem = saida["aprendizagem"].lower()
    assert "desenvolver habilidades relacionadas ao tema da aula" not in aprendizagem
    assert "leitura" in aprendizagem
    assert "interpretacao" in aprendizagem


def test_acompanhamento_matematica_nao_recebe_texto_de_astronomia_por_falso_positivo():
    itens = gerar_acompanhamento_aprimorado(
        tema="Media aritmetica",
        aprendizagem="Resolver problemas envolvendo media aritmetica.",
        desenvolvimento="Conduzir o preenchimento de uma tabela com gols e notas, seguido de resolucao de problemas e registro no caderno.",
        disciplina="Matematica",
        perfil="matematica",
    )

    texto = " ".join(itens).lower()
    assert "movimentos, fases" not in texto
    assert "informacoes cientificas" not in texto
    assert "tabelas" in texto or "dados" in texto or "grafica" in texto


def test_acessibilidade_historia_nao_usa_apoio_matematico():
    itens = gerar_acessibilidade_aprimorada(
        tema="Revoltas regenciais: Sabinada",
        aprendizagem="Analisar a Sabinada e seus contextos politicos.",
        desenvolvimento="Organizar leitura de fonte historica, quadro comparativo e registro em tabela sobre causas e consequencias da revolta.",
        disciplina="Historia",
        perfil="historia",
    )

    texto = " ".join(itens).lower()
    assert "tabuada" not in texto
    assert "calculadora" not in texto
    assert "fonte" in texto or "histor" in texto or "tabela" in texto
