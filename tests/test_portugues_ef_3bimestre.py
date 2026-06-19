import pytest

from core.lib.classificador import detectar_tipo_aula
from core.lib.gerador_colunas_pedagogicas import montar_colunas_pedagogicas, norm
from core.lib.metodologia import MotorMetodologico
from core.prompts_por_disciplina import get_orientacao_disciplina, get_system_prompt


def test_prompt_lingua_portuguesa_reconhece_turma_fundamental_com_ordinal():
    prompt = get_system_prompt("Língua Portuguesa", "7º ano A")
    orientacao = get_orientacao_disciplina("Língua Portuguesa", turma="7º ano A")

    assert "Ensino Fundamental" in prompt
    assert "Ensino Medio" not in prompt
    assert "Ensino Fundamental" in orientacao


def test_prompt_lingua_portuguesa_medio_permanece_medio():
    prompt = get_system_prompt("Língua Portuguesa", "1º ano C")

    assert "Ensino Medio" in prompt
    assert "Ensino Fundamental" not in prompt


@pytest.mark.parametrize(
    ("titulo", "texto", "tipo_esperado"),
    [
        (
            "AULA 3 - Leitura de campanha ambiental",
            "Cartaz de campanha ambiental com infografico, texto verbal, texto nao verbal e legenda sobre plastico nos oceanos.",
            "leitura_multimodal",
        ),
        (
            "AULA 5 - Do esquema ao resumo",
            "Infografico com topicos e informacoes principais. Resumo, paragrafos, topico frasal, coerencia e retextualizacao.",
            "resumo_retextualizacao",
        ),
        (
            "AULA 7 - Biscoito ou bolacha?",
            "Variacao linguistica, regionalismo, registro formal e informal, preconceito linguistico e usos da lingua.",
            "variacao_linguistica",
        ),
        (
            "AULA 9 - Debate sobre celular na escola",
            "Tema polemico sobre uso de celular na escola. Tese, argumento, contra-argumento, ponto de vista, lei e planejar debate.",
            "argumentacao_debate",
        ),
        (
            "AULA 11 - A voz da internet - Parte 2",
            "Post de blog, comentario, publico leitor, argumentos apresentados e relacao com a internet.",
            "texto_digital_blog",
        ),
        (
            "AULA 13 - Ortografia em contexto",
            "Ortografia, discurso direto, paragrafacao, topico frasal, concordancia nominal e x ou ch em trechos do texto.",
            "analise_linguistica_ortografia",
        ),
    ],
)
def test_detecta_tipos_novos_portugues_ef_3bimestre(titulo, texto, tipo_esperado):
    assert detectar_tipo_aula(texto, titulo, "Lingua Portuguesa", turma="9 ANO") == tipo_esperado


def test_metodologia_argumentacao_debate_inclui_planejamento():
    motor = MotorMetodologico()
    texto = (
        "Para comecar\n"
        "Tirinha sobre debate.\n"
        "Foco no conteudo\n"
        "Argumento, contra-argumento, tese e ponto de vista.\n"
        "Pause e responda\n"
        "Identificar o tipo de argumento.\n"
        "Hora da leitura\n"
        "Noticia sobre projeto de lei e uso de celular na escola.\n"
        "Na pratica\n"
        "Selecionar argumentos favoraveis e contrarios para o debate.\n"
    )

    metodologia = motor.gerar(
        texto_pdf=texto,
        disciplina="Lingua Portuguesa",
        turma="9 ANO",
        tema="Uso de celular na escola",
    )
    titulos = [etapa["titulo"] for etapa in metodologia]

    assert "Planejamento do debate" in titulos
    assert "Hora da leitura" in titulos
    assert "Pause e responda" in titulos


def test_metodologia_post_blog_de_continuidade_usa_relembre():
    motor = MotorMetodologico()
    texto = (
        "Relembre\n"
        "Retomar o post A voz da internet.\n"
        "Hora da leitura\n"
        "Post de blog com comentario, exemplos e publico leitor.\n"
        "Foco no conteudo\n"
        "Registro de linguagem e argumentos apresentados.\n"
        "Todo mundo escreve\n"
        "Escrever um comentario.\n"
    )

    metodologia = motor.gerar(
        texto_pdf=texto,
        disciplina="Lingua Portuguesa",
        turma="9 ANO",
        tema="A voz da internet - Parte 2",
    )
    titulos = [etapa["titulo"] for etapa in metodologia]

    assert titulos[0] == "Relembre"
    assert "Hora da leitura" in titulos
    assert "Todo mundo escreve" in titulos


@pytest.mark.parametrize(
    ("titulo", "texto", "perfil_esperado", "trecho_esperado"),
    [
        (
            "AULA 3 - Campanha ambiental",
            "Cartaz de campanha, infografico, texto verbal e texto nao verbal sobre plastico nos oceanos.",
            "leitura_multimodal",
            "texto multimodal",
        ),
        (
            "AULA 5 - Biscoito ou bolacha?",
            "Variacao linguistica, registro formal e informal, regionalismo e preconceito linguistico.",
            "variacao_linguistica_registro",
            "variacao linguistica",
        ),
        (
            "AULA 8 - Do infografico ao resumo",
            "Infografico, topicos, resumo, retextualizacao, paragrafos e topico frasal.",
            "resumo_retextualizacao",
            "paragrafos",
        ),
        (
            "AULA 11 - A voz da internet",
            "Post de blog, comentario, publico leitor e argumentos apresentados.",
            "texto_digital_blog",
            "post de blog",
        ),
        (
            "AULA 13 - Ortografia em contexto",
            "Ortografia, discurso direto, concordancia nominal, x ou ch e paragrafacao.",
            "analise_linguistica_ortografia",
            "ortografico",
        ),
    ],
)
def test_gerador_colunas_reconhece_novos_perfis_portugues_ef(titulo, texto, perfil_esperado, trecho_esperado):
    colunas = montar_colunas_pedagogicas(texto, titulo)
    desenvolvimento = norm(colunas["desenvolvimento"])

    assert colunas["pistas"].perfil == perfil_esperado
    assert trecho_esperado in desenvolvimento


def test_diario_pessoal_recupera_acompanhamento_e_acessibilidade_corretos():
    texto = (
        "Diario pessoal. Escrita em primeira pessoa, temporalidade, subjetividade e reflexoes do cotidiano.\n"
        "Registro de sentimentos e acontecimentos narrados."
    )
    colunas = montar_colunas_pedagogicas(texto, "AULA 10 - Diario pessoal")

    acompanhamento = norm(" ".join(colunas["acompanhamento_aprendizagem"]))
    acessibilidade = norm(" ".join(colunas["acessibilidade"]))

    assert "subjetividade" in acompanhamento or "experiencias narradas" in acompanhamento or "trechos do diario" in acompanhamento
    assert "roteiro" in acessibilidade or "temporalidade" in acessibilidade
