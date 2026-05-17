from core import lote
from core.projeto_vida_escopo import (
    buscar_item_projeto_vida,
    montar_aprendizagem_projeto_vida,
)


def test_busca_item_projeto_vida_no_escopo_sequencia():
    item = buscar_item_projeto_vida("3º ANO B", "2º Bimestre", "4")

    assert item["titulo"] == "Explorando possíveis profissões"
    assert "Determinação" in item["habilidade"]
    assert "Tomada de decisões" in item["objeto"]
    assert "Analisar informações" in item["objetivos"]


def test_monta_aprendizagem_projeto_vida_curta_e_com_sentido():
    item = buscar_item_projeto_vida("3º ANO B", "2º Bimestre", "4")

    aprendizagem = montar_aprendizagem_projeto_vida(item)

    assert len(aprendizagem) <= 260
    assert "determinação e assertividade" in aprendizagem
    assert "áreas profissionais" in aprendizagem
    assert "tomada de decisões" in aprendizagem
    assert "Apresentação dos programas" not in aprendizagem


def test_aula_projeto_vida_usa_escopo_para_aprendizagem_e_titulo(monkeypatch):
    monkeypatch.setattr(
        lote,
        "_extrair_texto_pdf",
        lambda caminho: "Projeto de Vida\nExplorando possíveis profissões\nAula 4\n",
    )

    aula = lote._aula_por_pdf(
        "AULA04_PROJETO_DE_VIDA.pdf",
        "Projeto de Vida",
        "3º ANO B",
        "2º Bimestre",
        usar_ia=False,
        provedor_ia="",
    )

    assert aula["tema"] == "Explorando possíveis profissões"
    assert aula["material"] == "AULA 4 - Explorando possíveis profissões"
    assert "determinação e assertividade" in aula["aprendizagem"]
    assert "tomada de decisões" in aula["aprendizagem"]


def test_fluxo_de_outra_disciplina_nao_usa_escopo_projeto_vida(monkeypatch):
    monkeypatch.setattr(
        lote,
        "_extrair_texto_pdf",
        lambda caminho: "Geografia\nUrbanização brasileira\nAula 4\n",
    )

    aula = lote._aula_por_pdf(
        "AULA04_GEOGRAFIA.pdf",
        "Geografia",
        "3º ANO B",
        "2º Bimestre",
        usar_ia=False,
        provedor_ia="",
    )

    assert aula["material"] == "AULA 4 - Urbanização brasileira"
    assert "determinação e assertividade" not in aula["aprendizagem"]
