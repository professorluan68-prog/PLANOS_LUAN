from core.lib.acessibilidade_perfis import gerar_acessibilidade_especifica_por_aula, gerar_acessibilidade_por_perfil
from core.lib.acompanhamento_perfis import gerar_acompanhamento_por_perfil
from core.lib.classificador import detectar_tipo_aula
from core.lote import _ajustar_texto_por_sequencia


def test_lingua_portuguesa_em_literatura_nao_usa_template_de_producao_textual():
    tema = "Gil Vicente e o Auto da Barca do Inferno"
    desenvolvimento = (
        "Realizar leitura orientada de trecho do Auto da Barca do Inferno, "
        "identificando personagens, vozes, crítica social e relação com o contexto literário."
    )

    acompanhamento = gerar_acompanhamento_por_perfil(
        "lingua_portuguesa_em",
        tema,
        "Interpretar texto literário em seu contexto.",
        desenvolvimento,
    )
    acessibilidade = gerar_acessibilidade_por_perfil(
        "lingua_portuguesa_em",
        tema,
        "Interpretar texto literário em seu contexto.",
        desenvolvimento,
    )

    assert len(acompanhamento) == 3
    assert len(acessibilidade) == 3
    assert all(item.startswith("☑ ") for item in acompanhamento)
    assert all(item.startswith("☑ ") for item in acessibilidade)
    assert "checklist" not in " ".join(acessibilidade).lower()
    assert "versão final" not in " ".join(acessibilidade).lower()
    assert "elementos do texto" in " ".join(acompanhamento).lower()


def test_lingua_portuguesa_em_anuncio_nao_confunde_cartazes_com_carta():
    acompanhamento = gerar_acompanhamento_por_perfil(
        "lingua_portuguesa_em",
        "Anúncios publicitários em mídias digitais – Parte 1",
        (
            "Analisar formas contemporâneas de publicidade em contexto digital, "
            "campanhas publicitárias, cartazes, folhetos, anúncios e propagandas."
        ),
        "Ler anúncios digitais, comparar público, suporte e recursos verbais e visuais.",
    )

    texto = " ".join(acompanhamento)

    assert "Carta" not in texto
    assert "Anúncio publicitário" in texto


def test_lingua_portuguesa_em_genero_comentario_e_texto_digital():
    tipo = detectar_tipo_aula(
        (
            "Gênero comentário: características, suporte e argumentação. "
            "Coesão e coerência. Coesão referencial e sequencial. "
            "Formar leitores capazes de ler, interpretar e escrever comentários "
            "nas redes sociais de forma clara, coerente e crítica."
        ),
        "Gênero comentário",
        "Língua Portuguesa",
        turma="2º ANO",
    )

    assert tipo == "texto_digital_blog"


def test_lingua_portuguesa_em_concluindo_jornada_e_autoavaliacao():
    tipo = detectar_tipo_aula(
        (
            "Autoavaliação, rubrica, portfólio e síntese do percurso de aprendizagem. "
            "Registrar avanços, dificuldades e próximos passos de estudo."
        ),
        "Concluindo a jornada",
        "Língua Portuguesa",
        turma="2º ANO",
    )

    assert tipo == "autoavaliacao"


def test_lingua_portuguesa_em_podcast_e_pratica_oral():
    tipo = detectar_tipo_aula(
        (
            "Planejar roteiro de podcast, definir falas, escuta ativa, gravação e "
            "socialização das produções orais da turma."
        ),
        "Podcast literário",
        "Língua Portuguesa",
        turma="3º ANO",
    )

    assert tipo == "pratica_oral"


def test_lingua_portuguesa_em_haicai_e_literatura():
    tipo = detectar_tipo_aula(
        "Haicai, poema curto, imagens poéticas, versos e leitura literária.",
        "Haicai: simplicidade e profundidade",
        "Língua Portuguesa",
        turma="1º ANO",
    )

    assert tipo == "literatura"


def test_texto_sintese_usa_vocabulario_neutro_na_acessibilidade():
    acessibilidade = gerar_acessibilidade_especifica_por_aula(
        "A literatura medieval portuguesa e suas influências",
        "Produzir texto-síntese sobre a formação da literatura portuguesa.",
        "Orientar leitura, registro em tópicos e escrita de texto-síntese.",
    )

    texto = " ".join(acessibilidade).lower()

    assert "vocabulário científico" not in texto
    assert "vocabulário adequado ao tema da aula" in texto


def test_visoes_de_mundo_nao_aciona_acessibilidade_de_anatomia_visual():
    acessibilidade = gerar_acessibilidade_especifica_por_aula(
        "Anúncios publicitários em mídias digitais",
        "Analisar visões de mundo e discursos veiculados nas mídias.",
        "Ler anúncios digitais, observar a seção De olho no material e discutir efeitos de sentido.",
    )

    texto = " ".join(acessibilidade).lower()

    assert "esquema anatômico" not in texto
    assert "retina" not in texto


def test_continuidade_metodologica_preserva_acentos():
    texto = _ajustar_texto_por_sequencia(
        "Na prática: orientar a leitura e o registro no caderno.",
        "foco",
        indice_aula=1,
        total_aulas=2,
        tema="Trovadorismo",
    )

    assert "necessário" in texto
    assert "necessario" not in texto


def test_lp_ef_acompanhamento_e_acessibilidade_especificos_por_conteudo():
    casos = [
        (
            "Conexões entre canção e reflexão",
            "Ler a letra da canção Pela internet e registrar impressões.",
            ["canção", "letra"],
        ),
        (
            "Explorando a intertextualidade",
            "Comparar Monte Castelo com Camões e reconhecer intertextualidade.",
            ["intertextualidade", "quadro comparativo"],
        ),
        (
            "Versos que envolvem",
            "Analisar figuras de linguagem e anáfora no poema.",
            ["figuras de linguagem", "versos"],
        ),
        (
            "Haicai: simplicidade e profundidade",
            "Ler haicai de Matsuo Bashô e observar imagens poéticas.",
            ["haicai", "três versos"],
        ),
        (
            "Pequenas histórias, grandes mensagens",
            "Ler minicontos e analisar pistas, vírgula e efeito final.",
            ["miniconto", "pistas"],
        ),
        (
            "Tramas das novelas literárias",
            "Ler trecho de O alienista, Casa Verde e personagens da novela.",
            ["novela", "personagens"],
        ),
    ]

    for tema, desenvolvimento, esperados in casos:
        acompanhamento = gerar_acompanhamento_por_perfil(
            "lingua_portuguesa_ef",
            tema,
            "Ler e interpretar textos literários e multissemióticos.",
            desenvolvimento,
        )
        acessibilidade = gerar_acessibilidade_por_perfil(
            "lingua_portuguesa_ef",
            tema,
            "Ler e interpretar textos literários e multissemióticos.",
            desenvolvimento,
        )
        texto_total = " ".join(acompanhamento + acessibilidade).lower()

        assert len(acompanhamento) == 3
        assert len(acessibilidade) == 3
        assert all(palavra in texto_total for palavra in esperados)
        assert "narrador, personagens e conflito" not in texto_total
        assert "checklist simplificado" not in texto_total
        assert "roteiro de fala ou gravação" not in texto_total
        assert "informação do material" not in texto_total


def test_lp_ef_habilidade_generica_nao_contamina_genero_da_aula():
    habilidade_ef89lp33 = (
        "Ler romances, contos contemporâneos, minicontos, novelas, poemas de forma livre "
        "e fixa como haicai, expressando avaliação sobre o texto lido."
    )
    casos = [
        (
            "Pequenas histórias, grandes mensagens",
            "Ler minicontos e analisar pistas, vírgula, concisão e efeito final.",
            ["miniconto", "pistas"],
            ["haicai", "três versos", "imagem poética"],
        ),
        (
            "Tramas das novelas literárias",
            "Ler trecho de O Alienista e interpretar personagens, conflito e crítica social.",
            ["novela", "personagens"],
            ["haicai", "três versos", "imagem poética"],
        ),
    ]

    for tema, desenvolvimento, esperados, proibidos in casos:
        acompanhamento = gerar_acompanhamento_por_perfil(
            "lingua_portuguesa_ef",
            tema,
            habilidade_ef89lp33,
            desenvolvimento,
        )
        acessibilidade = gerar_acessibilidade_por_perfil(
            "lingua_portuguesa_ef",
            tema,
            habilidade_ef89lp33,
            desenvolvimento,
        )
        texto_total = " ".join(acompanhamento + acessibilidade).lower()

        assert len(acompanhamento) == 3
        assert len(acessibilidade) == 3
        assert all(palavra in texto_total for palavra in esperados)
        assert not any(palavra in texto_total for palavra in proibidos)


def test_lp_ef_novela_com_ironia_nao_cai_em_figuras_de_linguagem():
    acompanhamento = gerar_acompanhamento_por_perfil(
        "lingua_portuguesa_ef",
        "Tramas das novelas literárias",
        "Ler e interpretar textos literários.",
        "Explorar O Alienista, de Machado de Assis, observando personagens, Casa Verde, ironia e crítica social.",
    )
    acessibilidade = gerar_acessibilidade_por_perfil(
        "lingua_portuguesa_ef",
        "Tramas das novelas literárias",
        "Ler e interpretar textos literários.",
        "Explorar O Alienista, de Machado de Assis, observando personagens, Casa Verde, ironia e crítica social.",
    )
    texto_total = " ".join(acompanhamento + acessibilidade).lower()

    assert "novela" in texto_total
    assert "personagens" in texto_total
    assert "figura de linguagem" not in texto_total
    assert "versos" not in texto_total


def test_lingua_portuguesa_em_classifica_conteudos_do_3_bimestre():
    casos = [
        ("Barroco - Gregório de Matos", "poesia satírica e lírica no Barroco", "literatura"),
        ("As várias faces da Canção do exílio", "identidade brasileira e intertextualidade", "literatura"),
        ("Artigo de opinião – Parte 1", "tese, argumentos e debate de ideias", "genero_textual"),
        ("Carta do leitor", "ponto de vista e interlocutor", "genero_textual"),
        ("Texto de divulgação científica – Parte 1", "público-alvo e linguagem acessível", "genero_textual"),
        ("Variação e norma – Parte I", "variação linguística, norma-padrão e adequação", "gramatica_integrada"),
        ("Debate regrado – Parte 1", "turnos de fala, argumento e contra-argumento", "pratica_oral"),
    ]

    for titulo, texto, esperado in casos:
        assert detectar_tipo_aula(texto, titulo, "Língua Portuguesa", turma="EM") == esperado


def test_lingua_portuguesa_em_3_bimestre_nao_usa_acompanhamento_generico():
    casos = [
        (
            "A literatura medieval portuguesa e suas influências",
            "Ler cantigas medievais, observar contexto histórico e marcas literárias.",
            ["literário", "contexto"],
        ),
        (
            "Anúncios publicitários em mídias digitais",
            "Analisar anúncio digital, público-alvo, suporte, imagem e persuasão.",
            ["público-alvo", "anúncio"],
        ),
        (
            "Um fato, duas versões - (im)parcialidade em textos noticiosos",
            "Comparar textos noticiosos e observar fato, opinião, fonte e parcialidade.",
            ["parcialidade", "noticiosos"],
        ),
        (
            "O gênero diário pessoal - reflexões do cotidiano",
            "Ler diário pessoal, marcas de subjetividade e registro do cotidiano.",
            ["subjetividade", "diário"],
        ),
        (
            "O texto teatral - esquete",
            "Analisar esquete, personagens, conflito, falas e rubricas.",
            ["rubricas", "personagens"],
        ),
        (
            "Resenha crítica – Parte 1",
            "Planejar resenha crítica com síntese, avaliação e recomendação.",
            ["resenha", "avaliação"],
        ),
        (
            "Artigo de opinião – Parte 5 - Planejamento",
            "Planejar artigo de opinião com tese, argumentos e conclusão.",
            ["tese", "argumentos"],
        ),
        (
            "Fotodenúncia – Parte 1",
            "Analisar fotodenúncia, imagem, denúncia social, legenda e autoria.",
            ["denúncia", "imagem"],
        ),
        (
            "Manifesto – Parte 1",
            "Ler manifesto, problema coletivo, reivindicação e chamada à ação.",
            ["reivindicação", "manifesto"],
        ),
        (
            "Debate regrado – Parte 1",
            "Planejar debate regrado com turnos de fala, argumentos e evidências.",
            ["debate", "turnos"],
        ),
        (
            "Texto de divulgação científica – Parte 1",
            "Ler texto de divulgação científica, público-alvo, conceito e exemplo.",
            ["científica", "público-alvo"],
        ),
        (
            "O texto dissertativo-argumentativo I – Parte 1",
            "Organizar texto dissertativo-argumentativo com tema, tese e repertório.",
            ["tese", "argumentativa"],
        ),
        (
            "Variação e norma – Parte I",
            "Comparar variação linguística, norma-padrão, registro e contexto.",
            ["norma-padrão", "variação"],
        ),
        (
            "Miniconto e microconto – Parte 1",
            "Ler miniconto e microconto, concisão, implícitos e efeito final.",
            ["concisão", "microconto"],
        ),
    ]
    proibidos = [
        "gênero estudado",
        "recursos gramaticais/linguísticos",
        "texto âncora",
        "roteiro estruturado",
    ]

    for tema, desenvolvimento, esperados in casos:
        acompanhamento = gerar_acompanhamento_por_perfil(
            "lingua_portuguesa_em",
            tema,
            "Interpretar e produzir sentidos a partir dos textos estudados.",
            desenvolvimento,
        )
        acessibilidade = gerar_acessibilidade_por_perfil(
            "lingua_portuguesa_em",
            tema,
            "Interpretar e produzir sentidos a partir dos textos estudados.",
            desenvolvimento,
        )
        texto_total = " ".join(acompanhamento + acessibilidade).lower()

        assert len(acompanhamento) == 3
        assert len(acessibilidade) == 3
        assert all(item.startswith("☑ ") for item in acompanhamento)
        assert all(item.startswith("☑ ") for item in acessibilidade)
        assert all(palavra in texto_total for palavra in esperados)
        assert not any(palavra in texto_total for palavra in proibidos)
