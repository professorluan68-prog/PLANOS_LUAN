from core.lib.extrator_pdf import ExtratorPDF


def test_descarta_fragmento_de_link_com_ae_como_habilidade():
    linhas = [
        "Geografia",
        "Desafios contemporâneos das cidades",
        "6e0607ae7bfa?_gl=1*153vq11*_gcl_au*Nzk2OTczMDM5LjE3MjMxNjEwODA.*_ga*ODczNDU0MDQyLjE3Mj",
        "Para começar",
    ]

    assert ExtratorPDF()._extrair_habilidade(linhas) == ""


def test_mantem_bncc_valida_como_habilidade():
    linhas = [
        "Habilidade: (EF08MA04) Resolver e elaborar problemas que envolvam cálculo de porcentagens.",
    ]

    assert "EF08MA04" in ExtratorPDF()._extrair_habilidade(linhas)


def test_mantem_codigo_bncc_do_ensino_medio_com_tres_letras():
    linhas = [
        "Para professores",
        "Habilidade:",
        "(EM13CHS105) Identificar, contextualizar e criticar tipologias evolutivas (populações nômades e",
        "sedentárias, entre outras) e oposições dicotômicas (cidade/campo, cultura/natureza,",
        "civilizados/bárbaros, razão/emoção, material/virtual etc.), explicitando suas ambiguidades.",
        "Slide 3",
    ]

    habilidade = ExtratorPDF()._extrair_habilidade(linhas)

    assert "EM13CHS105" in habilidade
    assert "Identificar, contextualizar" in habilidade
    assert "civilizados" in habilidade


def test_usa_primeira_habilidade_quando_pdf_traz_varias():
    linhas = [
        "Habilidade:",
        "(EM13CHS105) Identificar, contextualizar e criticar tipologias evolutivas.",
        "(EM13CHS106) Utilizar linguagens cartográficas e gráficas.",
        "(EM13CHS201) Analisar processos políticos, econômicos e sociais.",
    ]

    habilidade = ExtratorPDF()._extrair_habilidade(linhas)

    assert "EM13CHS105" in habilidade
    assert "EM13CHS106" not in habilidade


def test_mantem_ae_separada_com_texto_descritivo():
    linhas = [
        "AE 03 - Analisar transformações socioespaciais em diferentes escalas.",
    ]

    assert ExtratorPDF()._extrair_habilidade(linhas).startswith("AE 03")
