from core.lib.gerador_colunas_pedagogicas import montar_colunas_pedagogicas, norm
import pytest


def test_gerador_colunas_so_insere_lemov_quando_aparece_no_texto():
    texto_sem_lemov = (
        "Conteudos\n"
        "● Inflacao\n"
        "● IPCA\n"
        "Objetivos\n"
        "● Analisar a relacao entre inflacao e poder de compra.\n"
        "A aula apresenta grafico de colunas com variacao do IPCA e leitura de dados.\n"
    )
    texto_com_lemov = texto_sem_lemov + "\nNo momento inicial, fazer Virem e conversem antes da leitura do grafico.\n"

    sem_lemov = montar_colunas_pedagogicas(texto_sem_lemov, "AULA 10 - Inflacao")
    com_lemov = montar_colunas_pedagogicas(texto_com_lemov, "AULA 10 - Inflacao")

    desenvolvimento_sem = sem_lemov["desenvolvimento"].lower()
    desenvolvimento_com = com_lemov["desenvolvimento"].lower()

    assert "virem e conversem" not in desenvolvimento_sem
    assert "todo mundo escreve" not in desenvolvimento_sem
    assert "virem e conversem" in desenvolvimento_com


def test_gerador_colunas_para_inflacao_nao_puxa_credito_sem_necessidade():
    texto = (
        "Conteudos\n"
        "● Inflacao\n"
        "● IPCA\n"
        "● Poder de compra\n"
        "Objetivos\n"
        "● Analisar como a inflacao afeta os precos e o poder de compra.\n"
        "Para comecar: observar manchete sobre inflacao.\n"
        "Foco no conteudo: interpretar grafico e tabela do IPCA.\n"
        "Pause e responda: comparar variacoes e justificar conclusoes.\n"
    )

    colunas = montar_colunas_pedagogicas(texto, "AULA 10 - Inflacao e poder de compra")
    desenvolvimento = colunas["desenvolvimento"].lower()
    acompanhamento = " ".join(colunas["acompanhamento_aprendizagem"]).lower()
    acessibilidade = " ".join(colunas["acessibilidade"]).lower()

    desenvolvimento_norm = norm(desenvolvimento)
    assert "grafico" in desenvolvimento_norm or "graficos" in desenvolvimento_norm
    assert "ipca" in desenvolvimento_norm or "poder de compra" in desenvolvimento_norm
    assert "credito" not in desenvolvimento
    assert "parcel" not in desenvolvimento
    assert "credito" not in acompanhamento
    assert "parcel" not in acompanhamento
    assert "credito" not in acessibilidade
    assert "parcel" not in acessibilidade


def test_portugues_prosa_modernista_nao_vira_noticia_ou_tabela():
    texto = (
        "Segunda geração modernista: Prosa de 30 - Parte 1\n"
        "Conteúdos\n"
        "● Prosa regionalista\n"
        "● Rachel de Queiroz e O Quinze\n"
        "Objetivos\n"
        "● Analisar contexto histórico, narrador, personagens e linguagem literária.\n"
        "O material cita uma fonte jornalística apenas como apoio, mas a aula é de literatura."
    )

    colunas = montar_colunas_pedagogicas(texto, "AULA 17 - Segunda geração modernista: Prosa de 30")
    desenvolvimento = norm(colunas["desenvolvimento"])

    assert colunas["pistas"].perfil == "literatura_prosa"
    assert "noticia" not in desenvolvimento
    assert "tabela" not in desenvolvimento
    assert "grafico" not in desenvolvimento
    assert "texto literario" in desenvolvimento


def test_portugues_cronica_nao_vira_noticia():
    texto = (
        "Os olhares do cotidiano: desvendando o gênero crônica - Parte 1\n"
        "Conteúdos\n"
        "● Crônica\n"
        "● Voz narrativa e marcas de linguagem\n"
        "Objetivos\n"
        "● Analisar a relação entre cotidiano, linguagem e efeitos de sentido."
    )

    colunas = montar_colunas_pedagogicas(texto, "AULA 24 - Os olhares do cotidiano: desvendando o gênero crônica")
    desenvolvimento = norm(colunas["desenvolvimento"])

    assert colunas["pistas"].perfil == "cronica"
    assert "noticia" not in desenvolvimento
    assert "caso discutido" not in desenvolvimento
    assert "cronica" in desenvolvimento


def test_portugues_texto_normativo_nao_inventa_tabela_por_quadro():
    texto = (
        "Por dentro das normas - Parte 1\n"
        "Conteúdos\n"
        "● Estatuto da Pessoa Idosa\n"
        "● Textos legais e normativos\n"
        "Objetivos\n"
        "● Analisar finalidade, direitos assegurados e linguagem objetiva.\n"
        "O professor pode organizar um quadro de apoio na lousa."
    )

    colunas = montar_colunas_pedagogicas(texto, "AULA 1 - Por dentro das normas")
    desenvolvimento = norm(colunas["desenvolvimento"])

    assert colunas["pistas"].perfil == "texto_normativo"
    assert "noticia" not in desenvolvimento
    assert "tabela" not in desenvolvimento
    assert "texto normativo" in desenvolvimento


def test_portugues_editorial_fica_argumentativo_sem_grafico():
    texto = (
        "Visões diversas em editoriais - Parte 1\n"
        "Conteúdos\n"
        "● Editorial\n"
        "● Tese, argumentos e ponto de vista\n"
        "Objetivos\n"
        "● Analisar estratégias argumentativas e projeto editorial."
    )

    colunas = montar_colunas_pedagogicas(texto, "AULA 20 - Visões diversas em editoriais")
    desenvolvimento = norm(colunas["desenvolvimento"])

    assert colunas["pistas"].perfil == "editorial_argumentativo"
    assert "grafico" not in desenvolvimento
    assert "tabela" not in desenvolvimento
    assert "editorial" in desenvolvimento


@pytest.mark.parametrize(
    ("titulo", "texto", "perfil", "termo_esperado"),
    [
        (
            "AULA 3 - Textos contemporâneos na construção da opinião",
            "Artigo de opinião. Tese, argumentos, posicionamento e ponto de vista do autor.",
            "artigo_opiniao",
            "artigo de opiniao",
        ),
        (
            "AULA 7 - Oralidade: entrevista",
            "Entrevista oral. Turnos de fala, marcas de oralidade, transcrição e variação linguística.",
            "oralidade_entrevista",
            "entrevista",
        ),
        (
            "AULA 9 - O que o texto revela",
            "Poema, soneto, verso, estrofe, eu lírico, rima, métrica e imagens poéticas.",
            "poema",
            "poema",
        ),
        (
            "AULA 12 - Semana de Arte Moderna",
            "Modernismo, Semana de Arte Moderna, Mário de Andrade, Oswald de Andrade e rupturas estéticas.",
            "literatura_modernismo",
            "movimento literario",
        ),
        (
            "AULA 21 - Visões diversas em editoriais",
            "Editorial, tese, argumentos, posicionamento do veículo, regência verbal e modalização.",
            "editorial_argumentativo",
            "analise linguistica",
        ),
    ],
)
def test_gerador_reconhece_perfis_da_auditoria_portugues_2b(titulo, texto, perfil, termo_esperado):
    colunas = montar_colunas_pedagogicas(texto, titulo)
    desenvolvimento = norm(colunas["desenvolvimento"])

    assert colunas["pistas"].perfil == perfil
    assert termo_esperado in desenvolvimento
    assert "noticia" not in desenvolvimento
    assert "tabela" not in desenvolvimento
    assert "grafico" not in desenvolvimento
