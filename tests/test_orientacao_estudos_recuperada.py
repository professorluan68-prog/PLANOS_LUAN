from core.disciplinas import nomes_disciplinas
from core.lote import _material_digital_por_texto, _montar_etapas_metodologia
from core.orientacao_estudos_objetivos import buscar_objetivos_orientacao_estudos, formatar_objetivos_orientacao_estudos
from core.prompts_por_disciplina import get_orientacao_disciplina, get_system_prompt


def test_orientacao_estudos_aparece_no_cadastro():
    assert "Orientação de Estudos" in nomes_disciplinas()


def test_orientacao_estudos_trilha_usa_catalogo_recuperado():
    material = _material_digital_por_texto(
        "Texto inicial da trilha.",
        "TRILHA7.pdf",
        "Orientação de Estudos",
    )

    assert material == "TRILHA 7 - Projetos culturais e coesão textual"


def test_orientacao_estudos_jornada_usa_catalogo_recuperado():
    material = _material_digital_por_texto(
        "Texto inicial da jornada.",
        "JORNADA11.pdf",
        "Orientação de Estudos",
    )

    assert material == "JORNADA 11 - Linguagem poética: poema, slam e canção"


def test_orientacao_estudos_sp_ensino_fundamental_encontra_missao_pelo_texto():
    texto = (
        "SÃO PAULO EM AÇÃO\n"
        "Jogos com palavras e imagens\n"
        "DE OLHO NO SAEB\n"
        "1: LP5LERE01 | N2.3 | Fácil\n"
    )

    material = _material_digital_por_texto(
        texto,
        "SP-ENSINOFUNDAMENTAL.pdf",
        "Orientação de Estudos",
    )

    assert material == "MISSAO 1 - Jogos com palavras e imagens"


def test_metodologia_orientacao_estudos_tem_blocos_proprios_e_identidade_recuperada():
    metodologia = _montar_etapas_metodologia(
        texto=(
            "TRILHA 7 - Projetos culturais e coesão textual\n"
            "Etapa 1\n"
            "Leitura do projeto cultural.\n"
            "DE OLHO NO SAEB\n"
            "1: LP5LERE01 | N2.3 | Fácil\n"
        ),
        disciplina="Orientação de Estudos",
        turma="6º ano A",
        tema="TRILHA 7 - Projetos culturais e coesão textual - ETAPA 1",
    )

    titulos = [item["titulo"] for item in metodologia]
    corpo = " ".join(item["texto"] for item in metodologia).lower()

    assert titulos == [
        "Para comecar",
        "Leitura e construcao do conteudo",
        "Foco no conteudo",
        "Na pratica",
        "Encerramento",
    ]
    assert "projetos culturais" in corpo
    assert "palavras-chave" in corpo
    assert "resolver" in corpo or "respostas" in corpo


def test_prompt_orientacao_estudos_reforca_como_estudar():
    prompt = get_system_prompt("Orientação de Estudos")
    orientacao = get_orientacao_disciplina("Orientação de Estudos")

    assert "como estudar" in prompt.lower()
    assert "leitura e construcao do conteudo" in orientacao.lower()
    assert "na pratica e encerramento" in orientacao.lower()
    assert "de olho no saeb" in orientacao.lower()


def test_metodologia_orientacao_estudos_missao_6_etapa_1_fica_especifica():
    metodologia = _montar_etapas_metodologia(
        texto=(
            "MISSAO 6 - Uma palavra puxa a outra\n"
            "Etapa 1\n"
            "Greta Thunberg e o movimento #FridaysForFuture.\n"
            "Reportagem sobre mudancas climaticas.\n"
        ),
        disciplina="Orientação de Estudos",
        turma="6º ano A",
        tema="MISSAO 6 - Uma palavra puxa a outra - ETAPA 1",
    )

    corpo = " ".join(item["texto"] for item in metodologia).lower()

    assert "greta thunberg" in corpo
    assert "fridaysforfuture" in corpo
    assert "reportagem" in corpo


def test_metodologia_orientacao_estudos_missao_10_etapa_1_fica_especifica():
    metodologia = _montar_etapas_metodologia(
        texto=(
            "MISSAO 10 - A voz da poesia\n"
            "Etapa 1\n"
            "O gato.\n"
            "Leia o poema em silencio e tambem em voz alta, percebendo os sons que rimam.\n"
        ),
        disciplina="Orientação de Estudos",
        turma="6º ano A",
        tema="MISSAO 10 - A voz da poesia - ETAPA 1",
    )

    corpo = " ".join(item["texto"] for item in metodologia).lower()

    assert "o gato" in corpo
    assert "rimas" in corpo
    assert "versos" in corpo


def test_metodologia_orientacao_estudos_missao_11_etapa_1_fica_especifica():
    metodologia = _montar_etapas_metodologia(
        texto=(
            "MISSAO 11 - Um mergulho no cordel\n"
            "Etapa 1\n"
            "A Bela e a Fera em cordel.\n"
            "Leia-o, observando as rimas presentes nele.\n"
        ),
        disciplina="Orientação de Estudos",
        turma="6º ano A",
        tema="MISSAO 11 - Um mergulho no cordel - ETAPA 1",
    )

    corpo = " ".join(item["texto"] for item in metodologia).lower()

    assert "a bela e a fera em cordel" in corpo
    assert "cordel" in corpo
    assert "rimas" in corpo


def test_metodologia_orientacao_estudos_jornada_13_fica_especifica():
    metodologia = _montar_etapas_metodologia(
        texto=(
            "JORNADA 13 - Recursos midiaticos\n"
            "Observe a charge e o ranking apresentados na aula.\n"
            "As preferencias profissionais aparecem organizadas em recurso grafico.\n"
        ),
        disciplina="Orientação de Estudos",
        turma="3º ano C",
        tema="JORNADA 13 - Recursos midiáticos",
    )

    corpo = " ".join(item["texto"] for item in metodologia).lower()

    assert "charge" in corpo
    assert "ranking" in corpo
    assert "preferencias profissionais" in corpo or "profissionais" in corpo


def test_metodologia_orientacao_estudos_jornada_13_aula_4_fica_especifica():
    metodologia = _montar_etapas_metodologia(
        texto=(
            "JORNADA 13 - Recursos midiaticos\n"
            "A charge trata de amigos virtuais e redes sociais.\n"
            "O cartaz de conscientizacao apresenta recomendacoes de orgaos de saude sobre vacinacao.\n"
        ),
        disciplina="Orientação de Estudos",
        turma="3º ano C",
        tema="JORNADA 13 - Recursos midiáticos",
    )

    corpo = " ".join(item["texto"] for item in metodologia).lower()

    assert "redes" in corpo or "virtuais" in corpo
    assert "saude" in corpo
    assert "conscientizacao" in corpo or "campanhas" in corpo


def test_metodologia_orientacao_estudos_jornada_14_fica_especifica():
    metodologia = _montar_etapas_metodologia(
        texto=(
            "JORNADA 14 - A lingua (a) viva: variedades linguisticas\n"
            "Lingua portuguesa: existe so uma?\n"
            "Variacao linguistica historica, geografica e social/cultural.\n"
            "Registro formal e informal.\n"
        ),
        disciplina="Orientação de Estudos",
        turma="3º ano C",
        tema="JORNADA 14 - A língua (a) viva: variedades linguísticas",
    )

    corpo = " ".join(item["texto"] for item in metodologia).lower()

    assert "variacao linguistica" in corpo
    assert "registro formal" in corpo or "registro informal" in corpo
    assert "diversidade linguistica" in corpo or "lingua viva" in corpo


def test_metodologia_orientacao_estudos_jornada_14_aula_4_fica_especifica():
    metodologia = _montar_etapas_metodologia(
        texto=(
            "JORNADA 14 - A lingua (a) viva: variedades linguisticas\n"
            "Girias das redes sociais caem na boca do povo.\n"
            "Migna terra te parmeras.\n"
            "Hunsruckisch e falado em algumas regioes do pais.\n"
        ),
        disciplina="Orientação de Estudos",
        turma="3º ano C",
        tema="JORNADA 14 - A língua (a) viva: variedades linguísticas",
    )

    corpo = " ".join(item["texto"] for item in metodologia).lower()

    assert "girias" in corpo or "redes sociais" in corpo
    assert "plurilinguismo" in corpo or "hunsruckisch" in corpo or "diversidade linguistica" in corpo
    assert "preconceitos" in corpo or "preconceito" in corpo


def test_busca_objetivos_catalogados_da_missao_10():
    objetivos = buscar_objetivos_orientacao_estudos(
        caminho_pdf="MISSAO10 - ETAPA 2.pdf",
        tema="MISSAO 10 - A voz da poesia - ETAPA 2",
    )

    assert objetivos == [
        "Compreender as características de um poema.",
        "Analisar as marcas linguísticas de poemas para inferir quem é o eu lírico e com quem ele dialoga.",
    ]


def test_busca_objetivos_catalogados_da_jornada_14():
    objetivos = buscar_objetivos_orientacao_estudos(
        caminho_pdf="JORNADA14 - AULA 2.pdf",
        tema="JORNADA 14 - A língua (a) viva: variedades linguísticas",
    )

    assert objetivos == [
        "Compreender que a língua está viva e apresenta variedades linguísticas em diferentes tempos, lugares e grupos sociais.",
        "Analisar marcas de variação linguística e usos de registro formal e informal em diferentes gêneros e situações comunicativas.",
        "Refletir criticamente sobre preconceito linguístico, plurilinguismo e diversidade de formas de dizer.",
    ]


def test_formata_objetivos_catalogados_para_aprendizagem():
    texto = formatar_objetivos_orientacao_estudos(
        [
            "Compreender as características de um poema.",
            "Analisar as marcas linguísticas de poemas para inferir quem é o eu lírico e com quem ele dialoga.",
        ]
    )

    assert texto == (
        "Compreender as características de um poema. • "
        "Analisar as marcas linguísticas de poemas para inferir quem é o eu lírico e com quem ele dialoga."
    )
