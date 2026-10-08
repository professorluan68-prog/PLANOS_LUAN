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
COMPONENTES_CURRICULARES_CDP_CICLO_I = [
    "ANOS INICIAIS 4º e 5º ANO- EJA TURMA D",
    "ANOS INICIAIS 1º, 2º e 3º ANO- EJA TURMA C",
]


@dataclass(frozen=True)
class DisciplinaConfig:
    nome: str
    modo: str = MODO_PDF
    exige_pdf: bool = True
    habilitado: bool = True
    aprendizagem_padrao: str = (
        "Desenvolver habilidades relacionadas ao tema da aula, participando das "
        "atividades propostas e registrando as principais aprendizagens."
    )


DISCIPLINAS_CDP_PADRONIZADAS = [
    "HISTÓRIA - CDP - EJA - MULTISSERIADO",
    "CIÊNCIAS - CDP - EJA - MULTISSERIADO",
    "MATEMÁTICA - CDP - EJA - MULTISSERIADO",
    "GEOGRAFIA - CDP - EJA - MULTISSERIADO",
    "SOCIOLOGIA - CDP - EJA - MULTISSERIADO",
    "LIDERANÇA E ORATÓRIA - CDP - EJA - MULTISSERIADO",
    "LÍNGUA PORTUGUESA - CDP - EJA - MULTISSERIADO",
    "ARTE - CDP - EJA - MULTISSERIADO",
]

_DISCIPLINAS = [
    "Arte",
    "Arte e Mídias Digitais",
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
    "Orientação de Estudos Matemática",
    "Projeto de Vida",
    "Química",
    "Química-EJA",
    "Redação e Leitura",
    "Robótica",
    "Sociologia",
    "Tecnologia e Inovação",
    *DISCIPLINAS_CDP_PADRONIZADAS,
    DISCIPLINA_CDP_CICLO_I,
    "Outra",
]

TURMAS_CDP = [
    "C",
    "H",
    "J",
    "E",
]
TURMAS_CDP_MULTISSERIADA = TURMAS_CDP


def _normalizar_nome_disciplina(nome: str) -> str:
    valor = unicodedata.normalize("NFKD", str(nome or "").strip().upper())
    valor = "".join(ch for ch in valor if not unicodedata.combining(ch))
    return " ".join(valor.split())


def nomes_disciplinas() -> list[str]:
    return [nome for nome in _DISCIPLINAS if obter_config(nome).habilitado]


def componentes_curriculares_por_disciplina(disciplina: str) -> list[str]:
    disc_norm = _normalizar_nome_disciplina(disciplina)
    if disc_norm == _normalizar_nome_disciplina(DISCIPLINA_CDP_CICLO_I):
        return list(COMPONENTES_CURRICULARES_CDP_CICLO_I)
    if any(disc_norm == _normalizar_nome_disciplina(d) for d in DISCIPLINAS_CDP_PADRONIZADAS) or (
        "CDP" in disc_norm and "MULTISSERIAD" in disc_norm
    ):
        return [disciplina]
    if "MATEMATICA" in disc_norm and "CDP" in disc_norm:
        return ["MATEMÁTICA - CDP - EJA - MULTISSERIADO"]
    return []


def obter_config(disciplina: str) -> DisciplinaConfig:
    nome = (disciplina or "Outra").strip() or "Outra"
    nome_normalizado = _normalizar_nome_disciplina(nome)

    if nome_normalizado == _normalizar_nome_disciplina(DISCIPLINA_CDP_MULTISSERIADA):
        return DisciplinaConfig(nome=nome, modo=MODO_CDP, exige_pdf=False)
    if nome_normalizado == _normalizar_nome_disciplina(DISCIPLINA_CDP_CICLO_I):
        return DisciplinaConfig(
            nome=nome,
            modo=MODO_CDP_FUNDAMENTAL,
            exige_pdf=False,
            habilitado=False,
        )
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
            or "CDP_EJA" in chave
            or "CDPEJA" in chave_compacta
            or chave_compacta.endswith("CDPEM")
            or chave_compacta.endswith("CDPEF")
            or chave_compacta.endswith("CDPEJA")
            or chave_compacta.endswith("_CDP")
            or chave_compacta.endswith("-CDP")
            or "MULTISSERIAD" in chave_compacta
            or "CIENCIAS" in chave_compacta
            or "MATEMATICA" in chave_compacta
        )
    )
