"""
Testes unitários e de integração para o recurso de Aprofundamento.
"""

import os
from core.disciplinas import nomes_disciplinas
from core.lib.classificador import perfil_disciplina
from core.lib.aprofundamento import (
    eh_aprofundamento_biologia,
    eh_aprofundamento_geografia,
    quebrar_e_limpar_itens,
    comparar_aula,
    obter_dados_aprofundamento,
)
from core.lib.extrator_pdf import ExtratorPDF


def test_disciplinas_adicionadas():
    """Garante que as novas disciplinas estão na lista oficial de cadastro."""
    disciplinas = nomes_disciplinas()
    assert "Aprofundamento em Biologia" in disciplinas
    assert "Aprofundamento em Geografia" in disciplinas


def test_perfil_disciplinas_aprofundamento():
    """Garante que os perfis pedagógicos das novas disciplinas são mapeados corretamente."""
    assert perfil_disciplina("Aprofundamento em Biologia") == "biologia"
    assert perfil_disciplina("Aprofundamento em Geografia") == "geografia"
    assert perfil_disciplina("APROFUNDAMENTO EM GEOGRAFIA") == "geografia"
    assert perfil_disciplina("Aprofundamento em Biologia (Ensino Médio)") == "biologia"


def test_eh_aprofundamento_helpers():
    """Valida as funções auxiliares de verificação de nome da disciplina."""
    assert eh_aprofundamento_biologia("Aprofundamento em Biologia") is True
    assert eh_aprofundamento_biologia("Biologia") is False
    assert eh_aprofundamento_geografia("Aprofundamento em Geografia") is True
    assert eh_aprofundamento_geografia("Geografia") is False


def test_comparar_aula():
    """Valida a correspondência flexível do número da aula."""
    assert comparar_aula(2, "2") is True
    assert comparar_aula("02", "2") is True
    assert comparar_aula(2, "02") is True
    assert comparar_aula("3", 3) is True
    assert comparar_aula(None, "1") is False
    assert comparar_aula("1", None) is False
    assert comparar_aula("AULA 2", "2") is False  # A comparação espera apenas os números limpos


def test_quebrar_e_limpar_itens():
    """Valida a limpeza e separação de strings com bullet points."""
    texto = "● Item 1\n• Item 2\n* Item 3\n\t  Item 4  \n- Item 5"
    esperado = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]
    assert quebrar_e_limpar_itens(texto) == esperado
    assert quebrar_e_limpar_itens("") == []
    assert quebrar_e_limpar_itens(None) == []


def test_obter_dados_aprofundamento_geografia():
    """Valida a leitura e mapeamento de dados da planilha real de Geografia se ela existir."""
    dados = obter_dados_aprofundamento("Aprofundamento em Geografia", "1")
    if dados is not None:
        assert dados["titulo"] == "Uso de recursos naturais na sociedade contemporânea"
        assert "impactos ambientais" in dados["habilidade"].lower()
        assert dados["objetos_conhecimento"] == "Recursos naturais."
        assert "Identificar os principais recursos naturais" in dados["objetivos"]
    else:
        # Se rodar num ambiente sem a planilha física em D:\planilhas, este teste passa
        pass


def test_obter_dados_aprofundamento_biologia():
    """Valida a leitura e mapeamento de dados da planilha real de Biologia se ela existir."""
    dados = obter_dados_aprofundamento("Aprofundamento em Biologia", "2")
    if dados is not None:
        assert dados["titulo"] == "Atividade metabólica e mudanças nas características celulares visíveis ao microscópio"
        assert "fisiologia humana" in dados["habilidade"].lower()
        assert dados["objetos_conhecimento"] == "Citologia."
        assert "Distinguir os conceitos básicos de metabolismo" in dados["objetivos"]
    else:
        pass


def test_extrator_pdf_enriquecido():
    """Testa se a extração é enriquecida com os dados da planilha de aprofundamento."""
    texto_pdf_fake = "Texto qualquer que seria lido do PDF da aula."
    extrator = ExtratorPDF()

    # Sem passar disciplina de aprofundamento e aula
    resultado_normal = extrator.extrair(texto_pdf_fake, "Tema Original")
    assert resultado_normal["habilidade"] == ""  # sem habilidade no texto fake

    # Passando aprofundamento (Geografia Aula 1)
    resultado_enriquecido = extrator.extrair(
        texto_pdf_fake,
        "Tema Original",
        disciplina="Aprofundamento em Geografia",
        numero_aula="1",
    )

    dados_plan = obter_dados_aprofundamento("Aprofundamento em Geografia", "1")
    if dados_plan:
        assert resultado_enriquecido["habilidade"] == f"Habilidade: {dados_plan['habilidade']}"
        assert resultado_enriquecido["conceito_extraido"] == dados_plan["titulo"]
        assert len(resultado_enriquecido["objetivos_secao"]) > 0
    else:
        assert resultado_enriquecido["habilidade"] == ""
