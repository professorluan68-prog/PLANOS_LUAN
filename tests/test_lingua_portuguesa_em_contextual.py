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
