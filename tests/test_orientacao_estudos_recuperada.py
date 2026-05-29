from core.disciplinas import nomes_disciplinas
from core.lote import _material_digital_por_texto, _montar_etapas_metodologia
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
            "MISSAO 7 - Projetos culturais e coesão textual\n"
            "Leitura do projeto cultural.\n"
            "DE OLHO NO SAEB\n"
            "1: LP5LERE01 | N2.3 | Fácil\n"
        ),
        disciplina="Orientação de Estudos",
        turma="6º ano A",
        tema="MISSAO 7 - Projetos culturais e coesão textual",
    )

    titulos = [item["titulo"] for item in metodologia]
    corpo = " ".join(item["texto"] for item in metodologia).lower()

    assert titulos == [
        "Para comecar",
        "Leitura e construcao do conteudo",
        "Foco no conteudo",
        "Na pratica",
        "Pause e responda",
        "Encerramento",
    ]
    assert "estrategia de estudo" in corpo
    assert "palavras-chave" in corpo
    assert "de olho no saeb" in corpo


def test_prompt_orientacao_estudos_reforca_como_estudar():
    prompt = get_system_prompt("Orientação de Estudos")
    orientacao = get_orientacao_disciplina("Orientação de Estudos")

    assert "como estudar" in prompt.lower()
    assert "leitura e construcao do conteudo" in orientacao.lower()
    assert "de olho no saeb" in orientacao.lower()
