from core import lote


def test_cdp_detecta_disciplina_pela_capa_historia():
    texto = """
    2º bimestre
    Aula 14
    Ensino Fundamental
    História
    Resistência indígena na
    América portuguesa no
    final do Período Colonial:
    os Guaicurus
    Conteúdos
    Resistência indígena no Período Colonial.
    """
    assert lote._disciplina_base_cdp_contextual(texto, "", "PDF_AULAS/HISTÓRIA/AULA14_8ANO.pdf") == "História"


def test_cdp_detecta_disciplina_pela_capa_geografia():
    texto = """
    2º bimestre
    Aula 6
    Ensino Médio
    Geografia
    Desafios contemporâneos das cidades
    Conteúdos
    Desafios contemporâneos das cidades.
    """
    assert lote._disciplina_base_cdp_contextual(texto, "", "PDF_AULAS/GEOGRAFIA/AULA62ANO.pdf") == "Geografia"


def test_cdp_detecta_sociologia_sem_confundir_com_portugues():
    texto = """
    2º bimestre
    Aula 7
    Ensino Médio
    Sociologia
    Relações de classe, desigualdades e violências
    Para começar
    Analise a charge e responda.
    """
    assert lote._disciplina_base_cdp_contextual(texto, "", "") == "Sociologia"


def test_cdp_detecta_lideranca_oratoria_sem_confundir_com_portugues():
    texto = """
    Liderança e Oratória
    Persuasão e responsabilidade discursiva
    Aula 5
    Conteúdos
    Diferenciar persuasão ética, manipulação e responsabilidade discursiva.
    """
    assert lote._disciplina_base_cdp_contextual(texto, "", "") == "Liderança e Oratória"


def test_cdp_recupera_tema_multilinha_historia():
    texto = """
    2º bimestre
    Aula 14
    Ensino Fundamental
    História
    Resistência indígena na
    América portuguesa no
    final do Período Colonial:
    os Guaicurus
    Conteúdos
    Resistência indígena no Período Colonial.
    """
    tema = lote._tema_cdp_seguro(texto, "", "História", "Resistência indígena na")
    assert "Resistência indígena na América portuguesa" in tema
    assert "Resistência indígena na" != tema


def test_cdp_nao_traz_tecnologia_na_metodologia():
    texto = """
    Ensino Médio
    Geografia
    Desafios contemporâneos das cidades
    Link para vídeo
    Projetor e/ou TV para apresentação multimídia
    Para começar
    VIREM E CONVERSEM
    Observe o gráfico e responda.
    """
    extracao = lote._extrator_lib.extrair(texto, "Desafios contemporâneos das cidades")
    metodologia = " ".join(lote._metodologia_cdp_contextual(
        "geografia",
        "",
        "Desafios contemporâneos das cidades",
        "mobilidade urbana e smart cities",
        texto_pdf=texto,
        extracao_pdf=extracao,
        disciplina_base="Geografia",
    )).lower()

    proibidos = ["youtube", "projetor", "datashow", "tv", "celular", "aplicativo", "plataforma", "internet", "assistir ao vídeo"]
    assert not [p for p in proibidos if p in metodologia]
    assert "lousa" in metodologia or "material impresso" in metodologia
    assert "virem e conversem" in metodologia


def test_cdp_historia_metodologia_de_historia_nao_de_portugues():
    texto = """
    Ensino Fundamental
    História
    A elevação do Brasil à categoria de reino
    Observe a charge a seguir para responder às perguntas.
    Como a charge se relaciona ao conceito de pacto colonial?
    VIREM E CONVERSEM
    """
    extracao = lote._extrator_lib.extrair(texto, "A elevação do Brasil à categoria de reino")
    metodologia = " ".join(lote._metodologia_cdp_contextual(
        "historia",
        "",
        "A elevação do Brasil à categoria de reino",
        "pacto colonial e chegada da Corte portuguesa",
        texto_pdf=texto,
        extracao_pdf=extracao,
        disciplina_base="História",
    )).lower()

    assert "fonte histórica" in metodologia or "charge" in metodologia or "contexto histórico" in metodologia
    assert "conectivos" not in metodologia
    assert "relações lógico-discursivas" not in metodologia
    assert "equação" not in metodologia


def test_cdp_sociologia_usa_conceito_sociologico():
    texto = """
    Ensino Médio
    Sociologia
    Relações de classe, desigualdades e violências
    Para começar
    Analise a charge e reflita sobre tratamento desigual para pessoas de classes sociais diferentes.
    """
    extracao = lote._extrator_lib.extrair(texto, "Relações de classe, desigualdades e violências")
    metodologia = " ".join(lote._metodologia_cdp_contextual(
        "sociologia",
        "",
        "Relações de classe, desigualdades e violências",
        "relações de classe e desigualdades sociais",
        texto_pdf=texto,
        extracao_pdf=extracao,
        disciplina_base="Sociologia",
    )).lower()

    assert "conceito sociológico" in metodologia
    assert "desigualdade" in metodologia or "relações sociais" in metodologia
    assert "de acordo com o que estudamos hoje" not in metodologia


def test_cdp_lideranca_usa_analise_de_discurso():
    texto = """
    Liderança e Oratória
    Persuasão e responsabilidade discursiva
    Conteúdos
    Diferenciar persuasão ética e manipulação.
    Ponto de partida
    Leiam a tirinha abaixo.
    """
    extracao = lote._extrator_lib.extrair(texto, "Persuasão e responsabilidade discursiva")
    metodologia = " ".join(lote._metodologia_cdp_contextual(
        "lideranca_oratoria",
        "",
        "Persuasão e responsabilidade discursiva",
        "persuasão ética e manipulação",
        texto_pdf=texto,
        extracao_pdf=extracao,
        disciplina_base="Liderança e Oratória",
    )).lower()

    assert "discurso" in metodologia
    assert "persuasão" in metodologia or "persuasao" in metodologia
    assert "responsabilidade discursiva" in metodologia
