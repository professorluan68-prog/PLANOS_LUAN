from dataclasses import dataclass


BIMESTRES = ["1Âº Bimestre", "2Âº Bimestre", "3Âº Bimestre", "4Âº Bimestre"]
MODO_PDF = "pdf"
MODO_CDP = "cdp"
MODO_CDP_FUNDAMENTAL = "cdp_fundamental"


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
    "CiÃªncias",
    "EducaÃ§Ã£o Financeira",
    "EducaÃ§Ã£o FÃ­sica",
    "Filosofia",
    "FÃ­sica",
    "Geografia",
    "HistÃ³ria",
    "LideranÃ§a e OratÃ³ria",
    "LÃ­ngua Inglesa",
    "LÃ­ngua Portuguesa",
    "MatemÃ¡tica",
    "CDP-ENSINO FUNDAMENTAL",
    "CDP-ENSINO MÉDIO",
    "CDP- Multisseriada",
    "Projeto de Vida",
    "QuÃ­mica",
    "RedaÃ§Ã£o e Leitura",
    "Sociologia",
    "Tecnologia e Inovação",
    "Outra",
]

TURMAS_CDP = [
    "MULTISSERIADO 1Âº, 2Âº e 3Âº ano",
    "MULTISSERIADO 4Âº e 5Âº ano",
    "6º/7º E.F",
    "8º/9º E.F",
    "1º/2º/3º E.M",
]
TURMAS_CDP_MULTISSERIADA = TURMAS_CDP


def nomes_disciplinas() -> list[str]:
    return list(_DISCIPLINAS)


def obter_config(disciplina: str) -> DisciplinaConfig:
    nome = (disciplina or "Outra").strip() or "Outra"
    if nome == "CDP- Multisseriada":
        return DisciplinaConfig(nome=nome, modo=MODO_CDP, exige_pdf=False)
    if nome == "CDP - Ciclo I":
        return DisciplinaConfig(nome=nome, modo=MODO_CDP_FUNDAMENTAL, exige_pdf=False)
    return DisciplinaConfig(nome=nome)


def eh_cdp(nome: str) -> bool:
    return obter_config(nome).modo in {MODO_CDP, MODO_CDP_FUNDAMENTAL}


def eh_cdp_multisseriada(nome: str) -> bool:
    return obter_config(nome).modo == MODO_CDP


def eh_cdp_fundamental(nome: str) -> bool:
    return obter_config(nome).modo == MODO_CDP_FUNDAMENTAL


def eh_cdp_contextual(nome: str) -> bool:
    chave = (nome or "").strip().upper().replace(" ", "")
    return chave in {"CDP-ENSINOFUNDAMENTAL", "CDP-ENSINOMEDIO", "CDP-ENSINOMÉDIO"}

