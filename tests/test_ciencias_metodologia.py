from core.lib.acessibilidade import gerar_acessibilidade_aprimorada
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.classificador import detectar_tipo_aula, perfil_disciplina
from core.lib.metodologia import MotorMetodologico, _etapas_por_perfil


def test_ciencias_classifica_tipos_da_analise_metodologica():
    assert perfil_disciplina("Ciencias") == "ciencias_ef"
    assert (
        detectar_tipo_aula(
            "Para comecar. Foco no conteudo com definicao, camadas e estrutura da Terra. Pause e responda.",
            "Camadas da Terra",
            "Ciencias",
        )
        == "conceito_novo"
    )
    assert (
        detectar_tipo_aula(
            "Hora da leitura com noticia do INPE, dados sobre queimadas e perguntas de analise critica.",
            "Desmatamento e queimadas",
            "Ciencias",
        )
        == "leitura_analise"
    )
    assert (
        detectar_tipo_aula(
            "Relembre. Anteriormente estudamos genetica. Exercicio resolvido com quadro de Punnett.",
            "Segunda Lei de Mendel",
            "Ciencias",
        )
        == "revisao_retomada"
    )
    assert (
        detectar_tipo_aula(
            "Estudo de caso sobre fadiga muscular, mitocondria e consequencias para o organismo.",
            "Mitocondria e energia",
            "Ciencias",
        )
        == "estudo_caso"
    )
    assert (
        detectar_tipo_aula(
            "Relembre. Na pratica, organizem a apresentacao do seminario e revisem a cartilha da campanha.",
            "Campanha de saude",
            "Ciencias",
        )
        == "producao_projeto"
    )


def test_ciencias_etapas_mudam_por_tipo_de_aula():
    assert [chave for _, chave in _etapas_por_perfil("ciencias_ef", "conceito_novo")] == [
        "para_comecar",
        "foco",
        "pause",
        "pratica",
        "encerramento",
    ]
    assert "modelo" in [chave for _, chave in _etapas_por_perfil("ciencias_ef", "revisao_retomada")]
    assert "estudo_caso" in [chave for _, chave in _etapas_por_perfil("ciencias_ef", "estudo_caso")]
    assert "compartilhamento" in [chave for _, chave in _etapas_por_perfil("ciencias_ef", "producao_projeto")]


def test_motor_ciencias_leitura_analise_usa_dados_e_evidencias():
    etapas = MotorMetodologico().gerar(
        texto_pdf=(
            "Hora da leitura. Noticia do INPE sobre aumento de queimadas no Brasil. "
            "Dados indicam impacto sobre biodiversidade e servicos ecossistemicos. "
            "Na pratica, responda com evidencias do texto."
        ),
        disciplina="Ciencias",
        turma="7 ano A",
        tema="Desmatamento e queimadas",
    )

    titulos = [etapa["titulo"] for etapa in etapas]
    texto = " ".join(etapa["texto"] for etapa in etapas).lower()

    assert "Hora da leitura" in titulos
    assert "Pause e responda" in titulos
    assert "evidencias" in texto
    assert "saude" in texto or "ambiente" in texto or "sociedade" in texto


def test_ciencias_acompanhamento_e_acessibilidade_especificos():
    desenvolvimento = (
        "Estudo de caso sobre radiacao, DNA e consequencias para a saude. "
        "Os estudantes devem identificar evidencias e justificar a explicacao cientifica."
    )
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="Radiacao e DNA",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Radiacao e DNA",
        desenvolvimento=desenvolvimento,
        disciplina="Ciencias",
    )

    assert len(acompanhamento) == 3
    assert len(acessibilidade) == 3
    assert any("caso" in item.lower() for item in acompanhamento)
    assert any("causa" in item.lower() or "evidencias" in item.lower() for item in acessibilidade)
