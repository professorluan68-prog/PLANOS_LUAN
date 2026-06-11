# -*- coding: utf-8 -*-
from core.lib.classificador import detectar_tipo_aula, perfil_disciplina
from core.lib.metodologia import MotorMetodologico, _etapas_por_perfil
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada


def test_perfil_biologia_detectado_corretamente():
    assert perfil_disciplina("Biologia") == "biologia"


def test_tipo_aula_biologia_detectado_corretamente():
    # 1. etico_biotecnologico
    texto_etico = "Celulas HeLa: a importancia da bioetica em biotecnologia. CEP, CONEP, consentimento livre e esclarecido, dignidade e sigilo."
    assert detectar_tipo_aula(texto_etico, "Bioetica em pesquisa", "Biologia") == "etico_biotecnologico"

    # 2. debate_critico
    texto_debate = "Estudo do darwinismo social e eugenia. Racismo cientifico, pseudociencia e determinismo biologico na historia."
    assert detectar_tipo_aula(texto_debate, "Eugenia e racismo cientifico", "Biologia") == "debate_critico"

    # 3. molecular_genetico
    texto_molecular = "Bases nitrogenadas: adenina, timina, citosina e guanina. Replicacao semiconservativa do DNA e transcricao do RNA."
    assert detectar_tipo_aula(texto_molecular, "DNA e RNA", "Biologia") == "molecular_genetico"

    # 4. aplicacao_biotecnologica
    texto_biotec = "Vacinas e soros. Imunidade adquirida e resposta imunológica no Instituto Butantan e Fiocruz."
    assert detectar_tipo_aula(texto_biotec, "Imunidade e vacinacao", "Biologia") == "aplicacao_biotecnologica"

    # 5. revisao_aprofundamento
    texto_revisao = "Retomada dos conceitos de genetica mendeliana. Relembre o cruzamento de ervilhas e a segregacao."
    assert detectar_tipo_aula(texto_revisao, "Revisao de Genetica", "Biologia") == "revisao_aprofundamento"


def test_etapas_por_perfil_biologia():
    etapas_etico = _etapas_por_perfil("biologia", "etico_biotecnologico")
    chaves_etico = [e[1] for e in etapas_etico]
    assert "para_comecar" in chaves_etico
    assert "foco_1" in chaves_etico
    assert "foco_2" in chaves_etico
    assert "pause" in chaves_etico
    assert "pratica" in chaves_etico
    assert "encerramento" in chaves_etico

    etapas_molecular = _etapas_por_perfil("biologia", "molecular_genetico")
    chaves_molecular = [e[1] for e in etapas_molecular]
    assert "relembre" in chaves_molecular
    assert "foco_1" in chaves_molecular
    assert "foco_2" in chaves_molecular
    assert "pause" in chaves_molecular
    assert "pratica" in chaves_molecular
    assert "encerramento" in chaves_molecular


def test_motor_metodologico_biologia_etico():
    motor = MotorMetodologico()
    etapas = motor.gerar(
        texto_pdf='Assista ao video "A mulher que mudou a medicina" no canal Nerdologia com duracao de 7 minutos. Discutir bioetica e consentimento.',
        disciplina="Biologia",
        turma="1º ANO A",
        tema="Células HeLa e Bioética",
    )
    titulos = [e["titulo"] for e in etapas]
    assert "Para comecar" in titulos
    assert "Foco no conteudo" in titulos
    assert "Encerramento" in titulos

    textos = " ".join(e["texto"] for e in etapas)
    # Deve conter menções a vídeos e canais extraídos
    assert "Nerdologia" in textos
    assert "A mulher que mudou a medicina" in textos
    
    # Nenhuma etapa deve começar com definição direta de conceitos (ex: "X é...")
    for etapa in etapas:
        texto_etapa = etapa["texto"].strip()
        assert not texto_etapa.startswith(("Definir", "Apresentar a definição", "Explicar a definição", "O conceito de", "Conceito:"))


def test_acompanhamento_biologia_etico():
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Células HeLa e Bioética",
        desenvolvimento='Para comecar: video sobre Henrietta Lacks. Foco no conteudo: bioetica e consentimento. Na pratica: analise do caso.',
        disciplina="Biologia",
    )
    assert len(acompanhamento) == 3
    # Todos os itens de biologia devem conter o checkmark ☑
    for item in acompanhamento:
        assert item.startswith("☑")
    
    assert any("bioética" in item.lower() or "bioetica" in item.lower() for item in acompanhamento)
    assert any("dignidade" in item.lower() or "autonomia" in item.lower() for item in acompanhamento)


def test_acessibilidade_biologia_molecular():
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Cruzamento Genético",
        desenvolvimento='Relembre: genotipo e fenotipo. Foco no conteudo: Primeira Lei de Mendel. Na pratica: quadro de Punnett.',
        disciplina="Biologia",
    )
    assert len(acessibilidade) == 3
    # Todos os itens de biologia devem conter o checkmark ☑
    for item in acessibilidade:
        assert item.startswith("☑")

    # Deve conter templates de ferramentas práticas ou glossários
    assert any("glossário" in item.lower() or "glossario" in item.lower() for item in acessibilidade)
    assert any("punnett" in item.lower() or "heredograma" in item.lower() for item in acessibilidade)
