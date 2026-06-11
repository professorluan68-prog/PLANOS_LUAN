# -*- coding: utf-8 -*-
"""
Testes unitários para o higienizador pedagógico.
"""

from core.lib.higienizador_pedagogico import (
    higienizar_plano,
    detectar_perfil_pedagogico_real,
    detectar_recursos_reais,
    limpar_falsos_positivos_texto
)
import pytest


def test_detectar_perfil_pedagogico_real():
    assert detectar_perfil_pedagogico_real("Segunda geração modernista: Prosa de 30", "Língua Portuguesa") == "literatura"
    assert detectar_perfil_pedagogico_real("Os olhares do cotidiano desvendando o gênero crônica", "Língua Portuguesa") == "cronica"
    assert detectar_perfil_pedagogico_real("Por dentro das normas – Parte 2", "Língua Portuguesa") == "texto_normativo"
    assert detectar_perfil_pedagogico_real("Textos contemporâneos na construção da opinião", "Língua Portuguesa") == "artigo_opiniao"
    assert detectar_perfil_pedagogico_real("Visões diversas em editoriais", "Língua Portuguesa") == "editorial"
    assert detectar_perfil_pedagogico_real("Oralidade: entrevista – Parte 1", "Língua Portuguesa") == "entrevista"
    assert detectar_perfil_pedagogico_real("Análise de notícia e reportagem", "Língua Portuguesa") == "jornalistico_valido"
    assert detectar_perfil_pedagogico_real("Equações do 2º Grau", "Matemática") == "matematica_calculo"


@pytest.mark.parametrize(
    ("titulo", "esperado"),
    [
        ("Por dentro das normas – Parte 1", "texto_normativo"),
        ("Por dentro das normas – Parte 2", "texto_normativo"),
        ("Textos contemporâneos na construção da opinião – Parte 1", "artigo_opiniao"),
        ("Textos contemporâneos na construção da opinião – Parte 2", "artigo_opiniao"),
        ("Textos contemporâneos na construção da opinião – Parte 3", "artigo_opiniao"),
        ("Textos contemporâneos na construção da opinião – Parte 4", "artigo_opiniao"),
        ("Oralidade: entrevista – Parte 1", "entrevista"),
        ("Oralidade: entrevista – Parte 2", "entrevista"),
        ("O que o texto revela", "literatura"),
        ("Os movimentos da literatura: influências e inovações", "literatura"),
        ("Vanguardas europeias", "literatura"),
        ("Semana de Arte Moderna", "literatura"),
        ("Primeira geração modernista – Parte 1", "literatura"),
        ("Primeira geração modernista – Parte 2", "literatura"),
        ("Segunda geração modernista: poesia da década de 1930 – Parte 1", "literatura"),
        ("Segunda geração modernista: poesia da década de 1930 – Parte 2", "literatura"),
        ("Segunda geração modernista: Prosa de 30 – Parte 1", "literatura"),
        ("Segunda geração modernista: Prosa de 30 – Parte 2", "literatura"),
        ("Segunda geração modernista: Prosa de 30 – Parte 3", "literatura"),
        ("Visões diversas em editoriais – Parte 1", "editorial"),
        ("Visões diversas em editoriais – Parte 2", "editorial"),
        ("Visões diversas em editoriais – Parte 3", "editorial"),
        ("Visões diversas em editoriais – Parte 4", "editorial"),
        ("Os olhares do cotidiano: desvendando o gênero crônica – Parte 1", "cronica"),
        ("Os olhares do cotidiano: desvendando o gênero crônica – Parte 2", "cronica"),
        ("Os olhares do cotidiano: desvendando o gênero crônica – Parte 3", "cronica"),
    ],
)
def test_auditoria_portugues_2b_classifica_26_aulas(titulo, esperado):
    assert detectar_perfil_pedagogico_real(titulo, "Língua Portuguesa") == esperado


@pytest.mark.parametrize(
    ("titulo", "esperado"),
    [
        ("Anuncie aqui! – Parte 1", "texto_publicitario"),
        ("História de uma vida – Parte 2", "biografia"),
        ("O jornalismo em imagens – Parte 1", "noticia_multimodal"),
        ("Vozes da redação jornalística – Parte 2", "editorial"),
        ("Uma narrativa pode moldar uma imagem? – Parte 2", "conto_distopico"),
    ],
)
def test_auditoria_portugues_ef_em_classifica_modelos_adicionais(titulo, esperado):
    assert detectar_perfil_pedagogico_real(titulo, "Língua Portuguesa") == esperado


@pytest.mark.parametrize(
    ("disciplina", "titulo", "esperado"),
    [
        ("Arte", "A vida na música", "arte_musica"),
        ("Biologia", "Efeito estufa: manutenção da vida", "biologia_conceitual"),
        ("Ciências", "Materiais sintéticos", "ciencias_conceitual"),
        ("Educação Financeira", "Definição de objetivos – Parte 1", "educacao_financeira_planejamento"),
        ("Geografia", "A expansão da urbanização no Brasil ao longo dos séculos", "geografia_conceitual_espaco"),
        ("História", "O surgimento dos primeiros assentamentos, cidades e civilizações", "historia_contextual"),
        ("Liderança e Oratória", "A eficácia do discurso oral", "oratoria_pratica"),
        ("Língua Inglesa", "My preferences", "ingles_listening"),
        ("Matemática", "Estratégias de composição e decomposição de números naturais", "matematica_calculo"),
        ("Orientação de Estudos", "Uma palavra puxa a outra - ETAPA 1", "orientacao_estudos_etapas"),
        ("Projeto de Vida", "Quem sou quando estou comigo?", "projeto_vida_autoconhecimento"),
        ("Química", "Funções orgânicas: álcool, aldeído e ácido carboxílico", "quimica_funcoes_organicas"),
        ("Redação e Leitura", "Trilha Alice no País das Maravilhas", "leitura_literaria_trilha"),
        ("Tecnologia e Inovação", "Introdução à computação: entrada e saída no computador", "tecnologia_computacao_conceitual"),
    ],
)
def test_pacote_auditorias_classifica_perfis_por_disciplina(disciplina, titulo, esperado):
    assert detectar_perfil_pedagogico_real(titulo, disciplina) == esperado


def test_limpar_falsos_positivos_texto():
    texto_com_url = "Veja a imagem de Rachel de Queiroz em https://g1.globo.com/ce/ceara/noticia/2019/07/20/campo-de-concentracao.html e comente."
    texto_limpo = limpar_falsos_positivos_texto(texto_com_url)
    assert "g1.globo.com" not in texto_limpo
    assert "noticia" not in texto_limpo


def test_detectar_recursos_reais():
    texto_pdf = (
        "Esta aula trabalha a crônica de Clarice Lispector.\n"
        "Os alunos devem ler o texto e identificar a voz narrativa.\n"
        "Fonte: g1.globo.com/noticia/2026/06/06/imagem.jpg"
    )
    recursos = detectar_recursos_reais(texto_pdf)
    # Deve detectar cronica como presente, mas noticia como ausente por causa do falso positivo da fonte
    assert recursos.get("cronica") is True
    assert recursos.get("noticia") is False
    assert recursos.get("tabela") is False


def test_mapa_conceitual_nao_vira_mapa_geografico():
    recursos = detectar_recursos_reais(
        "A aula trabalha biografia de Lygia Fagundes Telles e organiza informações em mapa conceitual."
    )

    assert recursos.get("mapa_conceitual") is True
    assert recursos.get("mapa") is False


def test_percentual_em_editorial_nao_vira_calculo():
    recursos = detectar_recursos_reais(
        "Editorial sobre cotas raciais menciona 91% em texto corrido, sem comando de calcular ou resolver operações."
    )

    assert recursos.get("calculo") is False
    assert recursos.get("grafico") is False
    assert recursos.get("tabela") is False


def test_quadro_didatico_nao_vira_tabela_de_dados():
    recursos = detectar_recursos_reais(
        "O PDF apresenta quadro de conjunções e exemplos gramaticais para apoiar a análise linguística."
    )

    assert recursos.get("tabela") is False


def test_higienizador_remove_calculo_e_debate_quando_recurso_ausente():
    desenv = "Realizar debate formal e atividade de cálculo sobre o material."
    desenv_h, _, _ = higienizar_plano(
        desenv,
        [],
        [],
        perfil="educacao_financeira",
        disciplina="Educação Financeira",
        tema="Definição de objetivos – Parte 1",
        recursos_reais={"debate": False, "calculo": False, "tabela": False, "grafico": False},
    )

    assert "debate formal" not in desenv_h
    assert "cálculo" not in desenv_h
    assert "conversa orientada" in desenv_h


def test_higienizar_plano_literatura_com_noticia():
    # Desenvolvimento com contaminação de noticia
    desenv = (
        "Para começar: Iniciar a aula com leitura guiada da notícia apresentada no material, "
        "mobilizando conhecimentos prévios e incentivando a turma a identificar o problema central.\n"
        "Na prática: Propor atividade de análise e registro em que os estudantes retomem a notícia."
    )
    acomp = [
        "Verificar se os estudantes identificam o problema central e posicionamentos presentes na notícia analisada."
    ]
    acess = [
        "Oferecer leitura guiada da notícia com destaque para título, informações principais e problema central."
    ]

    # Recursos reais detectados (noticia ausente, tabela ausente, etc.)
    recursos_reais = {"noticia": False, "tabela": False}

    desenv_h, acomp_h, acess_h = higienizar_plano(
        desenv, acomp, acess,
        perfil="lingua_portuguesa_em",
        disciplina="Língua Portuguesa",
        tema="Segunda geração modernista: Prosa de 30",
        recursos_reais=recursos_reais
    )

    # Verifica que "notícia" foi substituída por termos de literatura
    assert "notícia" not in desenv_h
    assert "noticia" not in desenv_h
    assert "obra apresentada" in desenv_h
    assert "texto literário apresentada" not in desenv_h

    assert "notícia" not in acomp_h[0]
    assert "obra analisada" in acomp_h[0] or "texto literário" in acomp_h[0]

    assert "notícia" not in acess_h[0]
    assert "texto literário" in acess_h[0]


def test_higienizar_plano_sem_recurso_tabela():
    desenv = "Desenvolver o conteúdo central da aula por meio da análise de tabelas e gráficos explicativos."
    acomp = ["Verificar se os estudantes interpretam gráficos e tabelas do material."]
    acess = ["Organizar quadro comparativo ou tabela simples para apoiar a distinção."]

    recursos_reais = {"tabela": False, "grafico": False}

    desenv_h, acomp_h, acess_h = higienizar_plano(
        desenv, acomp, acess,
        perfil="matematica",
        disciplina="Matemática",
        tema="Equações do 2º grau",
        recursos_reais=recursos_reais
    )

    # Verifica que termos sobre tabelas e gráficos foram removidos/substituídos por dados/informações do material
    assert "tabela" not in desenv_h
    assert "tabelas" not in desenv_h
    assert "gráfico" not in desenv_h
    assert "gráficos" not in desenv_h
    assert "as informações do material" in desenv_h or "informações do material" in desenv_h


def test_higienizar_artigo_opiniao_nao_mantem_noticia():
    desenv = "Conduzir a leitura orientada da notícia apresentada e verificar o ponto de vista."
    acomp = ["Verificar informações principais presentes na notícia analisada."]
    acess = ["Oferecer leitura guiada da notícia com perguntas orientadoras."]

    desenv_h, acomp_h, acess_h = higienizar_plano(
        desenv, acomp, acess,
        perfil="lingua_portuguesa_em",
        disciplina="Língua Portuguesa",
        tema="Textos contemporâneos na construção da opinião – Parte 1",
        recursos_reais={"noticia": False, "tabela": False, "grafico": False}
    )

    assert "notícia" not in desenv_h
    assert "notícia" not in acomp_h[0]
    assert "notícia" not in acess_h[0]
    assert "artigo de opinião" in desenv_h
    assert "a artigo" not in desenv_h


def test_higienizar_editorial_nao_mantem_noticia():
    desenv = "Propor atividade em que os estudantes retomem a notícia e relacionem o caso discutido."
    acomp = ["Observar posicionamentos presentes na notícia analisada."]
    acess = ["Oferecer leitura guiada da notícia."]

    desenv_h, acomp_h, acess_h = higienizar_plano(
        desenv, acomp, acess,
        perfil="lingua_portuguesa_em",
        disciplina="Língua Portuguesa",
        tema="Visões diversas em editoriais – Parte 1",
        recursos_reais={"noticia": False, "tabela": False, "grafico": False}
    )

    assert "notícia" not in desenv_h
    assert "notícia" not in acomp_h[0]
    assert "notícia" not in acess_h[0]
    assert "editorial" in desenv_h
    assert "a editorial" not in desenv_h
    assert "caso discutido" not in desenv_h


def test_higienizar_reportagem_acordo_gramatical():
    desenv = "Conduzir a leitura mediada da reportagem lida na etapa anterior. Ler as informações na reportagem. O professor deve mobilizar a reportagem. Estudar com uma reportagem."

    desenv_h, _, _ = higienizar_plano(
        desenv, [], [],
        perfil="orientacao_estudos",
        disciplina="Orientação de Estudos",
        tema="Uma palavra puxa a outra - ETAPA 1",
        recursos_reais={"noticia": False, "tabela": False, "grafico": False}
    )

    assert "da material" not in desenv_h
    # Should replace "da reportagem lida" with "do material de estudo lido"
    assert "do material de estudo lido" in desenv_h
    # Should replace "na reportagem" with "no material de estudo"
    assert "no material de estudo" in desenv_h
    # Should replace "a reportagem" with "o material de estudo"
    assert "o material de estudo" in desenv_h
    # Should replace "uma reportagem" with "um material de estudo" (or similar)
    assert "uma material" not in desenv_h
    assert "um material de estudo" in desenv_h
