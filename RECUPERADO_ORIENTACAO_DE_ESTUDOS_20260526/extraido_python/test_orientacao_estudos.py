from core.ia import _prompt_usuario
from core.extractor import extrair_tema
from core.lote import _dividir_paginas_em_aulas
from core.methodologies.base import PedagogicalContext
from core.methodologies.orientacao_estudos import montar_desenvolvimento_orientacao_estudos
from core.referencias_metodologia import carregar_referencia_metodologica


SLIDES_MISSAO = [
    "Projetos culturais e coesão textual. Você já leu um projeto cultural?",
    "ETAPA. Leia o projeto cultural Projeto Viagem pela Literatura. Introdução, justificativa, objetivo, metodologia e avaliação.",
    "Quais são as etapas do projeto? Qual é o público-alvo? Fique ligado: um projeto cultural apresenta o planejamento de uma ação.",
    "Cartas de leitor e argumento. Você sabe o que é uma tese?",
    "Leia a carta de leitor. Reconheça os argumentos utilizados ao longo do texto para sustentar a tese.",
    "Agora é hora de produzir com os colegas uma carta de leitor. Organizem argumentos e escrevam um rascunho.",
]


def test_orientacao_estudos_metodologia_usa_etapas_do_exemplo():
    texto = montar_desenvolvimento_orientacao_estudos(
        SLIDES_MISSAO,
        "Projetos culturais e cartas de leitor",
        "Desenvolver estratégias de estudo.",
        PedagogicalContext("Orientação de estudos", "6º Ano A", "Projetos culturais"),
    )

    assert "Para começar:" in texto
    assert "Leitura e construção do conteúdo:" in texto
    assert "Foco no conteúdo:" in texto
    assert "Na prática:" in texto
    assert "Pause e responda:" in texto
    assert "Encerramento:" in texto
    assert "Realizar a leitura guiada" in texto
    assert "Organizar, no quadro" in texto
    assert "Orientar a resolução das atividades passo a passo" in texto
    assert "páginas" not in texto.lower()
    assert "Conduzir leitura mediada" not in texto
    assert "Sistematizar estratégias" not in texto


def test_orientacao_estudos_referencia_entra_no_prompt_do_gemini():
    referencia = carregar_referencia_metodologica("Orientação de estudos", "6º Ano A")
    prompt = _prompt_usuario(
        disciplina="Orientação de estudos",
        turma="6º Ano A",
        bimestre="2º BIMESTRE",
        tema="Projetos culturais e cartas de leitor",
        aprendizagem="Desenvolver estratégias de estudo.",
        slides_textos=SLIDES_MISSAO,
    )

    assert "ORIENTAÇÃO DE ESTUDOS" in referencia
    assert "Leitura e construção do conteúdo" in prompt
    assert "Não descreva página" in prompt


def test_orientacao_estudos_separa_pdf_com_mais_de_uma_missao():
    paginas = [
        ["77", "Projetos", "culturais e", "coesão", "textual", "1", "Você já leu um projeto cultural?"],
        ["1", "ETAPA", "Leia o projeto cultural."],
        ["ETAPA FINAL", "Produza uma justificativa."],
        ["kcotS", "88", "Cartas de leitor", "e", "argumento", "Você sabe o que é uma tese?"],
        ["1", "ETAPA", "Leia a carta de leitor."],
    ]

    blocos = _dividir_paginas_em_aulas(paginas, disciplina="Orientação de estudos")

    assert len(blocos) == 2
    assert extrair_tema(blocos[0], disciplina="Orientação de estudos") == "MISSÃO 7 - Projetos culturais e coesão textual"
    assert extrair_tema(blocos[1], disciplina="Orientação de estudos") == "MISSÃO 8 - Cartas de leitor e argumento"


def test_orientacao_estudos_limpa_ocr_e_creditos_no_titulo():
    paginas = [[
        "10",
        "10",
        "Not’cias e opini‹o",
        "Mary Taylor/Pexels",
        "1",
        "No dia a dia, como você reage diante de uma opinião diferente da sua?",
    ]]

    assert extrair_tema(paginas, disciplina="Orientação de estudos") == "MISSÃO 10 - Notícias e opinião"


def test_orientacao_estudos_identifica_numero_simples_da_missao():
    paginas = [[
        "9",
        "Elementos da not’cia",
        "yevgeniya131988/Adobe Stock",
        "• Identificar o modo de tratar o assunto em um texto.",
    ]]

    assert extrair_tema(paginas, disciplina="Orientação de estudos") == "MISSÃO 9 - Elementos da notícia"


def test_orientacao_estudos_nao_confunde_numero_de_atividade_com_missao():
    paginas = [[
        "benjamas/Adobe Stock",
        "1",
        "Você já leu ou escreveu alguma carta para veículos de comunicação?",
        "2",
        "Você já leu ou comentou em algum post de um portal de notícias?",
        "Cartas de leitor e argumento",
    ]]

    assert extrair_tema(paginas, disciplina="Orientação de estudos") == "MISSÃO 8 - Cartas de leitor e argumento"


def test_orientacao_estudos_linha_duplicada_1111_vira_jornada_11():
    paginas = [[
        "Linguagem poética:",
        "poema, slam",
        "e canção",
        "_jornada",
        "1111",
    ]]

    assert extrair_tema(paginas, disciplina="Orientação de estudos") == "JORNADA 11 - Linguagem poética: poema, slam e canção"


def test_orientacao_estudos_sp_ensino_fundamental_usa_catalogo_proprio():
    paginas = [[
        "9",
        "1",
        "Jogos com palavras",
        "e imagens",
        "DE OLHO NO SAEB",
        "1: LP5LERE01 | N2.3 | Fácil",
    ]]

    assert extrair_tema(paginas, disciplina="Orientação de estudos") == "MISSÃO 1 - Jogos com palavras e imagens"


def test_orientacao_estudos_metodologia_inclui_de_olho_no_saeb_quando_aparece():
    texto = montar_desenvolvimento_orientacao_estudos(
        [
            "Jogos com palavras e imagens.",
            "DE OLHO NO SAEB",
            "1: LP5LERE01 | N2.3 | Fácil",
            "2 e 3: LP5LERE02 | N1.1(*) | Fácil",
        ],
        "MISSÃO 1 - Jogos com palavras e imagens",
        "Desenvolver estratégias de leitura.",
        PedagogicalContext("Orientação de estudos", "5º Ano A", "Jogos com palavras e imagens"),
    )

    assert "DE OLHO NO SAEB" in texto
    assert "códigos de habilidade, nível e dificuldade" in texto
    assert "relação entre palavras, imagens e regras de jogo" in texto


def test_orientacao_estudos_metodologia_nao_inventa_de_olho_no_saeb():
    texto = montar_desenvolvimento_orientacao_estudos(
        SLIDES_MISSAO,
        "Projetos culturais e cartas de leitor",
        "Desenvolver estratégias de estudo.",
        PedagogicalContext("Orientação de estudos", "6º Ano A", "Projetos culturais"),
    )

    assert "DE OLHO NO SAEB" not in texto


def test_orientacao_estudos_perfil_fechado_nao_mistura_missoes():
    texto = montar_desenvolvimento_orientacao_estudos(
        [
            "A trama do texto",
            "DE OLHO NO SAEB",
            "1: LP5LEAN02 | N4.1 | Fácil",
            "Em outro trecho do material podem aparecer palavras como poema, teatro ou notícia.",
        ],
        "MISSÃO 7 - A trama do texto",
        "Desenvolver estratégias de leitura.",
        PedagogicalContext("Orientação de estudos", "6º Ano A", "A trama do texto"),
    )

    assert "coesão textual, retomadas e continuidade das ideias" in texto
    assert "poemas, versos" not in texto
    assert "texto teatral" not in texto
    assert "notícias e opinião" not in texto

