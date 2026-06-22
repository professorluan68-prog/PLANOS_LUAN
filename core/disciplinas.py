from dataclasses import dataclass
import unicodedata


BIMESTRES = ["1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"]
MODO_PDF = "pdf"
MODO_CDP = "cdp"
MODO_CDP_FUNDAMENTAL = "cdp_fundamental"

DISCIPLINA_CDP_MULTISSERIADA = "CDP- Multisseriada"
DISCIPLINA_CDP_CICLO_I = "CDP - Ciclo I"
DISCIPLINA_CDP_FUNDAMENTAL = "CDP-ENSINO FUNDAMENTAL"
DISCIPLINA_CDP_MEDIO = "CDP-ENSINO MÉDIO"
DISCIPLINA_GEOGRAFIA_CDP_MEDIO = "Geografia CDP Ensino Médio"


@dataclass(frozen=True)
class DisciplinaConfig:
    nome: str
    modo: str = MODO_PDF
    exige_pdf: bool = True
    aprendizagem_padrao: str = (
        "Desenvolver habilidades relacionadas ao tema da aula, participando das "
        "atividades propostas e registrando as principais aprendizagens."
    )


_DISCIPLINAS = [
    "Arte",
    "Biologia",
    "Aprofundamento em Biologia",
    "Ciências",
    "Educação Financeira",
    "Educação Física",
    "Filosofia",
    "Física",
    "Geografia",
    "Aprofundamento em Geografia",
    "História",
    "Liderança e Oratória",
    "Língua Inglesa",
    "Língua Portuguesa",
    "Matemática",
    "Orientação de Estudos",
    DISCIPLINA_CDP_FUNDAMENTAL,
    DISCIPLINA_CDP_MEDIO,
    DISCIPLINA_GEOGRAFIA_CDP_MEDIO,
    DISCIPLINA_CDP_MULTISSERIADA,
    "Projeto de Vida",
    "Química",
    "Redação e Leitura",
    "Sociologia",
    "Tecnologia e Inovação",
    "Outra",
]

TURMAS_CDP = [
    "MULTISSERIADO 1º, 2º e 3º ano",
    "MULTISSERIADO 4º e 5º ano",
    "6º/7º E.F",
    "8º/9º E.F",
    "1º/2º/3º E.M",
]
TURMAS_CDP_MULTISSERIADA = TURMAS_CDP


def _normalizar_nome_disciplina(nome: str) -> str:
    valor = unicodedata.normalize("NFKD", str(nome or "").strip().upper())
    valor = "".join(ch for ch in valor if not unicodedata.combining(ch))
    return " ".join(valor.split())


def nomes_disciplinas() -> list[str]:
    return list(_DISCIPLINAS)


def obter_config(disciplina: str) -> DisciplinaConfig:
    nome = (disciplina or "Outra").strip() or "Outra"
    nome_normalizado = _normalizar_nome_disciplina(nome)

    if nome_normalizado == _normalizar_nome_disciplina(DISCIPLINA_CDP_MULTISSERIADA):
        return DisciplinaConfig(nome=nome, modo=MODO_CDP, exige_pdf=False)
    if nome_normalizado == _normalizar_nome_disciplina(DISCIPLINA_CDP_CICLO_I):
        return DisciplinaConfig(nome=nome, modo=MODO_CDP_FUNDAMENTAL, exige_pdf=False)
    return DisciplinaConfig(nome=nome)


def eh_cdp(nome: str) -> bool:
    return obter_config(nome).modo in {MODO_CDP, MODO_CDP_FUNDAMENTAL}


def eh_cdp_multisseriada(nome: str) -> bool:
    return obter_config(nome).modo == MODO_CDP


def eh_cdp_fundamental(nome: str) -> bool:
    return obter_config(nome).modo == MODO_CDP_FUNDAMENTAL


def eh_cdp_contextual(nome: str) -> bool:
    chave = _normalizar_nome_disciplina(nome)
    chave_compacta = chave.replace(" ", "")
    return chave in {
        _normalizar_nome_disciplina(DISCIPLINA_CDP_FUNDAMENTAL),
        _normalizar_nome_disciplina(DISCIPLINA_CDP_MEDIO),
    } or (
        "CDP" in chave_compacta
        and (
            "ENSINOMEDIO" in chave_compacta
            or "ENSINOFUNDAMENTAL" in chave_compacta
            or chave_compacta.endswith("CDPEM")
            or chave_compacta.endswith("CDPEF")
        )
    )
