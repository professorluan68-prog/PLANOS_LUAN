from core.cdp import (
    carregar_planilha_cdp_multisseriada,
    habilidade_item_cdp,
    listar_componentes_cdp_multisseriada,
    listar_habilidades_cdp_multisseriada,
    limpar_texto_cdp,
    montar_acessibilidade_cdp,
    montar_acompanhamento_cdp,
    montar_metodologia_cdp,
    selecionar_item,
    titulo_item_cdp,
)


def test_lista_componentes_cdp_multisseriada():
    componentes = listar_componentes_cdp_multisseriada()

    assert "Ciências" in componentes
    assert "História" in componentes
    assert "Matemática" in componentes


def test_lista_habilidades_cdp_multisseriada_por_componente_turma_e_bimestre():
    habilidades = listar_habilidades_cdp_multisseriada(
        "Ciências",
        turma="MULTISSERIADO 1º, 2º e 3º ano",
        bimestre="2ºBIMESTRE",
    )

    assert habilidades
    assert "Habilidade" not in habilidades[0]["codigo"]
    assert "(EF0" in habilidades[0]["codigo"]


def test_selecionar_item_cdp_multisseriada_respeita_componente_turma_e_bimestre():
    item = selecionar_item(
        "História",
        0,
        turma="MULTISSERIADO 4º e 5º ano",
        bimestre="2ºBIMESTRE",
        multisseriada=True,
        componente_cdp="História",
    )

    assert item
    assert item.get("ANO", "").startswith(("4", "5"))
    assert item.get("BIMESTRE", "").startswith("2")


def test_multisseriada_usa_colunas_reais_para_titulo_e_metodologia():
    dados = carregar_planilha_cdp_multisseriada()
    item = dados["Língua Portuguesa"][0]

    assert titulo_item_cdp(item)
    assert "conteúdo proposto" not in montar_metodologia_cdp("português", item).lower()


def test_limpa_percentuais_da_planilha_multisseriada():
    assert limpar_texto_cdp("Quatro operações (90%) Números fracionários (60%)") == "Quatro operações Números fracionários"
    assert limpar_texto_cdp("Normativo (86,3% corrigem fala)") == "Normativo"


def test_metodologia_multisseriada_usa_estilo_eja_contextualizado():
    dados = carregar_planilha_cdp_multisseriada()
    item = dados["Matemática"][0]

    metodologia = montar_metodologia_cdp("matematica", item)
    acompanhamento = montar_acompanhamento_cdp("matematica", item)
    acessibilidade = montar_acessibilidade_cdp("matematica", item)

    assert "contextualizacao" in metodologia.lower() or "situação do cotidiano" in metodologia.lower()
    assert "conteúdo proposto" not in metodologia.lower()
    assert "cálculos" in acompanhamento[1]
    assert "explicação passo a passo" in acessibilidade[0].lower()

    texto_cdp = " ".join([metodologia, *acompanhamento, *acessibilidade]).lower()
    termos_bloqueados = ["lemov", "virem", "todo mundo", "tecnologia", "digital", "software", "aplicativo"]
    assert not any(termo in texto_cdp for termo in termos_bloqueados)


def test_multisseriada_separa_turmas_123_e_45():
    habilidades_123 = listar_habilidades_cdp_multisseriada(
        "Ciências",
        turma="MULTISSERIADO 1º, 2º e 3º ano",
    )
    habilidades_45 = listar_habilidades_cdp_multisseriada(
        "Ciências",
        turma="MULTISSERIADO 4º e 5º ano",
    )

    assert habilidades_123
    assert habilidades_45
    assert habilidades_123[0]["descricao"] != habilidades_45[0]["descricao"]


def test_cdp_ciclo_i_separa_turmas_123_e_45_na_planilha_fundamental():
    disciplina = "portugu\u00eas"
    turma_123 = "MULTISSERIADO 1\u00ba, 2\u00ba e 3\u00ba ano"
    turma_45 = "MULTISSERIADO 4\u00ba e 5\u00ba ano"
    bimestre = "1\u00b0"

    item_123 = selecionar_item(disciplina, 0, turma=turma_123, bimestre=bimestre, fundamental=True)
    item_45 = selecionar_item(disciplina, 0, turma=turma_45, bimestre=bimestre, fundamental=True)

    assert item_123
    assert item_45
    assert item_123.get("ANO", "").startswith("1")
    assert item_45.get("ANO", "").startswith("4")
    assert item_123 != item_45


def test_habilidade_item_cdp_retorna_apenas_a_primeira_habilidade():
    item = {
        "HABILIDADES": "(EF01LP16) Ler e compreender poemas. (EF01LP10A) Nomear as letras do alfabeto. (EF01LP10B) Recitar as letras do alfabeto."
    }

    habilidade = habilidade_item_cdp(item)

    assert habilidade.startswith("(EF01LP16)")
    assert "(EF01LP10A)" not in habilidade
    assert "(EF01LP10B)" not in habilidade


def test_metodologia_cdp_fundamental_fica_mais_detalhada():
    item = {
        "TÍTULO": "Vaca",
        "HABILIDADES": "(EF12LP19) Ler e compreender textos do campo artístico-literário.",
        "CONTEÚDO": "Leitura e interpretação",
    }

    metodologia = montar_metodologia_cdp("português", item, fundamental=True)

    assert "Abertura (" in metodologia
    assert "Desenvolvimento (" in metodologia
    assert "Atividade (" in metodologia
    assert "Fechamento (" in metodologia
    assert len(metodologia) > 650
