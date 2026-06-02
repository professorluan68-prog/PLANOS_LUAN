# -*- coding: utf-8 -*-
from core.lib.classificador import detectar_tipo_aula, perfil_disciplina
from core.lib.metodologia import MotorMetodologico, _etapas_por_perfil
from core.lib.acompanhamento import gerar_acompanhamento_aprimorado
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada


def test_perfil_biologia_detectado_corretamente():
    assert perfil_disciplina("Biologia") == "biologia"


def test_tipo_aula_biologia_detectado_corretamente():
    texto_desafio = "Aula desafio: o caso do virus Machupo. Desafio da semana. Entendendo o problema. Solucao em acao. Hora da verdade."
    assert detectar_tipo_aula(texto_desafio, "O caso do virus Machupo", "Biologia") == "aula_desafio"

    texto_pratica = "Relembre a fotossintese. Na pratica com materiais, montagem do experimento com elodea e observacao de bolhas."
    assert detectar_tipo_aula(texto_pratica, "Fotossintese e respiracao celular", "Biologia") == "aula_pratica"

    texto_revisao = "Relembre os conceitos de ecologia. Glossario e quiz de revisao. De quais voce sabe o significado?"
    assert detectar_tipo_aula(texto_revisao, "Ecologia", "Biologia") == "revisao_consolidacao"

    texto_impacto = "Biomas brasileiros, desmatamento, ODS, sustentabilidade, dados do INPE e impactos ambientais."
    assert detectar_tipo_aula(texto_impacto, "Biomas terrestres brasileiros", "Biologia") == "impacto_socioambiental"

    texto_conceito = "Para comecar. Foco no conteudo. Um passo de cada vez. Pause e responda. Fotossintese."
    assert detectar_tipo_aula(texto_conceito, "Metabolismo energetico: fotossintese", "Biologia") == "conceito_novo"


def test_etapas_por_perfil_biologia():
    etapas_desafio = _etapas_por_perfil("biologia", "aula_desafio")
    chaves_desafio = [e[1] for e in etapas_desafio]
    assert "desafio" in chaves_desafio
    assert "hora_verdade" in chaves_desafio

    etapas_pratica = _etapas_por_perfil("biologia", "aula_pratica")
    chaves_pratica = [e[1] for e in etapas_pratica]
    assert "discussao_resultados" in chaves_pratica


def test_motor_metodologico_biologia_impacto():
    motor = MotorMetodologico()
    etapas = motor.gerar(
        texto_pdf="Biomas brasileiros, dados do INPE, desmatamento, ODS, De olho no modelo e atividade de analise.",
        disciplina="Biologia",
        turma="1º ANO A",
        tema="Biomas terrestres brasileiros",
    )
    titulos = [e["titulo"] for e in etapas]
    assert "Para comecar" in titulos
    assert "De olho no modelo" in titulos
    assert "Encerramento" in titulos

    textos = " ".join(e["texto"] for e in etapas).lower()
    assert "impactos" in textos or "ambient" in textos
    assert "com suas palavras" in textos


def test_acompanhamento_biologia_desafio():
    acompanhamento = gerar_acompanhamento_aprimorado(
        tema="O caso do virus Machupo",
        desenvolvimento="Aula desafio. Desafio da semana. Entendendo o problema. Solucao em acao. Hora da verdade.",
        disciplina="Biologia",
    )
    assert len(acompanhamento) == 3
    assert any("hipóteses" in item.lower() or "hipoteses" in item.lower() for item in acompanhamento)
    assert any("evid" in item.lower() for item in acompanhamento)


def test_acessibilidade_biologia_pratica():
    acessibilidade = gerar_acessibilidade_aprimorada(
        tema="Fotossintese e respiracao celular",
        desenvolvimento="Relembre. Na pratica com materiais, montagem do experimento com elodea, observacao e discussao dos resultados.",
        disciplina="Biologia",
    )
    assert len(acessibilidade) == 3
    assert any("sequ" in item.lower() or "visual" in item.lower() for item in acessibilidade)
    assert any("desenho" in item.lower() or "oral" in item.lower() for item in acessibilidade)
