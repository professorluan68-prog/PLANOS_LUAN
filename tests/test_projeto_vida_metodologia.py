from core.ia import _normalizar_saida_ia
from core.lib.classificador import normalizar_texto
from core.lote import _montar_etapas_metodologia, _sanitizar_aprendizagem
from core.lib.acessibilidade import gerar_acessibilidade_aprimorada
from core.qualidade_metodologica import sanitizar_texto_metodologico


def test_projeto_vida_nao_usa_marcador_como_conceito():
    etapas = _montar_etapas_metodologia(
        texto=(
            "Relembre\n"
            "Nossas frases modelo Na última aula, a turma criou frases para conversar sobre respeito.\n"
            "Foco no conteúdo\n"
            "Pontos de vista Quando convivemos, lidamos com opiniões diferentes.\n"
        ),
        disciplina="Projeto de Vida",
        turma="6º ano A",
        tema="Preparando nosso círculo de convivência",
    )

    foco = next(etapa["texto"] for etapa in etapas if etapa["titulo"] == "Foco no conteudo")
    assert "Relembre" not in foco
    assert "Preparando nosso círculo de convivência" not in foco
    assert "relacionar sentir, pensar e agir" in foco


def test_projeto_vida_mantem_tom_acolhedor():
    etapas = _montar_etapas_metodologia(
        texto="Na prática\nRegistro individual e conversa em dupla sobre autoconhecimento.",
        disciplina="Projeto de Vida",
        turma="6º ano B",
        tema="Quem sou quando estou comigo?",
    )

    para_comecar = next(etapa["texto"] for etapa in etapas if etapa["titulo"] == "Para comecar")
    pratica = next(etapa["texto"] for etapa in etapas if etapa["titulo"] == "Na pratica")
    assert "sem exigir exposicao pessoal" in para_comecar
    assert "socializacao seja opcional ou mediada" in normalizar_texto(pratica)


def test_projeto_vida_nao_usa_apoios_matematicos_na_acessibilidade():
    itens = gerar_acessibilidade_aprimorada(
        disciplina="Projeto de Vida",
        tema="Roda das profissoes",
        perfil="projeto_de_vida",
        tipo="geral",
        recursos_detectados=["calculo_resolucao", "analise_grafico"],
    )

    texto = " ".join(itens).lower()
    assert "tabuada" not in texto
    assert "calculadora" not in texto
    assert "ambiente acolhedor" in texto


def test_projeto_vida_aprendizagem_nao_fica_generica():
    aprendizagem = _sanitizar_aprendizagem(
        "Desenvolver habilidades relacionadas ao tema da aula, com foco em o tema da aula.",
        tema="Como saber se postar vale a pena?",
        perfil="projeto_de_vida",
    )

    texto = aprendizagem.lower()
    assert "tema da aula" not in texto
    assert "ambiente digital" in texto
    assert "responsabilidade" in texto


def test_projeto_vida_sanitiza_tecnicas_lemov_na_metodologia():
    texto = sanitizar_texto_metodologico(
        'Aplicar a tecnica VIREM E CONVERSEM para discutir o tema. Utilizar a tecnica TODO MUNDO ESCREVE para registro individual.',
        perfil="projeto_de_vida",
        tema="Deu ruim, e agora?",
    )

    assert 'técnica "Virem e conversem"' in texto
    assert "todo mundo escreve" not in texto.lower()


def test_projeto_vida_ia_fallback_gera_aprendizagem_especifica():
    saida = _normalizar_saida_ia(
        {
            "tema": "Antes que vire print: mostra de HQs.",
            "aprendizagem": "Desenvolver habilidades relacionadas ao tema da aula, com foco em o tema da aula.",
            "metodologia": [
                {"titulo": "Para começar", "texto": "Abrir a aula com situacao acolhedora sobre publicacoes e compartilhamentos."},
                {"titulo": "Foco no conteúdo", "texto": "Discutir exposicao, respeito e consequencias no ambiente digital."},
                {"titulo": "Encerramento", "texto": "Retomar cuidados antes de postar ou compartilhar."},
            ],
        },
        texto_pdf="Projeto de Vida\nAntes que vire print: mostra de HQs.\nExposicao e responsabilidade digital.",
        disciplina="Projeto de Vida",
        turma="8º ano A",
    )

    aprendizagem = saida["aprendizagem"].lower()
    metodologia = " ".join(etapa["texto"].lower() for etapa in saida["metodologia"])
    assert "tema da aula" not in aprendizagem
    assert "ambiente digital" in aprendizagem
    assert "virem e conversem" not in metodologia


def test_projeto_vida_classificacao_e_etapas_futureme():
    from core.lib.classificador import detectar_tipo_aula
    from core.lib.metodologia import _etapas_por_perfil

    tipo = detectar_tipo_aula(
        texto="Plataforma digital FutureMe. Responder ao Questionário de Personalidade e ver o Pódio das Profissões.",
        tema="Descobrindo minhas afinidades no FutureMe",
        disciplina="Projeto de Vida"
    )
    assert tipo == "futureme"

    etapas_config = _etapas_por_perfil("projeto_de_vida", "futureme")
    titulos = [t[0] for t in etapas_config]
    assert "Para começar" in titulos
    assert "Na prática" in titulos
    assert "Compartilhamento" in titulos
    assert "Encerramento" in titulos


def test_projeto_vida_classificacao_e_etapas_producao_coletiva():
    from core.lib.classificador import detectar_tipo_aula
    from core.lib.metodologia import _etapas_por_perfil

    tipo = detectar_tipo_aula(
        texto="Elaboração em grupos de um biomapa representando a escola.",
        tema="Nosso Biomapa da Escola",
        disciplina="Projeto de Vida"
    )
    assert tipo == "producao_coletiva"

    etapas_config = _etapas_por_perfil("projeto_de_vida", "producao_coletiva")
    titulos = [t[0] for t in etapas_config]
    assert "Relembre" in titulos
    assert "Foco no conteúdo" in titulos
    assert "Na prática" in titulos
    assert "Compartilhamento" in titulos
    assert "Encerramento" in titulos


def test_projeto_vida_acompanhamento_especifico_futureme():
    from core.lib.acompanhamento import gerar_acompanhamento_aprimorado

    itens = gerar_acompanhamento_aprimorado(
        tema="Autoconhecimento",
        desenvolvimento="FutureMe questionário de personalidade",
        disciplina="Projeto de Vida",
        tipo="futureme"
    )
    assert len(itens) >= 2
    assert any("futureme" in item.lower() or "questionário" in item.lower() for item in itens)


def test_projeto_vida_acessibilidade_especifica_convivencia():
    from core.lib.acessibilidade import gerar_acessibilidade_aprimorada

    itens = gerar_acessibilidade_aprimorada(
        tema="Círculo de convivência",
        desenvolvimento="dinâmica de mediação e conselho escolar",
        disciplina="Projeto de Vida",
        tipo="convivencia"
    )
    assert len(itens) >= 2
    assert any("círculo" in item.lower() or "tímidos" in item.lower() or "dilema" in item.lower() for item in itens)
