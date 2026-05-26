from core.ia import _normalizar_saida_ia
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
    assert "socializacao seja opcional ou mediada" in pratica


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

    texto_norm = texto.lower()
    assert "virem e conversem" not in texto_norm
    assert "todo mundo escreve" not in texto_norm


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
