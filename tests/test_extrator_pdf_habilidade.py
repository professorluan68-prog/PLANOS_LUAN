from core.lib.extrator_pdf import ExtratorPDF


def test_descarta_fragmento_de_link_com_ae_como_habilidade():
    linhas = [
        "Geografia",
        "Desafios contemporaneos das cidades",
        "6e0607ae7bfa?_gl=1*153vq11*_gcl_au*Nzk2OTczMDM5LjE3MjMxNjEwODA.*_ga*ODczNDU0MDQyLjE3Mj",
        "Para comecar",
    ]

    assert ExtratorPDF()._extrair_habilidade(linhas) == ""


def test_mantem_bncc_valida_como_habilidade():
    linhas = [
        "Habilidade: (EF08MA04) Resolver e elaborar problemas que envolvam calculo de porcentagens.",
    ]

    assert "EF08MA04" in ExtratorPDF()._extrair_habilidade(linhas)


def test_mantem_codigo_bncc_do_ensino_medio_com_tres_letras():
    linhas = [
        "Para professores",
        "Habilidade:",
        "(EM13CHS105) Identificar, contextualizar e criticar tipologias evolutivas (populacoes nomades e",
        "sedentarias, entre outras) e oposicoes dicotomicas (cidade/campo, cultura/natureza,",
        "civilizados/barbaros, razao/emocao, material/virtual etc.), explicitando suas ambiguidades.",
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
        "(EM13CHS106) Utilizar linguagens cartograficas e graficas.",
        "(EM13CHS201) Analisar processos politicos, economicos e sociais.",
    ]

    habilidade = ExtratorPDF()._extrair_habilidade(linhas)

    assert "EM13CHS105" in habilidade
    assert "EM13CHS106" not in habilidade


def test_mantem_ae_separada_com_texto_descritivo():
    linhas = [
        "AE 03 - Analisar transformacoes socioespaciais em diferentes escalas.",
    ]

    assert ExtratorPDF()._extrair_habilidade(linhas).startswith("AE 03")


def test_habilidade_para_antes_da_metodologia():
    linhas = [
        "Habilidade: (EF69LP46) Participar de praticas de compartilhamento de leitura/recepcao de obras literarias.",
        "Trilha Harry Potter e o Calice de Fogo",
        "1. Disparo inicial",
        "Explique o objetivo da aula.",
    ]

    habilidade = ExtratorPDF()._extrair_habilidade(linhas)

    assert "EF69LP46" in habilidade
    assert "Trilha Harry Potter" not in habilidade
    assert "Disparo inicial" not in habilidade


def test_extrai_habilidade_textual_da_secao_habilidades():
    linhas = [
        "Objetivos da aula",
        "• Identificar as principais causas das migracoes internacionais.",
        "Habilidades",
        "Analisar criticamente as influencias da globalizacao e mundializacao nas juventudes, avaliando como esses processos impactam diferentes contextos sociais, economicos e culturais e as oportunidades e desafios no mundo do trabalho.",
        "Conteudos",
        "• Causas das migracoes internacionais.",
    ]

    habilidade = ExtratorPDF()._extrair_habilidade(linhas)

    assert habilidade.startswith("Habilidade:")
    assert "globalizacao e mundializacao" in habilidade


def test_rejeita_habilidade_textual_truncada():
    linhas = [
        "Habilidades",
        "s para estimular a inovacao e o desenvolvimento sustentavel.",
        "Conteudos",
        "• Migracoes internacionais.",
    ]

    habilidade = ExtratorPDF()._extrair_habilidade(linhas)

    assert habilidade == ""
